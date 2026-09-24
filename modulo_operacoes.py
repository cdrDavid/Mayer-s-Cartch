import tkinter as tk
import json
import unicodedata
from tkinter import messagebox
from tkinter import ttk, simpledialog
from datetime import datetime
import config
import modulo_financeiro


def anexar_historico_estorno(status_atual, novo_evento):
    """Mantém cada estorno/devolução em uma linha separada."""
    status_atual = str(status_atual or "").strip()
    status_normalizado = unicodedata.normalize("NFKD", status_atual).encode("ascii", "ignore").decode().upper()
    if not status_atual or status_normalizado in {"ATIVO", "CONCLUIDO", "CONCLU?DO"}:
        return novo_evento
    return f"{status_atual}\n{novo_evento}"

# ==========================================
# TELA DE ENTRADA DE PEÇAS E MATERIAIS
# ==========================================
def mostrar_tela_entrada(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=10)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📥 Registrar compra e entrada de peças", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 6))

    # --- TOPO: DADOS DA ORDEM DE COMPRA ---
    f_topo_oc = tk.LabelFrame(frame_principal, text=" Dados da compra e fornecedor ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_topo_oc.pack(fill="x", pady=(0, 6))

    f_l1 = tk.Frame(f_topo_oc)
    f_l1.pack(fill="x", pady=(0, 4))

    tk.Label(f_l1, text="Nº da compra:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_num_oc = tk.Entry(f_l1, font=("Arial", 9), width=10)
    entry_num_oc.pack(side="left", padx=(0, 10))
    entry_num_oc.insert(0, "")

    tk.Label(f_l1, text="Fornecedor / Descrição:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_fornecedor = tk.Entry(f_l1, font=("Arial", 9), width=35)
    entry_fornecedor.pack(side="left", padx=(0, 10))

    # --- TABELA DE ITENS DA OC ---
    frame_tabela_container = tk.Frame(frame_principal)
    frame_tabela_container.pack(fill="both", expand=True, pady=(0, 4))

    colunas = ("Cod", "Equipamento", "QtdEntrada", "Observacao")
    tabela_oc = ttk.Treeview(frame_tabela_container, columns=colunas, show="headings", height=8)
    for col, txt in zip(colunas, ["Cód. Equipamento", "Nome do Equipamento", "Quantidade", "Observação"]):
        tabela_oc.heading(col, text=txt)
    tabela_oc.pack(side="left", fill="both", expand=True)

    scrollbar_oc = ttk.Scrollbar(frame_tabela_container, orient="vertical", command=tabela_oc.yview)
    tabela_oc.configure(yscrollcommand=scrollbar_oc.set)
    scrollbar_oc.pack(side="right", fill="y")

    global itens_entrada_memoria
    itens_entrada_memoria = []

    def remover_item_selecionado():
        selecao = tabela_oc.selection()
        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um item na tabela para remover!")
            return
        item_id = selecao[0]
        valores = tabela_oc.item(item_id, "values")
        cod_rem = valores[0]
        
        global itens_entrada_memoria
        itens_entrada_memoria = [it for it in itens_entrada_memoria if it["cod"] != cod_rem]
        tabela_oc.delete(item_id)

    tk.Button(frame_principal, text="❌ Remover Item Selecionado", command=remover_item_selecionado, bg="#B45F06", fg="white", font=("Arial", 8, "bold")).pack(anchor="w", pady=(0, 4))

    # --- BLOCO DE ADICIONAR EQUIPAMENTO ---
    f_add_item_oc = tk.LabelFrame(frame_principal, text=" Adicionar peça ao recebimento por código ", font=("Arial", 9, "bold"), padx=10, pady=6)
    f_add_item_oc.pack(fill="x", pady=(0, 6))

    f_campos_item_oc = tk.Frame(f_add_item_oc)
    f_campos_item_oc.pack(fill="x")

    tk.Label(f_campos_item_oc, text="Cód:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_cod = tk.Entry(f_campos_item_oc, font=("Arial", 9), width=12)
    entry_item_cod.pack(side="left", padx=(0, 10))

    tk.Label(f_campos_item_oc, text="Qtd:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_qtd = tk.Entry(f_campos_item_oc, font=("Arial", 9), width=8)
    entry_item_qtd.pack(side="left", padx=(0, 10))

    tk.Label(f_campos_item_oc, text="Obs:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_obs = tk.Entry(f_campos_item_oc, font=("Arial", 9), width=25)
    entry_item_obs.pack(side="left", padx=(0, 15))

    def buscar_equipamento_por_codigo(cod_busca):
        conn = config.obter_conexao_banco()
        if not conn: return None, 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tipo FROM estoque WHERE cod = %s;", (str(cod_busca).strip(),))
            res = cursor.fetchone()
            cursor.close(); conn.close()
            if res: return str(res[0])
        except: pass
        return None

    def adicionar_item_oc_lista():
        cod = entry_item_cod.get().strip()
        qtd_str = entry_item_qtd.get().strip()
        obs = entry_item_obs.get().strip()
        if not cod or not qtd_str:
            messagebox.showwarning("Atenção", "Preencha o código e a quantidade!")
            return
        try:
            qtd = int(qtd_str)
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida.")
            return

        nome_equipamento = buscar_equipamento_por_codigo(cod)
        if not nome_equipamento:
            messagebox.showerror("Erro", f"Código '{cod}' não encontrado no estoque!")
            return

        itens_entrada_memoria.append({"cod": cod, "nome": nome_equipamento, "qtd": qtd, "obs": obs})
        tabela_oc.insert("", "end", values=(cod, nome_equipamento, qtd, obs))
        entry_item_cod.delete(0, tk.END); entry_item_qtd.delete(0, tk.END); entry_item_obs.delete(0, tk.END)

    tk.Button(f_campos_item_oc, text="➕ Adicionar à OC", command=adicionar_item_oc_lista, bg="#2F5597", fg="white", font=("Arial", 9, "bold")).pack(side="left")

    # --- BOTÕES INFERIORES ---
    f_baixo_oc = tk.Frame(frame_principal)
    f_baixo_oc.pack(fill="x", pady=(2, 0))

    def salvar_ordem_compra():
        num_oc = entry_num_oc.get().strip()
        fornecedor = entry_fornecedor.get().strip()

        if not fornecedor:
            messagebox.showwarning("Atenção", "Preencha o campo de Fornecedor / Descrição!")
            return
        if not itens_entrada_memoria:
            messagebox.showwarning("Atenção", "Adicione pelo menos um item à Ordem de Compra!")
            return

        data_hoje = datetime.now().strftime("%d/%m/%Y")
        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Erro ao conectar com o banco na nuvem.")
            return

        try:
            cursor = conn.cursor()
            for item in itens_entrada_memoria:
                tipo = item["nome"]
                qtde = item["qtd"]
                obs_item = item["obs"]

                obs_final = f"Ordem de Compra: {num_oc} | Fornecedor: {fornecedor}"
                if obs_item:
                    obs_final += f" | {obs_item}"

                # Atualiza o estoque somando a quantidade de entrada
                cursor.execute(
                    "UPDATE estoque SET disponivel = disponivel + %s WHERE LOWER(tipo) = LOWER(%s);",
                    (qtde, tipo)
                )

                # Registra na tabela de entrada
                cursor.execute(
                    "INSERT INTO entrada (data, fornecedor_descricao, nome_item, quantidade, usuario, status) VALUES (%s, %s, %s, %s, %s, %s);",
                    (data_hoje, f"Ordem de Compra: {num_oc} | Fornecedor: {fornecedor}", tipo, qtde, config.usuario_logado, "Concluído")
                )

            conn.commit()
            cursor.close(); conn.close()

            config.atualizar_feed_estoque_critico()
            messagebox.showinfo("Sucesso", f"Ordem de Compra {num_oc} registrada e estoque atualizado com sucesso!")
            for i in tabela_oc.get_children(): tabela_oc.delete(i)
            itens_entrada_memoria.clear()
            entry_fornecedor.delete(0, tk.END)
            entry_num_oc.delete(0, tk.END); entry_num_oc.insert(0, "")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar Ordem de Compra: {e}")

    tk.Button(f_baixo_oc, text="💾 Confirmar entrada de peças", command=salvar_ordem_compra, bg="#38761D", fg="white", font=("Arial", 10, "bold"), height=2).pack(side="right")
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 9), height=1).pack(fill="x", pady=(2, 0))


# ==========================================
# TELA DE PRÉ-EMISSÃO DE ORÇAMENTO (SUPABASE + PDF)
# ==========================================
def mostrar_tela_pre_emissao_os(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=20, pady=15)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="💰 Solicitação de orçamento", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_form = tk.LabelFrame(frame_principal, text=" Dados do Orçamento e do Cliente ", font=("Arial", 9, "bold"), padx=15, pady=12)
    f_form.pack(fill="x", pady=(0, 15))

    f_l1 = tk.Frame(f_form)
    f_l1.pack(fill="x", pady=(0, 8))

    tk.Label(f_l1, text="Nº do Orçamento:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_num_orcamento = tk.Entry(f_l1, font=("Arial", 10), width=15)
    entry_num_orcamento.pack(side="left", padx=(0, 20))
    entry_num_orcamento.insert(0, "")

    tk.Label(f_l1, text="Cód. do Cliente:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_cod_cli = tk.Entry(f_l1, font=("Arial", 10), width=12)
    entry_cod_cli.pack(side="left", padx=(0, 15))

    lbl_cliente_info = tk.Label(f_l1, text="Cliente: [Digite o código e pressione Enter]", font=("Arial", 9, "italic"), fg="#555555")
    lbl_cliente_info.pack(side="left")

    f_l2 = tk.Frame(f_form)
    f_l2.pack(fill="x", pady=(0, 4))

    tk.Label(f_l2, text="Descrição da solicitação / serviço:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 4))
    text_solicitacao = tk.Text(f_l2, font=("Arial", 10), height=3, wrap="word")
    text_solicitacao.pack(fill="x", expand=True)

    itens_orcamento = []
    f_l3 = tk.Frame(f_form)
    f_l3.pack(fill="x", pady=(8, 0))
    tk.Label(f_l3, text="Código do item:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_cod_item_orcamento = tk.Entry(f_l3, font=("Arial", 10), width=12)
    entry_cod_item_orcamento.pack(side="left", padx=(0, 5))
    tk.Button(f_l3, text="🔍", command=lambda: pesquisar_item_estoque(), bg="#1F4E79", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 12))
    tk.Label(f_l3, text="Item:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_item_orcamento = tk.Entry(f_l3, font=("Arial", 10), width=28, state="readonly")
    entry_item_orcamento.pack(side="left", padx=(0, 12))
    tk.Label(f_l3, text="Qtd.:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_qtd_orcamento = tk.Entry(f_l3, font=("Arial", 10), width=6)
    entry_qtd_orcamento.pack(side="left", padx=(0, 10))
    entry_qtd_orcamento.insert(0, "1")
    tk.Label(f_l3, text="Valor unitário:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_valor_item = tk.Entry(f_l3, font=("Arial", 10), width=12, state="readonly")
    entry_valor_item.pack(side="left", padx=(0, 10))

    f_l4 = tk.Frame(f_form)
    f_l4.pack(fill="x", pady=(6, 0))
    tk.Label(f_l4, text="Observação do item:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_obs_item = tk.Entry(f_l4, font=("Arial", 10), width=55)
    entry_obs_item.pack(side="left", padx=(0, 12))
    tk.Button(f_l4, text="➕ Adicionar item", command=lambda: adicionar_item_orcamento(), bg="#38761D", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))
    tk.Button(f_l4, text="🗑 Remover selecionado", command=lambda: remover_item_orcamento(), bg="#CC0000", fg="white", font=("Arial", 9, "bold")).pack(side="left")

    frame_itens_orcamento = tk.LabelFrame(f_form, text=" Itens adicionados ao orçamento ", font=("Arial", 9, "bold"), padx=6, pady=5)
    frame_itens_orcamento.pack(fill="both", expand=True, pady=(8, 0))
    colunas_itens_orcamento = ("codigo", "item", "quantidade", "unitario", "total", "observacao")
    tabela_itens_orcamento = ttk.Treeview(frame_itens_orcamento, columns=colunas_itens_orcamento, show="headings", height=4)
    cabecalhos_itens = {"codigo": ("Código", 90), "item": ("Item / Serviço", 250), "quantidade": ("Qtd.", 55), "unitario": ("Valor unitário", 100), "total": ("Total", 100), "observacao": ("Observação", 220)}
    for coluna, (texto, largura) in cabecalhos_itens.items():
        tabela_itens_orcamento.heading(coluna, text=texto)
        tabela_itens_orcamento.column(coluna, width=largura, anchor="w")
    tabela_itens_orcamento.pack(fill="both", expand=True)

    tk.Label(f_l3, text="Mão de obra:", font=("Arial", 9, "bold")).pack(side="left", padx=(10, 4))
    entry_mao_obra_orcamento = tk.Entry(f_l3, font=("Arial", 10), width=12)
    entry_mao_obra_orcamento.pack(side="left")
    entry_mao_obra_orcamento.insert(0, "0,00")

    def preencher_item_selecionado(codigo, nome, valor):
        entry_cod_item_orcamento.delete(0, tk.END)
        entry_cod_item_orcamento.insert(0, codigo)
        entry_item_orcamento.config(state="normal")
        entry_item_orcamento.delete(0, tk.END)
        entry_item_orcamento.insert(0, nome)
        entry_item_orcamento.config(state="readonly")
        entry_valor_item.config(state="normal")
        entry_valor_item.delete(0, tk.END)
        entry_valor_item.insert(0, f"{float(valor or 0):.2f}".replace('.', ','))
        entry_valor_item.config(state="readonly")

    def buscar_item_por_codigo(event=None):
        codigo = entry_cod_item_orcamento.get().strip()
        if not codigo:
            return "break"

        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.", parent=janela_principal)
            return "break"

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT cod, tipo, valor_unitario FROM estoque WHERE cod = %s;", (codigo,))
            item = cursor.fetchone()
            cursor.close()
            conn.close()
            if item:
                preencher_item_selecionado(item[0], item[1], item[2])
                entry_qtd_orcamento.focus_set()
            else:
                messagebox.showwarning("Item não encontrado", f"Nenhum item com o código '{codigo}' foi encontrado no estoque.", parent=janela_principal)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar item no estoque: {e}", parent=janela_principal)
        return "break"

    entry_cod_item_orcamento.bind("<Return>", buscar_item_por_codigo)

    def pesquisar_item_estoque():
        janela_itens = tk.Toplevel(janela_principal)
        janela_itens.title("Pesquisar item do estoque")
        centralizar_janela(janela_itens, 780, 430)
        janela_itens.transient(janela_principal)
        janela_itens.grab_set()
        frame_busca_item = tk.Frame(janela_itens, padx=12, pady=12)
        frame_busca_item.pack(fill="both", expand=True)
        tk.Label(frame_busca_item, text="Código ou nome do item:", font=("Arial", 10, "bold")).pack(anchor="w")
        entry_busca_item = tk.Entry(frame_busca_item, font=("Arial", 10))
        entry_busca_item.pack(fill="x", pady=(4, 8))
        colunas_busca_item = ("codigo", "nome", "valor", "fornecedor")
        tabela_busca_item = ttk.Treeview(frame_busca_item, columns=colunas_busca_item, show="headings", height=13)
        for coluna, texto, largura in [("codigo", "Código", 100), ("nome", "Item / Serviço", 300), ("valor", "Valor unitário", 120), ("fornecedor", "Fornecedor", 180)]:
            tabela_busca_item.heading(coluna, text=texto)
            tabela_busca_item.column(coluna, width=largura, anchor="w")
        tabela_busca_item.pack(side="left", fill="both", expand=True)
        barra_item = ttk.Scrollbar(frame_busca_item, orient="vertical", command=tabela_busca_item.yview)
        tabela_busca_item.configure(yscrollcommand=barra_item.set)
        barra_item.pack(side="right", fill="y")

        def carregar_itens(event=None):
            termo = entry_busca_item.get().strip()
            for item in tabela_busca_item.get_children():
                tabela_busca_item.delete(item)
            conn = config.obter_conexao_banco()
            if not conn:
                return
            try:
                cursor = conn.cursor()
                parametro = f"%{termo}%"
                cursor.execute("""SELECT cod, tipo, valor_unitario, fornecedor FROM estoque
                                  WHERE cod ILIKE %s OR tipo ILIKE %s ORDER BY tipo ASC;""", (parametro, parametro))
                for codigo, nome, valor, fornecedor in cursor.fetchall():
                    tabela_busca_item.insert("", "end", values=(codigo or "-", nome or "-", f"R$ {float(valor or 0):.2f}".replace('.', ','), fornecedor or "-"))
                cursor.close(); conn.close()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao pesquisar estoque: {e}", parent=janela_itens)

        def selecionar_item(event=None):
            selecao = tabela_busca_item.selection()
            if not selecao:
                return
            valores = tabela_busca_item.item(selecao[0], "values")
            valor = valores[2].replace("R$", "").replace(".", "").replace(",", ".").strip()
            preencher_item_selecionado(valores[0], valores[1], valor)
            janela_itens.destroy()

        entry_busca_item.bind("<Return>", carregar_itens)
        tabela_busca_item.bind("<Double-1>", selecionar_item)
        tk.Button(frame_busca_item, text="🔍 Pesquisar", command=carregar_itens, bg="#1F4E79", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True, pady=(8, 0), padx=(0, 4))
        tk.Button(frame_busca_item, text="Selecionar", command=selecionar_item, bg="#38761D", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True, pady=(8, 0), padx=(4, 0))
        entry_busca_item.focus_set()

    def adicionar_item_orcamento():
        codigo = entry_cod_item_orcamento.get().strip()
        nome = entry_item_orcamento.get().strip()
        try:
            quantidade = int(entry_qtd_orcamento.get().strip())
            valor_unitario = float(entry_valor_item.get().strip().replace('.', '').replace(',', '.'))
            if not codigo or not nome or quantidade <= 0 or valor_unitario < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Pesquise um item válido e informe uma quantidade correta.", parent=janela_principal)
            return
        observacao = entry_obs_item.get().strip()
        item = {"cod": codigo, "nome": nome, "qtd": quantidade, "valor_unitario": valor_unitario, "obs": observacao}
        itens_orcamento.append(item)
        tabela_itens_orcamento.insert("", "end", values=(codigo, nome, quantidade, f"R$ {valor_unitario:.2f}".replace('.', ','), f"R$ {quantidade * valor_unitario:.2f}".replace('.', ','), observacao or "-"))
        entry_cod_item_orcamento.delete(0, tk.END)
        entry_item_orcamento.config(state="normal"); entry_item_orcamento.delete(0, tk.END); entry_item_orcamento.config(state="readonly")
        entry_valor_item.config(state="normal"); entry_valor_item.delete(0, tk.END); entry_valor_item.config(state="readonly")
        entry_qtd_orcamento.delete(0, tk.END); entry_qtd_orcamento.insert(0, "1")
        entry_obs_item.delete(0, tk.END)

    def remover_item_orcamento():
        selecao = tabela_itens_orcamento.selection()
        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um item para remover.", parent=janela_principal)
            return
        indice = tabela_itens_orcamento.index(selecao[0])
        tabela_itens_orcamento.delete(selecao[0])
        itens_orcamento.pop(indice)

    dados_cliente_memoria = {}

    def buscar_cliente(event=None):
        cod = entry_cod_cli.get().strip()
        if not cod:
            lbl_cliente_info.config(text="Cliente: [Não informado]", fg="#555555")
            dados_cliente_memoria.clear()
            return

        conn = config.obter_conexao_banco()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT codigo, nome, tipo, documento, cep, rua, numero, bairro, cidade,
                              contato, email, modelo_central, modulo, mac_address, operadora, linha_numero, iccid,
                              data_atualizacao
                              FROM clientes WHERE codigo = %s;""", (cod,))
            res = cursor.fetchone()
            cursor.close(); conn.close()
            if res:
                dados_cliente_memoria.update({
                    "cod_cliente": res[0], "cliente": res[1], "tipo": res[2], "documento": res[3],
                    "cep": res[4], "rua": res[5], "numero": res[6], "bairro": res[7], "cidade": res[8],
                    "contato": res[9], "email": res[10], "central": res[11], "modulo": res[12],
                    "mac": res[13], "operadora": res[14], "linha": res[15], "iccid": res[16],
                    "data_atualizacao": res[17]
                })
                lbl_cliente_info.config(text=f"Cliente: {res[1]} ({res[2]})", fg="#38761D")
            else:
                lbl_cliente_info.config(text="Cliente: ⚠️ Não cadastrado!", fg="#CC0000")
                dados_cliente_memoria.clear()
        except Exception as e:
            print("Erro ao buscar cliente para PDF:", e)

    def pesquisar_cliente_por_nome():
        janela_busca = tk.Toplevel(janela_principal)
        janela_busca.title("Pesquisar cliente")
        centralizar_janela(janela_busca, 720, 420)
        janela_busca.resizable(True, True)
        janela_busca.transient(janela_principal)
        janela_busca.grab_set()

        frame_busca = tk.Frame(janela_busca, padx=12, pady=12)
        frame_busca.pack(fill="both", expand=True)

        tk.Label(frame_busca, text="Nome do cliente:", font=("Arial", 10, "bold")).pack(anchor="w")
        entry_nome_busca = tk.Entry(frame_busca, font=("Arial", 10))
        entry_nome_busca.pack(fill="x", pady=(4, 8))

        colunas_busca = ("codigo", "nome", "tipo", "cidade", "contato")
        tabela_busca = ttk.Treeview(frame_busca, columns=colunas_busca, show="headings", height=12)
        cabecalhos = {
            "codigo": ("Código", 90),
            "nome": ("Nome / Razão Social", 260),
            "tipo": ("Tipo", 110),
            "cidade": ("Cidade", 150),
            "contato": ("Contato", 120)
        }
        for coluna in colunas_busca:
            texto, largura = cabecalhos[coluna]
            tabela_busca.heading(coluna, text=texto)
            tabela_busca.column(coluna, width=largura, anchor="w")
        tabela_busca.pack(side="left", fill="both", expand=True)

        barra_busca = ttk.Scrollbar(frame_busca, orient="vertical", command=tabela_busca.yview)
        tabela_busca.configure(yscrollcommand=barra_busca.set)
        barra_busca.pack(side="right", fill="y")

        def carregar_resultados(event=None):
            termo = entry_nome_busca.get().strip()
            for item in tabela_busca.get_children():
                tabela_busca.delete(item)
            if not termo:
                return

            conn = config.obter_conexao_banco()
            if not conn:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco.", parent=janela_busca)
                return
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT codigo, nome, tipo, cidade, contato
                    FROM clientes
                    WHERE LOWER(nome) LIKE LOWER(%s)
                    ORDER BY nome ASC;
                """, (f"%{termo}%",))
                for cliente in cursor.fetchall():
                    tabela_busca.insert("", "end", values=tuple(valor or "-" for valor in cliente))
                cursor.close()
                conn.close()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao pesquisar clientes: {e}", parent=janela_busca)

        def selecionar_cliente(event=None):
            selecao = tabela_busca.selection()
            if not selecao:
                return
            codigo = tabela_busca.item(selecao[0], "values")[0]
            entry_cod_cli.delete(0, tk.END)
            entry_cod_cli.insert(0, codigo)
            buscar_cliente()
            janela_busca.destroy()

        entry_nome_busca.bind("<Return>", carregar_resultados)
        tabela_busca.bind("<Double-1>", selecionar_cliente)

        frame_botoes_busca = tk.Frame(frame_busca)
        frame_botoes_busca.pack(fill="x", pady=(8, 0))
        tk.Button(frame_botoes_busca, text="🔍 Pesquisar", command=carregar_resultados, bg="#1F4E79", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(frame_botoes_busca, text="Selecionar", command=selecionar_cliente, bg="#38761D", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True, padx=(4, 4))
        tk.Button(frame_botoes_busca, text="Cancelar", command=janela_busca.destroy, bg="#595959", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True, padx=(4, 0))
        entry_nome_busca.focus_set()

    # lupa de busca de cliente caso não saiba o código do cliente
    btn_buscar_cliente = tk.Button(f_l1, text="🔍", command=pesquisar_cliente_por_nome)
    btn_buscar_cliente.pack(side="left", padx=(0, 15))

    entry_cod_cli.bind("<Return>", buscar_cliente)
    entry_cod_cli.bind("<FocusOut>", buscar_cliente)

    def gerar_pdf():
        num_orcamento = entry_num_orcamento.get().strip()
        if not num_orcamento or not dados_cliente_memoria:
            messagebox.showwarning("Atenção", "Preencha o número do orçamento e informe um cliente válido!", parent=janela_principal)
            return

        try:
            valor_mao_obra = float(entry_mao_obra_orcamento.get().strip().replace('.', '').replace(',', '.'))
            if valor_mao_obra < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade e valores devem ser números válidos.", parent=janela_principal)
            return

        if not itens_orcamento:
            messagebox.showwarning("Atenção", "Adicione pelo menos um item ao orçamento.", parent=janela_principal)
            return

        dados_cliente_memoria['num_orcamento'] = num_orcamento
        solicitacao_txt = text_solicitacao.get("1.0", tk.END).strip()
        dados_cliente_memoria['solicitacao'] = solicitacao_txt
        dados_cliente_memoria['itens_orcamento'] = list(itens_orcamento)
        dados_cliente_memoria['valor_mao_obra'] = valor_mao_obra

        import modulo_pdf
        modulo_pdf.gerar_pdf_orcamento(dados_cliente_memoria, janela_principal)

    tk.Button(frame_principal, text="🖨️ Gerar e Imprimir Solicitação de Orçamento", command=gerar_pdf, bg="#1F4E79", fg="white", font=("Arial", 11, "bold"), height=2).pack(fill="x", pady=(10, 5))
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(5, 0))


# ==========================================
# TELA DE SAÍDA / ORDEM DE SERVIÇO (OS) - SUPABASE
# ==========================================
def mostrar_tela_saida(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=10)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="🛠️ Abrir ordem de serviço", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 6))

    # --- SISTEMA DE ABAS (Lançamento da OS x Histórico Dinâmico) ---
    notebook_os = ttk.Notebook(frame_principal)
    notebook_os.pack(fill="both", expand=True, pady=(0, 6))

    # ==========================================
    # ABA 1: LANÇAMENTO DA ORDEM DE SERVIÇO
    # ==========================================
    tab_lancamento = ttk.Frame(notebook_os, padding=10)
    notebook_os.add(tab_lancamento, text="  📝 Lançamento da OS  ")

    f_topo_os = tk.LabelFrame(tab_lancamento, text=" Informações da Ordem de Serviço, Cliente, Técnico e Serviço ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_topo_os.pack(fill="x", pady=(0, 6))

    f_l1 = tk.Frame(f_topo_os)
    f_l1.pack(fill="x", pady=(0, 4))

    tk.Label(f_l1, text="Nº da OS:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_num_os = tk.Entry(f_l1, font=("Arial", 9), width=10)
    entry_num_os.pack(side="left", padx=(0, 10))
    entry_num_os.insert(0, "")
    btn_pre_os = tk.Button(f_l1, text="📋", width=3, command=lambda: pesquisar_pre_os())
    btn_pre_os.pack(side="left", padx=(0, 12))

    tk.Label(f_l1, text="Cód. Cli:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_cod_cli = tk.Entry(f_l1, font=("Arial", 9), width=7)
    entry_cod_cli.pack(side="left", padx=(0, 8))
    tk.Button(f_l1, text="🔍", width=3, command=lambda: pesquisar_cliente_os()).pack(side="left", padx=(0, 6))

    label_info_cliente = tk.Label(f_l1, text="Cliente: [Não informado]", font=("Arial", 9, "italic"), fg="#555555")
    label_info_cliente.pack(side="left", padx=(0, 15))

    # Linha 2: Técnico e Valor de Mão de Obra
    f_l_tec = tk.Frame(f_topo_os)
    f_l_tec.pack(fill="x", pady=(0, 4))

    tk.Label(f_l_tec, text="Cód. Técnico:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_cod_tec = tk.Entry(f_l_tec, font=("Arial", 9), width=9)
    entry_cod_tec.pack(side="left", padx=(0, 8))
    tk.Button(f_l_tec, text="🔍", width=3, command=lambda: pesquisar_tecnico_os()).pack(side="left", padx=(0, 8))

    label_info_tecnico = tk.Label(f_l_tec, text="Técnico: [Não informado]", font=("Arial", 9, "italic"), fg="#555555")
    label_info_tecnico.pack(side="left", padx=(0, 30))

    f_2_tec = tk.Frame(f_topo_os)
    f_2_tec.pack(fill="x", pady=(0, 4))

    tk.Label(f_2_tec, text="Valor Mão de Obra (R$):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_mao_obra = tk.Entry(f_2_tec, font=("Arial", 9), width=12)
    entry_mao_obra.pack(side="left")
    entry_mao_obra.insert(0, "0,00")

    # Linha 3: Caixa de Texto Multilinha para Descrição do Serviço Prestado
    f_l_servico = tk.Frame(f_topo_os)
    f_l_servico.pack(fill="x", pady=(2, 0))

    tk.Label(f_l_servico, text="Descrição Detalhada do Serviço Prestado:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 2))
    
    frame_txt_servico = tk.Frame(f_l_servico)
    frame_txt_servico.pack(fill="x", expand=True)

    text_desc_servico = tk.Text(frame_txt_servico, font=("Arial", 9), height=3, wrap="word")
    text_desc_servico.pack(side="left", fill="x", expand=True)

    scrollbar_serv = ttk.Scrollbar(frame_txt_servico, orient="vertical", command=text_desc_servico.yview)
    text_desc_servico.configure(yscrollcommand=scrollbar_serv.set)
    scrollbar_serv.pack(side="right", fill="y")

    # ==========================================
    # ABA 2: HISTÓRICO DE OS DO CLIENTE SELECIONADO (DINÂMICA)
    # ==========================================
    tab_historico = ttk.Frame(notebook_os, padding=10)

    # Tabela de Histórico (Metade Superior da Aba)
    frame_tabela_hist_container = tk.Frame(tab_historico)
    frame_tabela_hist_container.pack(fill="both", expand=True, pady=(0, 6))

    colunas_hist = ("Data", "OS", "Equipamento", "Qtd", "Usuário")
    tabela_historico_os = ttk.Treeview(frame_tabela_hist_container, columns=colunas_hist, show="headings", height=8)
    
    tabela_historico_os.heading("Data", text="Data"); tabela_historico_os.column("Data", width=90, anchor="center")
    tabela_historico_os.heading("OS", text="Nº OS"); tabela_historico_os.column("OS", width=100, anchor="center")
    tabela_historico_os.heading("Equipamento", text="Equipamento Principal"); tabela_historico_os.column("Equipamento", width=220, anchor="w")
    tabela_historico_os.heading("Qtd", text="Qtd"); tabela_historico_os.column("Qtd", width=60, anchor="center")
    tabela_historico_os.heading("Usuário", text="Usuário"); tabela_historico_os.column("Usuário", width=120, anchor="center")

    scrollbar_hist_os = ttk.Scrollbar(frame_tabela_hist_container, orient="vertical", command=tabela_historico_os.yview)
    tabela_historico_os.configure(yscrollcommand=scrollbar_hist_os.set)
    tabela_historico_os.pack(side="left", fill="both", expand=True)
    scrollbar_hist_os.pack(side="right", fill="y")

    # Painel Inferior de Detalhes da OS (Igual à tela de relatórios)
    f_detalhes_os = tk.LabelFrame(tab_historico, text=" Detalhes Completos, Serviço & Itens Utilizados ", font=("Arial", 9, "bold"), padx=10, pady=6)
    f_detalhes_os.pack(fill="x", pady=(0, 4))

    text_detalhes_os = tk.Text(f_detalhes_os, font=("Arial", 9), height=5, wrap="word", bg="#F4F4F4")
    text_detalhes_os.pack(fill="x", expand=True)
    text_detalhes_os.config(state="disabled")

    def carregar_historico_cliente_na_aba(nome_cliente):
        for item in tabela_historico_os.get_children():
            tabela_historico_os.delete(item)
        text_detalhes_os.config(state="normal")
        text_detalhes_os.delete("1.0", tk.END)
        text_detalhes_os.config(state="disabled")

        if not nome_cliente:
            return

        conn = config.obter_conexao_banco()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT data, observacao, nome_equipamento, quantidade_usada, usuario 
                              FROM uso WHERE local_setor ILIKE %s ORDER BY id DESC;""", (f"%{nome_cliente}%",))
            for row in cursor.fetchall():
                d_reg, o_reg, e_reg, q_reg, u_reg = row
                os_str = "OS-N/D"
                if o_reg and "OS:" in o_reg:
                    for p in str(o_reg).split("|"):
                        if "OS:" in p: os_str = p.split(":")[-1].strip()
                tabela_historico_os.insert("", "end", values=(d_reg or "-", os_str, e_reg or "-", q_reg or 0, u_reg or "-"), tags=(o_reg or "-",))
            cursor.close(); conn.close()
        except Exception as e:
            print("Erro ao carregar histórico na OS:", e)

    def ao_clicar_linha_historico_os(event):
        selecao = tabela_historico_os.selection()
        if selecao:
            item_dados = tabela_historico_os.item(selecao[0])
            tags = item_dados.get("tags")
            if tags:
                obs_completa = tags[0]
                text_detalhes_os.config(state="normal")
                text_detalhes_os.delete("1.0", tk.END)
                text_detalhes_os.insert("1.0", obs_completa)
                text_detalhes_os.config(state="disabled")

    tabela_historico_os.bind("<<TreeviewSelect>>", ao_clicar_linha_historico_os)

    def buscar_cliente_por_codigo(event=None):
        cod_cliente = entry_cod_cli.get().strip()
        if not cod_cliente:
            label_info_cliente.config(text="Cliente: [Não informado]", fg="#555555")
            carregar_historico_cliente_na_aba("")
            if str(tab_historico) in notebook_os.tabs():
                notebook_os.forget(tab_historico)
            return

        conn = config.obter_conexao_banco()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT nome, tipo FROM clientes WHERE codigo = %s;", (cod_cliente,))
            res = cursor.fetchone()
            cursor.close(); conn.close()
            if res:
                label_info_cliente.config(text=f"Cliente: {res[0]} ({res[1]})", fg="#38761D")
                carregar_historico_cliente_na_aba(res[0])
                if str(tab_historico) not in notebook_os.tabs():
                    notebook_os.add(tab_historico, text="  📜 Histórico de OS do Cliente  ")
            else:
                label_info_cliente.config(text="Cliente: ⚠️ Não cadastrado!", fg="#CC0000")
                carregar_historico_cliente_na_aba("")
                if str(tab_historico) in notebook_os.tabs():
                    notebook_os.forget(tab_historico)
        except: pass

    def buscar_tecnico_por_codigo(event=None):
        cod_tecnico = entry_cod_tec.get().strip()
        if not cod_tecnico:
            label_info_tecnico.config(text="Técnico: [Não informado]", fg="#555555")
            return
        conn = config.obter_conexao_banco()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM tecnicos WHERE codigo = %s;", (cod_tecnico,))
            res = cursor.fetchone()
            cursor.close(); conn.close()
            if res:
                label_info_tecnico.config(text=f"Técnico: {res[0]}", fg="#38761D")
            else:
                label_info_tecnico.config(text="Técnico: ⚠️ Não cadastrado!", fg="#CC0000")
        except: pass

    def abrir_pesquisa_pessoa(tipo):
        janela_pesquisa = tk.Toplevel(janela_principal)
        titulo = "Pesquisar cliente" if tipo == "cliente" else "Pesquisar técnico"
        janela_pesquisa.title(titulo)
        centralizar_janela(janela_pesquisa, 720, 420)
        janela_pesquisa.transient(janela_principal)
        janela_pesquisa.grab_set()

        frame_pesquisa = tk.Frame(janela_pesquisa, padx=12, pady=12)
        frame_pesquisa.pack(fill="both", expand=True)
        tk.Label(frame_pesquisa, text="Digite parte do nome:", font=("Arial", 10, "bold")).pack(anchor="w")
        entry_pesquisa = tk.Entry(frame_pesquisa, font=("Arial", 10))
        entry_pesquisa.pack(fill="x", pady=(4, 8))

        colunas = ("codigo", "nome", "tipo", "cidade") if tipo == "cliente" else ("codigo", "nome", "tipo", "contato")
        tabela = ttk.Treeview(frame_pesquisa, columns=colunas, show="headings", height=13)
        titulos = ("Código", "Nome", "Tipo", "Cidade") if tipo == "cliente" else ("Código", "Nome", "Tipo", "Contato")
        larguras = (90, 280, 120, 170)
        for coluna, titulo_coluna, largura in zip(colunas, titulos, larguras):
            tabela.heading(coluna, text=titulo_coluna)
            tabela.column(coluna, width=largura, anchor="w")
        tabela.pack(side="left", fill="both", expand=True)
        barra = ttk.Scrollbar(frame_pesquisa, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")

        def carregar_pessoas(event=None):
            termo = entry_pesquisa.get().strip()
            for item in tabela.get_children():
                tabela.delete(item)
            conn = config.obter_conexao_banco()
            if not conn:
                return "break"
            try:
                cursor = conn.cursor()
                parametro = f"%{termo}%"
                if tipo == "cliente":
                    cursor.execute("""SELECT codigo, nome, tipo, cidade FROM clientes
                                      WHERE nome ILIKE %s ORDER BY nome ASC;""", (parametro,))
                else:
                    cursor.execute("""SELECT codigo, nome, tipo, contato FROM tecnicos
                                      WHERE nome ILIKE %s ORDER BY nome ASC;""", (parametro,))
                for pessoa in cursor.fetchall():
                    tabela.insert("", "end", values=tuple(valor or "-" for valor in pessoa))
                cursor.close(); conn.close()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível pesquisar: {e}", parent=janela_pesquisa)
            return "break"

        def selecionar_pessoa(event=None):
            selecao = tabela.selection()
            if not selecao:
                return "break"
            codigo = tabela.item(selecao[0], "values")[0]
            if tipo == "cliente":
                entry_cod_cli.delete(0, tk.END)
                entry_cod_cli.insert(0, codigo)
                buscar_cliente_por_codigo()
            else:
                entry_cod_tec.delete(0, tk.END)
                entry_cod_tec.insert(0, codigo)
                buscar_tecnico_por_codigo()
            janela_pesquisa.destroy()
            return "break"

        entry_pesquisa.bind("<Return>", carregar_pessoas)
        tabela.bind("<Double-1>", selecionar_pessoa)
        tk.Button(frame_pesquisa, text="🔍 Pesquisar", command=carregar_pessoas, bg="#1F4E79", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True, pady=(8, 0), padx=(0, 4))
        tk.Button(frame_pesquisa, text="Selecionar", command=selecionar_pessoa, bg="#38761D", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True, pady=(8, 0))
        entry_pesquisa.focus_set()

    def pesquisar_cliente_os():
        abrir_pesquisa_pessoa("cliente")

    def pesquisar_tecnico_os():
        abrir_pesquisa_pessoa("tecnico")

    def pesquisar_pre_os():
        janela_pre_os = tk.Toplevel(janela_principal)
        janela_pre_os.title("Pré-OS registradas")
        centralizar_janela(janela_pre_os, 900, 460)
        janela_pre_os.transient(janela_principal)
        janela_pre_os.grab_set()

        frame_pre_os = tk.Frame(janela_pre_os, padx=12, pady=12)
        frame_pre_os.pack(fill="both", expand=True)
        tk.Label(frame_pre_os, text="Pré-ordens de serviço registradas", font=("Arial", 11, "bold")).pack(anchor="w")
        tk.Label(frame_pre_os, text="Selecione uma pré-OS para carregar seus dados nesta ordem de serviço.", font=("Arial", 9, "italic"), fg="#555555").pack(anchor="w", pady=(2, 8))

        f_filtro_pre_os = tk.Frame(frame_pre_os)
        f_filtro_pre_os.pack(fill="x", pady=(0, 8))
        tk.Label(f_filtro_pre_os, text="Pesquisar:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))
        entry_filtro_pre_os = tk.Entry(f_filtro_pre_os, font=("Arial", 9), width=35)
        entry_filtro_pre_os.pack(side="left", fill="x", expand=True)

        colunas_pre_os = ("numero", "codigo", "cliente", "data", "usuario", "status")
        tabela_pre_os = ttk.Treeview(frame_pre_os, columns=colunas_pre_os, show="headings", height=14)
        cabecalhos_pre_os = [("numero", "Nº OS", 110), ("codigo", "Cód. Cliente", 100), ("cliente", "Cliente", 260), ("data", "Data da pré-OS", 135), ("usuario", "Registrado por", 130), ("status", "Status", 130)]
        for coluna, titulo_coluna, largura in cabecalhos_pre_os:
            tabela_pre_os.heading(coluna, text=titulo_coluna)
            tabela_pre_os.column(coluna, width=largura, anchor="w")
        tabela_pre_os.pack(side="left", fill="both", expand=True)
        barra_pre_os = ttk.Scrollbar(frame_pre_os, orient="vertical", command=tabela_pre_os.yview)
        tabela_pre_os.configure(yscrollcommand=barra_pre_os.set)
        barra_pre_os.pack(side="right", fill="y")

        def carregar_pre_os(event=None):
            termo = entry_filtro_pre_os.get().strip()
            for item in tabela_pre_os.get_children():
                tabela_pre_os.delete(item)
            conn = config.obter_conexao_banco()
            if not conn:
                return "break"
            try:
                cursor = conn.cursor()
                parametro = f"%{termo}%"
                cursor.execute("""SELECT o.numero_os, o.codigo_cliente, c.nome, o.data, o.usuario, o.status
                                  FROM orcamentos o LEFT JOIN clientes c ON c.codigo = o.codigo_cliente
                                  WHERE o.numero_os ILIKE %s OR COALESCE(o.codigo_cliente, '') ILIKE %s
                                  OR COALESCE(c.nome, '') ILIKE %s
                                  ORDER BY o.id DESC;""", (parametro, parametro, parametro))
                for registro in cursor.fetchall():
                    tabela_pre_os.insert("", "end", values=tuple(valor or "-" for valor in registro))
                cursor.close(); conn.close()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível carregar as pré-OS: {e}", parent=janela_pre_os)
            return "break"

        def selecionar_pre_os(event=None):
            selecao = tabela_pre_os.selection()
            if not selecao:
                return "break"
            numero_selecionado = tabela_pre_os.item(selecao[0], "values")[0]
            entry_num_os.delete(0, tk.END)
            entry_num_os.insert(0, numero_selecionado)
            janela_pre_os.destroy()
            carregar_orcamento_salvo(numero_selecionado)
            return "break"

        entry_filtro_pre_os.bind("<KeyRelease>", carregar_pre_os)
        entry_filtro_pre_os.bind("<Return>", carregar_pre_os)
        tabela_pre_os.bind("<Double-1>", selecionar_pre_os)
        f_botoes_pre_os = tk.Frame(frame_pre_os)
        f_botoes_pre_os.pack(fill="x", pady=(8, 0))
        tk.Button(f_botoes_pre_os, text="🔍 Atualizar lista", command=carregar_pre_os, bg="#1F4E79", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(f_botoes_pre_os, text="Carregar selecionada", command=selecionar_pre_os, bg="#38761D", fg="white", font=("Arial", 9, "bold")).pack(side="left", fill="x", expand=True)
        carregar_pre_os()
        entry_filtro_pre_os.focus_set()

    entry_cod_cli.bind("<Double-1>", lambda event: (pesquisar_cliente_os(), "break")[1])
    entry_cod_tec.bind("<Double-1>", lambda event: (pesquisar_tecnico_os(), "break")[1])

    entry_cod_cli.bind("<Return>", buscar_cliente_por_codigo)
    entry_cod_cli.bind("<FocusOut>", buscar_cliente_por_codigo)
    entry_cod_tec.bind("<Return>", buscar_tecnico_por_codigo)
    entry_cod_tec.bind("<FocusOut>", buscar_tecnico_por_codigo)

    # --- TABELA DE ITENS DA OS (LANÇAMENTO) ---
    frame_tabela_container = tk.Frame(tab_lancamento)
    frame_tabela_container.pack(fill="both", expand=True, pady=(0, 4))

    colunas = ("Cod", "Equipamento", "QtdSaida", "Observacao")
    tabela_os = ttk.Treeview(frame_tabela_container, columns=colunas, show="headings", height=4)
    for col, txt in zip(colunas, ["Cód. Equipamento", "Nome do Equipamento", "Quantidade", "Observação"]):
        tabela_os.heading(col, text=txt)
    tabela_os.pack(side="left", fill="both", expand=True)

    def remover_item_selecionado():
        selecao = tabela_os.selection()
        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um item na tabela para remover!")
            return
        item_id = selecao[0]
        valores = tabela_os.item(item_id, "values")
        cod_rem = valores[0]
        
        global itens_saida_memoria
        itens_saida_memoria = [it for it in itens_saida_memoria if it["cod"] != cod_rem]
        tabela_os.delete(item_id)

    tk.Button(tab_lancamento, text="❌ Remover Item Selecionado", command=remover_item_selecionado, bg="#B45F06", fg="white", font=("Arial", 8, "bold")).pack(anchor="w", pady=(0, 4))

    # --- BLOCO DE ADICIONAR EQUIPAMENTO ---
    f_add_item_os = tk.LabelFrame(tab_lancamento, text=" Adicionar Equipamento à OS por Código (Opcional) ", font=("Arial", 9, "bold"), padx=10, pady=6)
    f_add_item_os.pack(fill="x", pady=(0, 6))

    f_campos_item_os = tk.Frame(f_add_item_os)
    f_campos_item_os.pack(fill="x")

    tk.Label(f_campos_item_os, text="Cód:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_cod = tk.Entry(f_campos_item_os, font=("Arial", 9), width=12)
    entry_item_cod.pack(side="left", padx=(0, 10))

    tk.Label(f_campos_item_os, text="Qtd:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_qtd = tk.Entry(f_campos_item_os, font=("Arial", 9), width=8)
    entry_item_qtd.pack(side="left", padx=(0, 10))

    tk.Label(f_campos_item_os, text="Obs:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 3))
    entry_item_obs = tk.Entry(f_campos_item_os, font=("Arial", 9), width=22)
    entry_item_obs.pack(side="left", padx=(0, 15))

    def buscar_equipamento_por_codigo(cod_busca):
        conn = config.obter_conexao_banco()
        if not conn: return None, 0
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tipo, disponivel FROM estoque WHERE cod = %s;", (str(cod_busca).strip(),))
            res = cursor.fetchone()
            cursor.close(); conn.close()
            if res: return str(res[0]), int(res[1] or 0)
        except: pass
        return None, 0

    global itens_saida_memoria
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
        entry_item_cod.delete(0, tk.END); entry_item_qtd.delete(0, tk.END); entry_item_obs.delete(0, tk.END)

    tk.Button(f_campos_item_os, text="➕ Adicionar à OS", command=adicionar_item_os_lista, bg="#2F5597", fg="white", font=("Arial", 9, "bold")).pack(side="left")

    # --- BOTÕES INFERIORES ---
    f_baixo_os = tk.Frame(frame_principal)
    f_baixo_os.pack(fill="x", pady=(2, 0))

    def obter_dados_cliente_pdf(codigo):
        conn = config.obter_conexao_banco()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""SELECT codigo, nome, tipo, documento, cep, rua, numero, bairro, cidade,
                              contato, email, modelo_central, modulo, mac_address, operadora, linha_numero, iccid,
                              data_atualizacao FROM clientes WHERE codigo = %s;""", (codigo,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if not row:
                return None
            return {
                "cod_cliente": row[0], "cliente": row[1], "tipo": row[2], "documento": row[3],
                "cep": row[4], "rua": row[5], "numero": row[6], "bairro": row[7], "cidade": row[8],
                "contato": row[9], "email": row[10], "central": row[11], "modulo": row[12],
                "mac": row[13], "operadora": row[14], "linha": row[15], "iccid": row[16],
                "data_atualizacao": row[17]
            }
        except Exception as e:
            print("Erro ao carregar dados completos do cliente:", e)
            return None

    def obter_itens_pdf():
        itens = []
        for item_id in tabela_os.get_children():
            valores = tabela_os.item(item_id, "values")
            codigo, nome, quantidade, observacao = valores
            valor_unitario = 0.0
            conn = config.obter_conexao_banco()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT valor_unitario FROM estoque WHERE cod = %s;", (codigo,))
                    row = cursor.fetchone()
                    valor_unitario = float(row[0] or 0) if row else 0.0
                    cursor.close(); conn.close()
                except Exception:
                    pass
            itens.append({"cod": codigo, "nome": nome, "qtd": int(quantidade or 0), "obs": observacao, "valor_unitario": valor_unitario})
        return itens

    def ler_valor_mo():
        try:
            return float(entry_mao_obra.get().strip().replace('.', '').replace(',', '.'))
        except ValueError:
            raise ValueError("O valor da mão de obra deve ser um número válido.")

    def gerar_orcamento_os():
        numero_os = entry_num_os.get().strip()
        codigo_cliente = entry_cod_cli.get().strip()
        descricao = text_desc_servico.get("1.0", tk.END).strip()
        if not numero_os or numero_os == "OS-" or not codigo_cliente:
            messagebox.showwarning("Atenção", "Informe o número da OS e o código do cliente.", parent=janela_principal)
            return
        dados_cliente = obter_dados_cliente_pdf(codigo_cliente)
        if not dados_cliente:
            messagebox.showwarning("Atenção", "O cliente informado não foi encontrado.", parent=janela_principal)
            return
        itens = obter_itens_pdf()
        if not itens and not descricao:
            messagebox.showwarning("Atenção", "Informe o serviço ou adicione pelo menos uma peça.", parent=janela_principal)
            return
        try:
            valor_mao_obra = ler_valor_mo()
            if valor_mao_obra < 0:
                raise ValueError
        except ValueError as e:
            messagebox.showerror("Erro", str(e), parent=janela_principal)
            return

        dados_pdf = dict(dados_cliente)
        dados_pdf.update({"num_orcamento": numero_os, "solicitacao": descricao, "itens_orcamento": itens, "valor_mao_obra": valor_mao_obra})
        conn = config.obter_conexao_banco()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO orcamentos
                (numero_os, codigo_cliente, data, dados_cliente, itens, descricao, valor_mao_obra, status, usuario)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
                ON CONFLICT (numero_os) DO UPDATE SET codigo_cliente = EXCLUDED.codigo_cliente,
                data = EXCLUDED.data, dados_cliente = EXCLUDED.dados_cliente, itens = EXCLUDED.itens,
                descricao = EXCLUDED.descricao, valor_mao_obra = EXCLUDED.valor_mao_obra,
                status = EXCLUDED.status, usuario = EXCLUDED.usuario;""",
                (numero_os, codigo_cliente, datetime.now().strftime("%d/%m/%Y %H:%M"), json.dumps(dados_cliente), json.dumps(itens), descricao, valor_mao_obra, "Orçamento", config.usuario_logado))
            conn.commit()
            cursor.close(); conn.close()
            import modulo_pdf
            modulo_pdf.gerar_pdf_orcamento(dados_pdf, janela_principal)
        except Exception as e:
            if conn:
                conn.rollback(); conn.close()
            messagebox.showerror("Erro", f"Não foi possível salvar o orçamento: {e}", parent=janela_principal)

    def salvar_ordem_servico():
        num_os = entry_num_os.get().strip()
        cod_cli = entry_cod_cli.get().strip()
        desc_servico = text_desc_servico.get("1.0", tk.END).strip()
        
        conn_b = config.obter_conexao_banco()
        if not conn_b:
            messagebox.showerror("Erro", "Erro ao conectar com o banco na nuvem.")
            return
        
        try:
            cur_b = conn_b.cursor()
            cur_b.execute("SELECT nome, tipo FROM clientes WHERE codigo = %s;", (cod_cli,))
            cli_res = cur_b.fetchone()
            cur_b.close(); conn_b.close()
            
            if not cli_res:
                messagebox.showwarning("Atenção", "Informe um código de cliente válido!")
                return
            nome_cliente, tipo_cliente = cli_res[0], cli_res[1]
        except:
            messagebox.showwarning("Atenção", "Erro ao validar o cliente.")
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
            
            # Formatação estruturada solicitada:
            # Linha 1: OS, Cliente, Mão de Obra
            # Linha 2 em diante: Serviço (separado por parágrafos)
            # Abaixo: Itens Utilizados
            
            cabecalho_os = f"OS: {num_os} | Cliente: {nome_cliente} ({tipo_cliente}) | Mão de Obra: R$ {val_mao_obra:.2f}"
            
            bloco_servico = ""
            if desc_servico:
                bloco_servico = f"\nServiço:\n{desc_servico}"

            bloco_itens = "\nItens Utilizados:"
            if itens_saida_memoria:
                for item in itens_saida_memoria:
                    bloco_itens += f"\n- {item['qtd']} * {item['nome']}"
                    if item['obs']:
                        bloco_itens += f" ({item['obs']})"
            else:
                bloco_itens += "\n- Nenhum item utilizado (Ajuste / Suporte)"

            obs_final = f"{cabecalho_os}{bloco_servico}\n{bloco_itens}"

            if not itens_saida_memoria:
                cursor.execute(
                    "INSERT INTO uso (data, local_setor, nome_equipamento, quantidade_usada, observacao, usuario, status, descricao_servico) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                    (data_hoje, f"{nome_cliente} ({tipo_cliente})", "Nenhum (Ajuste / Suporte)", 0, obs_final, config.usuario_logado, "Aberta", desc_servico)
                )
            else:
                for index, item in enumerate(itens_saida_memoria):
                    tipo = item["nome"]
                    qtde = item["qtd"]

                    cursor.execute(
                        "UPDATE estoque SET disponivel = disponivel - %s WHERE LOWER(tipo) = LOWER(%s);",
                        (qtde, tipo)
                    )

                    cursor.execute(
                        "INSERT INTO uso (data, local_setor, nome_equipamento, quantidade_usada, observacao, usuario, status, descricao_servico) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                        (data_hoje, f"{nome_cliente} ({tipo_cliente})", tipo, qtde, obs_final, config.usuario_logado, "Aberta", desc_servico)
                    )

            cursor.execute("UPDATE orcamentos SET status = %s WHERE numero_os = %s;", ("Aprovado/OS registrada", num_os))
            conn.commit()
            cursor.close(); conn.close()

            config.atualizar_feed_estoque_critico()
            messagebox.showinfo("Sucesso", f"Ordem de Serviço {num_os} registrada com sucesso na nuvem!")
            import modulo_pdf
            dados_pdf = obter_dados_cliente_pdf(cod_cli) or {"cliente": nome_cliente, "tipo": tipo_cliente, "cod_cliente": cod_cli}
            dados_pdf.update({"num_os": num_os, "status": "Aberta", "descricao": desc_servico, "itens": obter_itens_pdf(), "valor_mao_obra": val_mao_obra})
            modulo_pdf.gerar_pdf_ordem_servico_detalhada(dados_pdf, janela_principal)
            for i in tabela_os.get_children(): tabela_os.delete(i)
            for i in tabela_historico_os.get_children(): tabela_historico_os.delete(i)
            itens_saida_memoria.clear()
            entry_cod_cli.delete(0, tk.END)
            entry_cod_tec.delete(0, tk.END)
            text_desc_servico.delete("1.0", tk.END)
            entry_mao_obra.delete(0, tk.END); entry_mao_obra.insert(0, "0,00")
            label_info_cliente.config(text="Cliente: [Não informado]", fg="#555555")
            label_info_tecnico.config(text="Técnico: [Não informado]", fg="#555555")
            
            if str(tab_historico) in notebook_os.tabs():
                notebook_os.forget(tab_historico)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar OS: {e}")

    def carregar_orcamento_salvo(numero_os):
        conn = config.obter_conexao_banco()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT dados_cliente, itens, descricao, valor_mao_obra, status FROM orcamentos WHERE numero_os = %s;", (numero_os,))
            row = cursor.fetchone()
            cursor.close(); conn.close()
            if not row:
                return False
            dados_cliente, itens, descricao, valor_mao_obra, status = row
            if isinstance(dados_cliente, str):
                dados_cliente = json.loads(dados_cliente)
            if isinstance(itens, str):
                itens = json.loads(itens)
            entry_cod_cli.delete(0, tk.END)
            entry_cod_cli.insert(0, dados_cliente.get("cod_cliente", ""))
            buscar_cliente_por_codigo()
            text_desc_servico.delete("1.0", tk.END)
            text_desc_servico.insert("1.0", descricao or "")
            entry_mao_obra.delete(0, tk.END)
            entry_mao_obra.insert(0, f"{float(valor_mao_obra or 0):.2f}".replace('.', ','))
            for item_id in tabela_os.get_children():
                tabela_os.delete(item_id)
            itens_saida_memoria.clear()
            for item in itens or []:
                registro = {"cod": item.get("cod", ""), "nome": item.get("nome", ""), "qtd": int(item.get("qtd", 0)), "obs": item.get("obs", "")}
                itens_saida_memoria.append(registro)
                tabela_os.insert("", "end", values=(registro["cod"], registro["nome"], registro["qtd"], registro["obs"]))
            messagebox.showinfo("Orçamento carregado", f"Orçamento da {numero_os} carregado. Status: {status}.", parent=janela_principal)
            return True
        except Exception as e:
            print("Erro ao carregar orçamento salvo:", e)
            return False

    def buscar_os_por_numero(event=None):
        num_os_digitado = entry_num_os.get().strip()
        if not num_os_digitado or num_os_digitado == "OS-":
            return

        if carregar_orcamento_salvo(num_os_digitado):
            return

        conn = config.obter_conexao_banco()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT observacao, descricao_servico FROM uso WHERE observacao ILIKE %s ORDER BY id DESC LIMIT 1;", (f"%{num_os_digitado}%",))
            res = cursor.fetchone()
            cursor.close(); conn.close()
            
            if res:
                obs_completa, desc_serv = res
                
                # Extrai o código do cliente diretamente da string de observação salva
                if "Cód.Cli:" in obs_completa:
                    for parte in obs_completa.split("|"):
                        if "Cód.Cli:" in parte:
                            cod_extraido = parte.split(":")[-1].strip()
                            entry_cod_cli.delete(0, tk.END)
                            entry_cod_cli.insert(0, cod_extraido)
                            buscar_cliente_por_codigo() # Dispara a busca para preencher o label do cliente
                            break

                # Preenche a solicitação original separada do serviço do técnico
                if desc_serv:
                    texto_separado = f"--- SOLICITAÇÃO ORIGINAL ---\n{desc_serv}\n\n--- SERVIÇO EXECUTADO PELO TÉCNICO ---\n"
                    text_desc_servico.delete("1.0", tk.END)
                    text_desc_servico.insert("1.0", texto_separado)
                    
                messagebox.showinfo("OS Encontrada", f"Pré-registro da {num_os_digitado} carregado com sucesso!", parent=janela_principal)
            '''else:
                messagebox.showwarning("Aviso", f"Nenhum pré-registro encontrado para a {num_os_digitado}.", parent=janela_principal)'''
        except Exception as e:
            print("Erro ao buscar OS por número:", e)

    entry_num_os.bind("<Return>", buscar_os_por_numero)
    entry_num_os.bind("<FocusOut>", buscar_os_por_numero)

    tk.Button(f_baixo_os, text="📄 Gerar orçamento / pré-OS", command=gerar_orcamento_os, bg="#7030A0", fg="white", font=("Arial", 10, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 5))
    tk.Button(f_baixo_os, text="✅ Registrar ordem de serviço", command=salvar_ordem_servico, bg="#2F5597", fg="white", font=("Arial", 10, "bold"), height=2).pack(side="right", fill="x", expand=True, padx=(5, 0))
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 9), height=1).pack(fill="x", pady=(2, 0))


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
    estilo_estorno = ttk.Style()
    estilo_estorno.configure("Estorno.Treeview", rowheight=42)

    tab_oc = ttk.Frame(notebook_estorno)
    notebook_estorno.add(tab_oc, text="  📦 Ordens de Compra (OC / Fornecedor)  ")

    f_oc_esq = tk.Frame(tab_oc, padx=10, pady=10)
    f_oc_esq.pack(side="left", fill="both", expand=True)

    tk.Label(f_oc_esq, text="Ordens de Compra Registradas:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 4))
    
    arvore_oc = ttk.Treeview(f_oc_esq, columns=("Detalhes", "Status", "ObsEstorno"), show="tree headings", height=13, style="Estorno.Treeview")
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
                if not desc and not tipo:
                    continue
                if desc and "Ordem de Compra:" in str(desc):
                    num_oc = str(desc).split("Ordem de Compra:", 1)[1].split("|", 1)[0].strip()
                else:
                    num_oc = f"OC-ENTRADA-{row_id}"
                if num_oc not in ocs_dict:
                    ocs_dict[num_oc] = []
                ocs_dict[num_oc].append({"id": row_id, "tipo": tipo, "qtd": int(qtd) if qtd else 0, "data": data, "status": status or "ATIVO", "fornecedor": desc or ""})
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
                cursor.execute("SELECT nome_item, quantidade, status FROM entrada WHERE id = %s;", (row_id,))
                res = cursor.fetchone()
                cursor.close()
                conn.close()
                if not res:
                    return
                tipo_item, qtd_atual, status_atual = res[0], int(res[1] or 0), res[2]
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
                historico_estorno = anexar_historico_estorno(status_atual, nova_auditoria)

                cursor_e.execute(
                    "UPDATE entrada SET quantidade = %s, status = %s WHERE id = %s;",
                    (novo_saldo, historico_estorno, row_id)
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
    
    arvore_os = ttk.Treeview(f_os_esq, columns=("Detalhes", "Status", "ObsEstorno"), show="tree headings", height=13, style="Estorno.Treeview")
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
                    num_os = ""
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
                cursor.execute("SELECT nome_equipamento, quantidade_usada, status FROM uso WHERE id = %s;", (row_id,))
                res = cursor.fetchone()
                cursor.close()
                conn.close()
                if not res:
                    return
                tipo_item, qtd_atual, status_atual = res[0], int(res[1] or 0), res[2]
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
                historico_devolucao = anexar_historico_estorno(status_atual, nova_auditoria)

                cursor_e.execute(
                    "UPDATE uso SET quantidade_usada = %s, status = %s WHERE id = %s;",
                    (novo_saldo, historico_devolucao, row_id)
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

    tk.Label(frame_principal, text="📦 Estoque de peças e materiais", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

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