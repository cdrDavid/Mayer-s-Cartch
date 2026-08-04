import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
import subprocess
import sys
import config

# Garante a instalação automática do matplotlib para os gráficos do dashboard
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import matplotlib.pyplot as plt
    except Exception as e:
        print("Aviso: Não foi possível instalar o matplotlib automaticamente:", e)

# ==========================================
# 1. TELA DE DASHBOARD ANALÍTICO AVANÇADO - SUPABASE
# ==========================================
def mostrar_tela_dashboard(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Dashboard Rico em Detalhes com Gráficos e Filtros Analíticos via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=12)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📊 Dashboard Analítico & Indicadores (Nuvem)", font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 8))

    f_controles = tk.LabelFrame(frame_principal, text=" Filtros e Opções de Visualização ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_controles.pack(fill="x", pady=(0, 8))

    f_l_ctrl = tk.Frame(f_controles)
    f_l_ctrl.pack(fill="x", pady=2)

    tk.Label(f_l_ctrl, text="Tipo de Gráfico:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    combo_tipo_grafico = ttk.Combobox(f_l_ctrl, values=["Gráfico de Barras (Itens Mais Movimentados)", "Gráfico de Pizza (Proporção de Movimentações)", "Gráfico de Linha (Evolução Temporal)"], width=42, state="readonly")
    combo_tipo_grafico.set("Gráfico de Barras (Itens Mais Movimentados)")
    combo_tipo_grafico.pack(side="left", padx=(0, 20))

    tk.Label(f_l_ctrl, text="Período:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    combo_periodo = ttk.Combobox(f_l_ctrl, values=["Todo o Período", "Este Mês", "Últimos 3 Meses"], width=18, state="readonly")
    combo_periodo.set("Todo o Período")
    combo_periodo.pack(side="left", padx=(0, 20))

    f_kpis = tk.Frame(frame_principal)
    f_kpis.pack(fill="x", pady=(0, 8))

    lbl_kpi_entradas = tk.Label(f_kpis, text="📥 Total Entradas: 0", font=("Arial", 10, "bold"), bg="#D9EAD3", fg="#274E13", padx=15, pady=8, relief="solid", bd=1)
    lbl_kpi_entradas.pack(side="left", padx=(0, 10), expand=True, fill="x")

    lbl_kpi_saidas = tk.Label(f_kpis, text="📤 Total Saídas (OS): 0", font=("Arial", 10, "bold"), bg="#F4CCCC", fg="#660000", padx=15, pady=8, relief="solid", bd=1)
    lbl_kpi_saidas.pack(side="left", padx=(0, 10), expand=True, fill="x")

    lbl_kpi_itens = tk.Label(f_kpis, text="📦 Tipos de Itens Ativos: 0", font=("Arial", 10, "bold"), bg="#CFE2F3", fg="#1F4E79", padx=15, pady=8, relief="solid", bd=1)
    lbl_kpi_itens.pack(side="left", expand=True, fill="x")

    frame_grafico = tk.Frame(frame_principal, bg="white", relief="solid", bd=1)
    frame_grafico.pack(fill="both", expand=True, pady=(0, 10))

    def atualizar_dashboard(event=None):
        for widget in frame_grafico.winfo_children():
            widget.destroy()

        total_ent = 0
        total_sai = 0
        itens_contagem = {}
        total_tipos_itens = 0

        conn = config.obter_conexao_banco()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Entradas
                cursor.execute("SELECT nome_item, quantidade FROM entrada;")
                for item, qtd in cursor.fetchall():
                    q = int(qtd or 0)
                    if item:
                        total_ent += q
                        itens_contagem[item] = itens_contagem.get(item, 0) + q

                # Saídas (Uso)
                cursor.execute("SELECT nome_equipamento, quantidade_usada FROM uso;")
                for item, qtd in cursor.fetchall():
                    q = int(qtd or 0)
                    if item:
                        total_sai += q
                        itens_contagem[item] = itens_contagem.get(item, 0) + q

                # Total Tipos de Itens no Estoque
                cursor.execute("SELECT COUNT(*) FROM estoque;")
                res_est = cursor.fetchone()
                if res_est:
                    total_tipos_itens = res_est[0]

                cursor.close()
                conn.close()
            except Exception as e:
                print("Erro ao carregar dados do Supabase para o dashboard:", e)

        lbl_kpi_entradas.config(text=f"📥 Total Entradas: {total_ent}")
        lbl_kpi_saidas.config(text=f"📤 Total Saídas (OS): {total_sai}")
        lbl_kpi_itens.config(text=f"📦 Tipos de Itens Ativos: {total_tipos_itens}")

        fig, ax = plt.subplots(figsize=(10, 4.3), dpi=100)
        fig.patch.set_facecolor('#F8F9FA')
        ax.set_facecolor('white')

        escolha_grafico = combo_tipo_grafico.get()

        if "Barras" in escolha_grafico:
            if itens_contagem:
                itens_ordenados = sorted(itens_contagem.items(), key=lambda x: x[1], reverse=True)[:6]
                nomes = [x[0] for x in itens_ordenados]
                valores = [x[1] for x in itens_ordenados]
                
                barras = ax.bar(nomes, valores, color='#1F4E79', width=0.55)
                ax.set_title("Top Equipamentos Mais Movimentados", fontsize=11, fontweight='bold', color='#333333')
                ax.set_ylabel("Quantidade Total", fontsize=9, fontweight='bold')
                ax.tick_params(axis='x', rotation=15)
                
                for barra in barras:
                    yval = barra.get_height()
                    ax.text(barra.get_x() + barra.get_width()/2, yval + 0.2, int(yval), ha='center', va='bottom', fontsize=9, fontweight='bold')
            else:
                ax.text(0.5, 0.5, "Nenhum dado encontrado.", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=11)

        elif "Pizza" in escolha_grafico:
            labels = ['Entradas (Compras)', 'Saídas (OS)']
            tamanhos = [total_ent, total_sai]
            cores = ['#38761D', '#CC0000']
            
            if sum(tamanhos) > 0:
                ax.pie(tamanhos, labels=labels, autopct='%1.1f%%', startangle=90, colors=cores, textprops={'fontsize': 10, 'weight': 'bold'}, wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
                ax.set_title("Proporção Geral: Entradas vs Saídas", fontsize=11, fontweight='bold', color='#333333')
            else:
                ax.text(0.5, 0.5, "Sem dados suficientes.", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=11)

        elif "Linha" in escolha_grafico:
            dias_exemplo = ['Início', 'Parcial', 'Atual']
            mov_exemplo = [0, max(1, total_ent // 2), total_ent + total_sai]
            
            ax.plot(dias_exemplo, mov_exemplo, marker='o', color='#B45F06', linewidth=2.5, markersize=8)
            ax.set_title("Evolução Consolidada do Fluxo", fontsize=11, fontweight='bold', color='#333333')
            ax.set_ylabel("Volume Acumulado", fontsize=9, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.6)

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    combo_tipo_grafico.bind("<<ComboboxSelected>>", atualizar_dashboard)
    combo_periodo.bind("<<ComboboxSelected>>", atualizar_dashboard)
    atualizar_dashboard()

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(5, 0))


# ==========================================
# 2. RELATÓRIO DE INDICADORES FINANCEIROS DE COMPRAS - SUPABASE
# ==========================================
def mostrar_tela_relatorio_financeiro(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Painel Detalhado de Ordens de Compra, Itens e Histórico via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=12)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="💰 Detalhamento de Ordens de Compra & Itens (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    frame_tabela = tk.Frame(frame_principal)
    frame_tabela.pack(fill="both", expand=True, pady=(0, 10))

    colunas = ("Detalhes", "Qtd", "ValorUnit", "ValorTotal")
    tabela_fin = ttk.Treeview(frame_tabela, columns=colunas, show="tree headings", height=14)
    
    tabela_fin.heading("#0", text="Nº da Compra / Nome do Item")
    tabela_fin.column("#0", width=380, anchor="w")
    tabela_fin.heading("Detalhes", text="Cód. do Item / Status / Data")
    tabela_fin.column("Detalhes", width=220, anchor="w")
    tabela_fin.heading("Qtd", text="Quantidade")
    tabela_fin.column("Qtd", width=100, anchor="center")
    tabela_fin.heading("ValorUnit", text="Valor Unit. (R$)")
    tabela_fin.column("ValorUnit", width=140, anchor="center")
    tabela_fin.heading("ValorTotal", text="Total Gasto (R$)")
    tabela_fin.column("ValorTotal", width=150, anchor="center")

    scrollbar_fin = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela_fin.yview)
    tabela_fin.configure(yscrollcommand=scrollbar_fin.set)
    tabela_fin.pack(side="left", fill="both", expand=True)
    scrollbar_fin.pack(side="right", fill="y")

    def carregar_dados_financeiros_detalhados():
        for i in tabela_fin.get_children():
            tabela_fin.delete(i)
        
        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            
            # Mapeia códigos e preços cadastrados no estoque
            dados_estoque = {}
            cursor.execute("SELECT tipo, valor_unitario, cod FROM estoque;")
            for nome_eq, val_eq, cod_eq in cursor.fetchall():
                if nome_eq:
                    dados_estoque[str(nome_eq).strip().lower()] = {
                        "cod": cod_eq or "N/D",
                        "val": float(val_eq or 0.0)
                    }

            # Agrupa os itens por Ordem de Compra
            cursor.execute("SELECT data, fornecedor_descricao, nome_item, quantidade, status FROM entrada ORDER BY id ASC;")
            ocs_dict = {}
            for data, desc_forn, nome_item, qtd, status_estorno in cursor.fetchall():
                if not data or not nome_item:
                    continue

                num_oc = "Outras Entradas"
                if "Ordem de Compra:" in str(desc_forn):
                    num_oc = str(desc_forn).split(":")[-1].strip()

                if num_oc not in ocs_dict:
                    ocs_dict[num_oc] = []

                info_est = dados_estoque.get(str(nome_item).strip().lower(), {"cod": "N/D", "val": 0.0})
                ocs_dict[num_oc].append({
                    "data": data,
                    "nome": str(nome_item).strip(),
                    "cod": info_est["cod"],
                    "qtd": int(qtd) if qtd is not None else 0,
                    "val_unit": info_est["val"],
                    "status": str(status_estorno or "ATIVO")
                })

            cursor.close()
            conn.close()

            for oc_num, itens in ocs_dict.items():
                total_oc = sum(it["qtd"] * it["val_unit"] for it in itens)
                qtd_total_oc = sum(it["qtd"] for it in itens)
                
                ativos = [it for it in itens if it["qtd"] > 0]
                st_pai = "ESTORNADA" if not ativos else "ATIVO"
                tag_pai = "estornado" if st_pai == "ESTORNADA" else "normal"
                txt_pai = f"📋 {oc_num}" if st_pai == "ATIVO" else f"❌ [ESTORNADA] {oc_num}"

                pai_id = tabela_fin.insert("", "end", text=txt_pai, values=(f"Total Ativo: {qtd_total_oc} un", "", "", f"R$ {total_oc:.2f}".replace('.', ',')), tags=(tag_pai,))
                
                for it in itens:
                    tot_item = it["qtd"] * it["val_unit"]
                    
                    if it["qtd"] == 0:
                        txt_label = f"   ↳ ❌ [ESTORNADO] {it['nome']}"
                        tag_nome = "estornado"
                        status_txt = "ESTORNADO"
                    else:
                        tag_nome = "normal"
                        if it["status"] != "ATIVO":
                            txt_label = f"   ↳ 🔹 {it['nome']} (Parcial)"
                            status_txt = it["status"]
                        else:
                            txt_label = f"   ↳ 🔹 {it['nome']}"
                            status_txt = "ATIVO"

                    tabela_fin.insert(pai_id, "end", text=txt_label, values=(f"Cód: {it['cod']} | {status_txt}", it["qtd"], f"R$ {it['val_unit']:.2f}".replace('.', ','), f"R$ {tot_item:.2f}".replace('.', ',')), tags=(tag_nome,))

        except Exception as e:
            print("Erro ao carregar detalhes financeiros de compras do Supabase:", e)

    tabela_fin.tag_configure("estornado", foreground="#999999")
    carregar_dados_financeiros_detalhados()

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(5, 0))


# ==========================================
# 3. PRÉ-VISUALIZAÇÃO E RELATÓRIO DE ATENDIMENTOS - SUPABASE
# ==========================================
def mostrar_tela_previa_relatorio(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Tela de filtragem, visualização e cálculo de acréscimo via Supabase"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, 1250, 750)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=12)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="🔍 Filtros e Pré-visualização de Atendimentos (Nuvem)", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 10))

    f_filtros = tk.LabelFrame(frame_principal, text=" Critérios de Filtragem e Cobrança ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_filtros.pack(fill="x", pady=(0, 10))

    f_l1 = tk.Frame(f_filtros)
    f_l1.pack(fill="x", pady=(0, 5))

    tk.Label(f_l1, text="Tipo de Cliente:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    combo_tipo_cliente = ttk.Combobox(f_l1, values=["Todos", "Particular", "Prefeitura"], width=15, state="readonly")
    combo_tipo_cliente.set("Todos")
    combo_tipo_cliente.pack(side="left", padx=(0, 15))

    tk.Label(f_l1, text="Busca (Nome / Descrição / Palavra-chave):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_busca_livre = tk.Entry(f_l1, font=("Arial", 9), width=25)
    entry_busca_livre.pack(side="left", padx=(0, 15))

    tk.Label(f_l1, text="Acréscimo (%):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_porcentagem = tk.Entry(f_l1, font=("Arial", 9), width=8)
    entry_porcentagem.pack(side="left", padx=(0, 5))
    entry_porcentagem.insert(0, "0")

    frame_tabela = tk.Frame(frame_principal)
    frame_tabela.pack(fill="both", expand=True, pady=(0, 10))

    colunas = ("Data", "Cliente", "TipoCliente", "Equipamento", "Qtd", "ValorBase", "ValorComAcrescimo", "Observacao")
    tabela_previa = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=12)
    
    for col, txt in zip(colunas, ["Data", "Cliente / Setor", "Tipo", "Equipamento", "Qtd", "Valor Base (R$)", "Valor Cobrança (R$)", "Observação / OS"]):
        tabela_previa.heading(col, text=txt)
    
    tabela_previa.column("Data", width=85, anchor="center")
    tabela_previa.column("Cliente", width=180, anchor="w")
    tabela_previa.column("TipoCliente", width=90, anchor="center")
    tabela_previa.column("Equipamento", width=170, anchor="w")
    tabela_previa.column("Qtd", width=60, anchor="center")
    tabela_previa.column("ValorBase", width=110, anchor="center")
    tabela_previa.column("ValorComAcrescimo", width=140, anchor="center")
    tabela_previa.column("Observacao", width=280, anchor="w")

    scrollbar_prev = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela_previa.yview)
    tabela_previa.configure(yscrollcommand=scrollbar_prev.set)
    tabela_previa.pack(side="left", fill="both", expand=True)
    scrollbar_prev.pack(side="right", fill="y")

    def carregar_dados_filtrados():
        for i in tabela_previa.get_children():
            tabela_previa.delete(i)

        f_tipo_cli = combo_tipo_cliente.get()
        f_termo = entry_busca_livre.get().strip().lower()
        
        try:
            porcent_str = entry_porcentagem.get().strip().replace(",", ".")
            percentual = float(porcent_str) if porcent_str else 0.0
        except ValueError:
            percentual = 0.0

        conn = config.obter_conexao_banco()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            
            precos_tabela = {}
            cursor.execute("SELECT tipo, valor_unitario FROM estoque;")
            for nome_eq, val_eq in cursor.fetchall():
                if nome_eq:
                    precos_tabela[str(nome_eq).strip().lower()] = float(val_eq or 0.0)

            cursor.execute("SELECT data, local_setor, nome_equipamento, quantidade_usada, observacao FROM uso;")
            for data, setor, tipo_item, qtd, obs in cursor.fetchall():
                if not data:
                    continue

                tipo_cliente_detectado = "Particular"
                if setor and "prefeitura" in str(setor).lower():
                    tipo_cliente_detectado = "Prefeitura"
                elif setor and "particular" in str(setor).lower():
                    tipo_cliente_detectado = "Particular"

                if f_tipo_cli != "Todos" and f_tipo_cli.lower() != tipo_cliente_detectado.lower():
                    continue

                texto_geral = f"{setor} {tipo_item} {obs}".lower()
                if f_termo and f_termo not in texto_geral:
                    continue

                quantidade = int(qtd or 0)
                val_unitario = precos_tabela.get(str(tipo_item).strip().lower(), 0.0)
                valor_base_total = val_unitario * quantidade
                valor_com_acrescimo = valor_base_total * (1 + (percentual / 100.0))

                tabela_previa.insert("", "end", values=(
                    data, 
                    setor or "-", 
                    tipo_cliente_detectado, 
                    tipo_item or "-", 
                    quantidade, 
                    f"R$ {valor_base_total:.2f}".replace('.', ','), 
                    f"R$ {valor_com_acrescimo:.2f}".replace('.', ','), 
                    obs or "-"
                ))

            cursor.close()
            conn.close()
        except Exception as e:
            print("Erro ao carregar prévia de relatórios do Supabase:", e)

    carregar_dados_filtrados()

    f_botoes = tk.Frame(frame_principal)
    f_botoes.pack(fill="x", pady=(5, 5))

    tk.Button(f_botoes, text="🔍 Aplicar Filtros e Recalcular", command=carregar_dados_filtrados, bg="#1F4E79", fg="white", font=("Arial", 9, "bold"), width=25).pack(side="left", padx=(0, 10))

    def gerar_relatorio_final_excel():
        try:
            import openpyxl
            wb_rel = openpyxl.Workbook()
            ws = wb_rel.active
            ws.title = "Relatorio_Atendimentos"

            ws.append(["Data", "Cliente / Setor", "Tipo de Cliente", "Equipamento", "Quantidade", "Valor Base (R$)", f"Valor com Acrescimo ({entry_porcentagem.get().strip()}%)", "Observação / OS"])

            for item_id in tabela_previa.get_children():
                vals = tabela_previa.item(item_id, "values")
                ws.append(vals)

            nome_arquivo = f"Relatorio_Filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            wb_rel.save(nome_arquivo)
            wb_rel.close()

            messagebox.showinfo("Sucesso", f"Relatório gerado e salvo com sucesso como:\n{nome_arquivo}", parent=janela_principal)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório: {e}", parent=janela_principal)

    tk.Button(f_botoes, text="📥 Gerar Relatório em Excel", command=gerar_relatorio_final_excel, bg="#38761D", fg="white", font=("Arial", 9, "bold"), width=25).pack(side="left")

    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(8, 0))