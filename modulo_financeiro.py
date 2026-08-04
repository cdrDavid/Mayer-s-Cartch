import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
import config


# ==========================================
# TELA 1: HISTÓRICO DE MOVIMENTAÇÕES (SUPABASE)
# ==========================================
def mostrar_tela_historico_movimentacoes(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela Separada de Histórico Detalhado de Movimentações via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📊 Histórico de Movimentações (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_filtros = tk.LabelFrame(frame_principal, text=" Filtros de Pesquisa ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_filtros.pack(fill="x", pady=(0, 10))

    f_l_filtro = tk.Frame(f_filtros)
    f_l_filtro.pack(fill="x", pady=2)

    tk.Label(f_l_filtro, text="Tipo:", font=("Arial", 9)).pack(side="left", padx=(0, 2))
    combo_filtro_tipo = ttk.Combobox(f_l_filtro, values=["Todos", "Entrada", "Saída", "Atualização"], width=14, state="readonly")
    combo_filtro_tipo.set("Todos")
    combo_filtro_tipo.pack(side="left", padx=(0, 15))

    tk.Label(f_l_filtro, text="Busca Geral:", font=("Arial", 9)).pack(side="left", padx=(0, 2))
    entry_filtro_busca = tk.Entry(f_l_filtro, font=("Arial", 9), width=22)
    entry_filtro_busca.pack(side="left", padx=(0, 15))

    frame_tabela_mov = tk.Frame(frame_principal)
    frame_tabela_mov.pack(fill="both", expand=True, pady=(0, 10))

    colunas_mov = ("Tipo", "Data", "Nº Conta / Cliente", "Descrição do Log", "Item", "Quantidade", "Usuário")
    tabela_mov = ttk.Treeview(frame_tabela_mov, columns=colunas_mov, show="headings", height=13)
    
    for col, txt in zip(colunas_mov, colunas_mov):
        tabela_mov.heading(col, text=txt)
    
    tabela_mov.column("Tipo", width=100, minwidth=90, anchor="center", stretch=True)
    tabela_mov.column("Data", width=130, minwidth=120, anchor="center", stretch=True)
    tabela_mov.column("Nº Conta / Cliente", width=130, minwidth=110, anchor="center", stretch=True)
    tabela_mov.column("Descrição do Log", width=350, minwidth=200, anchor="w", stretch=True)
    tabela_mov.column("Item", width=140, minwidth=100, anchor="w", stretch=True)
    tabela_mov.column("Quantidade", width=80, minwidth=70, anchor="center", stretch=True)
    tabela_mov.column("Usuário", width=90, minwidth=80, anchor="center", stretch=True)

    scrollbar_mov_y = ttk.Scrollbar(frame_tabela_mov, orient="vertical", command=tabela_mov.yview)
    scrollbar_mov_x = ttk.Scrollbar(frame_tabela_mov, orient="horizontal", command=tabela_mov.xview)
    tabela_mov.configure(yscrollcommand=scrollbar_mov_y.set, xscrollcommand=scrollbar_mov_x.set)

    tabela_mov.grid(row=0, column=0, sticky="nsew")
    scrollbar_mov_y.grid(row=0, column=1, sticky="ns")
    scrollbar_mov_x.grid(row=1, column=0, sticky="ew")

    frame_tabela_mov.grid_rowconfigure(0, weight=1)
    frame_tabela_mov.grid_columnconfigure(0, weight=1)

    def carregar_movimentacoes(filtro_tipo="Todos", termo=""):
        for i in tabela_mov.get_children():
            tabela_mov.delete(i)
        
        registros_lidos = []
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # 1. Entradas
            if filtro_tipo in ["Todos", "Entrada"]:
                cursor.execute("SELECT data, fornecedor_descricao, nome_item, quantidade, usuario FROM entrada;")
                for data, desc, tipo_item, qtd, user in cursor.fetchall():
                    if data:
                        txt_geral = f"{desc} {tipo_item} {user}".lower()
                        if termo and termo.lower() not in txt_geral: 
                            continue
                        conta_cliente = str(desc).split(":")[-1].strip() if "Ordem de Compra:" in str(desc) else "Fornecedor / Geral"
                        registros_lidos.append(("Entrada", str(data), conta_cliente, desc or "-", tipo_item or "-", qtd or 0, user or "-"))

            # 2. Uso / Saídas
            if filtro_tipo in ["Todos", "Saída"]:
                cursor.execute("SELECT data, local_setor, nome_equipamento, quantidade_usada, observacao, usuario FROM uso;")
                for data, setor, tipo_item, qtd, obs, user in cursor.fetchall():
                    if data:
                        txt_geral = f"{setor} {tipo_item} {obs} {user}".lower()
                        if termo and termo.lower() not in txt_geral: 
                            continue
                        conta_cliente = setor or "Desconhecido"
                        if "OS:" in str(obs):
                            for parte in str(obs).split("|"):
                                if "OS:" in parte: 
                                    conta_cliente = parte.split(":")[-1].strip()
                                    break
                        registros_lidos.append(("Saída", str(data), conta_cliente, obs or "-", tipo_item or "-", qtd or 0, user or "-"))

            # 3. Atualizações / Logs
            if filtro_tipo in ["Todos", "Atualização"]:
                cursor.execute("SELECT data, num_conta, descricao_log, item, quantidade, usuario FROM atualizacoes;")
                for data, conta, desc_log, item, qtd, user in cursor.fetchall():
                    if data:
                        txt_geral = f"{conta} {desc_log} {item} {user}".lower()
                        if termo and termo.lower() not in txt_geral: 
                            continue
                        registros_lidos.append(("Atualização", str(data), conta or "-", desc_log or "-", item or "-", qtd or 0, user or "-"))

            cursor.close()
            conn.close()

            # Insere direto na tabela (já ordenadas ou em lote)
            for reg in registros_lidos:
                tabela_mov.insert("", "end", values=reg)

        except Exception as e:
            print("Erro ao carregar movimentações do Supabase:", e)

    carregar_movimentacoes()

    def aplicar_filtros():
        carregar_movimentacoes(combo_filtro_tipo.get(), entry_filtro_busca.get().strip())

    def limpar_filtros():
        combo_filtro_tipo.set("Todos")
        entry_filtro_busca.delete(0, tk.END)
        carregar_movimentacoes()

    f_botoes_filtro = tk.Frame(frame_principal)
    f_botoes_filtro.pack(fill="x", pady=(0, 10))
    tk.Button(f_botoes_filtro, text="🔍 Aplicar Filtros", command=aplicar_filtros, bg="#1F4E79", fg="white", font=("Arial", 9, "bold"), width=16).pack(side="left", padx=(0, 10))
    tk.Button(f_botoes_filtro, text="🧹 Limpar", command=limpar_filtros, bg="#595959", fg="white", font=("Arial", 9), width=10).pack(side="left")

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x")


# ==========================================
# TELA 2: CADASTRO CENTRAL DE EQUIPAMENTOS E PRODUTOS (SUPABASE)
# ==========================================
def mostrar_tela_fornecedores(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela de Cadastro e Gerenciamento de Produtos/Equipamentos via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=20, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📦 Cadastro Central de Equipamentos e Produtos (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_form = tk.LabelFrame(frame_principal, text=" Dados do Produto / Equipamento ", font=("Arial", 9, "bold"), padx=15, pady=10)
    f_form.pack(fill="x", pady=(0, 10))

    f_l1 = tk.Frame(f_form)
    f_l1.pack(fill="x", pady=(0, 8))

    tk.Label(f_l1, text="Cód. do Produto:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_cod = tk.Entry(f_l1, font=("Arial", 10), width=15)
    entry_cod.pack(side="left", padx=(0, 20))

    tk.Label(f_l1, text="Nome do Produto:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_nome = tk.Entry(f_l1, font=("Arial", 10), width=28)
    entry_nome.pack(side="left", padx=(0, 20))

    tk.Label(f_l1, text="Valor Unit. (R$):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_valor = tk.Entry(f_l1, font=("Arial", 10), width=12)
    entry_valor.pack(side="left")

    f_l2 = tk.Frame(f_form)
    f_l2.pack(fill="x")

    tk.Label(f_l2, text="Fornecedor:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_forn = tk.Entry(f_l2, font=("Arial", 10), width=35)
    entry_forn.pack(side="left", padx=(0, 20))

    frame_tabela = tk.Frame(frame_principal)
    frame_tabela.pack(fill="both", expand=True, pady=(0, 10))

    colunas = ("Cod", "NomeProduto", "ValorUnit", "Fornecedor")
    tabela_produtos = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=10)
    
    tabela_produtos.heading("Cod", text="Cód. do Produto")
    tabela_produtos.column("Cod", width=130, anchor="center")
    tabela_produtos.heading("NomeProduto", text="Nome do Produto")
    tabela_produtos.column("NomeProduto", width=330, anchor="w")
    tabela_produtos.heading("ValorUnit", text="Valor Unitário (R$)")
    tabela_produtos.column("ValorUnit", width=160, anchor="center")
    tabela_produtos.heading("Fornecedor", text="Fornecedor")
    tabela_produtos.column("Fornecedor", width=250, anchor="w")
    
    scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela_produtos.yview)
    tabela_produtos.configure(yscrollcommand=scrollbar.set)
    tabela_produtos.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def carregar_produtos():
        for item in tabela_produtos.get_children():
            tabela_produtos.delete(item)
        
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT cod, tipo, fornecedor, valor_unitario FROM estoque;")
            for cod, tipo, fornecedor, val in cursor.fetchall():
                if tipo:
                    val_float = float(val or 0.0)
                    tabela_produtos.insert("", "end", values=(cod or "N/D", tipo, f"R$ {val_float:.2f}".replace('.', ','), fornecedor or "Não informado"))
            cursor.close()
            conn.close()
        except Exception as e:
            print("Erro ao carregar produtos do Supabase:", e)

    carregar_produtos()

    def ao_selecionar_produto(event):
        selecao = tabela_produtos.selection()
        if selecao:
            vals = tabela_produtos.item(selecao[0], "values")
            entry_cod.delete(0, tk.END)
            entry_cod.insert(0, vals[0])
            
            entry_nome.delete(0, tk.END)
            entry_nome.insert(0, vals[1])

            val_limpo = vals[2].replace("R$", "").replace(".", "").replace(",", ".").strip()
            entry_valor.delete(0, tk.END)
            entry_valor.insert(0, val_limpo)

            entry_forn.delete(0, tk.END)
            entry_forn.insert(0, vals[3] if vals[3] != "Não informado" else "")

    tabela_produtos.bind("<<TreeviewSelect>>", ao_selecionar_produto)

    def salvar_produto():
        cod = entry_cod.get().strip()
        nome = entry_nome.get().strip()
        val_str = entry_valor.get().strip().replace(",", ".")
        forn = entry_forn.get().strip()

        if not cod or not nome or not val_str:
            messagebox.showwarning("Atenção", "Preencha o Código, o Nome do Produto e o Valor Unitário!")
            return

        try:
            valor_unitario = float(val_str)
        except ValueError:
            messagebox.showerror("Erro", "O valor unitário deve ser um número válido.")
            return

        data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Erro ao conectar com o banco na nuvem.")
            return

        try:
            cursor = conn.cursor()
            # Verifica se já existe o produto pelo código
            cursor.execute("SELECT tipo, valor_unitario FROM estoque WHERE cod = %s;", (cod,))
            res = cursor.fetchone()

            if res:
                nome_antigo, valor_antigo = res[0], float(res[1] or 0.0)
                cursor.execute(
                    "UPDATE estoque SET tipo = %s, fornecedor = %s, valor_unitario = %s WHERE cod = %s;",
                    (nome, forn, valor_unitario, cod)
                )
                if valor_antigo != valor_unitario:
                    desc_log = f"Alteração de Preço: R$ {valor_antigo:.2f} ➔ R$ {valor_unitario:.2f}".replace('.', ',')
                else:
                    desc_log = f"Atualização de cadastro [Código: {cod}]"
            else:
                # Insere novo produto (com total e disponivel inicial 0)
                cursor.execute(
                    "INSERT INTO estoque (cod, tipo, total, disponivel, fornecedor, valor_unitario) VALUES (%s, %s, 0, 0, %s, %s);",
                    (cod, nome, forn, valor_unitario)
                )
                desc_log = f"Novo Produto Cadastrado [{cod}] - Valor: R$ {valor_unitario:.2f}".replace('.', ',')

            # Registra no log de atualizações
            cursor.execute(
                "INSERT INTO atualizacoes (data, num_conta, descricao_log, item, quantidade, usuario) VALUES (%s, %s, %s, %s, %s, %s);",
                (data_hoje, f"PROD-{cod}", desc_log, nome, "1", config.usuario_logado)
            )

            conn.commit()
            cursor.close()
            conn.close()

            config.atualizar_feed_estoque_critico()
            messagebox.showinfo("Sucesso", f"Produto '{nome}' salvo/atualizado com sucesso!")
            
            entry_cod.delete(0, tk.END)
            entry_nome.delete(0, tk.END)
            entry_valor.delete(0, tk.END)
            entry_forn.delete(0, tk.END)
            carregar_produtos()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar produto no Supabase: {e}")

    f_botoes = tk.Frame(frame_principal)
    f_botoes.pack(fill="x", pady=(5, 5))
    
    tk.Button(f_botoes, text="💾 Salvar / Atualizar Produto", command=salvar_produto, bg="#38761D", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x")
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(5, 0))


# ==========================================
# TELA 3: CADASTRO CENTRAL DE CLIENTES (SUPABASE)
# ==========================================
def mostrar_tela_clientes(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela de Cadastro e Gerenciamento Completo de Clientes via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, 1150, 780)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=10)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="👥 Cadastro Central de Clientes (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 6))

    # --- BLOCO 1: DADOS CADASTRAIS DO CLIENTE ---
    f_form = tk.LabelFrame(frame_principal, text=" 📋 Dados Cadastrais do Cliente ", font=("Arial", 9, "bold"), padx=12, pady=8)
    f_form.pack(fill="x", pady=(0, 6))

    f_l1 = tk.Frame(f_form)
    f_l1.pack(fill="x", pady=(0, 6))

    tk.Label(f_l1, text="Cód:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_cod_cli = tk.Entry(f_l1, font=("Arial", 9), width=8)
    entry_cod_cli.pack(side="left", padx=(0, 15))

    tk.Label(f_l1, text="Nome / Razão Social:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_nome_cli = tk.Entry(f_l1, font=("Arial", 9), width=35)
    entry_nome_cli.pack(side="left", padx=(0, 15))

    tk.Label(f_l1, text="Tipo:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_tipo_cli = ttk.Combobox(f_l1, values=["Particular", "Prefeitura"], width=12, state="readonly")
    combo_tipo_cli.set("Particular")
    combo_tipo_cli.pack(side="left", padx=(0, 15))

    tk.Label(f_l1, text="CNPJ/CPF:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_doc_cli = tk.Entry(f_l1, font=("Arial", 9), width=18)
    entry_doc_cli.pack(side="left")

    f_l2 = tk.Frame(f_form)
    f_l2.pack(fill="x", pady=(0, 2))

    tk.Label(f_l2, text="Endereço:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_end_cli = tk.Entry(f_l2, font=("Arial", 9), width=35)
    entry_end_cli.pack(side="left", padx=(0, 15))

    tk.Label(f_l2, text="Contato:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_tel_cli = tk.Entry(f_l2, font=("Arial", 9), width=16)
    entry_tel_cli.pack(side="left", padx=(0, 15))

    tk.Label(f_l2, text="E-mail:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_email_cli = tk.Entry(f_l2, font=("Arial", 9), width=28)
    entry_email_cli.pack(side="left")


    # --- BLOCO 2: DADOS TÉCNICOS (CENTRAL, MAC E CHIP) ---
    f_tec = tk.LabelFrame(frame_principal, text=" ⚙️ Informações Técnicas / Equipamento & Linha ", font=("Arial", 9, "bold"), padx=12, pady=8)
    f_tec.pack(fill="x", pady=(0, 8))

    f_t1 = tk.Frame(f_tec)
    f_t1.pack(fill="x", pady=(0, 6))

    tk.Label(f_t1, text="Mod. Central:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_modelo_central = tk.Entry(f_t1, font=("Arial", 9), width=18)
    entry_modelo_central.pack(side="left", padx=(0, 15))

    tk.Label(f_t1, text="Módulo:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_modulo = tk.Entry(f_t1, font=("Arial", 9), width=18)
    entry_modulo.pack(side="left", padx=(0, 15))

    tk.Label(f_t1, text="Mac Address:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_mac = tk.Entry(f_t1, font=("Arial", 9), width=20)
    entry_mac.pack(side="left")

    f_t2 = tk.Frame(f_tec)
    f_t2.pack(fill="x", pady=(0, 2))

    tk.Label(f_t2, text="Operadora:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_operadora = ttk.Combobox(f_t2, values=["Vivo", "Claro", "Outra"], width=12, state="readonly")
    combo_operadora.pack(side="left", padx=(0, 15))

    tk.Label(f_t2, text="Linha / Nº:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_linha = tk.Entry(f_t2, font=("Arial", 9), width=18)
    entry_linha.pack(side="left", padx=(0, 15))

    tk.Label(f_t2, text="ICCID:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_iccid = tk.Entry(f_t2, font=("Arial", 9), width=28)
    entry_iccid.pack(side="left")


    # --- FUNÇÕES DE FORMATAÇÃO AUTOMÁTICA ---
    def formatar_cpf_cnpj(texto):
        digitos = "".join(filter(str.isdigit, texto))
        if len(digitos) == 11:
            return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
        elif len(digitos) == 14:
            return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
        return texto

    def formatar_telefone(texto):
        digitos = "".join(filter(str.isdigit, texto))
        if len(digitos) == 11:
            return f"({digitos[:2]}) {digitos[2]} {digitos[3:7]}-{digitos[7:]}"
        elif len(digitos) == 10:
            return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
        return texto

    def formatar_mac_address(texto):
        # Remove tudo que não for letra hexadecimal ou número
        limpo = "".join(c for c in texto.upper() if c.isalnum())
        pares = [limpo[i:i+2] for i in range(0, min(len(limpo), 12), 2)]
        return ":".join(pares)

    frame_tabela_cli = tk.Frame(frame_principal)
    frame_tabela_cli.pack(fill="both", expand=True, pady=(0, 6))

    colunas_cli = ("Cod", "Nome", "Tipo", "Documento", "Contato", "Central", "Módulo", "Operadora", "Linha")
    tabela_clientes = ttk.Treeview(frame_tabela_cli, columns=colunas_cli, show="headings", height=9)
    
    tabela_clientes.heading("Cod", text="Cód")
    tabela_clientes.column("Cod", width=60, anchor="center")
    tabela_clientes.heading("Nome", text="Nome / Razão Social")
    tabela_clientes.column("Nome", width=190, anchor="w")
    tabela_clientes.heading("Tipo", text="Tipo")
    tabela_clientes.column("Tipo", width=80, anchor="center")
    tabela_clientes.heading("Documento", text="CNPJ / CPF")
    tabela_clientes.column("Documento", width=120, anchor="center")
    tabela_clientes.heading("Contato", text="Contato")
    tabela_clientes.column("Contato", width=110, anchor="center")
    tabela_clientes.heading("Central", text="Mod. Central")
    tabela_clientes.column("Central", width=110, anchor="center")
    tabela_clientes.heading("Módulo", text="Módulo")
    tabela_clientes.column("Módulo", width=100, anchor="center")
    tabela_clientes.heading("Operadora", text="Operadora")
    tabela_clientes.column("Operadora", width=90, anchor="center")
    tabela_clientes.heading("Linha", text="Linha / Nº")
    tabela_clientes.column("Linha", width=110, anchor="center")
    
    scrollbar_cli = ttk.Scrollbar(frame_tabela_cli, orient="vertical", command=tabela_clientes.yview)
    tabela_clientes.configure(yscrollcommand=scrollbar_cli.set)
    tabela_clientes.pack(side="left", fill="both", expand=True)
    scrollbar_cli.pack(side="right", fill="y")

    def carregar_clientes():
        for item in tabela_clientes.get_children():
            tabela_clientes.delete(item)
        
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, nome, tipo, documento, contato, modelo_central, modulo, operadora, linha_numero FROM clientes;")
            for row in cursor.fetchall():
                cod, nome, tipo, doc, tel, m_cent, mod, op, linha = row
                if cod and nome:
                    tabela_clientes.insert("", "end", values=(
                        cod, nome, tipo or "Particular", doc or "", tel or "", 
                        m_cent or "-", mod or "-", op or "-", linha or "-"
                    ))
            cursor.close()
            conn.close()
        except Exception as e:
            print("Erro ao carregar clientes do Supabase:", e)

    carregar_clientes()

    def ao_selecionar_cliente(event):
        selecao = tabela_clientes.selection()
        if selecao:
            item_selecionado = tabela_clientes.item(selecao[0], "values")
            cod_buscado = item_selecionado[0]
            
            conn = config.obter_conexao_banco()
            if not conn:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT codigo, nome, tipo, documento, endereco, contato, email, modelo_central, modulo, mac_address, operadora, linha_numero, iccid FROM clientes WHERE codigo = %s;", (cod_buscado,))
                res = cursor.fetchone()
                cursor.close()
                conn.close()

                if res:
                    entry_cod_cli.delete(0, tk.END); entry_cod_cli.insert(0, res[0] or "")
                    entry_nome_cli.delete(0, tk.END); entry_nome_cli.insert(0, res[1] or "")
                    combo_tipo_cli.set(res[2] or "Particular")
                    entry_doc_cli.delete(0, tk.END); entry_doc_cli.insert(0, res[3] or "")
                    entry_end_cli.delete(0, tk.END); entry_end_cli.insert(0, res[4] or "")
                    entry_tel_cli.delete(0, tk.END); entry_tel_cli.insert(0, res[5] or "")
                    entry_email_cli.delete(0, tk.END); entry_email_cli.insert(0, res[6] or "")
                    entry_modelo_central.delete(0, tk.END); entry_modelo_central.insert(0, res[7] or "")
                    entry_modulo.delete(0, tk.END); entry_modulo.insert(0, res[8] or "")
                    
                    # Formata o MAC ao carregar do banco
                    mac_formatado = formatar_mac_address(res[9] or "")
                    entry_mac.delete(0, tk.END); entry_mac.insert(0, mac_formatado)
                    
                    combo_operadora.set(res[10] if res[10] in ["Vivo", "Claro", "Outra"] else "")
                    entry_linha.delete(0, tk.END); entry_linha.insert(0, res[11] or "")
                    entry_iccid.delete(0, tk.END); entry_iccid.insert(0, res[12] or "")
            except Exception as e:
                print("Erro ao buscar detalhes do cliente selecionado:", e)

    tabela_clientes.bind("<<TreeviewSelect>>", ao_selecionar_cliente)

    def salvar_cliente():
        cod = entry_cod_cli.get().strip()
        nome = entry_nome_cli.get().strip()
        tipo = combo_tipo_cli.get().strip()
        doc = formatar_cpf_cnpj(entry_doc_cli.get().strip())
        tel = formatar_telefone(entry_tel_cli.get().strip())
        end = entry_end_cli.get().strip()
        email = entry_email_cli.get().strip()
        
        m_cent = entry_modelo_central.get().strip()
        modulo = entry_modulo.get().strip()
        mac = formatar_mac_address(entry_mac.get().strip()) # Salva formatado com separadores
        operadora = combo_operadora.get().strip()
        linha = entry_linha.get().strip()
        iccid = entry_iccid.get().strip()

        if not cod or not nome:
            messagebox.showwarning("Atenção", "Preencha pelo menos o Código e o Nome / Razão Social do Cliente!")
            return

        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Erro ao conectar com o banco na nuvem.")
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT codigo FROM clientes WHERE codigo = %s;", (cod,))
            existe = cursor.fetchone()

            if existe:
                cursor.execute(
                    """UPDATE clientes SET nome = %s, tipo = %s, documento = %s, endereco = %s, 
                       contato = %s, email = %s, modelo_central = %s, modulo = %s, 
                       mac_address = %s, operadora = %s, linha_numero = %s, iccid = %s 
                       WHERE codigo = %s;""",
                    (nome, tipo, doc, end, tel, email, m_cent, modulo, mac, operadora, linha, iccid, cod)
                )
                acao_log = f"Atualização de cadastro do cliente [{cod}] {nome}"
            else:
                cursor.execute(
                    """INSERT INTO clientes (codigo, nome, tipo, documento, endereco, contato, email, 
                       modelo_central, modulo, mac_address, operadora, linha_numero, iccid) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                    (cod, nome, tipo, doc, end, tel, email, m_cent, modulo, mac, operadora, linha, iccid)
                )
                acao_log = f"Novo cadastro de cliente [{cod}] {nome}"

            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            cursor.execute(
                "INSERT INTO atualizacoes (data, num_conta, descricao_log, item, quantidade, usuario) VALUES (%s, %s, %s, %s, %s, %s);",
                (data_hoje, str(cod), acao_log, "-", "-", config.usuario_logado)
            )

            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Sucesso", f"Cliente '{nome}' salvo com sucesso!")
            
            for ent in [entry_cod_cli, entry_nome_cli, entry_doc_cli, entry_end_cli, entry_tel_cli, entry_email_cli, entry_modelo_central, entry_modulo, entry_mac, entry_linha, entry_iccid]:
                ent.delete(0, tk.END)
            combo_operadora.set('')
            carregar_clientes()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar cliente no Supabase: {e}")

    f_botoes = tk.Frame(frame_principal)
    f_botoes.pack(fill="x", pady=(4, 2))
    
    tk.Button(f_botoes, text="💾 Salvar / Atualizar Cliente", command=salvar_cliente, bg="#38761D", fg="white", font=("Arial", 9, "bold"), height=2).pack(fill="x")
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 9), height=1).pack(fill="x", pady=(2, 0))


# ==========================================
# TELA 4: CADASTRO CENTRAL DE TÉCNICOS (SUPABASE)
# ==========================================
def mostrar_tela_tecnicos(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela de Cadastro e Gerenciamento Completo de Técnicos via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=20, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="👥 Cadastro Central de Técnicos (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_form = tk.LabelFrame(frame_principal, text=" Informações Completas do Técnico ", font=("Arial", 9, "bold"), padx=15, pady=10)
    f_form.pack(fill="x", pady=(0, 10))

    f_l1 = tk.Frame(f_form)
    f_l1.pack(fill="x", pady=(0, 6))

    tk.Label(f_l1, text="Cód:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_cod_tec = tk.Entry(f_l1, font=("Arial", 10), width=10)
    entry_cod_tec.pack(side="left", padx=(0, 15))
    entry_cod_tec.insert(0, "")

    tk.Label(f_l1, text="Nome Completo", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_nome_tec = tk.Entry(f_l1, font=("Arial", 10), width=32)
    entry_nome_tec.pack(side="left", padx=(0, 15))

    tk.Label(f_l1, text="Tipo:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_tipo_tec = ttk.Combobox(f_l1, values=["Particular", "Prefeitura"], width=14, state="readonly")
    combo_tipo_tec.set("Particular")
    combo_tipo_tec.pack(side="left")

    f_l2 = tk.Frame(f_form)
    f_l2.pack(fill="x", pady=(0, 4))

    tk.Label(f_l2, text="CNPJ / CPF:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_doc_tec = tk.Entry(f_l2, font=("Arial", 10), width=18)
    entry_doc_tec.pack(side="left", padx=(0, 15))

    tk.Label(f_l2, text="Endereço:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_end_tec = tk.Entry(f_l2, font=("Arial", 10), width=28)
    entry_end_tec.pack(side="left", padx=(0, 15))
    
    tk.Label(f_l2, text="Contato:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_tel_tec = tk.Entry(f_l2, font=("Arial", 10), width=15)
    entry_tel_tec.pack(side="left", padx=(0, 15))

    tk.Label(f_l2, text="E-mail:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_email_tec = tk.Entry(f_l2, font=("Arial", 10), width=22)
    entry_email_tec.pack(side="left")

    def formatar_cpf_cnpj(texto):
        digitos = "".join(filter(str.isdigit, texto))
        if len(digitos) == 11:
            return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
        elif len(digitos) == 14:
            return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
        return texto

    def formatar_telefone(texto):
        digitos = "".join(filter(str.isdigit, texto))
        if len(digitos) == 11:
            return f"({digitos[:2]}) {digitos[2]} {digitos[3:7]}-{digitos[7:]}"
        elif len(digitos) == 10:
            return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
        return texto

    frame_tabela_tec = tk.Frame(frame_principal)
    frame_tabela_tec.pack(fill="both", expand=True, pady=(0, 10))

    colunas_tec = ("Cod", "Nome", "Tipo", "Documento", "Endereco", "Contato", "Email")
    tabela_tecnicos = ttk.Treeview(frame_tabela_tec, columns=colunas_tec, show="headings", height=11)
    
    tabela_tecnicos.heading("Cod", text="Cód")
    tabela_tecnicos.column("Cod", width=70, anchor="center")
    tabela_tecnicos.heading("Nome", text="Nome / Razão Social")
    tabela_tecnicos.column("Nome", width=220, anchor="w")
    tabela_tecnicos.heading("Tipo", text="Tipo")
    tabela_tecnicos.column("Tipo", width=90, anchor="center")
    tabela_tecnicos.heading("Documento", text="CNPJ / CPF")
    tabela_tecnicos.column("Documento", width=130, anchor="center")
    tabela_tecnicos.heading("Endereco", text="Endereço")
    tabela_tecnicos.column("Endereco", width=240, anchor="w")
    tabela_tecnicos.heading("Contato", text="Contato")
    tabela_tecnicos.column("Contato", width=120, anchor="center")
    tabela_tecnicos.heading("Email", text="E-mail")
    tabela_tecnicos.column("Email", width=180, anchor="w")
    
    scrollbar_tec = ttk.Scrollbar(frame_tabela_tec, orient="vertical", command=tabela_tecnicos.yview)
    tabela_tecnicos.configure(yscrollcommand=scrollbar_tec.set)
    tabela_tecnicos.pack(side="left", fill="both", expand=True)
    scrollbar_tec.pack(side="right", fill="y")

    def carregar_tecnicos():
        for item in tabela_tecnicos.get_children():
            tabela_tecnicos.delete(item)
        
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, nome, tipo, documento, endereco, contato, email FROM tecnicos;")
            for cod, nome, tipo, doc, end, tel, email in cursor.fetchall():
                if cod and nome:
                    tabela_tecnicos.insert("", "end", values=(cod, nome, tipo or "Particular", doc or "", end or "", tel or "", email or ""))
            cursor.close()
            conn.close()
        except Exception as e:
            print("Erro ao carregar técnicos do Supabase:", e)

    carregar_tecnicos()

    def ao_selecionar_tecnico(event):
        selecao = tabela_tecnicos.selection()
        if selecao:
            vals = tabela_tecnicos.item(selecao[0], "values")
            entry_cod_tec.delete(0, tk.END)
            entry_cod_tec.insert(0, vals[0])
            
            entry_nome_tec.delete(0, tk.END)
            entry_nome_tec.insert(0, vals[1])

            combo_tipo_tec.set(vals[2])

            entry_doc_tec.delete(0, tk.END)
            entry_doc_tec.insert(0, vals[3] if vals[3] != "None" else "")

            entry_end_tec.delete(0, tk.END)
            entry_end_tec.insert(0, vals[4] if vals[4] != "None" else "")

            entry_tel_tec.delete(0, tk.END)
            entry_tel_tec.insert(0, vals[5] if vals[5] != "None" else "")

            entry_email_tec.delete(0, tk.END)
            entry_email_tec.insert(0, vals[6] if vals[6] != "None" else "")

    tabela_tecnicos.bind("<<TreeviewSelect>>", ao_selecionar_tecnico)

    def salvar_tecnico():
        cod = entry_cod_tec.get().strip()
        nome = entry_nome_tec.get().strip()
        tipo = combo_tipo_tec.get().strip()
        doc = formatar_cpf_cnpj(entry_doc_tec.get().strip())
        tel = formatar_telefone(entry_tel_tec.get().strip())
        end = entry_end_tec.get().strip()
        email = entry_email_tec.get().strip()

        if not cod or not nome:
            messagebox.showwarning("Atenção", "Preencha pelo menos o Código e o Nome do Técnico!")
            return

        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Erro ao conectar com o banco na nuvem.")
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT codigo FROM tecnicos WHERE codigo = %s;", (cod,))
            existe = cursor.fetchone()

            if existe:
                if not messagebox.askyesno("Confirmar Atualização", f"O técnico '{cod}' já está cadastrado.\nDeseja realmente aplicar as alterações?"):
                    cursor.close()
                    conn.close()
                    return
                
                cursor.execute(
                    "UPDATE tecnicos SET nome = %s, tipo = %s, documento = %s, endereco = %s, contato = %s, email = %s WHERE codigo = %s;",
                    (nome, tipo, doc, end, tel, email, cod)
                )
                acao_log = f"Atualização de cadastro do técnico [{cod}] {nome}"
            else:
                cursor.execute(
                    "INSERT INTO tecnicos (codigo, nome, tipo, documento, endereco, contato, email) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                    (cod, nome, tipo, doc, end, tel, email)
                )
                acao_log = f"Novo cadastro de técnico [{cod}] {nome}"

            data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            cursor.execute(
                "INSERT INTO atualizacoes (data, num_conta, descricao_log, item, quantidade, usuario) VALUES (%s, %s, %s, %s, %s, %s);",
                (data_hoje, str(cod), acao_log, "-", "-", config.usuario_logado)
            )

            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Sucesso", f"Técnico '{nome}' salvo com sucesso!")
            
            entry_cod_tec.delete(0, tk.END)
            entry_cod_tec.insert(0, f"TEC-{tabela_tecnicos.get_children().__len__() + 2:03d}")
            entry_nome_tec.delete(0, tk.END)
            entry_doc_tec.delete(0, tk.END)
            entry_end_tec.delete(0, tk.END)
            entry_tel_tec.delete(0, tk.END)
            entry_email_tec.delete(0, tk.END)
            carregar_tecnicos()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar técnico no Supabase: {e}")

    f_botoes = tk.Frame(frame_principal)
    f_botoes.pack(fill="x", pady=(5, 5))
    
    tk.Button(f_botoes, text="💾 Salvar / Atualizar Técnico", command=salvar_tecnico, bg="#38761D", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x")
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(5, 0))