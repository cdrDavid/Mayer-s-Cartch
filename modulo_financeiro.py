import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
import config


# ==========================================
# TELA 1: HISTÓRICO DE MOVIMENTAÇÕES (SUPABASE)
# ==========================================
def mostrar_tela_historico_movimentacoes(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela Separada de Histórico Detalhado de Movimentações, Logs e Auditoria via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=10)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📊 Histórico da oficina e auditoria", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 6))

    # --- FILTROS DE PESQUISA ---
    f_filtros = tk.LabelFrame(frame_principal, text=" Filtros de Pesquisa ", font=("Arial", 9, "bold"), padx=10, pady=6)
    f_filtros.pack(fill="x", pady=(0, 6))

    f_l_filtro = tk.Frame(f_filtros)
    f_l_filtro.pack(fill="x", pady=2)

    tk.Label(f_l_filtro, text="Tipo:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_filtro_tipo = ttk.Combobox(f_l_filtro, values=["Todos", "Entrada", "Saída", "Atualização / Log"], width=16, state="readonly")
    combo_filtro_tipo.set("Todos")
    combo_filtro_tipo.pack(side="left", padx=(0, 15))

    tk.Label(f_l_filtro, text="Busca Geral:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_filtro_busca = tk.Entry(f_l_filtro, font=("Arial", 9), width=25)
    entry_filtro_busca.pack(side="left", padx=(0, 15))

    # --- TABELA DE MOVIMENTAÇÕES ---
    frame_tabela_mov = tk.Frame(frame_principal)
    frame_tabela_mov.pack(fill="both", expand=True, pady=(0, 6))

    colunas_mov = ("ID_Oculto", "Tipo", "Data", "Nº Conta / Cliente", "Resumo da Descrição", "Item", "Quantidade", "Usuário")
    tabela_mov = ttk.Treeview(frame_tabela_mov, columns=colunas_mov, show="headings", height=8)
    
    tabela_mov.heading("ID_Oculto", text="ID"); tabela_mov.column("ID_Oculto", width=0, stretch=False)
    tabela_mov.heading("Tipo", text="Tipo"); tabela_mov.column("Tipo", width=110, anchor="center")
    tabela_mov.heading("Data", text="Data / Hora"); tabela_mov.column("Data", width=130, anchor="center")
    tabela_mov.heading("Nº Conta / Cliente", text="Nº Conta / Cliente"); tabela_mov.column("Nº Conta / Cliente", width=140, anchor="center")
    tabela_mov.heading("Resumo da Descrição", text="Resumo da Descrição / Ação"); tabela_mov.column("Resumo da Descrição", width=420, anchor="w")
    tabela_mov.heading("Item", text="Item"); tabela_mov.column("Item", width=150, anchor="w")
    tabela_mov.heading("Quantidade", text="Qtd"); tabela_mov.column("Quantidade", width=65, anchor="center")
    tabela_mov.heading("Usuário", text="Usuário"); tabela_mov.column("Usuário", width=110, anchor="center")

    scrollbar_mov_y = ttk.Scrollbar(frame_tabela_mov, orient="vertical", command=tabela_mov.yview)
    tabela_mov.configure(yscrollcommand=scrollbar_mov_y.set)
    tabela_mov.pack(side="left", fill="both", expand=True)
    scrollbar_mov_y.pack(side="right", fill="y")

    # --- PAINEL INFERIOR DE DETALHES (Expansível / Ocultável com ESC) ---
    f_detalhes_mov = tk.LabelFrame(frame_principal, text=" Detalhes Completos da Movimentação / Log (Pressione ESC para ocultar) ", font=("Arial", 9, "bold"), padx=10, pady=6)
    f_detalhes_mov.pack(fill="x", pady=(0, 6))

    text_detalhes_mov = tk.Text(f_detalhes_mov, font=("Arial", 9), height=4, wrap="word", bg="#F4F4F4")
    text_detalhes_mov.pack(fill="x", expand=True)
    text_detalhes_mov.config(state="disabled")

    def carregar_movimentacoes(filtro_tipo="Todos", termo=""):
        for i in tabela_mov.get_children():
            tabela_mov.delete(i)
        
        text_detalhes_mov.config(state="normal")
        text_detalhes_mov.delete("1.0", tk.END)
        text_detalhes_mov.config(state="disabled")

        registros_lidos = []
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # 1. Entradas (OC)
            if filtro_tipo in ["Todos", "Entrada"]:
                cursor.execute("SELECT id, data, fornecedor_descricao, nome_item, quantidade, usuario, status FROM entrada;")
                for row_id, data, desc, tipo_item, qtd, user, status in cursor.fetchall():
                    if data:
                        txt_geral = f"{desc} {tipo_item} {user} {status}".lower()
                        if termo and termo.lower() not in txt_geral: 
                            continue
                        conta_cliente = str(desc).split(":")[-1].strip() if "Ordem de Compra:" in str(desc) else "Fornecedor / Geral"
                        resumo = f"Entrada de mercadoria ({tipo_item})"
                        detalhe_completo = f"ID: {row_id} | Data: {data}\nFornecedor / Descrição: {desc}\nItem: {tipo_item} | Quantidade: {qtd}\nStatus: {status}\nRegistrado por: {user}"
                        registros_lidos.append((f"ENT-{row_id}", "Entrada", str(data), conta_cliente, resumo, tipo_item or "-", qtd or 0, user or "-", detalhe_completo))

            # 2. Uso / Saídas (OS)
            if filtro_tipo in ["Todos", "Saída"]:
                cursor.execute("SELECT id, data, local_setor, nome_equipamento, quantidade_usada, observacao, usuario, status FROM uso;")
                for row_id, data, setor, tipo_item, qtd, obs, user, status in cursor.fetchall():
                    if data:
                        txt_geral = f"{setor} {tipo_item} {obs} {user} {status}".lower()
                        if termo and termo.lower() not in txt_geral: 
                            continue
                        conta_cliente = setor or "Desconhecido"
                        num_os = "OS-N/D"
                        if obs and "OS:" in str(obs):
                            for parte in str(obs).split("|"):
                                if "OS:" in parte: 
                                    num_os = parte.split(":")[-1].strip()
                                    break
                        resumo = f"Ordem de Serviço ({num_os}) — Status: {status}"
                        detalhe_completo = f"ID: {row_id} | Data: {data} | Nº OS: {num_os}\nCliente / Setor: {setor}\nStatus Atual: {status}\nRegistrado por: {user}\n\nDetalhes e Serviços:\n{obs}"
                        registros_lidos.append((f"SAI-{row_id}", "Saída", str(data), conta_cliente, resumo, tipo_item or "-", qtd or 0, user or "-", detalhe_completo))

            # 3. Atualizações / Logs / Alterações / Cancelamentos / Estornos
            if filtro_tipo in ["Todos", "Atualização / Log"]:
                cursor.execute("SELECT id, data, num_conta, descricao_log, item, quantidade, usuario FROM atualizacoes;")
                for row_id, data, conta, desc_log, item, qtd, user in cursor.fetchall():
                    if data:
                        txt_geral = f"{conta} {desc_log} {item} {user}".lower()
                        if termo and termo.lower() not in txt_geral: 
                            continue
                        
                        # Cria um resumo amigável com base no log
                        resumo_log = str(desc_log)
                        if "|" in resumo_log:
                            resumo_log = resumo_log.split("|")[0].strip()

                        detalhe_completo = f"ID Log: {row_id} | Data / Hora: {data}\nConta / Referência: {conta}\nUsuário Responsável: {user}\n\nDescrição Detalhada:\n{desc_log}"
                        registros_lidos.append((f"LOG-{row_id}", "Atualização / Log", str(data), conta or "-", resumo_log, item or "-", qtd or "-", user or "-", detalhe_completo))

            cursor.close()
            conn.close()

            # Ordena do mais recente para o mais antigo baseando-se no ID (maior ID = mais recente inserido)
            registros_ordenados = sorted(registros_lidos, key=lambda x: str(x[0]), reverse=True)

            for reg in registros_ordenados:
                # Insere excluindo o último elemento (que é o detalhe completo guardado nas tags)
                tabela_mov.insert("", "end", values=reg[:-1], tags=(reg[-1],))

        except Exception as e:
            print("Erro ao carregar histórico unificado do Supabase:", e)

    carregar_movimentacoes()

    def ao_clicar_linha_movimentacao(event):
        selecao = tabela_mov.selection()
        if selecao:
            item_dados = tabela_mov.item(selecao[0])
            tags = item_dados.get("tags")
            if tags:
                detalhe_texto = tags[0]
                text_detalhes_mov.config(state="normal")
                text_detalhes_mov.delete("1.0", tk.END)
                text_detalhes_mov.insert("1.0", detalhe_texto)
                text_detalhes_mov.config(state="disabled")

    tabela_mov.bind("<<TreeviewSelect>>", ao_clicar_linha_movimentacao)

    def ocultar_detalhes_com_esc(event):
        """Oculta o painel de detalhes ao pressionar a tecla ESC"""
        text_detalhes_mov.config(state="normal")
        text_detalhes_mov.delete("1.0", tk.END)
        text_detalhes_mov.config(state="disabled")
        tabela_mov.selection_remove(tabela_mov.selection())

    janela_principal.bind("<Escape>", ocultar_detalhes_com_esc)

    def aplicar_filtros():
        carregar_movimentacoes(combo_filtro_tipo.get(), entry_filtro_busca.get().strip())

    def limpar_filtros():
        combo_filtro_tipo.set("Todos")
        entry_filtro_busca.delete(0, tk.END)
        carregar_movimentacoes()

    f_botoes_filtro = tk.Frame(frame_principal)
    f_botoes_filtro.pack(fill="x", pady=(2, 4))
    tk.Button(f_botoes_filtro, text="🔍 Aplicar Filtros", command=aplicar_filtros, bg="#1F4E79", fg="white", font=("Arial", 9, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 4))
    tk.Button(f_botoes_filtro, text="🧹 Limpar", command=limpar_filtros, bg="#595959", fg="white", font=("Arial", 9, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 4))

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 9), height=1).pack(fill="x", pady=(2, 0))


# ==========================================
# TELA 2: CADASTRO CENTRAL DE EQUIPAMENTOS E PRODUTOS (SUPABASE)
# ==========================================
def mostrar_tela_fornecedores(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela de Cadastro e Gerenciamento de Produtos/Equipamentos via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=20, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="🔩 Cadastro de peças e serviços", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_form = tk.LabelFrame(frame_principal, text=" Dados da peça ou serviço ", font=("Arial", 9, "bold"), padx=15, pady=10)
    f_form.pack(fill="x", pady=(0, 10))

    f_l1 = tk.Frame(f_form)
    f_l1.pack(fill="x", pady=(0, 8))

    tk.Label(f_l1, text="Código:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_cod = tk.Entry(f_l1, font=("Arial", 10), width=15)
    entry_cod.pack(side="left", padx=(0, 20))

    tk.Label(f_l1, text="Nome do Produto:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_nome = tk.Entry(f_l1, font=("Arial", 10), width=45)
    entry_nome.pack(side="left", padx=(0, 20))

    tk.Label(f_l1, text="Valor Unit. (R$):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_valor = tk.Entry(f_l1, font=("Arial", 10), width=12)
    entry_valor.pack(side="left")
    
    '''
    f_l2 = tk.Frame(f_form)
    f_l2.pack(fill="x")
    '''

    tk.Label(f_l1, text="Fornecedor:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_forn = tk.Entry(f_l1, font=("Arial", 10), width=35)
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
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=10)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="👥 Clientes e veículos", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 6))

    # --- BLOCO 1: DADOS CADASTRAIS DO CLIENTE ---
    f_form = tk.LabelFrame(frame_principal, text=" 📋 Dados Cadastrais do Cliente ", font=("Arial", 9, "bold"), padx=12, pady=8)
    f_form.pack(fill="x", pady=(0, 6))

    f_l1 = tk.Frame(f_form)
    f_l1.pack(fill="x", pady=(0, 4))

    tk.Label(f_l1, text="Cód:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_cod_cli = tk.Entry(f_l1, font=("Arial", 9), width=8)
    entry_cod_cli.pack(side="left", padx=(0, 10))

    tk.Label(f_l1, text="Nome / Razão Social:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_nome_cli = tk.Entry(f_l1, font=("Arial", 9), width=30)
    entry_nome_cli.pack(side="left", padx=(0, 10))

    tk.Label(f_l1, text="Tipo:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_tipo_cli = ttk.Combobox(f_l1, values=["P.Fisica", "P.Juridica"], width=11, state="readonly")
    combo_tipo_cli.set("P.Fisica")
    combo_tipo_cli.pack(side="left", padx=(0, 10))

    tk.Label(f_l1, text="CNPJ/CPF:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_doc_cli = tk.Entry(f_l1, font=("Arial", 9), width=16)
    entry_doc_cli.pack(side="left", padx=(0, 10))

    tk.Label(f_l1, text="Últ. Atualização:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_data_atl = tk.Entry(f_l1, font=("Arial", 9), width=11)
    entry_data_atl.pack(side="left")
    entry_data_atl.insert(0, datetime.now().strftime("%d/%m/%Y"))

    f_l2 = tk.Frame(f_form)
    f_l2.pack(fill="x", pady=(0, 4))

    tk.Label(f_l2, text="CEP:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_cep = tk.Entry(f_l2, font=("Arial", 9), width=10)
    entry_cep.pack(side="left", padx=(0, 8))

    tk.Label(f_l2, text="Rua:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_rua = tk.Entry(f_l2, font=("Arial", 9), width=32)
    entry_rua.pack(side="left", padx=(0, 8))

    tk.Label(f_l2, text="Nº:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_numero = tk.Entry(f_l2, font=("Arial", 9), width=6)
    entry_numero.pack(side="left", padx=(0, 8))

    tk.Label(f_l2, text="Bairro:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_bairro = tk.Entry(f_l2, font=("Arial", 9), width=16)
    entry_bairro.pack(side="left", padx=(0, 8))

    tk.Label(f_l2, text="Cidade:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_cidade = tk.Entry(f_l2, font=("Arial", 9), width=16)
    entry_cidade.pack(side="left")

    f_l3 = tk.Frame(f_form)
    f_l3.pack(fill="x", pady=(0, 2))

    tk.Label(f_l3, text="Contato:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_tel_cli = tk.Entry(f_l3, font=("Arial", 9), width=16)
    entry_tel_cli.pack(side="left", padx=(0, 15))

    tk.Label(f_l3, text="E-mail:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_email_cli = tk.Entry(f_l3, font=("Arial", 9), width=45)
    entry_email_cli.pack(side="left")


    # --- BLOCO 2: DADOS TÉCNICOS / EQUIPAMENTO & LINHA ---
    f_tec = tk.LabelFrame(frame_principal, text=" 🚗 Dados do veículo ", font=("Arial", 9, "bold"), padx=12, pady=8)
    f_tec.pack(fill="x", pady=(0, 8))

    f_t1 = tk.Frame(f_tec)
    f_t1.pack(fill="x", pady=(0, 4))

    marcas_modelos = {
        "Chevrolet": ["Onix", "Cruze", "Tracker", "S10", "Spin", "Montana", "Equinox", "Corsa", "Outros"],
        "Ford": ["Ka", "Fiesta", "Focus", "EcoSport", "Ranger", "Territory", "Outros"],
        "Toyota": ["Corolla", "Hilux", "Yaris", "RAV4", "SW4", "Outros"],
        "Honda": ["Civic", "Fit", "HR-V", "CR-V", "City", "Outros"],
        "Volkswagen": ["Gol", "Golf", "Polo", "T-Cross", "Virtus", "Saveiro", "Outros"],
        "Nissan": ["March", "Versa", "Kicks", "Frontier", "Sentra", "Outros"],
        "Hyundai": ["HB20", "Creta", "ix35", "Tucson", "Santa Fe", "Outros"],
        "Kia": ["Picanto", "Cerato", "Sportage", "Sorento", "Outros"],
        "Renault": ["Kwid", "Sandero", "Logan", "Duster", "Master", "Outros"],
        "Peugeot": ["208", "2008", "3008", "Partner", "Outros"],
        "Fiat": ["Uno", "Argo", "Mobi", "Strada", "Toro", "Fiorino", "Outros"],
        "Jeep": ["Renegade", "Compass", "Commander", "Wrangler", "Outros"],
        "Mitsubishi": ["Lancer", "ASX", "Outlander", "Pajero", "L200", "Outros"],
        "Suzuki": ["Jimny", "Vitara", "S-Cross", "Outros"],
        "Mazda": ["Mazda 2", "Mazda 3", "CX-3", "CX-5", "Outros"],
        "Outras": ["Outros"]
    }

    tk.Label(f_t1, text="Marca do Carro:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_tipo_carro = ttk.Combobox(f_t1, values=list(marcas_modelos), width=12, state="readonly")
    combo_tipo_carro.set("Selecione")
    combo_tipo_carro.pack(side="left", padx=(0, 15))
    
    tk.Label(f_t1, text="Linha:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_linha = ttk.Combobox(f_t1, values=["Selecione"], width=12, state="readonly")
    combo_linha.set("Selecione")
    combo_linha.pack(side="left", padx=(0, 15))

    def atualizar_linhas(event=None):
        marca = combo_tipo_carro.get()
        opcoes = marcas_modelos.get(marca, ["Outros"])
        combo_linha.configure(values=opcoes)
        combo_linha.set("Selecione")

    combo_tipo_carro.bind("<<ComboboxSelected>>", atualizar_linhas)

    tk.Label(f_t1, text="Modelo:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_modelo = ttk.Combobox(f_t1, values=["Sedan", "Hatch", "SUV", "Pickup", "Coupe", "Convertible", "Minivan", "Outros"], width=12, state="readonly")
    combo_modelo.set("Selecione")
    combo_modelo.pack(side="left", padx=(0, 15))

    tk.Label(f_t1, text="Ano:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_ano = ttk.Combobox(f_t1, values=[str(year) for year in range(1980, 2031)], width=8, state="readonly")
    combo_ano.set("Selecione")
    combo_ano.pack(side="left")

    tk.Label(f_t1, text="Tipo de Combustível:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    combo_combustivel = ttk.Combobox(f_t1, values=["Gasolina", "Etanol", "Diesel", "Elétrico", "Híbrido", "Outro"], width=12, state="readonly")
    combo_combustivel.set("Selecione")
    combo_combustivel.pack(side="left", padx=(0, 15))
    
    # --- ABAS / DIVISÃO INFERIOR ---
    notebook_baixo = ttk.Notebook(frame_principal)
    notebook_baixo.pack(fill="both", expand=True, pady=(0, 6))

    # Aba 1: Clientes Cadastrados com Barra de Pesquisa Integrada no Topo
    tab_cli_lista = ttk.Frame(notebook_baixo, padding=6)
    notebook_baixo.add(tab_cli_lista, text=" 📋 Clientes Cadastrados ")

    f_pesquisa_barra = tk.Frame(tab_cli_lista)
    f_pesquisa_barra.pack(fill="x", pady=(0, 4))

    tk.Label(f_pesquisa_barra, text="🔍 Pesquisar (digite e aperte Enter):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 6))
    entry_busca_geral = tk.Entry(f_pesquisa_barra, font=("Arial", 9), width=35)
    entry_busca_geral.pack(side="left", padx=(0, 10))

    def limpar_busca(event=None):
        if not entry_busca_geral.get().strip():
            carregar_clientes()

    tk.Button(f_pesquisa_barra, text="🔄 Ver Todos", command=lambda: [entry_busca_geral.delete(0, tk.END), carregar_clientes()], bg="#595959", fg="white", font=("Arial", 8, "bold")).pack(side="left")

    colunas_cli = ("Cod", "Nome", "Tipo", "CPF/ CNPJ", "Rua", "Nº", "Bairro", "Cidade", "Contato", "E-mail", "Atualização")
    
    frame_tabela_cli_container = tk.Frame(tab_cli_lista)
    frame_tabela_cli_container.pack(fill="both", expand=True)

    tabela_clientes = ttk.Treeview(frame_tabela_cli_container, columns=colunas_cli, show="headings", height=5)
    
    tabela_clientes.heading("Cod", text="Cód"); tabela_clientes.column("Cod", width=50, anchor="center")
    tabela_clientes.heading("Nome", text="Nome / Razão Social"); tabela_clientes.column("Nome", width=160, anchor="w")
    tabela_clientes.heading("Tipo", text="Tipo"); tabela_clientes.column("Tipo", width=75, anchor="center")
    tabela_clientes.heading("CPF/ CNPJ", text="CPF/ CNPJ"); tabela_clientes.column("CPF/ CNPJ", width=120, anchor="center")
    tabela_clientes.heading("Rua", text="Rua"); tabela_clientes.column("Rua", width=140, anchor="w")
    tabela_clientes.heading("Nº", text="Nº"); tabela_clientes.column("Nº", width=45, anchor="center")
    tabela_clientes.heading("Bairro", text="Bairro"); tabela_clientes.column("Bairro", width=100, anchor="w")
    tabela_clientes.heading("Cidade", text="Cidade"); tabela_clientes.column("Cidade", width=100, anchor="w")
    tabela_clientes.heading("Contato", text="Contato"); tabela_clientes.column("Contato", width=100, anchor="w")
    tabela_clientes.heading("E-mail", text="E-mail"); tabela_clientes.column("E-mail", width=150, anchor="w")
    tabela_clientes.heading("Atualização", text="Atualizado em"); tabela_clientes.column("Atualização", width=95, anchor="center")
    
    scrollbar_cli = ttk.Scrollbar(frame_tabela_cli_container, orient="vertical", command=tabela_clientes.yview)
    tabela_clientes.configure(yscrollcommand=scrollbar_cli.set)
    tabela_clientes.pack(side="top", fill="both", expand=True)
    scrollbar_cli.pack(side="right", fill="y")

    # Aba 2: Histórico de Atualizações (Dinâmica - Oculta por padrão)
    tab_cli_hist = ttk.Frame(notebook_baixo)

    colunas_hist = ("Data", "Descrição da Alteração / Motivo", "Usuário")
    tabela_historico_alt = ttk.Treeview(tab_cli_hist, columns=colunas_hist, show="headings", height=6)
    
    tabela_historico_alt.heading("Data", text="Data / Hora"); tabela_historico_alt.column("Data", width=140, anchor="center")
    tabela_historico_alt.heading("Descrição da Alteração / Motivo", text="Descrição da Alteração, Motivo & Detalhes"); tabela_historico_alt.column("Descrição da Alteração / Motivo", width=800, anchor="w")
    tabela_historico_alt.heading("Usuário", text="Usuário"); tabela_historico_alt.column("Usuário", width=150, anchor="center")

    scrollbar_hist = ttk.Scrollbar(tab_cli_hist, orient="vertical", command=tabela_historico_alt.yview)
    tabela_historico_alt.configure(yscrollcommand=scrollbar_hist.set)
    tabela_historico_alt.pack(side="left", fill="both", expand=True)
    scrollbar_hist.pack(side="right", fill="y")


    # --- FUNÇÕES DE AUXÍLIO ---
    def consultar_cep(event=None):
        cep_limpo = "".join(filter(str.isdigit, entry_cep.get()))
        if len(cep_limpo) != 8:
            return
        try:
            import urllib.request
            import json
            url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resposta:
                dados = json.loads(resposta.read().decode())
                if "erro" not in dados:
                    entry_rua.delete(0, tk.END); entry_rua.insert(0, dados.get("logradouro", ""))
                    entry_bairro.delete(0, tk.END); entry_bairro.insert(0, dados.get("bairro", ""))
                    entry_cidade.delete(0, tk.END); entry_cidade.insert(0, dados.get("localidade", ""))
                    entry_numero.focus()
        except Exception as e:
            print("Erro ao consultar CEP:", e)

    entry_cep.bind("<Return>", consultar_cep)
    entry_cep.bind("<FocusOut>", consultar_cep)

    def limpar_formulario():
        for ent in [entry_cod_cli, entry_nome_cli, entry_doc_cli, entry_cep, entry_rua, entry_numero, entry_bairro, entry_cidade, entry_tel_cli, entry_email_cli]:
            ent.delete(0, tk.END)
        combo_tipo_cli.set('Particular')
        combo_tipo_carro.set('Selecione')
        combo_linha.configure(values=['Selecione'])
        combo_linha.set('Selecione')
        combo_modelo.set('Selecione')
        combo_ano.set('Selecione')
        combo_combustivel.set('Selecione')
        entry_data_atl.delete(0, tk.END)
        entry_data_atl.insert(0, datetime.now().strftime("%d/%m/%Y"))
        for item in tabela_historico_alt.get_children():
            tabela_historico_alt.delete(item)
        
        if str(tab_cli_hist) in notebook_baixo.tabs():
            notebook_baixo.forget(tab_cli_hist)

    def formatar_mac_address(texto):
        limpo = "".join(c for c in texto.upper() if c.isalnum())
        pares = [limpo[i:i+2] for i in range(0, min(len(limpo), 12), 2)]
        return ":".join(pares)

    def formatar_data(texto):
        digitos = "".join(filter(str.isdigit, texto))
        if len(digitos) >= 5:
            return f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:8]}"
        return texto

    def carregar_historico_atualizacoes(cod_cliente):
        for item in tabela_historico_alt.get_children():
            tabela_historico_alt.delete(item)
            
        if not cod_cliente:
            return

        conn = config.obter_conexao_banco()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT data, descricao_log, usuario 
                              FROM atualizacoes WHERE num_conta = %s ORDER BY id DESC;""", (str(cod_cliente),))
            for row in cursor.fetchall():
                data_reg, desc_reg, usuario_reg = row
                tabela_historico_alt.insert("", "end", values=(
                    data_reg or "-", desc_reg or "-", usuario_reg or "-"
                ))
            cursor.close()
            conn.close()
        except Exception as e:
            print("Erro ao carregar histórico de atualizações:", e)

    def carregar_dados_por_codigo(event=None):
        cod_digitado = entry_cod_cli.get().strip()
        if not cod_digitado:
            limpar_formulario()
            return

        conn = config.obter_conexao_banco()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT codigo, nome, tipo, documento, cep, rua, numero, bairro, cidade, 
                              contato, email, modelo_central, modulo, mac_address, operadora, linha_numero, iccid, data_atualizacao 
                              FROM clientes WHERE codigo = %s;""", (cod_digitado,))
            res = cursor.fetchone()
            cursor.close()
            conn.close()

            if res:
                entry_nome_cli.delete(0, tk.END); entry_nome_cli.insert(0, res[1] or "")
                combo_tipo_cli.set(res[2] or "Particular")
                entry_doc_cli.delete(0, tk.END); entry_doc_cli.insert(0, res[3] or "")
                entry_cep.delete(0, tk.END); entry_cep.insert(0, res[4] or "")
                entry_rua.delete(0, tk.END); entry_rua.insert(0, res[5] or "")
                entry_numero.delete(0, tk.END); entry_numero.insert(0, res[6] or "")
                entry_bairro.delete(0, tk.END); entry_bairro.insert(0, res[7] or "")
                entry_cidade.delete(0, tk.END); entry_cidade.insert(0, res[8] or "")
                entry_tel_cli.delete(0, tk.END); entry_tel_cli.insert(0, res[9] or "")
                entry_email_cli.delete(0, tk.END); entry_email_cli.insert(0, res[10] or "")
                marca = res[11] or "Selecione"
                combo_tipo_carro.set(marca if marca in marcas_modelos else "Selecione")
                atualizar_linhas()
                linha = res[12] or "Selecione"
                combo_linha.set(linha if linha in combo_linha['values'] else "Selecione")
                modelo = res[13] or "Selecione"
                combo_modelo.set(modelo if modelo in combo_modelo['values'] else "Selecione")
                ano = res[14] or "Selecione"
                combo_ano.set(ano if ano in combo_ano['values'] else "Selecione")
                combustivel = res[15] or "Selecione"
                combo_combustivel.set(combustivel if combustivel in combo_combustivel['values'] else "Selecione")
                if res[17]:
                    entry_data_atl.delete(0, tk.END); entry_data_atl.insert(0, res[17])
                
                carregar_historico_atualizacoes(cod_digitado)
                
                if str(tab_cli_hist) not in notebook_baixo.tabs():
                    notebook_baixo.add(tab_cli_hist, text=" 📜 Histórico de Atualizações do Cliente ")
            else:
                if str(tab_cli_hist) in notebook_baixo.tabs():
                    notebook_baixo.forget(tab_cli_hist)
        except Exception as e:
            print("Erro ao buscar por código:", e)

    entry_cod_cli.bind("<Return>", carregar_dados_por_codigo)
    entry_cod_cli.bind("<FocusOut>", carregar_dados_por_codigo)

    def carregar_clientes(termo_busca=None):
        for item in tabela_clientes.get_children():
            tabela_clientes.delete(item)
        
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            try:
                cursor.execute("""SELECT codigo, nome, tipo, documento, rua, numero, bairro, cidade,
                                  contato, email, data_atualizacao
                                  FROM clientes ORDER BY CAST(codigo AS INTEGER) ASC;""")
            except:
                cursor.execute("""SELECT codigo, nome, tipo, documento, rua, numero, bairro, cidade,
                                  contato, email, data_atualizacao
                                  FROM clientes ORDER BY codigo ASC;""")

            termo = termo_busca.strip().lower() if termo_busca else ""

            for row in cursor.fetchall():
                cod, nome, tipo, documento, rua, num, bairro, cidade, contato, email, dt_atl = row
                if cod and nome:
                    if termo:
                        linha_str = " ".join([str(v) if v else "" for v in row]).lower()
                        if termo not in linha_str:
                            continue

                    tabela_clientes.insert("", "end", values=(
                        cod, nome, tipo or "Particular", documento or "-", rua or "-", num or "-",
                        bairro or "-", cidade or "-", contato or "-", email or "-", dt_atl or "-"
                    ))
            cursor.close()
            conn.close()
        except Exception as e:
            print("Erro ao carregar clientes do Supabase:", e)

    carregar_clientes()

    def realizar_busca_geral(event=None):
        termo = entry_busca_geral.get().strip()
        carregar_clientes(termo)

    entry_busca_geral.bind("<Return>", realizar_busca_geral)

    def ao_selecionar_cliente(event):
        selecao = tabela_clientes.selection()
        if selecao:
            item_selecionado = tabela_clientes.item(selecao[0], "values")
            cod_buscado = item_selecionado[0]
            entry_cod_cli.delete(0, tk.END)
            entry_cod_cli.insert(0, cod_buscado)
            carregar_dados_por_codigo()

    tabela_clientes.bind("<<TreeviewSelect>>", ao_selecionar_cliente)

    def salvar_cliente():
        cod = entry_cod_cli.get().strip()
        nome = entry_nome_cli.get().strip()
        tipo = combo_tipo_cli.get().strip()
        doc = entry_doc_cli.get().strip()
        cep = entry_cep.get().strip()
        rua = entry_rua.get().strip()
        numero = entry_numero.get().strip()
        bairro = entry_bairro.get().strip()
        cidade = entry_cidade.get().strip()
        tel = entry_tel_cli.get().strip()
        email = entry_email_cli.get().strip()
        
        m_cent = combo_tipo_carro.get().strip()
        modulo = combo_linha.get().strip()
        mac = combo_modelo.get().strip()
        operadora = combo_ano.get().strip()
        linha = combo_combustivel.get().strip()
        iccid = ""
        data_atl = formatar_data(entry_data_atl.get().strip())

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

            motivo_alt = ""
            if existe:
                from tkinter import simpledialog
                motivo_alt = simpledialog.askstring("Motivo da Alteração", f"O cliente código '{cod}' já existe.\nDigite o motivo desta alteração/atualização cadastral:", parent=janela_principal)
                if not motivo_alt:
                    messagebox.showwarning("Atenção", "A atualização foi cancelada. O motivo é obrigatório.")
                    cursor.close(); conn.close()
                    return

                cursor.execute(
                    """UPDATE clientes SET nome = %s, tipo = %s, documento = %s, cep = %s, rua = %s, 
                       numero = %s, bairro = %s, cidade = %s, contato = %s, email = %s, 
                       modelo_central = %s, modulo = %s, mac_address = %s, operadora = %s, 
                       linha_numero = %s, iccid = %s, data_atualizacao = %s WHERE codigo = %s;""",
                    (nome, tipo, doc, cep, rua, numero, bairro, cidade, tel, email, 
                     m_cent, modulo, mac, operadora, linha, iccid, data_atl, cod)
                )
                acao_log = f"Atualização de cadastro: {nome} | Motivo: {motivo_alt}"
            else:
                cursor.execute(
                    """INSERT INTO clientes (codigo, nome, tipo, documento, cep, rua, numero, bairro, cidade, 
                       contato, email, modelo_central, modulo, mac_address, operadora, linha_numero, iccid, data_atualizacao) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                    (cod, nome, tipo, doc, cep, rua, numero, bairro, cidade, tel, email, 
                     m_cent, modulo, mac, operadora, linha, iccid, data_atl)
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
            carregar_clientes()
            carregar_historico_atualizacoes(cod)
            
            if str(tab_cli_hist) not in notebook_baixo.tabs():
                notebook_baixo.add(tab_cli_hist, text=" 📜 Histórico de Atualizações do Cliente ")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar cliente no Supabase: {e}")

    # --- BOTÕES DE AÇÃO ---
    f_botoes = tk.Frame(frame_principal)
    f_botoes.pack(fill="x", pady=(4, 2))
    
    tk.Button(f_botoes, text="💾 Salvar / Atualizar Cliente", command=salvar_cliente, bg="#38761D", fg="white", font=("Arial", 9, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 5))
    tk.Button(f_botoes, text="🧹 Limpar Campos", command=limpar_formulario, bg="#B45F06", fg="white", font=("Arial", 9, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 5))
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

    tk.Label(frame_principal, text="👨‍🔧 Mecânicos e técnicos", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_form = tk.LabelFrame(frame_principal, text=" Dados cadastrais do técnico ", font=("Arial", 9, "bold"), padx=15, pady=10)
    f_form.pack(fill="x", pady=(0, 10))

    f_l1 = tk.Frame(f_form)
    f_l1.pack(fill="x", pady=(0, 6))

    tk.Label(f_l1, text="Cód:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_cod_tec = tk.Entry(f_l1, font=("Arial", 10), width=10)
    entry_cod_tec.pack(side="left", padx=(0, 15))
    entry_cod_tec.insert(0, "")

    tk.Label(f_l1, text="Nome / Razão Social:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_nome_tec = tk.Entry(f_l1, font=("Arial", 10), width=32)
    entry_nome_tec.pack(side="left", padx=(0, 15))

    tk.Label(f_l1, text="CPF/CNPJ:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_doc_tec = tk.Entry(f_l1, font=("Arial", 10), width=18)
    entry_doc_tec.pack(side="left")

    f_l2 = tk.Frame(f_form)
    f_l2.pack(fill="x", pady=(0, 4))

    tk.Label(f_l2, text="CEP:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_cep_tec = tk.Entry(f_l2, font=("Arial", 10), width=10)
    entry_cep_tec.pack(side="left", padx=(0, 8))
    tk.Label(f_l2, text="Rua:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_rua_tec = tk.Entry(f_l2, font=("Arial", 10), width=30)
    entry_rua_tec.pack(side="left", padx=(0, 8))
    tk.Label(f_l2, text="Nº:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_numero_tec = tk.Entry(f_l2, font=("Arial", 10), width=7)
    entry_numero_tec.pack(side="left", padx=(0, 8))
    tk.Label(f_l2, text="Bairro:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_bairro_tec = tk.Entry(f_l2, font=("Arial", 10), width=18)
    entry_bairro_tec.pack(side="left", padx=(0, 8))
    tk.Label(f_l2, text="Cidade:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_cidade_tec = tk.Entry(f_l2, font=("Arial", 10), width=18)
    entry_cidade_tec.pack(side="left")

    f_l3 = tk.Frame(f_form)
    f_l3.pack(fill="x", pady=(0, 4))
    tk.Label(f_l3, text="Contato:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_tel_tec = tk.Entry(f_l3, font=("Arial", 10), width=18)
    entry_tel_tec.pack(side="left", padx=(0, 15))
    tk.Label(f_l3, text="E-mail:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 2))
    entry_email_tec = tk.Entry(f_l3, font=("Arial", 10), width=38)
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

    def consultar_cep_tecnico(event=None):
        cep_limpo = "".join(filter(str.isdigit, entry_cep_tec.get()))
        if len(cep_limpo) != 8:
            return
        try:
            import urllib.request
            import json
            url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
            req = urllib.request.Request(url, headers={"User-Agent": "MayerCartch/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
            if "erro" not in dados:
                entry_rua_tec.delete(0, tk.END); entry_rua_tec.insert(0, dados.get("logradouro", ""))
                entry_bairro_tec.delete(0, tk.END); entry_bairro_tec.insert(0, dados.get("bairro", ""))
                entry_cidade_tec.delete(0, tk.END); entry_cidade_tec.insert(0, dados.get("localidade", ""))
                entry_numero_tec.focus_set()
        except Exception as e:
            print("Erro ao consultar CEP do técnico:", e)

    entry_cep_tec.bind("<Return>", consultar_cep_tecnico)
    entry_cep_tec.bind("<FocusOut>", consultar_cep_tecnico)

    frame_tabela_tec = tk.Frame(frame_principal)
    frame_tabela_tec.pack(fill="both", expand=True, pady=(0, 10))

    colunas_tec = ("Cod", "Nome", "Documento", "CEP", "Rua", "Nº", "Bairro", "Cidade", "Contato", "Email")
    tabela_tecnicos = ttk.Treeview(frame_tabela_tec, columns=colunas_tec, show="headings", height=11)
    
    tabela_tecnicos.heading("Cod", text="Cód")
    tabela_tecnicos.column("Cod", width=70, anchor="center")
    tabela_tecnicos.heading("Nome", text="Nome / Razão Social")
    tabela_tecnicos.column("Nome", width=220, anchor="w")
    tabela_tecnicos.heading("Documento", text="CNPJ / CPF")
    tabela_tecnicos.column("Documento", width=130, anchor="center")
    for coluna, titulo, largura in [("CEP", "CEP", 90), ("Rua", "Rua", 180), ("Nº", "Nº", 55), ("Bairro", "Bairro", 130), ("Cidade", "Cidade", 130)]:
        tabela_tecnicos.heading(coluna, text=titulo)
        tabela_tecnicos.column(coluna, width=largura, anchor="w")
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
            cursor.execute("SELECT codigo, nome, documento, cep, rua, numero, bairro, cidade, contato, email FROM tecnicos;")
            for cod, nome, doc, cep, rua, numero, bairro, cidade, tel, email in cursor.fetchall():
                if cod and nome:
                    tabela_tecnicos.insert("", "end", values=(cod, nome, doc or "", cep or "", rua or "", numero or "", bairro or "", cidade or "", tel or "", email or ""))
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

            entry_doc_tec.delete(0, tk.END)
            entry_doc_tec.insert(0, vals[2] if vals[2] != "None" else "")
            entry_cep_tec.delete(0, tk.END); entry_cep_tec.insert(0, vals[3] if vals[3] != "None" else "")
            entry_rua_tec.delete(0, tk.END); entry_rua_tec.insert(0, vals[4] if vals[4] != "None" else "")
            entry_numero_tec.delete(0, tk.END); entry_numero_tec.insert(0, vals[5] if vals[5] != "None" else "")
            entry_bairro_tec.delete(0, tk.END); entry_bairro_tec.insert(0, vals[6] if vals[6] != "None" else "")
            entry_cidade_tec.delete(0, tk.END); entry_cidade_tec.insert(0, vals[7] if vals[7] != "None" else "")

            entry_tel_tec.delete(0, tk.END)
            entry_tel_tec.insert(0, vals[8] if vals[8] != "None" else "")

            entry_email_tec.delete(0, tk.END)
            entry_email_tec.insert(0, vals[9] if vals[9] != "None" else "")

    tabela_tecnicos.bind("<<TreeviewSelect>>", ao_selecionar_tecnico)

    def salvar_tecnico():
        cod = entry_cod_tec.get().strip()
        nome = entry_nome_tec.get().strip()
        doc = formatar_cpf_cnpj(entry_doc_tec.get().strip())
        tel = formatar_telefone(entry_tel_tec.get().strip())
        cep = entry_cep_tec.get().strip()
        rua = entry_rua_tec.get().strip()
        numero = entry_numero_tec.get().strip()
        bairro = entry_bairro_tec.get().strip()
        cidade = entry_cidade_tec.get().strip()
        end = ", ".join(parte for parte in [rua, numero, bairro, cidade] if parte)
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
                    "UPDATE tecnicos SET nome = %s, documento = %s, endereco = %s, cep = %s, rua = %s, numero = %s, bairro = %s, cidade = %s, contato = %s, email = %s WHERE codigo = %s;",
                    (nome, doc, end, cep, rua, numero, bairro, cidade, tel, email, cod)
                )
                acao_log = f"Atualização de cadastro do técnico [{cod}] {nome}"
            else:
                cursor.execute(
                    "INSERT INTO tecnicos (codigo, nome, documento, endereco, cep, rua, numero, bairro, cidade, contato, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                    (cod, nome, doc, end, cep, rua, numero, bairro, cidade, tel, email)
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
            entry_cod_tec.insert(0, f"{tabela_tecnicos.get_children().__len__() + 2:03d}") # Gera o próximo código do técnico automaticamente
            entry_nome_tec.delete(0, tk.END)
            entry_doc_tec.delete(0, tk.END)
            entry_cep_tec.delete(0, tk.END)
            entry_rua_tec.delete(0, tk.END)
            entry_numero_tec.delete(0, tk.END)
            entry_bairro_tec.delete(0, tk.END)
            entry_cidade_tec.delete(0, tk.END)
            entry_tel_tec.delete(0, tk.END)
            entry_email_tec.delete(0, tk.END)
            carregar_tecnicos()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar técnico no Supabase: {e}")

    f_botoes = tk.Frame(frame_principal)
    f_botoes.pack(fill="x", pady=(5, 5))
    
    tk.Button(f_botoes, text="💾 Salvar / Atualizar Técnico", command=salvar_tecnico, bg="#38761D", fg="white", font=("Arial", 10, "bold"), height=2).pack(fill="x")
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(5, 0))