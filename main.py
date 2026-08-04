import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import modulo_nfe
import config
import modulo_operacoes
import modulo_financeiro
import modulo_relatorios
import modulo_admin

def limpar_tela(janela):
    for widget in janela.winfo_children():
        widget.destroy()

def centralizar_janela(janela, largura, altura):
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

# ==========================================
# TELA DE LOGIN
# ==========================================
def mostrar_tela_login():
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, 450, 380)
    
    bg_cor = "#222222" if config.modo_escuro_ativo else "#F0F0F0"
    fg_cor = "white" if config.modo_escuro_ativo else "black"

    frame_login = tk.Frame(janela_principal, padx=35, pady=30, bg=bg_cor)
    frame_login.place(relx=0.5, rely=0.5, anchor="center", width=420)

    tk.Label(frame_login, text="🔐 Login do Sistema", font=("Arial", 17, "bold"), bg=bg_cor, fg=fg_cor).pack(pady=(0, 20))
    tk.Label(frame_login, text="Usuário:", font=("Arial", 11), bg=bg_cor, fg=fg_cor).pack(anchor="w")
    entry_user = tk.Entry(frame_login, font=("Arial", 11), width=30)
    entry_user.pack(pady=(0, 12), anchor="w", fill="x")
    entry_user.insert(0, "")

    tk.Label(frame_login, text="Senha:", font=("Arial", 11), bg=bg_cor, fg=fg_cor).pack(anchor="w")
    entry_pass = tk.Entry(frame_login, font=("Arial", 11), width=30, show="*")
    entry_pass.pack(pady=(0, 22), anchor="w", fill="x")

    def fazer_login():
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
            cursor.execute("SELECT senha FROM usuarios WHERE username = %s;", (usuario,))
            res = cursor.fetchone()
            cursor.close()
            conn.close()

            if res and res[0] == senha:
                config.usuario_logado = usuario
                config.atualizar_feed_estoque_critico()
                mostrar_menu_principal()
            else:
                messagebox.showerror("Erro de Acesso", "Usuário ou senha incorretos!", parent=janela_principal)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao validar login no banco: {e}", parent=janela_principal)

    tk.Button(frame_login, text="Entrar", command=fazer_login, bg="#2F5597", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", pady=(0, 8))

# ==========================================
# MENU PRINCIPAL (COM ABAS E LETREIRO - SUPABASE)
# ==========================================
def mostrar_menu_principal(aba_selecionada_indice=0):
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    cor_fundo_geral = "#1E1E1E" if config.modo_escuro_ativo else "#F0F0F0"
    janela_principal.configure(bg=cor_fundo_geral)

    # --- BARRA DE FEED COM LETREIRO NO TOPO ---
    frame_feed = tk.Frame(janela_principal, bg="#112233", height=38)
    frame_feed.pack(side="top", fill="x")
    frame_feed.pack_propagate(False)

    tk.Label(frame_feed, text="📢 FEED:", bg="#112233", fg="#FFD966", font=("Arial", 10, "bold")).pack(side="left", padx=(12, 6))
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
        avisos = ["[sistema]: Nenhum aviso cadastrado."]

    estado_ticker = {"indice_atual": 0, "pos_x": 950, "texto_ativo": avisos[0]}
    texto_item_id = canvas_ticker.create_text(950, 19, text=estado_ticker["texto_ativo"], fill="#00FFCC", font=("Arial", 10, "bold"), anchor="w")

    def animar_letreiro():
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
    tk.Label(f_topo_menu, text=f"👤 Logado como: {config.usuario_logado}", font=("Arial", 10, "italic"), bg=cor_fundo_geral, fg="gray").pack(side="left")
    tk.Button(f_topo_menu, text="❌ Sair", command=mostrar_tela_login, bg="#CC0000", fg="white", font=("Arial", 9, "bold")).pack(side="right")

    # --- SISTEMA DE ABAS ---
    notebook = ttk.Notebook(janela_principal)
    notebook.pack(fill="both", expand=True, padx=15, pady=15)

    # 0. ABA DE EMISSÃO NF-E (Índice 0)
    tab_nf = ttk.Frame(notebook)
    notebook.add(tab_nf, text="  📄 Emissão NF-E  ")
    f_adm = tk.Frame(tab_nf, padx=40, pady=20)
    f_adm.place(relx=0.5, rely=0.5, anchor="center")

    tk.Button(f_adm, text="📄 Emitir Nota Fiscal Eletrônica", command=lambda: modulo_nfe.mostrar_tela_emissao_nfe(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(0)), bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    # 1. ABA DE GESTÃO DE EQUIPAMENTOS (Índice 1)
    tab_op = ttk.Frame(notebook)
    notebook.add(tab_op, text="  📦 Gestão de Equipamentos  ")
    f_op = tk.Frame(tab_op, padx=40, pady=20)
    f_op.place(relx=0.5, rely=0.5, anchor="center")

    tk.Button(f_op, text="📦 Armazém (Visão Geral do Estoque)", command=lambda: modulo_operacoes.mostrar_tela_armazem(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(1)), bg="#134F5C", fg="white", font=("Arial", 10, "bold"), height=2, width=42).pack(pady=(0, 6))
    tk.Button(f_op, text="📥 Registrar Entrada / Ordem de Compra", command=lambda: modulo_operacoes.mostrar_tela_entrada(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(1)), bg="#38761D", fg="white", font=("Arial", 10, "bold"), height=2, width=42).pack(pady=(0, 6))
    tk.Button(f_op, text="📤 Registrar Saída de Equipamento", command=lambda: modulo_operacoes.mostrar_tela_saida(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(1)), bg="#2F5597", fg="white", font=("Arial", 10, "bold"), height=2, width=42).pack(pady=(0, 6))
    tk.Button(f_op, text="🔄 Estornar Saída", command=lambda: modulo_operacoes.mostrar_tela_estorno(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(1)), bg="#1F4E79", fg="white", font=("Arial", 10, "bold"), height=2, width=42).pack()
    
    # 2. ABA CADASTROS (Índice 2)
    tab_fin = ttk.Frame(notebook)
    notebook.add(tab_fin, text="  📝 Cadastros  ")
    f_fin = tk.Frame(tab_fin, padx=40, pady=20)
    f_fin.place(relx=0.5, rely=0.5, anchor="center")
    
    tk.Button(f_fin, text="📦 Cadastro Central de Equipamentos", command=lambda: modulo_financeiro.mostrar_tela_fornecedores(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(2)), bg="#134F5C", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    tk.Button(f_fin, text="👥 Cadastro Central de Clientes", command=lambda: modulo_financeiro.mostrar_tela_clientes(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(2)), bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    tk.Button(f_fin, text="👨‍🔧 Cadastro Central de Técnicos", command=lambda: modulo_financeiro.mostrar_tela_tecnicos(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(2)), bg="#375623", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    # 3. ABA RELATÓRIOS & DASHBOARD (Índice 3)
    tab_rel = ttk.Frame(notebook)
    notebook.add(tab_rel, text="  📊 Relatórios & Dashboard  ")
    f_rel = tk.Frame(tab_rel, padx=40, pady=15)
    f_rel.place(relx=0.5, rely=0.5, anchor="center")
    
    tk.Button(f_rel, text="📊 Histórico Movimentações", command=lambda: modulo_financeiro.mostrar_tela_historico_movimentacoes(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(3)), bg="#1F4E79", fg="white", font=("Arial", 10, "bold"), height=2, width=45).pack(pady=(0, 6))
    tk.Button(f_rel, text="📈 Dashboard", command=lambda: modulo_relatorios.mostrar_tela_dashboard(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(3)), bg="#7030A0", fg="white", font=("Arial", 10, "bold"), height=2, width=45).pack(pady=(0, 6))
    tk.Button(f_rel, text="🔍 Gerar Relatório de Atendimentos", command=lambda: modulo_relatorios.mostrar_tela_previa_relatorio(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(3)), bg="#38761D", fg="white", font=("Arial", 10, "bold"), height=2, width=45).pack(pady=(0, 6))
    tk.Button(f_rel, text="💰 Indicadores Financeiros de Compras", command=lambda: modulo_relatorios.mostrar_tela_relatorio_financeiro(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(3)), bg="#274E13", fg="white", font=("Arial", 10, "bold"), height=2, width=45).pack()

    # 4. ABA ADMIN (Índice 4)
    tab_adm = ttk.Frame(notebook)
    notebook.add(tab_adm, text="  ⚙️ Administração & Feed  ")
    f_adm = tk.Frame(tab_adm, padx=40, pady=20)
    f_adm.place(relx=0.5, rely=0.5, anchor="center")
    
    tk.Button(f_adm, text="📢 Feed de Notícias", command=lambda: modulo_admin.mostrar_tela_gerenciar_feed(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(4)), bg="#333333", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    tk.Button(f_adm, text="⚙️ Configurações do Sistema", command=lambda: modulo_admin.mostrar_tela_configuracoes(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(4)), bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))
    tk.Button(f_adm, text="🔑 Alterar Senha", command=lambda: modulo_admin.mostrar_tela_alterar_senha(janela_principal, limpar_tela, centralizar_janela, lambda: mostrar_menu_principal(4)), bg="#38761D", fg="white", font=("Arial", 11, "bold"), height=2, width=45).pack(pady=(0, 10))

    # Seleciona e foca na aba correta ao retornar
    try:
        notebook.select(aba_selecionada_indice)
    except Exception:
        pass

# ==========================================
# INICIALIZAÇÃO
# ==========================================
janela_principal = tk.Tk()
janela_principal.title("Portland - Sistema de Gestão (Nuvem)")
janela_principal.resizable(False, False)

config.realizar_backup_automatico()
mostrar_tela_login()
janela_principal.mainloop()