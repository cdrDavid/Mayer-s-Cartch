import os
import sys
import sqlite3
import json
import hashlib
import hmac
import secrets

try:
    import psycopg2
except ImportError:
    psycopg2 = None

# Descobre se o código está rodando como executável compilado ou como script normal
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Carrega a configuração local sem exibir valores sensíveis.
def carregar_configuracao_local():
    caminho_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(caminho_env):
        return

    with open(caminho_env, 'r', encoding='utf-8') as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha or linha.startswith('#') or '=' not in linha:
                continue
            chave, valor = linha.split('=', 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


carregar_configuracao_local()

# Configurações globais do sistema
LARGURA_PADRAO = 1280
ALTURA_PADRAO = 720
usuario_logado = None
usuario_id_logado = None
usuario_nivel_logado = None
modo_escuro_ativo = False
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
PLACEHOLDER_SQL = '%s' if DATABASE_URL else '?'

# Nome do arquivo do banco de dados local SQLite
NOME_BANCO = os.path.join(base_path, 'sistema.db')
NOME_ARQUIVO = os.path.join(base_path, 'dados_sistema.xlsx')

PASTA_DADOS_USUARIO = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'MayersCartchOficina')
ARQUIVO_PREFERENCIAS = os.path.join(PASTA_DADOS_USUARIO, 'preferencias.json')
PASTAS_SAIDA_PADRAO = {
    'orcamentos': os.path.join(PASTA_DADOS_USUARIO, 'Orcamentos'),
    'ordens_servico': os.path.join(PASTA_DADOS_USUARIO, 'OrdensServico'),
    'ordens_compra': os.path.join(PASTA_DADOS_USUARIO, 'OrdensCompra'),
    'relatorios': os.path.join(PASTA_DADOS_USUARIO, 'Relatorios')
}


def carregar_preferencias_arquivos():
    preferencias = dict(PASTAS_SAIDA_PADRAO)
    try:
        with open(ARQUIVO_PREFERENCIAS, 'r', encoding='utf-8') as arquivo:
            preferencias.update(json.load(arquivo))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    for pasta in preferencias.values():
        os.makedirs(pasta, exist_ok=True)
    return preferencias


PASTAS_SAIDA = carregar_preferencias_arquivos()


def salvar_pastas_saida(preferencias):
    global PASTAS_SAIDA
    PASTAS_SAIDA = dict(preferencias)
    os.makedirs(PASTA_DADOS_USUARIO, exist_ok=True)
    for pasta in PASTAS_SAIDA.values():
        os.makedirs(pasta, exist_ok=True)
    with open(ARQUIVO_PREFERENCIAS, 'w', encoding='utf-8') as arquivo:
        json.dump(PASTAS_SAIDA, arquivo, ensure_ascii=False, indent=2)


def obter_pasta_saida(tipo):
    pasta = PASTAS_SAIDA.get(tipo, PASTA_DADOS_USUARIO)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def obter_conexao_banco():
    """Abre o banco usado pelo aplicativo.

    `DATABASE_URL` vem do `.env`: com ela, o app conecta ao PostgreSQL/Supabase;
    sem ela, usa o arquivo SQLite em `NOME_BANCO`. `PLACEHOLDER_SQL` acompanha
    essa escolha e é consumido por consultas parametrizadas de outros módulos.
    Em erro, retorna `None`, que as telas tratam como banco indisponível.
    """
    try:
        if DATABASE_URL:
            if psycopg2 is None:
                raise RuntimeError('O pacote psycopg2 não está instalado.')
            return psycopg2.connect(DATABASE_URL, connect_timeout=10)
        conexao = sqlite3.connect(NOME_BANCO)
        return conexao
    except Exception as e:
        print("Erro ao conectar com o banco de dados:", e)
        return None


def gerar_hash_senha(senha):
    """Deriva o valor que será persistido no campo `usuarios.senha`.

    PBKDF2-SHA256 aplica 600 mil iterações e um salt aleatório por senha. O
    formato salvo contém algoritmo, custo, salt e resultado; não há como obter
    a senha original a partir desse texto. Login e troca de senha chamam esta
    função para nunca gravarem a nova senha em texto puro.
    """
    salt = secrets.token_bytes(16)
    iteracoes = 600_000
    derivado = hashlib.pbkdf2_hmac('sha256', senha.encode('utf-8'), salt, iteracoes)
    return f"pbkdf2_sha256${iteracoes}${salt.hex()}${derivado.hex()}"


def verificar_senha(senha_armazenada, senha_informada):
    """Compara a senha digitada com o valor persistido em `usuarios.senha`.

    Para hashes PBKDF2, recalcula o derivado usando o salt guardado e compara
    em tempo constante. A comparação direta existe apenas para autenticar contas
    antigas durante a migração; `main.py:fazer_login` converte a senha legada em
    hash logo após um login válido.
    """
    if not senha_armazenada:
        return False
    if not str(senha_armazenada).startswith('pbkdf2_sha256$'):
        return hmac.compare_digest(str(senha_armazenada), senha_informada)
    try:
        algoritmo, iteracoes, salt_hex, esperado = str(senha_armazenada).split('$', 3)
        if algoritmo != 'pbkdf2_sha256':
            return False
        derivado = hashlib.pbkdf2_hmac(
            'sha256', senha_informada.encode('utf-8'), bytes.fromhex(salt_hex), int(iteracoes)
        ).hex()
        return hmac.compare_digest(derivado, esperado)
    except (TypeError, ValueError):
        return False


def senha_usa_hash(senha_armazenada):
    """Identifica o formato para o login decidir se precisa migrar a senha.

    A função não autentica por conta própria: ela complementa
    `verificar_senha` no callback de login em `main.py`.
    """
    return bool(senha_armazenada and str(senha_armazenada).startswith('pbkdf2_sha256$'))


def inicializar_banco_postgres():
    """Cria e atualiza o esquema PostgreSQL usado pelos módulos do sistema.

    É acionada por `realizar_backup_automatico` na inicialização de `main.py`.
    Além das tabelas operacionais, cria os registros LGPD e acrescenta colunas
    de consentimento, nível de usuário e código de cliente em ordens existentes.
    """
    conn = obter_conexao_banco()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                nivel TEXT DEFAULT 'operador'
            );
            CREATE TABLE IF NOT EXISTS feed_noticias (
                id SERIAL PRIMARY KEY,
                autor TEXT,
                aviso TEXT
            );
            CREATE TABLE IF NOT EXISTS estoque (
                id SERIAL PRIMARY KEY,
                cod TEXT UNIQUE,
                tipo TEXT,
                total INTEGER DEFAULT 0,
                disponivel INTEGER DEFAULT 0,
                fornecedor TEXT,
                valor_unitario DOUBLE PRECISION
            );
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                codigo TEXT UNIQUE,
                nome TEXT,
                tipo TEXT,
                documento TEXT,
                cep TEXT,
                rua TEXT,
                numero TEXT,
                bairro TEXT,
                cidade TEXT,
                contato TEXT,
                email TEXT,
                modelo_central TEXT,
                modulo TEXT,
                mac_address TEXT,
                operadora TEXT,
                linha_numero TEXT,
                iccid TEXT,
                data_atualizacao TEXT,
                consentimento_email BOOLEAN DEFAULT FALSE,
                consentimento_whatsapp BOOLEAN DEFAULT FALSE,
                consentimento_atualizado_em TEXT
            );
            CREATE TABLE IF NOT EXISTS tecnicos (
                id SERIAL PRIMARY KEY,
                codigo TEXT UNIQUE,
                nome TEXT,
                tipo TEXT,
                documento TEXT,
                endereco TEXT,
                cep TEXT,
                rua TEXT,
                numero TEXT,
                bairro TEXT,
                cidade TEXT,
                contato TEXT,
                email TEXT
            );
            CREATE TABLE IF NOT EXISTS entrada (
                id SERIAL PRIMARY KEY,
                data TEXT,
                fornecedor_descricao TEXT,
                nome_item TEXT,
                quantidade INTEGER,
                usuario TEXT,
                status TEXT
            );
            CREATE TABLE IF NOT EXISTS uso (
                id SERIAL PRIMARY KEY,
                data TEXT,
                codigo_cliente TEXT,
                local_setor TEXT,
                nome_equipamento TEXT,
                quantidade_usada INTEGER,
                observacao TEXT,
                usuario TEXT,
                status TEXT,
                descricao_servico TEXT
            );
            CREATE TABLE IF NOT EXISTS orcamentos (
                id SERIAL PRIMARY KEY,
                numero_os TEXT UNIQUE NOT NULL,
                codigo_cliente TEXT,
                data TEXT,
                dados_cliente JSONB,
                itens JSONB,
                descricao TEXT,
                valor_mao_obra DOUBLE PRECISION DEFAULT 0,
                status TEXT DEFAULT 'Orçamento',
                usuario TEXT
            );
            CREATE TABLE IF NOT EXISTS atualizacoes (
                id SERIAL PRIMARY KEY,
                data TEXT,
                num_conta TEXT,
                descricao_log TEXT,
                item TEXT,
                quantidade TEXT,
                usuario TEXT
            );
            INSERT INTO usuarios (username, senha)
            VALUES ('admin', 'admin')
            ON CONFLICT (username) DO NOTHING;
            ALTER TABLE tecnicos ADD COLUMN IF NOT EXISTS cep TEXT;
            ALTER TABLE tecnicos ADD COLUMN IF NOT EXISTS rua TEXT;
            ALTER TABLE tecnicos ADD COLUMN IF NOT EXISTS numero TEXT;
            ALTER TABLE tecnicos ADD COLUMN IF NOT EXISTS bairro TEXT;
            ALTER TABLE tecnicos ADD COLUMN IF NOT EXISTS cidade TEXT;
            ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nivel TEXT DEFAULT 'operador';
            ALTER TABLE clientes ADD COLUMN IF NOT EXISTS consentimento_email BOOLEAN DEFAULT FALSE;
            ALTER TABLE clientes ADD COLUMN IF NOT EXISTS consentimento_whatsapp BOOLEAN DEFAULT FALSE;
            ALTER TABLE clientes ADD COLUMN IF NOT EXISTS consentimento_atualizado_em TEXT;
            ALTER TABLE uso ADD COLUMN IF NOT EXISTS codigo_cliente TEXT;
            CREATE TABLE IF NOT EXISTS termos_aceites_log (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                data_hora TEXT NOT NULL,
                versao_termo TEXT NOT NULL,
                endereco_ip TEXT
            );
            CREATE TABLE IF NOT EXISTS lgpd_eventos (
                id SERIAL PRIMARY KEY,
                codigo_cliente TEXT,
                acao TEXT NOT NULL,
                usuario TEXT,
                data_hora TEXT NOT NULL
            );
        """)
        cursor.execute("UPDATE usuarios SET nivel = 'admin' WHERE username = 'admin';")
        cursor.execute(
            "UPDATE usuarios SET senha = %s WHERE username = 'admin' AND senha = 'admin';",
            (gerar_hash_senha('admin'),)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        conn.rollback()
        conn.close()
        print("Erro ao inicializar as tabelas do Supabase:", e)


def inicializar_banco_local():
    """Cria e migra o arquivo SQLite sem descartar os dados que ele já contém.

    Esta é a versão local de `inicializar_banco_postgres`. As verificações de
    `PRAGMA table_info` fazem migração incremental: só adicionam colunas que
    faltam. O login, cadastro, OS e painel LGPD dependem dessas tabelas/colunas.
    """
    conn = obter_conexao_banco()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        
        # Tabela de Usuários (com admin padrão se não existir)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                senha TEXT,
                nivel TEXT DEFAULT 'operador'
            );
        """)
        colunas_usuarios = {linha[1] for linha in cursor.execute("PRAGMA table_info(usuarios);").fetchall()}
        if 'nivel' not in colunas_usuarios:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN nivel TEXT DEFAULT 'operador';")
        cursor.execute(
            "INSERT OR IGNORE INTO usuarios (username, senha, nivel) VALUES (?, ?, 'admin');",
            ('admin', gerar_hash_senha('admin'))
        )
        cursor.execute("UPDATE usuarios SET nivel = 'admin' WHERE username = 'admin';")

        # Tabela de Feed / Notícias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feed_noticias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                autor TEXT,
                aviso TEXT
            );
        """)

        # Tabela de Estoque / Produtos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estoque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cod TEXT UNIQUE,
                tipo TEXT,
                total INTEGER,
                disponivel INTEGER,
                fornecedor TEXT,
                valor_unitario REAL
            );
        """)

        # Tabela de Clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nome TEXT,
                tipo TEXT,
                documento TEXT,
                cep TEXT,
                rua TEXT,
                numero TEXT,
                bairro TEXT,
                cidade TEXT,
                contato TEXT,
                email TEXT,
                modelo_central TEXT,
                modulo TEXT,
                mac_address TEXT,
                operadora TEXT,
                linha_numero TEXT,
                iccid TEXT,
                data_atualizacao TEXT,
                consentimento_email INTEGER DEFAULT 0,
                consentimento_whatsapp INTEGER DEFAULT 0,
                consentimento_atualizado_em TEXT
            );
        """)
        colunas_clientes = {linha[1] for linha in cursor.execute("PRAGMA table_info(clientes);").fetchall()}
        # Esses campos registram os opt-ins independentes exibidos no cadastro.
        for coluna, definicao in (
            ('consentimento_email', 'INTEGER DEFAULT 0'),
            ('consentimento_whatsapp', 'INTEGER DEFAULT 0'),
            ('consentimento_atualizado_em', 'TEXT')
        ):
            if coluna not in colunas_clientes:
                cursor.execute(f"ALTER TABLE clientes ADD COLUMN {coluna} {definicao};")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS termos_aceites_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                data_hora TEXT NOT NULL,
                versao_termo TEXT NOT NULL,
                endereco_ip TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lgpd_eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_cliente TEXT,
                acao TEXT NOT NULL,
                usuario TEXT,
                data_hora TEXT NOT NULL
            );
        """)

        # Tabela de Técnicos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tecnicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nome TEXT,
                tipo TEXT,
                documento TEXT,
                endereco TEXT,
                contato TEXT,
                email TEXT
            );
        """)

        # Tabela de Entradas (Ordens de Compra)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entrada (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                fornecedor_descricao TEXT,
                nome_item TEXT,
                quantidade INTEGER,
                usuario TEXT,
                status TEXT
            );
        """)

        # Tabela de Uso / Saídas (Ordens de Serviço)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                codigo_cliente TEXT,
                local_setor TEXT,
                nome_equipamento TEXT,
                quantidade_usada INTEGER,
                observacao TEXT,
                usuario TEXT,
                status TEXT,
                descricao_servico TEXT
            );
        """)
        colunas_uso = {linha[1] for linha in cursor.execute("PRAGMA table_info(uso);").fetchall()}
        if 'codigo_cliente' not in colunas_uso:
            # Permite ao painel LGPD localizar/anonimizar cada OS sem depender do nome.
            cursor.execute("ALTER TABLE uso ADD COLUMN codigo_cliente TEXT;")

        # Tabela de Atualizações / Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atualizacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                num_conta TEXT,
                descricao_log TEXT,
                item TEXT,
                quantidade TEXT,
                usuario TEXT
            );
        """)
        for coluna in ["cep", "rua", "numero", "bairro", "cidade"]:
            try:
                cursor.execute(f"ALTER TABLE tecnicos ADD COLUMN {coluna} TEXT;")
            except sqlite3.OperationalError:
                pass
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orcamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_os TEXT UNIQUE NOT NULL,
                codigo_cliente TEXT,
                data TEXT,
                dados_cliente TEXT,
                itens TEXT,
                descricao TEXT,
                valor_mao_obra REAL DEFAULT 0,
                status TEXT DEFAULT 'Orçamento',
                usuario TEXT
            );
        """)

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Erro ao inicializar as tabelas do banco local:", e)


def realizar_backup_automatico():
    """Seleciona a migração do banco correta durante a inicialização do app.

    Apesar do nome histórico, esta função prepara o esquema; o backup de dados
    é tratado em outro fluxo. `main.py` chama esta função antes de mostrar login.
    """
    if DATABASE_URL:
        inicializar_banco_postgres()
    else:
        inicializar_banco_local()


def atualizar_feed_estoque_critico():
    """Verifica o estoque inteligentemente no SQLite"""
    conn = obter_conexao_banco()
    if not conn:
        return

    try:
        cursor = conn.cursor()
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

        alertas_atuais_textos = [a[1] for a in avisos_mantidos]

        for esq in itens_esgotados:
            msg_esq = f"[sistema] ESGOTADO: O produto '{esq}' não possui mais estoque disponível!"
            if not any(esq.lower() in t.lower() and "esgotado" in t.lower() for t in alertas_atuais_textos):
                avisos_mantidos.append(("sistema", msg_esq))

        for crit, qtd in itens_criticos:
            msg_crit = f"[sistema] ATENÇÃO: O produto '{crit}' está com estoque crítico ({qtd} unidades disponíveis)."
            if not any(crit.lower() in t.lower() and "crítico" in t.lower() for t in alertas_atuais_textos):
                avisos_mantidos.append(("sistema", msg_crit))

        cursor.execute("DELETE FROM feed_noticias;")
        for aut, av in avisos_mantidos:
            cursor.execute("INSERT INTO feed_noticias (autor, aviso) VALUES (%s, %s);", (aut, av))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Erro ao atualizar feed inteligente no banco local:", e)