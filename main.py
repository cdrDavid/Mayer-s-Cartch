import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import modulo_nfe
import config
import modulo_operacoes
import modulo_financeiro
import modulo_relatorios
import modulo_admin
import modulo_lgpd


temporizador_sessao = None


def encerrar_sessao_por_inatividade():
    """Encerra a sessão quando o temporizador de inatividade vence.

    `registrar_atividade_usuario` agenda esta função com `after()`. Ela limpa
    as três variáveis globais de identidade/autorização em `config.py` e troca
    a interface atual pela tela de login, evitando deixar os dados abertos.
    """
    global temporizador_sessao
    temporizador_sessao = None
    config.usuario_logado = None
    config.usuario_id_logado = None
    config.usuario_nivel_logado = None
    mostrar_tela_login()
    messagebox.showinfo("Sessão encerrada", "Sua sessão foi encerrada após 15 minutos sem atividade.", parent=janela_principal)


def registrar_atividade_usuario(event=None):
    """Reinicia o prazo de sessão sempre que há ação de teclado ou mouse.

    Os eventos globais são registrados na inicialização do Tk. Sem usuário
    autenticado, não agenda nada; durante a sessão, cancela o prazo antigo e
    cria outro usando `PRAZO_SESSAO_MS` definido no módulo LGPD.
    """
    global temporizador_sessao
    if not config.usuario_logado:
        return
    if temporizador_sessao:
        janela_principal.after_cancel(temporizador_sessao)
    temporizador_sessao = janela_principal.after(modulo_lgpd.PRAZO_SESSAO_MS, encerrar_sessao_por_inatividade)


def fazer_logout():
    """Executa o logout manual e cancela o callback de timeout pendente.

    O botão "Sair" do menu chama esta função. As variáveis de usuário ficam
    em `config.py`, por isso são zeradas antes de redesenhar a tela de login.
    """
    global temporizador_sessao
    if temporizador_sessao:
        janela_principal.after_cancel(temporizador_sessao)
        temporizador_sessao = None
    config.usuario_logado = None
    config.usuario_id_logado = None
    config.usuario_nivel_logado = None
    mostrar_tela_login()


def solicitar_nova_senha_administrativa():
    """Troca a senha padrão do administrador antes de permitir o primeiro acesso.

    `fazer_login` chama esta janela quando a autenticação ocorreu com `admin/admin`.
    A senha digitada é convertida por `config.gerar_hash_senha` antes de atualizar
    `usuarios`; a função retorna `True` somente depois do commit no banco.
    """
    dialogo = tk.Toplevel(janela_principal)
    dialogo.title("Defina uma senha administrativa")
    dialogo.geometry("420x230")
    centralizar_janela(dialogo, 420, 230)
    dialogo.transient(janela_principal)
    dialogo.grab_set()
    resultado = {"salvou": False}
    tk.Label(dialogo, text="A senha padrão precisa ser substituída", font=("Arial", 12, "bold")).pack(pady=(18, 8))
    tk.Label(dialogo, text="Use pelo menos 12 caracteres.").pack()
    nova_senha = tk.Entry(dialogo, show="*", width=34)
    nova_senha.pack(pady=(10, 6))
    confirmar_senha = tk.Entry(dialogo, show="*", width=34)
    confirmar_senha.pack(pady=6)
    nova_senha.focus_set()

    def salvar_senha():
        """Valida os dois campos e persiste o hash da senha administrativa."""
        senha = nova_senha.get()
        confirmacao = confirmar_senha.get()
        if len(senha) < 12:
            messagebox.showwarning("Senha curta", "A senha deve ter pelo menos 12 caracteres.", parent=dialogo)
            return
        if senha != confirmacao:
            messagebox.showwarning("Confirmação diferente", "As senhas informadas não coincidem.", parent=dialogo)
            return
        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Banco indisponível", "Não foi possível salvar a nova senha.", parent=dialogo)
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE usuarios SET senha = {config.PLACEHOLDER_SQL} WHERE username = {config.PLACEHOLDER_SQL};",
                (config.gerar_hash_senha(senha), "admin")
            )
            conn.commit()
            cursor.close()
            conn.close()
            resultado["salvou"] = True
            dialogo.destroy()
        except Exception as erro:
            conn.rollback()
            conn.close()
            messagebox.showerror("Falha ao salvar", str(erro), parent=dialogo)

    botoes = tk.Frame(dialogo)
    botoes.pack(fill="x", padx=20, pady=12)
    tk.Button(botoes, text="Cancelar", command=dialogo.destroy).pack(side="left")
    tk.Button(botoes, text="Salvar senha", command=salvar_senha).pack(side="right")
    janela_principal.wait_window(dialogo)
    return resultado["salvou"]


def limpar_tela(janela):
    """Remove os widgets da tela atual antes de uma função construir a próxima."""
    for widget in janela.winfo_children():
        widget.destroy()


def centralizar_janela(janela, largura, altura):
    """Aplica tamanho e posição central a uma janela Tk/Toplevel."""
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")


def configurar_atalho_esc_global(janela):
    """Registra o ESC global para limpar seleções nas tabelas da interface."""
    def desmarcar_tabelas_global(event=None):
        """Percorre widgets filhos e remove seleção de cada Treeview encontrado."""
        def limpar_recursivo(widget):
            if isinstance(widget, ttk.Treeview):
                for item in widget.selection():
                    widget.selection_remove(item)
            for filho in widget.winfo_children():
                limpar_recursivo(filho)
                
        limpar_recursivo(janela)

    janela.bind_all("<Escape>", desmarcar_tabelas_global)


def configurar_atalho_enter_global(janela):
    """Faz Enter avançar o foco quando o controle atual é um campo de texto."""
    def avancar_tabelas_global(event=None):
        """Move o cursor para o próximo campo, sem interferir em outros widgets."""
        widget_focado = janela.focus_get()
        if isinstance(widget_focado, tk.Entry):
            widget_focado.tk_focusNext().focus()
    janela.bind_all("<Return>", avancar_tabelas_global)


# ==========================================
# TELA DE LOGIN
# ==========================================
def mostrar_tela_login():
    """Constrói o formulário que autentica o usuário contra `usuarios`."""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, 450, 380)
    
    bg_cor = "#222222" if config.modo_escuro_ativo else "#F0F0F0"
    fg_cor = "white" if config.modo_escuro_ativo else "black"

    frame_login = tk.Frame(janela_principal, padx=35, pady=30, bg=bg_cor)
    frame_login.place(relx=0.5, rely=0.5, anchor="center", width=420)

    tk.Label(frame_login, text="Login do Sistema", font=("Arial", 17, "bold"), bg=bg_cor, fg=fg_cor).pack(pady=(0, 20))
    tk.Label(frame_login, text="Usuário:", font=("Arial", 11), bg=bg_cor, fg=fg_cor).pack(anchor="w")
    entry_user = tk.Entry(frame_login, font=("Arial", 11), width=30)
    entry_user.pack(pady=(0, 12), anchor="w", fill="x")
    entry_user.insert(0, "")

    tk.Label(frame_login, text="Senha:", font=("Arial", 11), bg=bg_cor, fg=fg_cor).pack(anchor="w")
    entry_pass = tk.Entry(frame_login, font=("Arial", 11), width=30, show="*")
    entry_pass.pack(pady=(0, 22), anchor="w", fill="x")

    def fazer_login():
        """Valida credenciais, migra senha antiga e exige aceite antes do menu.

        Esta callback consulta `config.py`; em sucesso, a identidade é guardada
        nas variáveis globais de sessão. Em seguida, `modulo_lgpd` verifica os
        termos. Só com aceite a aplicação carrega avisos e chama o menu principal.
        """
        usuario = entry_user.get().strip()
        senha = entry_pass.get().strip()

        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Preencha o usuário e a senha!", parent=janela_principal)
            return

        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao banco de dados na nuvem.", parent=janela_principal)
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, senha, nivel FROM usuarios WHERE username = {config.PLACEHOLDER_SQL};",
                (usuario,)
            )
            res = cursor.fetchone()
            if res and config.verificar_senha(res[1], senha):
                if not config.senha_usa_hash(res[1]):
                    cursor.execute(
                        f"UPDATE usuarios SET senha = {config.PLACEHOLDER_SQL} WHERE id = {config.PLACEHOLDER_SQL};",
                        (config.gerar_hash_senha(senha), res[0])
                    )
                    conn.commit()
                cursor.close()
                conn.close()
                if usuario == "admin" and senha == "admin":
                    if not solicitar_nova_senha_administrativa():
                        mostrar_tela_login()
                        return
                config.usuario_id_logado = res[0]
                config.usuario_logado = usuario
                config.usuario_nivel_logado = res[2] or ("admin" if usuario == "admin" else "operador")
                if modulo_lgpd.exigir_aceite_termos(janela_principal, config.usuario_id_logado, usuario):
                    registrar_atividade_usuario()
                    config.atualizar_feed_estoque_critico()
                    mostrar_menu_principal()
                else:
                    config.usuario_logado = None
                    config.usuario_id_logado = None
                    config.usuario_nivel_logado = None
                    mostrar_tela_login()
            else:
                cursor.close()
                conn.close()
                messagebox.showerror("Erro de Acesso", "Usuário ou senha incorretos!", parent=janela_principal)
        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass
            messagebox.showerror("Erro", f"Erro ao validar login no banco: {e}", parent=janela_principal)

    tk.Button(frame_login, text="Entrar", command=fazer_login, bg="#2F5597", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", pady=(0, 8))

    def finalizar_aplicacao():
        janela_principal.destroy()

    tk.Button(frame_login, text="Sair", command=finalizar_aplicacao, bg="#CC0000", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", pady=(0, 8))


# ==========================================
# MENU PRINCIPAL (COM ABAS E LETREIRO - SUPABASE)
# ==========================================
def mostrar_menu_principal(aba_selecionada_indice=0):
    """Monta as abas principais e conecta cada comando ao módulo responsável.

    As telas auxiliares recebem callbacks que voltam para esta função e
    selecionam a aba adequada. A aba Privacidade/LGPD encaminha para
    `modulo_lgpd.mostrar_painel_lgpd`; o botão Sair usa `fazer_logout`.
    """
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    cor_fundo_geral = "#1E1E1E" if config.modo_escuro_ativo else "#F0F0F0"
    janela_principal.configure(bg=cor_fundo_geral)

    # --- BARRA DE FEED COM LETREIRO NO TOPO ---
    frame_feed = tk.Frame(janela_principal, bg="#112233", height=38)
    frame_feed.pack(side="top", fill="x")
    frame_feed.pack_propagate(False)

    tk.Label(frame_feed, text="AVISOS DA OFICINA:", bg="#112233", fg="#FFD966", font=("Arial", 10, "bold")).pack(side="left", padx=(12, 6))
    canvas_ticker = tk.Canvas(frame_feed, bg="#112233", highlightthickness=0, height=38)
    canvas_ticker.pack(side="left", fill="both", expand=True)

    avisos = []
    conn = config.obter_conexao_banco()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT autor, aviso FROM feed_noticias;")
            for aut, av in cursor.fetchall():
                if av: 
                    avisos.append(f"[{aut or 'admin'}]: {av}")
            cursor.close()
            conn.close()
        except:
            pass

    if not avisos: 
        avisos = [""]  # Nenhum aviso disponível

    estado_ticker = {"indice_atual": 0, "pos_x": 950, "texto_ativo": avisos[0]}
    texto_item_id = canvas_ticker.create_text(950, 19, text=estado_ticker["texto_ativo"], fill="#00FFCC", font=("Arial", 10, "bold"), anchor="w")

    def animar_letreiro():
        """Move os avisos do banco no Canvas e agenda a próxima animação."""
        try:
            if janela_principal.winfo_exists() and canvas_ticker.winfo_exists():
                estado_ticker["pos_x"] -= 2.5
                canvas_ticker.coords(texto_item_id, estado_ticker["pos_x"], 19)
                if estado_ticker["pos_x"] < -len(estado_ticker["texto_ativo"]) * 8.5:
                    estado_ticker["indice_atual"] = (estado_ticker["indice_atual"] + 1) % len(avisos)
                    estado_ticker["texto_ativo"] = avisos[estado_ticker["indice_atual"]]
                    canvas_ticker.itemconfig(texto_item_id, text=estado_ticker["texto_ativo"])
                    estado_ticker["pos_x"] = 980
                janela_principal.after(25, animar_letreiro)
        except Exception:
            pass
            
    animar_letreiro()

    # --- TOPO (USUÁRIO E LOGOUT) ---
    f_topo_menu = tk.Frame(janela_principal, bg=cor_fundo_geral)
    f_topo_menu.pack(fill="x", padx=20, pady=(8, 0))
    tk.Label(f_topo_menu, text=f"Logado como: {config.usuario_logado}", font=("Arial", 10, "italic"), bg=cor_fundo_geral, fg="gray").pack(side="left")
    tk.Button(f_topo_menu, text="Sair", command=fazer_logout, bg="#CC0000", fg="white", font=("Arial", 9, "bold")).pack(side="right")

    # --- SISTEMA DE ABAS ---
    notebook = ttk.Notebook(janela_principal)
    notebook.pack(fill="both", expand=True, padx=15, pady=15)

    '''# 0. ABA DE EMISSÃO NF-E (Índice 0)
    tab_nf = ttk.Frame(notebook)
    notebook.add(tab_nf, text="  Emissão NF-E  ")
    f_adm = tk.Frame(tab_nf, padx=40, pady=20)
    f_adm.place(relx=0.5, rely=0.5, anchor="center")

    tk.Button(f_adm, text="Emitir Nota Fiscal Eletrônica", command=lambda: modulo_nfe.mostrar_tela_emissao_nfe(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(0)), bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    '''
    # 1. ABA DE OPERAÇÕES DA OFICINA
    tab_op = ttk.Frame(notebook)
    notebook.add(tab_op, text="  Oficina  ")
    f_op = tk.Frame(tab_op, padx=40, pady=20)
    f_op.place(relx=0.5, rely=0.5, anchor="center")

    tk.Button(f_op, text="Estoque de Peças e Materiais", command=lambda: modulo_operacoes.mostrar_tela_armazem(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(0)), bg="#134F5C", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    tk.Button(f_op, text="Registrar compra e entrada de peças", command=lambda: modulo_operacoes.mostrar_tela_entrada(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(0)), bg="#38761D", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    
    tk.Button(f_op, text="Abrir ordem de serviço", command=lambda: modulo_operacoes.mostrar_tela_saida(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(0)), bg="#2F5597", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    tk.Button(f_op, text="Devoluções e estornos", command=lambda: modulo_operacoes.mostrar_tela_estorno(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(0)), bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    
    # 2. ABA CADASTROS (Índice 2)
    tab_fin = ttk.Frame(notebook)
    notebook.add(tab_fin, text="  Cadastros  ")
    f_fin = tk.Frame(tab_fin, padx=40, pady=20)
    f_fin.place(relx=0.5, rely=0.5, anchor="center")
    
    tk.Button(f_fin, text="Cadastro de peças e serviços", command=lambda: modulo_financeiro.mostrar_tela_fornecedores(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(1)), bg="#134F5C", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    tk.Button(f_fin, text="Clientes e veículos", command=lambda: modulo_financeiro.mostrar_tela_clientes(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(1)), bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    tk.Button(f_fin, text="Mecânicos e técnicos", command=lambda: modulo_financeiro.mostrar_tela_tecnicos(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(1)), bg="#375623", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    # 3. ABA RELATÓRIOS & DASHBOARD (Índice 3)
    tab_rel = ttk.Frame(notebook)
    notebook.add(tab_rel, text="  Gestão e relatórios  ")
    f_rel = tk.Frame(tab_rel, padx=40, pady=20) 
    f_rel.place(relx=0.5, rely=0.5, anchor="center")
    
    tk.Button(f_rel, text="Histórico de movimentações", command=lambda: modulo_financeiro.mostrar_tela_historico_movimentacoes(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(2)), bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    
    tk.Button(f_rel, text="Dashboard", command=lambda: modulo_relatorios.mostrar_tela_dashboard(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(2)), bg="#7030A0", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    tk.Button(f_rel, text="Relatório de serviços e ordens", command=lambda: modulo_relatorios.mostrar_tela_previa_relatorio(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(2)), bg="#38761D", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    tk.Button(f_rel, text="Custos de peças e serviços", command=lambda: modulo_relatorios.mostrar_tela_relatorio_financeiro(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(2)), bg="#274E13", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    # 4. ABA ADMIN (Índice 4)
    tab_adm = ttk.Frame(notebook)
    notebook.add(tab_adm, text="  Administração  ")
    f_adm = tk.Frame(tab_adm, padx=40, pady=20)
    f_adm.place(relx=0.5, rely=0.5, anchor="center")
    
    tk.Button(f_adm, text="Feed de Notícias", command=lambda: modulo_admin.mostrar_tela_gerenciar_feed(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(3)), bg="#333333", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    tk.Button(f_adm, text="Configurações do Sistema", command=lambda: modulo_admin.mostrar_tela_configuracoes(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(3)), bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    # 5. ABA PRIVACIDADE: busca e atendimento aos direitos dos titulares
    tab_lgpd = ttk.Frame(notebook)
    notebook.add(tab_lgpd, text="  Privacidade / LGPD  ")
    f_lgpd = tk.Frame(tab_lgpd, padx=40, pady=20)
    f_lgpd.place(relx=0.5, rely=0.5, anchor="center")
    tk.Button(
        f_lgpd, text="Abrir painel do titular", command=lambda: modulo_lgpd.mostrar_painel_lgpd(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(4)), bg="#8F8F8F", fg="white", font=("Arial", 11, "bold"), height=2, width=45
        ).pack(pady=(0, 10))
    
    # Seleciona e foca na aba correta ao retornar
    try:
        notebook.select(aba_selecionada_indice)
    except Exception:
        pass


# ==========================================
# INICIALIZAÇÃO
# ==========================================
janela_principal = tk.Tk()
janela_principal.title("Mayer's Cartch - Gestão de Oficina")
janela_principal.resizable(False, False)

# Ativa o atalho ESC universal em todas as tabelas do sistema
configurar_atalho_esc_global(janela_principal)
configurar_atalho_enter_global(janela_principal)
janela_principal.bind_all("<KeyPress>", registrar_atividade_usuario, add="+")
janela_principal.bind_all("<ButtonPress>", registrar_atividade_usuario, add="+")
janela_principal.bind_all("<MouseWheel>", registrar_atividade_usuario, add="+")

config.realizar_backup_automatico()
mostrar_tela_login()
janela_principal.mainloop()