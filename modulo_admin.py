import tkinter as tk
import os
from tkinter import messagebox
from tkinter import ttk, filedialog
from datetime import datetime
import config


# ==========================================
# 1. GERENCIAR FEED DE NOTÍCIAS (SUPABASE)
# ==========================================
def mostrar_tela_gerenciar_feed(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela completa de gerenciamento do Feed de Notícias e Avisos do sistema via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=20, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="Avisos internos da oficina", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_form = tk.LabelFrame(frame_principal, text=" Publicar Novo Aviso no Feed ", font=("Arial", 9, "bold"), padx=12, pady=10)
    f_form.pack(fill="x", pady=(0, 12))

    tk.Label(f_form, text="Digite o Aviso ou Notícia:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 4))
    entry_aviso = tk.Entry(f_form, font=("Arial", 10), width=85)
    entry_aviso.pack(side="left", padx=(0, 10), pady=4)

    frame_tabela = tk.Frame(frame_principal)
    frame_tabela.pack(fill="both", expand=True, pady=(0, 10))

    colunas = ("ID", "Autor", "Aviso")
    tabela_feed = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=10)
    
    tabela_feed.heading("ID", text="Nº ID")
    tabela_feed.column("ID", width=60, anchor="center")
    tabela_feed.heading("Autor", text="Autor / Usuário")
    tabela_feed.column("Autor", width=150, anchor="center")
    tabela_feed.heading("Aviso", text="Conteúdo do Aviso")
    tabela_feed.column("Aviso", width=700, anchor="w")

    scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela_feed.yview)
    tabela_feed.configure(yscrollcommand=scrollbar.set)
    tabela_feed.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def carregar_avisos():
        for item in tabela_feed.get_children():
            tabela_feed.delete(item)
        
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, autor, aviso FROM feed_noticias ORDER BY id ASC;")
            resultados = cursor.fetchall()
            
            for row_id, autor, aviso in resultados:
                if aviso:
                    tabela_feed.insert("", "end", values=(row_id, autor or "admin", aviso))
            
            cursor.close()
            conn.close()
        except Exception as e:
            print("Erro ao carregar feed do Supabase:", e)

    carregar_avisos()

    def publicar_aviso():
        texto = entry_aviso.get().strip()
        if not texto:
            messagebox.showwarning("Atenção", "O texto do aviso não pode estar vazio!")
            return

        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados na nuvem.")
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO feed_noticias (autor, aviso) VALUES (%s, %s);",
                (config.usuario_logado, texto)
            )
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Aviso publicado no feed com sucesso!")
            entry_aviso.delete(0, tk.END)
            carregar_avisos()
            config.atualizar_feed_estoque_critico()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao publicar no banco: {e}")

    def excluir_aviso_selecionado():
        selecionado = tabela_feed.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um aviso na tabela para remover!")
            return

        if not messagebox.askyesno("Confirmar", "Deseja remover o aviso selecionado do feed?"):
            return

        vals = tabela_feed.item(selecionado[0], "values")
        id_registro = int(vals[0])

        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados na nuvem.")
            return

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feed_noticias WHERE id = %s;", (id_registro,))
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Aviso removido do feed!")
            carregar_avisos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir do banco: {e}")

    tk.Button(f_form, text="Publicar Aviso", command=publicar_aviso, bg="#38761D", fg="white", font=("Arial", 9, "bold"), width=16).pack(side="left", pady=4)

    f_botoes = tk.Frame(frame_principal)
    f_botoes.pack(fill="x", pady=(5, 5))
    tk.Button(f_botoes, text="Excluir Aviso Selecionado", command=excluir_aviso_selecionado, bg="#CC0000", fg="white", font=("Arial", 9, "bold"), width=25).pack(side="left")

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(10, 0))


# ==========================================
# 2. TELA DE CONFIGURAÇÕES DO SISTEMA (COM ALTERAÇÃO DE SENHA)
# ==========================================
def mostrar_tela_configuracoes(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela de Configurações gerais do sistema e alteração de senha unificadas"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, altura=config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=25, pady=20)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="Configurações do Sistema", font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))

    # --- Bloco de Preferências ---
    f_opcoes = tk.LabelFrame(frame_principal, text=" Preferências Gerais ", font=("Arial", 9, "bold"), padx=15, pady=10)
    f_opcoes.pack(fill="x", pady=(0, 10))

    var_modo_escuro = tk.BooleanVar(value=config.modo_escuro_ativo)

    def alterar_modo_visual():
        config.modo_escuro_ativo = var_modo_escuro.get()
        messagebox.showinfo("Configurações", "Preferência de tema alterada!", parent=janela_principal)

    chk_modo = tk.Checkbutton(f_opcoes, text="Ativar Modo Escuro (Dark Theme)", variable=var_modo_escuro, command=alterar_modo_visual, font=("Arial", 10))
    chk_modo.pack(anchor="w", pady=2)

    tk.Label(f_opcoes, text=f"Banco de Dados Ativo: Supabase PostgreSQL", font=("Arial", 9, "italic"), fg="gray").pack(anchor="w", pady=(6, 0))
    tk.Label(f_opcoes, text=f"Usuário Conectado: {config.usuario_logado}", font=("Arial", 9, "italic"), fg="gray").pack(anchor="w", pady=(2, 0))

    f_pastas = tk.LabelFrame(frame_principal, text=" Pastas de arquivos gerados ", font=("Arial", 9, "bold"), padx=12, pady=8)
    f_pastas.pack(fill="x", pady=(0, 12))
    campos_pastas = {
        'orcamentos': 'Orçamentos',
        'ordens_servico': 'Ordens de serviço',
        'ordens_compra': 'Ordens de compra',
        'relatorios': 'Relatórios'
    }
    variaveis_pastas = {}

    def selecionar_pasta(tipo, variavel):
        pasta = filedialog.askdirectory(initialdir=variavel.get(), title=f"Escolher pasta para {campos_pastas[tipo]}", parent=janela_principal)
        if pasta:
            variavel.set(os.path.normpath(pasta))

    for tipo, titulo in campos_pastas.items():
        linha_pasta = tk.Frame(f_pastas)
        linha_pasta.pack(fill="x", pady=2)
        tk.Label(linha_pasta, text=f"{titulo}:", width=22, anchor="w", font=("Arial", 9)).pack(side="left")
        variavel = tk.StringVar(value=config.obter_pasta_saida(tipo))
        variaveis_pastas[tipo] = variavel
        tk.Entry(linha_pasta, textvariable=variavel, font=("Arial", 9), state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 6))
        tk.Button(linha_pasta, text="Escolher...", command=lambda t=tipo, v=variavel: selecionar_pasta(t, v), bg="#1F4E79", fg="white", font=("Arial", 8, "bold")).pack(side="right")

    def salvar_pastas_arquivos():
        try:
            config.salvar_pastas_saida({tipo: variavel.get() for tipo, variavel in variaveis_pastas.items()})
            messagebox.showinfo("Configurações", "Pastas de arquivos salvas com sucesso.", parent=janela_principal)
        except Exception as erro:
            messagebox.showerror("Erro", f"Não foi possível salvar as pastas: {erro}", parent=janela_principal)

    tk.Button(f_pastas, text="Salvar pastas de arquivos", command=salvar_pastas_arquivos, bg="#38761D", fg="white", font=("Arial", 9, "bold")).pack(anchor="e", pady=(6, 0))

    # --- Bloco de Alteração de Senha ---
    f_senha = tk.LabelFrame(frame_principal, text=" Segurança: Alterar Senha do Usuário ", font=("Arial", 9, "bold"), padx=15, pady=10)
    f_senha.pack(fill="x", pady=(0, 15))

    f_campos_s = tk.Frame(f_senha)
    f_campos_s.pack(fill="x")

    tk.Label(f_campos_s, text="Senha Atual:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=3)
    entry_s_atual = tk.Entry(f_campos_s, font=("Arial", 9), width=25, show="*")
    entry_s_atual.grid(row=0, column=1, sticky="w", padx=10, pady=3)

    tk.Label(f_campos_s, text="Nova Senha:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=3)
    entry_s_nova = tk.Entry(f_campos_s, font=("Arial", 9), width=25, show="*")
    entry_s_nova.grid(row=1, column=1, sticky="w", padx=10, pady=3)

    tk.Label(f_campos_s, text="Confirmar Nova:", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=3)
    entry_s_conf = tk.Entry(f_campos_s, font=("Arial", 9), width=25, show="*")
    entry_s_conf.grid(row=2, column=1, sticky="w", padx=10, pady=3)

    def processar_alteracao_senha():
        """Confere a senha atual e grava a nova senha em formato hash.

        Esta callback é acionada pelo botão de configurações. A verificação e a
        geração do hash são centralizadas em `config.py`, para que o login e a
        troca de senha usem exatamente o mesmo formato persistido no banco.
        """
        s_atual = entry_s_atual.get().strip()
        s_nova = entry_s_nova.get().strip()
        s_conf = entry_s_conf.get().strip()

        if not s_atual or not s_nova or not s_conf:
            messagebox.showwarning("Atenção", "Preencha todos os campos de senha!", parent=janela_principal)
            return

        if s_nova != s_conf:
            messagebox.showerror("Erro", "A nova senha e a confirmação não coincidem!", parent=janela_principal)
            return

        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco na nuvem.", parent=janela_principal)
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT senha FROM usuarios WHERE username = {config.PLACEHOLDER_SQL};",
                (config.usuario_logado,)
            )
            res = cursor.fetchone()

            if not res or not config.verificar_senha(res[0], s_atual):
                messagebox.showerror("Erro", "A senha atual informada está incorreta!", parent=janela_principal)
                cursor.close()
                conn.close()
                return

            cursor.execute(
                f"UPDATE usuarios SET senha = {config.PLACEHOLDER_SQL} WHERE username = {config.PLACEHOLDER_SQL};",
                (config.gerar_hash_senha(s_nova), config.usuario_logado)
            )
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Senha alterada com sucesso na nuvem!", parent=janela_principal)
            entry_s_atual.delete(0, tk.END)
            entry_s_nova.delete(0, tk.END)
            entry_s_conf.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar senha: {e}", parent=janela_principal)

    tk.Button(f_senha, text="Atualizar Senha", command=processar_alteracao_senha, bg="#1F4E79", fg="white", font=("Arial", 9, "bold"), width=18).pack(anchor="e", pady=(5, 0))

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x")