import os
import sys
import psycopg2
from dotenv import load_dotenv

# Descobre se o código está rodando como executável compilado ou como script normal
if getattr(sys, 'frozen', False):
    # Se for executável, pega o caminho temporário onde o PyInstaller descompacta os arquivos
    base_path = sys._MEIPASS
else:
    # Se for no VS Code, pega a pasta atual do projeto
    base_path = os.path.dirname(os.path.abspath(__file__))

env_path = os.path.join(base_path, '.env')
load_dotenv(env_path)

# Configurações globais do sistema
LARGURA_PADRAO = 1280
ALTURA_PADRAO = 720
usuario_logado = None
modo_escuro_ativo = False

# Puxa a string de conexão completa
DATABASE_URL = os.getenv("DATABASE_URL")

def obter_conexao_banco():
    """Abre e retorna uma conexão ativa com o banco de dados PostgreSQL no Supabase via DATABASE_URL"""
    try:
        if not DATABASE_URL:
            print("Erro: A variável DATABASE_URL não foi encontrada no arquivo .env!")
            return None
            
        conexao = psycopg2.connect(DATABASE_URL)
        return conexao
    except Exception as e:
        print("Erro ao conectar com o banco de dados na nuvem:", e)
        return None

def realizar_backup_automatico():
    """Como os dados agora estão na nuvem com backups automáticos do Supabase, 
       mantemos a função para garantir compatibilidade com o sistema."""
    pass

def garantir_arquivo_existente():
    """Mantido por compatibilidade. As tabelas já foram criadas no Supabase."""
    pass

def atualizar_feed_estoque_critico():
    """Verifica o estoque inteligentemente no Supabase: 
       - Adiciona alertas para itens esgotados (0) ou críticos.
       - Remove automaticamente os alertas de itens que foram repostos e estão normais."""
    conn = obter_conexao_banco()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        
        # 1. Mapeia o estado atual do estoque do banco
        cursor.execute("SELECT tipo, disponivel FROM estoque;")
        resultados_estoque = cursor.fetchall()
        
        itens_esgotados = []
        itens_criticos = []
        
        for nome, disponivel in resultados_estoque:
            disp_int = int(disponivel or 0)
            if nome:
                if disp_int <= 0:
                    itens_esgotados.append(str(nome).strip())
                elif disp_int <= 2:
                    itens_criticos.append((str(nome).strip(), disp_int))

        # 2. Lê os avisos atuais da tabela feed_noticias
        cursor.execute("SELECT autor, aviso FROM feed_noticias;")
        avisos_atuais = cursor.fetchall()

        avisos_mantidos = []
        for autor, aviso in avisos_atuais:
            if aviso:
                if "[sistema] ATENÇÃO:" in str(aviso) or "[sistema] ESGOTADO:" in str(aviso):
                    resolvido = True
                    for esq in itens_esgotados:
                        if esq.lower() in str(aviso).lower():
                            resolvido = False
                            break
                    for crit, _ in itens_criticos:
                        if crit.lower() in str(aviso).lower():
                            resolvido = False
                            break
                    
                    if not resolvido:
                        avisos_mantidos.append((autor, aviso))
                else:
                    avisos_mantidos.append((autor, aviso))

        # 3. Adiciona novos alertas inteligentes
        alertas_atuais_textos = [a[1] for a in avisos_mantidos]

        for esq in itens_esgotados:
            msg_esq = f"[sistema] ESGOTADO: O produto '{esq}' não possui mais estoque disponível!"
            if not any(esq.lower() in t.lower() and "esgotado" in t.lower() for t in alertas_atuais_textos):
                avisos_mantidos.append(("sistema", msg_esq))

        for crit, qtd in itens_criticos:
            msg_crit = f"[sistema] ATENÇÃO: O produto '{crit}' está com estoque crítico ({qtd} unidades disponíveis)."
            if not any(crit.lower() in t.lower() and "crítico" in t.lower() for t in alertas_atuais_textos):
                avisos_mantidos.append(("sistema", msg_crit))

        # 4. Atualiza a tabela feed_noticias no banco
        cursor.execute("DELETE FROM feed_noticias;")
        for aut, av in avisos_mantidos:
            cursor.execute("INSERT INTO feed_noticias (autor, aviso) VALUES (%s, %s);", (aut, av))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Erro ao atualizar feed inteligente no banco:", e)