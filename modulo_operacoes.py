import tkinter as tk
from tkinter import messagebox
from tkinter import ttk, simpledialog
from datetime import datetime
import config
import modulo_financeiro

# ==========================================
# TELA DE ENTRADA / ORDEM DE COMPRA (OC) - SUPABASE
# ==========================================
def mostrar_tela_entrada(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=20, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📥 Registrar Entrada / Ordem de Compra (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_topo = tk.Frame(frame_principal)
    f_topo.pack(fill="x", pady=(0, 10))

    tk.Label(f_topo, text="Nº da Ordem de Compra:", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
    entry_ordem = tk.Entry(f_topo, font=("Arial", 10), width=15)
    entry_ordem.pack(side="left", padx=(0, 20))
    entry_ordem.insert(0, "OC-")

    tk.Label(f_topo, text="Data:", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
    entry_data_oc = tk.Entry(f_topo, font=("Arial", 10), width=18)
    entry_data_oc.pack(side="left", padx=(0, 5))
    entry_data_oc.insert(0, datetime.now().strftime("%d/%m/%Y"))

    tk.Label(f_topo, text="Fornecedor:", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
    entry_fornecedor = tk.Entry(f_topo, font=("Arial", 10), width=30)
    entry_fornecedor.pack(side="left", padx=(0, 5))

    frame_tabela_container = tk.Frame(frame_principal)
    frame_tabela_container.pack(fill="both", expand=True, pady=(0, 10))

    colunas = ("Cod", "Descricao", "ValorUnit", "Qtd", "ValorTotal")
    tabela_oc = ttk.Treeview(frame_tabela_container, columns=colunas, show="headings", height=7)
    
    for col, txt in zip(colunas, ["Código", "Descrição do Item", "Valor Unit. (R$)", "Quantidade", "Valor Total (R$)"]):
        tabela_oc.heading(col, text=txt)
    
    tabela_oc.column("Cod", width=90, anchor="center")
    tabela_oc.column("Descricao", width=330, anchor="w")
    tabela_oc.column("ValorUnit", width=130, anchor="center")
    tabela_oc.column("Qtd", width=90, anchor="center")
    tabela_oc.column("ValorTotal", width=140, anchor="center")

    scrollbar_oc = ttk.Scrollbar(frame_tabela_container, orient="vertical", command=tabela_oc.yview)
    tabela_oc.configure(yscrollcommand=scrollbar_oc.set)
    tabela_oc.pack(side="left", fill="both", expand=True)
    scrollbar_oc.pack(side="right", fill="y")

    f_add_item = tk.LabelFrame(frame_principal, text=" Adicionar Item à Ordem por Código ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_add_item.pack(fill="x", pady=(0, 8))

    f_campos_item = tk.Frame(f_add_item)
    f_campos_item.pack(fill="x")

    tk.Label(f_campos_item, text="Código:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_add_cod = tk.Entry(f_campos_item, font=("Arial", 10), width=15)
    entry_add_cod.pack(side="left", padx=(0, 10))

    tk.Label(f_campos_item, text="Qtd:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_add_qtd = tk.Entry(f_campos_item, font=("Arial", 10), width=8)
    entry_add_qtd.pack(side="left", padx=(0, 15))

    def buscar_produto_por_codigo(codigo_procurado):
        conn = config.obter_conexao_banco()
        if not conn:
            return None, 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tipo, valor_unitario FROM estoque WHERE cod = %s;", (str(codigo_procurado).strip(),))
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            if res:
                return str(res[0]), float(res[1] or 0.0)
        except Exception as e:
            print("Erro ao buscar produto:", e)
        return None, 0.0

    itens_memoria = []

    def adicionar_item_na_lista():
        cod = entry_add_cod.get().strip()
        qtd_str = entry_add_qtd.get().strip()
        if not cod or not qtd_str:
            messagebox.showwarning("Atenção", "Informe o código e a quantidade!")
            return
        try:
            qtd = int(qtd_str)
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida.")
            return

        descricao, valor_unit = buscar_produto_por_codigo(cod)
        if not descricao:
            resposta = messagebox.askyesno(
                "Produto Não Cadastrado", 
                f"O código '{cod}' não está cadastrado no sistema.\n\nDeseja ir para a tela de Cadastro de Equipamentos e Produtos agora?"
            )
            if resposta:
                modulo_financeiro.mostrar_tela_fornecedores(
                    janela_principal, 
                    limpar_tela, 
                    centralizar_janela, 
                    lambda: mostrar_tela_entrada(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback)
                )
            return

        valor_total = valor_unit * qtd
        itens_memoria.append({"cod": cod, "descricao": descricao, "valor_unit": valor_unit, "qtd": qtd, "valor_total": valor_total})
        tabela_oc.insert("", "end", values=(cod, descricao, f"R$ {valor_unit:.2f}".replace('.', ','), qtd, f"R$ {valor_total:.2f}".replace('.', ',')))
        entry_add_cod.delete(0, tk.END)
        entry_add_qtd.delete(0, tk.END)
        atualizar_subtotal()

    tk.Button(f_campos_item, text="➕ Adicionar à Ordem", command=adicionar_item_na_lista, bg="#2F5597", fg="white", font=("Arial", 9, "bold"), width=16).pack(side="left")

    f_baixo = tk.Frame(frame_principal)
    f_baixo.pack(fill="x", pady=(5, 5))

    label_subtotal = tk.Label(f_baixo, text="Subtotal da Ordem: R$ 0,00", font=("Arial", 13, "bold"), fg="#38761D")
    label_subtotal.pack(side="left")

    def atualizar_subtotal():
        sub = sum(item["valor_total"] for item in itens_memoria)
        label_subtotal.config(text=f"Subtotal da Ordem: R$ {sub:.2f}".replace('.', ','))

    def salvar_ordem_compra():
        if not itens_memoria:
            messagebox.showwarning("Atenção", "Adicione itens à OC!")
            return
        num_ordem = entry_ordem.get().strip()
        data_oc = entry_data_oc.get().strip()
        fornecedor = entry_fornecedor.get().strip()

        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Erro ao conectar com o banco na nuvem.")
            return

        try:
            cursor = conn.cursor()
            for item in itens_memoria:
                tipo = item["descricao"]
                qtd_comprada = item["qtd"]

                # Atualiza total e disponivel no estoque
                cursor.execute(
                    "UPDATE estoque SET total = total + %s, disponivel = disponivel + %s WHERE LOWER(tipo) = LOWER(%s);",
                    (qtd_comprada, qtd_comprada, tipo)
                )

                # Registra na tabela entrada
                cursor.execute(
                    "INSERT INTO entrada (data, fornecedor_descricao, nome_item, quantidade, usuario, status) VALUES (%s, %s, %s, %s, %s, %s);",
                    (data_oc, f"Ordem de Compra: {num_ordem}", tipo, qtd_comprada, config.usuario_logado, "ATIVO")
                )

            conn.commit()
            cursor.close()
            conn.close()

            config.atualizar_feed_estoque_critico()
            messagebox.showinfo("Sucesso", f"Ordem de Compra {num_ordem} registrada na nuvem!")
            for i in tabela_oc.get_children(): 
                tabela_oc.delete(i)
            itens_memoria.clear()
            atualizar_subtotal()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar OC: {e}")

    tk.Button(f_baixo, text="💾 Registrar Ordem de Compra", command=salvar_ordem_compra, bg="#38761D", fg="white", font=("Arial", 11, "bold"), height=2).pack(side="right")
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(8, 0))


# ==========================================
# TELA DE SAÍDA / ORDEM DE SERVIÇO (OS) - SUPABASE
# ==========================================
def mostrar_tela_saida(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=20, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📤 Registrar Saída / Ordem de Serviço (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_topo_os = tk.LabelFrame(frame_principal, text=" Informações da Ordem de Serviço, Cliente e Técnico ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_topo_os.pack(fill="x", pady=(0, 10))

    f_l1 = tk.Frame(f_topo_os)
    f_l1.pack(fill="x", pady=(0, 6))

    tk.Label(f_l1, text="Nº da OS:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_num_os = tk.Entry(f_l1, font=("Arial", 10), width=15)
    entry_num_os.pack(side="left", padx=(0, 15))
    entry_num_os.insert(0, "OS-000001")

    tk.Label(f_l1, text="Cód. Cliente:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_cod_cli = tk.Entry(f_l1, font=("Arial", 10), width=10)
    entry_cod_cli.pack(side="left", padx=(0, 8))

    label_info_cliente = tk.Label(f_l1, text="Cliente: [Não informado]", font=("Arial", 10, "italic"), fg="#555555")
    label_info_cliente.pack(side="left")

    f_l_tec = tk.Frame(f_topo_os)
    f_l_tec.pack(fill="x", pady=(4, 6))

    tk.Label(f_l_tec, text="Cód. Técnico:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_cod_tec = tk.Entry(f_l_tec, font=("Arial", 10), width=10)
    entry_cod_tec.pack(side="left", padx=(0, 8))

    label_info_tecnico = tk.Label(f_l_tec, text="Técnico: [Não informado]", font=("Arial", 10, "italic"), fg="#555555")
    label_info_tecnico.pack(side="left")

    f_l2 = tk.Frame(f_topo_os)
    f_l2.pack(fill="x", pady=(4, 0))

    tk.Label(f_l2, text="Valor Mão de Obra (R$):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_mao_obra = tk.Entry(f_l2, font=("Arial", 10), width=12)
    entry_mao_obra.pack(side="left", padx=(0, 20))
    entry_mao_obra.insert(0, "0,00")

    def buscar_cliente_por_codigo(cod_cliente):
        conn = config.obter_conexao_banco()
        if not conn:
            return None, None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT nome, tipo FROM clientes WHERE codigo = %s;", (str(cod_cliente).strip(),))
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            if res:
                return res[0], res[1]
        except:
            pass
        return None, None

    def buscar_tecnico_por_codigo(cod_tecnico):
        conn = config.obter_conexao_banco()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM tecnicos WHERE codigo = %s;", (str(cod_tecnico).strip(),))
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            if res:
                return res[0]
        except:
            pass
        return None

    def ao_digitar_cliente(event=None):
        cod = entry_cod_cli.get().strip()
        if not cod:
            label_info_cliente.config(text="Cliente: [Não informado]", fg="#555555")
            return
        nome, tipo = buscar_cliente_por_codigo(cod)
        if nome:
            label_info_cliente.config(text=f"Cliente: {nome} ({tipo})", fg="#38761D")
        else:
            label_info_cliente.config(text="Cliente: ⚠️ Não cadastrado!", fg="#CC0000")

    def ao_digitar_tecnico(event=None):
        cod = entry_cod_tec.get().strip()
        if not cod:
            label_info_tecnico.config(text="Técnico: [Não informado]", fg="#555555")
            return
        nome = buscar_tecnico_por_codigo(cod)
        if nome:
            label_info_tecnico.config(text=f"Técnico: {nome}", fg="#38761D")
        else:
            label_info_tecnico.config(text="Técnico: ⚠️ Não cadastrado!", fg="#CC0000")

    entry_cod_cli.bind("<KeyRelease>", ao_digitar_cliente)
    entry_cod_tec.bind("<KeyRelease>", ao_digitar_tecnico)

    frame_tabela_container = tk.Frame(frame_principal)
    frame_tabela_container.pack(fill="both", expand=True, pady=(0, 10))

    colunas = ("Cod", "Equipamento", "QtdSaida", "Observacao")
    tabela_os = ttk.Treeview(frame_tabela_container, columns=colunas, show="headings", height=5)
    for col, txt in zip(colunas, ["Cód. Equipamento", "Nome do Equipamento", "Quantidade", "Observação"]):
        tabela_os.heading(col, text=txt)
    tabela_os.pack(side="left", fill="both", expand=True)

    f_add_item_os = tk.LabelFrame(frame_principal, text=" Adicionar Equipamento à OS por Código ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_add_item_os.pack(fill="x", pady=(0, 10))

    f_campos_item_os = tk.Frame(f_add_item_os)
    f_campos_item_os.pack(fill="x")

    tk.Label(f_campos_item_os, text="Cód:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_cod = tk.Entry(f_campos_item_os, font=("Arial", 10), width=12)
    entry_item_cod.pack(side="left", padx=(0, 10))

    tk.Label(f_campos_item_os, text="Qtd:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_qtd = tk.Entry(f_campos_item_os, font=("Arial", 10), width=8)
    entry_item_qtd.pack(side="left", padx=(0, 10))

    tk.Label(f_campos_item_os, text="Obs:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_obs = tk.Entry(f_campos_item_os, font=("Arial", 10), width=22)
    entry_item_obs.pack(side="left", padx=(0, 15))

    def buscar_equipamento_por_codigo(cod_busca):
        conn = config.obter_conexao_banco()
        if not conn:
            return None, 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tipo, disponivel FROM estoque WHERE cod = %s;", (str(cod_busca).strip(),))
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            if res:
                return str(res[0]), int(res[1] or 0)
        except:
            pass
        return None, 0

    itens_saida_memoria = []

    def adicionar_item_os_lista():
        cod = entry_item_cod.get().strip()
        qtd_str = entry_item_qtd.get().strip()
        obs = entry_item_obs.get().strip()
        if not cod or not qtd_str:
            messagebox.showwarning("Atenção", "Preencha código e quantidade!")
            return
        try:
            qtd = int(qtd_str)
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida.")
            return

        nome_equipamento, estoque_disponivel = buscar_equipamento_por_codigo(cod)
        if not nome_equipamento:
            messagebox.showerror("Erro", f"Código '{cod}' não encontrado no estoque!")
            return
        if qtd > estoque_disponivel:
            messagebox.showerror("Estoque", f"Estoque insuficiente ({estoque_disponivel} disponíveis).")
            return

        itens_saida_memoria.append({"cod": cod, "nome": nome_equipamento, "qtd": qtd, "obs": obs})
        tabela_os.insert("", "end", values=(cod, nome_equipamento, qtd, obs))
        entry_item_cod.delete(0, tk.END)
        entry_item_qtd.delete(0, tk.END)
        entry_item_obs.delete(0, tk.END)

    tk.Button(f_campos_item_os, text="➕ Adicionar à OS", command=adicionar_item_os_lista, bg="#2F5597", fg="white", font=("Arial", 9, "bold")).pack(side="left")

    f_baixo_os = tk.Frame(frame_principal)
    f_baixo_os.pack(fill="x", pady=(5, 5))

    def salvar_ordem_servico():
        if not itens_saida_memoria:
            messagebox.showwarning("Atenção", "Adicione itens à OS!")
            return
        num_os = entry_num_os.get().strip()
        cod_cli = entry_cod_cli.get().strip()
        nome_cliente, tipo_cliente = buscar_cliente_por_codigo(cod_cli)
        if not nome_cliente:
            messagebox.showwarning("Atenção", "Informe um código de cliente válido!")
            return

        try:
            val_mao_obra = float(entry_mao_obra.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "O valor da mão de obra deve ser um número válido.")
            return

        data_hoje = datetime.now().strftime("%d/%m/%Y")
        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Erro ao conectar com o banco na nuvem.")
            return

        try:
            cursor = conn.cursor()
            for index, item in enumerate(itens_saida_memoria):
                tipo = item["nome"]
                qtd_saida = item["qtd"]
                
                if index == 0 and val_mao_obra > 0:
                    obs_final = f"OS: {num_os} | Cliente: {nome_cliente} ({tipo_cliente}) | Mão de Obra: R$ {val_mao_obra:.2f} | {item['obs']}"
                else:
                    obs_final = f"OS: {num_os} | Cliente: {nome_cliente} ({tipo_cliente}) | {item['obs']}"

                # Baixa no disponivel do estoque
                cursor.execute(
                    "UPDATE estoque SET disponivel = disponivel - %s WHERE LOWER(tipo) = LOWER(%s);",
                    (qtd_saida, tipo)
                )

                # Registra na tabela uso
                cursor.execute(
                    "INSERT INTO uso (data, local_setor, nome_equipamento, quantidade_usada, observacao, usuario, status) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                    (data_hoje, f"{nome_cliente} ({tipo_cliente})", tipo, qtd_saida, obs_final, config.usuario_logado, "ATIVO")
                )

            conn.commit()
            cursor.close()
            conn.close()

            config.atualizar_feed_estoque_critico()
            messagebox.showinfo("Sucesso", f"Ordem de Serviço {num_os} registrada com sucesso na nuvem!")
            for i in tabela_os.get_children(): 
                tabela_os.delete(i)
            itens_saida_memoria.clear()
            entry_cod_cli.delete(0, tk.END)
            entry_mao_obra.delete(0, tk.END)
            entry_mao_obra.insert(0, "0,00")
            label_info_cliente.config(text="Cliente: [Não informado]", fg="#555555")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar OS: {e}")

    tk.Button(f_baixo_os, text="💾 Registrar Ordem de Serviço (Saída)", command=salvar_ordem_servico, bg="#2F5597", fg="white", font=("Arial", 11, "bold"), height=2).pack(side="right")
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(8, 0))


# ==========================================
# TELA DE ESTORNO UNIFICADA - SUPABASE
# ==========================================
def mostrar_tela_estorno(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=10)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="🔄 Central de Estornos (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 8))

    notebook_estorno = ttk.Notebook(frame_principal)
    notebook_estorno.pack(fill="both", expand=True, pady=(0, 10))

    tab_oc = ttk.Frame(notebook_estorno)
    notebook_estorno.add(tab_oc, text="  📦 Ordens de Compra (OC / Fornecedor)  ")

    f_oc_esq = tk.Frame(tab_oc, padx=10, pady=10)
    f_oc_esq.pack(side="left", fill="both", expand=True)

    tk.Label(f_oc_esq, text="Ordens de Compra Registradas:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 4))
    
    arvore_oc = ttk.Treeview(f_oc_esq, columns=("Detalhes", "Status", "ObsEstorno"), show="tree headings", height=13)
    arvore_oc.heading("#0", text="OC / Itens / Histórico")
    arvore_oc.heading("Detalhes", text="Data / ID")
    arvore_oc.column("Detalhes", width=180, anchor="w")
    arvore_oc.heading("Status", text="Status")
    arvore_oc.column("Status", width=100, anchor="center")
    arvore_oc.heading("ObsEstorno", text="Informações de Estorno")
    arvore_oc.column("ObsEstorno", width=340, anchor="w")
    arvore_oc.pack(side="left", fill="both", expand=True)

    scrollbar_oc = ttk.Scrollbar(f_oc_esq, orient="vertical", command=arvore_oc.yview)
    arvore_oc.configure(yscrollcommand=scrollbar_oc.set)
    scrollbar_oc.pack(side="right", fill="y")

    def carregar_ocs_estorno():
        for i in arvore_oc.get_children(): 
            arvore_oc.delete(i)
        
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, data, fornecedor_descricao, nome_item, quantidade, status FROM entrada ORDER BY id ASC;")
            ocs_dict = {}
            for row_id, data, desc, tipo, qtd, status in cursor.fetchall():
                if desc and "Ordem de Compra:" in str(desc):
                    num_oc = str(desc).split(":")[-1].strip()
                    if num_oc not in ocs_dict:
                        ocs_dict[num_oc] = []
                    ocs_dict[num_oc].append({"id": row_id, "tipo": tipo, "qtd": int(qtd) if qtd else 0, "data": data, "status": status or "ATIVO"})
            cursor.close()
            conn.close()

            for oc_num, itens in ocs_dict.items():
                ativos = [it for it in itens if it["qtd"] > 0]
                data_oc = itens[0]["data"]
                
                st_pai = "ESTORNADA" if not ativos else "ATIVO"
                tag_pai = "normal" if st_pai == "ATIVO" else "estornado"
                txt_pai = f"📋 {oc_num}" if st_pai == "ATIVO" else f"❌ [ESTORNADA] {oc_num}"

                pai_id = arvore_oc.insert("", "end", text=txt_pai, values=(f"Data: {data_oc}", st_pai, f"Ativos: {len(ativos)}/{len(itens)} itens"), tags=(tag_pai,))
                
                for it in itens:
                    qtd_item = it["qtd"]
                    st_txt = str(it["status"])
                    
                    if qtd_item == 0:
                        tag_nome = "estornado"
                        txt_label = f"❌ [ESTORNADO] {it['tipo']}"
                        status_str = "ESTORNADO"
                    else:
                        tag_nome = "normal"
                        txt_label = f"🔹 {it['tipo']}"
                        status_str = "ATIVO"
                    
                    arvore_oc.insert(pai_id, "end", text=txt_label, values=(f"ID: {it['id']} | Qtd: {qtd_item}", status_str, st_txt if st_txt != "ATIVO" else "-"), tags=(str(it['id']), tag_nome))
        except Exception as e:
            print("Erro ao carregar OCs para estorno:", e)

        arvore_oc.tag_configure("estornado", foreground="#999999")

    carregar_ocs_estorno()

    def estornar_oc_selecionada():
        selecionado = arvore_oc.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um item específico na árvore!")
            return

        item_id = selecionado[0]
        texto_item = arvore_oc.item(item_id, "text")
        tags_item = arvore_oc.item(item_id, "tags")

        if "📋" in texto_item or "❌ [ESTORNADA]" in texto_item:
            messagebox.showinfo("Aviso", "Por favor, selecione o item específico (filho) da OC para estornar.")
            return

        if tags_item and tags_item[0] != "estornado":
            row_id = int(tags_item[0])
            
            conn = config.obter_conexao_banco()
            if not conn:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT nome_item, quantidade FROM entrada WHERE id = %s;", (row_id,))
                res = cursor.fetchone()
                cursor.close()
                conn.close()
                if not res:
                    return
                tipo_item, qtd_atual = res[0], int(res[1] or 0)
            except:
                return

            if qtd_atual <= 0:
                messagebox.showinfo("Aviso", "Este item já está com quantidade zero.")
                return

            if qtd_atual > 1:
                qtd_para_estornar = simpledialog.askinteger("Estorno", f"Quantidade atual: {qtd_atual}\nDigite a quantidade a estornar:", initialvalue=qtd_atual, minvalue=1, maxvalue=qtd_atual)
                if not qtd_para_estornar:
                    return
            else:
                if not messagebox.askyesno("Confirmar", "Confirmar o estorno deste item (quantidade 1)?"):
                    return
                qtd_para_estornar = 1

            # Executa estorno no banco
            try:
                conn_e = config.obter_conexao_banco()
                cursor_e = conn_e.cursor()
                timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Remove do estoque (total e disponivel)
                cursor_e.execute(
                    "UPDATE estoque SET total = GREATEST(0, total - %s), disponivel = GREATEST(0, disponivel - %s) WHERE LOWER(tipo) = LOWER(%s);",
                    (qtd_para_estornar, qtd_para_estornar, tipo_item)
                )

                novo_saldo = qtd_atual - qtd_para_estornar
                nova_auditoria = f"ESTORNADO ({qtd_para_estornar} un) em {timestamp} por {config.usuario_logado}"

                cursor_e.execute(
                    "UPDATE entrada SET quantidade = %s, status = %s WHERE id = %s;",
                    (novo_saldo, nova_auditoria, row_id)
                )

                conn_e.commit()
                cursor_e.close()
                conn_e.close()

                config.atualizar_feed_estoque_critico()
                messagebox.showinfo("Sucesso", "Estorno registrado na nuvem!")
                carregar_ocs_estorno()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao executar estorno: {e}")

    f_botoes_oc = tk.Frame(tab_oc, padx=10, pady=5)
    f_botoes_oc.pack(fill="x")
    tk.Button(f_botoes_oc, text="🔄 Executar Estorno", command=estornar_oc_selecionada, bg="#CC0000", fg="white", font=("Arial", 9, "bold"), height=2).pack(fill="x")

    tab_os = ttk.Frame(notebook_estorno)
    notebook_estorno.add(tab_os, text="  📋 Ordens de Serviço (OS / Inventário)  ")

    f_os_esq = tk.Frame(tab_os, padx=10, pady=10)
    f_os_esq.pack(side="left", fill="both", expand=True)

    tk.Label(f_os_esq, text="Ordens de Serviço Registradas:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 4))
    
    arvore_os = ttk.Treeview(f_os_esq, columns=("Detalhes", "Status", "ObsEstorno"), show="tree headings", height=13)
    arvore_os.heading("#0", text="OS / Equipamentos / Histórico")
    arvore_os.heading("Detalhes", text="Data / ID")
    arvore_os.column("Detalhes", width=180, anchor="w")
    arvore_os.heading("Status", text="Status")
    arvore_os.column("Status", width=100, anchor="center")
    arvore_os.heading("ObsEstorno", text="Informações de Devolução")
    arvore_os.column("ObsEstorno", width=340, anchor="w")
    arvore_os.pack(side="left", fill="both", expand=True)

    scrollbar_os = ttk.Scrollbar(f_os_esq, orient="vertical", command=arvore_os.yview)
    arvore_os.configure(yscrollcommand=scrollbar_os.set)
    scrollbar_os.pack(side="right", fill="y")

    def carregar_oss_estorno():
        for i in arvore_os.get_children(): 
            arvore_os.delete(i)
        
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, data, local_setor, nome_equipamento, quantidade_usada, observacao, status FROM uso ORDER BY id ASC;")
            oss_dict = {}
            for row_id, data, cliente, tipo, qtd, obs, status in cursor.fetchall():
                if obs and "OS:" in str(obs):
                    num_os = "OS-000001"
                    for parte in str(obs).split("|"):
                        if "OS:" in parte: 
                            num_os = parte.split(":")[-1].strip()
                            break

                    if num_os not in oss_dict:
                        oss_dict[num_os] = []
                    oss_dict[num_os].append({"id": row_id, "tipo": tipo, "qtd": int(qtd) if qtd else 0, "cliente": cliente, "data": data, "status": status or "ATIVO"})
            cursor.close()
            conn.close()

            for os_num, itens in oss_dict.items():
                ativos = [it for it in itens if it["qtd"] > 0]
                data_os = itens[0]["data"]
                
                st_pai = "ESTORNADA" if not ativos else "ATIVO"
                tag_pai = "normal" if st_pai == "ATIVO" else "estornado"
                txt_pai = f"📋 {os_num}" if st_pai == "ATIVO" else f"❌ [ESTORNADA] {os_num}"

                pai_id = arvore_os.insert("", "end", text=txt_pai, values=(f"Data: {data_os}", st_pai, f"Ativos: {len(ativos)}/{len(itens)} itens"), tags=(tag_pai,))
                
                for it in itens:
                    qtd_item = it["qtd"]
                    st_txt = str(it["status"])
                    
                    if qtd_item == 0:
                        tag_nome = "estornado"
                        txt_label = f"❌ [ESTORNADO] {it['tipo']}"
                        status_str = "ESTORNADO"
                    else:
                        tag_nome = "normal"
                        txt_label = f"🔹 {it['tipo']}"
                        status_str = "ATIVO"
                    
                    arvore_os.insert(pai_id, "end", text=txt_label, values=(f"ID: {it['id']} | Qtd: {qtd_item}", status_str, st_txt if st_txt != "ATIVO" else "-"), tags=(str(it['id']), tag_nome))
        except Exception as e:
            print("Erro ao carregar OSs para estorno:", e)

        arvore_os.tag_configure("estornado", foreground="#999999")

    carregar_oss_estorno()

    def estornar_os_selecionada():
        selecionado = arvore_os.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um equipamento específico na árvore!")
            return

        item_id = selecionado[0]
        texto_item = arvore_os.item(item_id, "text")
        tags_item = arvore_os.item(item_id, "tags")

        if "📋" in texto_item or "❌ [ESTORNADA]" in texto_item:
            messagebox.showinfo("Aviso", "Por favor, selecione o equipamento específico (filho) da OS para devolver.")
            return

        if tags_item and tags_item[0] != "estornado":
            row_id = int(tags_item[0])
            
            conn = config.obter_conexao_banco()
            if not conn:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT nome_equipamento, quantidade_usada FROM uso WHERE id = %s;", (row_id,))
                res = cursor.fetchone()
                cursor.close()
                conn.close()
                if not res:
                    return
                tipo_item, qtd_atual = res[0], int(res[1] or 0)
            except:
                return

            if qtd_atual <= 0:
                messagebox.showinfo("Aviso", "Este item já está com quantidade zero.")
                return

            if qtd_atual > 1:
                qtd_para_estornar = simpledialog.askinteger("Devolução", f"Quantidade retirada: {qtd_atual}\nDigite a quantidade a devolver:", initialvalue=qtd_atual, minvalue=1, maxvalue=qtd_atual)
                if not qtd_para_estornar:
                    return
            else:
                if not messagebox.askyesno("Confirmar", "Confirmar a devolução deste item (quantidade 1)?"):
                    return
                qtd_para_estornar = 1

            # Executa devolução no banco
            try:
                conn_e = config.obter_conexao_banco()
                cursor_e = conn_e.cursor()
                timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Devolve ao disponivel do estoque
                cursor_e.execute(
                    "UPDATE estoque SET disponivel = disponivel + %s WHERE LOWER(tipo) = LOWER(%s);",
                    (qtd_para_estornar, tipo_item)
                )

                novo_saldo = qtd_atual - qtd_para_estornar
                nova_auditoria = f"DEVOLVIDO ({qtd_para_estornar} un) em {timestamp} por {config.usuario_logado}"

                cursor_e.execute(
                    "UPDATE uso SET quantidade_usada = %s, status = %s WHERE id = %s;",
                    (novo_saldo, nova_auditoria, row_id)
                )

                conn_e.commit()
                cursor_e.close()
                conn_e.close()

                config.atualizar_feed_estoque_critico()
                messagebox.showinfo("Sucesso", "Devolução registrada na nuvem!")
                carregar_oss_estorno()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao registrar devolução: {e}")

    f_botoes_os = tk.Frame(tab_os, padx=10, pady=5)
    f_botoes_os.pack(fill="x")
    tk.Button(f_botoes_os, text="🔄 Executar Devolução", command=estornar_os_selecionada, bg="#1F4E79", fg="white", font=("Arial", 9, "bold"), height=2).pack(fill="x")

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(10, 0))


# ==========================================
# TELA DE ARMAZÉM (ESTOQUE GERAL) - SUPABASE
# ==========================================
def mostrar_tela_armazem(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Painel de visualização geral de todos os equipamentos disponíveis e totais em estoque via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=20, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📦 Armazém — Visão Geral do Estoque (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    frame_tabela = tk.Frame(frame_principal)
    frame_tabela.pack(fill="both", expand=True, pady=(0, 10))

    colunas = ("Cod", "Equipamento", "EstoqueTotal", "EstoqueDisponivel", "Fornecedor", "ValorUnitario", "StatusEstoque")
    tabela_armazem = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=14)
    
    tabela_armazem.heading("Cod", text="Cód. Produto")
    tabela_armazem.column("Cod", width=110, anchor="center")
    tabela_armazem.heading("Equipamento", text="Nome do Equipamento / Item")
    tabela_armazem.column("Equipamento", width=250, anchor="w")
    tabela_armazem.heading("EstoqueTotal", text="Qtd. Total")
    tabela_armazem.column("EstoqueTotal", width=100, anchor="center")
    tabela_armazem.heading("EstoqueDisponivel", text="Qtd. Disponível")
    tabela_armazem.column("EstoqueDisponivel", width=110, anchor="center")
    tabela_armazem.heading("Fornecedor", text="Fornecedor")
    tabela_armazem.column("Fornecedor", width=200, anchor="w")
    tabela_armazem.heading("ValorUnitario", text="Valor Unit. (R$)")
    tabela_armazem.column("ValorUnitario", width=130, anchor="center")
    tabela_armazem.heading("StatusEstoque", text="Status do Estoque")
    tabela_armazem.column("StatusEstoque", width=140, anchor="center")

    scrollbar_arm = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela_armazem.yview)
    tabela_armazem.configure(yscrollcommand=scrollbar_arm.set)
    tabela_armazem.pack(side="left", fill="both", expand=True)
    scrollbar_arm.pack(side="right", fill="y")

    def carregar_dados_armazem():
        for item in tabela_armazem.get_children():
            tabela_armazem.delete(item)
            
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT cod, tipo, total, disponivel, fornecedor, valor_unitario FROM estoque;")
            for cod, nome, total, disponivel, fornecedor, valor in cursor.fetchall():
                if nome:
                    tot_int = int(total or 0)
                    disp_int = int(disponivel or 0)
                    val_float = float(valor or 0.0)

                    if disp_int <= 0:
                        status = "⚠️ ESGOTADO"
                    elif disp_int <= 2:
                        status = "⚠️ BAIXO"
                    else:
                        status = "✅ NORMAL"

                    tabela_armazem.insert("", "end", values=(
                        cod or "N/D", 
                        nome, 
                        tot_int, 
                        disp_int, 
                        fornecedor or "Não informado", 
                        f"R$ {val_float:.2f}".replace('.', ','), 
                        status
                    ))
            cursor.close()
            conn.close()
        except Exception as e:
            print("Erro ao carregar dados do armazém do Supabase:", e)

    carregar_dados_armazem()

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(8, 0))