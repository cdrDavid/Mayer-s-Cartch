import tkinter as tk
import os
import re
import unicodedata
from tkinter import messagebox
from tkinter import ttk
import openpyxl
from datetime import datetime
import subprocess
import sys
import config


def extrair_valor_mao_obra(texto):
    """Extrai somente o valor numérico do marcador de mão de obra."""
    texto_normalizado = unicodedata.normalize("NFKD", str(texto or ""))
    texto_normalizado = "".join(caractere for caractere in texto_normalizado if not unicodedata.combining(caractere))
    correspondencia = re.search(r"Mao de Obra:\s*R\$\s*([0-9.,]+)", texto_normalizado, re.IGNORECASE)
    if not correspondencia:
        return 0.0
    valor = correspondencia.group(1)
    if "," in valor and "." in valor:
        valor = valor.replace(".", "").replace(",", ".")
    else:
        valor = valor.replace(",", ".")
    return float(valor)


def formatar_numero_os(numero):
    """Exibe a OS com prefixo e seis dígitos, preservando o valor de busca."""
    texto = str(numero or "").strip()
    texto = re.sub(r"^OS\s*[-:]?\s*", "", texto, flags=re.IGNORECASE)
    if texto.isdigit():
        return f"OS {int(texto):06d}"
    return texto or "OS-N/D"


def extrair_numero_os(texto):
    correspondencia = re.search(r"(?:^|\|)\s*OS\s*:\s*([^|\n]+)", str(texto or ""), re.IGNORECASE)
    return correspondencia.group(1).strip() if correspondencia else "OS-N/D"

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

    tk.Label(frame_principal, text="📊 Painel da oficina", font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 8))

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

    lbl_kpi_saidas = tk.Label(f_kpis, text="🛠️ Ordens de serviço: 0", font=("Arial", 10, "bold"), bg="#F4CCCC", fg="#660000", padx=15, pady=8, relief="solid", bd=1)
    lbl_kpi_saidas.pack(side="left", padx=(0, 10), expand=True, fill="x")

    lbl_kpi_itens = tk.Label(f_kpis, text="🔩 Peças cadastradas: 0", font=("Arial", 10, "bold"), bg="#CFE2F3", fg="#1F4E79", padx=15, pady=8, relief="solid", bd=1)
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
                
                cursor.execute("SELECT nome_item, quantidade FROM entrada;")
                for item, qtd in cursor.fetchall():
                    q = int(qtd or 0)
                    if item:
                        total_ent += q
                        itens_contagem[item] = itens_contagem.get(item, 0) + q

                cursor.execute("SELECT nome_equipamento, quantidade_usada FROM uso;")
                for item, qtd in cursor.fetchall():
                    q = int(qtd or 0)
                    if item:
                        total_sai += q
                        itens_contagem[item] = itens_contagem.get(item, 0) + q

                cursor.execute("SELECT COUNT(*) FROM estoque;")
                res_est = cursor.fetchone()
                if res_est:
                    total_tipos_itens = res_est[0]

                cursor.close()
                conn.close()
            except Exception as e:
                print("Erro ao carregar dados do Supabase para o dashboard:", e)

        lbl_kpi_entradas.config(text=f"📥 Total Entradas: {total_ent}")
        lbl_kpi_saidas.config(text=f"🛠️ Ordens de serviço: {total_sai}")
        lbl_kpi_itens.config(text=f"🔩 Peças cadastradas: {total_tipos_itens}")

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
                ax.set_title("Peças mais utilizadas", fontsize=11, fontweight='bold', color='#333333')
                ax.set_ylabel("Quantidade Total", fontsize=9, fontweight='bold')
                ax.tick_params(axis='x', rotation=15)
                
                for barra in barras:
                    yval = barra.get_height()
                    ax.text(barra.get_x() + barra.get_width()/2, yval + 0.2, int(yval), ha='center', va='bottom', fontsize=9, fontweight='bold')
            else:
                ax.text(0.5, 0.5, "Nenhum dado encontrado.", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=11)

        elif "Pizza" in escolha_grafico:
            labels = ['Compras de peças', 'Ordens de serviço']
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
            
            dados_estoque = {}
            cursor.execute("SELECT tipo, valor_unitario, cod FROM estoque;")
            for nome_eq, val_eq, cod_eq in cursor.fetchall():
                if nome_eq:
                    dados_estoque[str(nome_eq).strip().lower()] = {
                        "cod": cod_eq or "N/D",
                        "val": float(val_eq or 0.0)
                    }

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
# 3. RELATÓRIO DE ATENDIMENTOS & ORDENS DE SERVIÇO (CONSOLIDADO + JANELA FLUTUANTE)
# ==========================================
def mostrar_tela_previa_relatorio(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Central unificada de Relatório de Atendimentos Consolidado por OS com Janela Flutuante de Detalhes"""
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)

    frame_principal = tk.Frame(janela_principal, padx=15, pady=12)
    frame_principal.pack(fill="both", expand=True)

    tk.Label(frame_principal, text="📊 Serviços e ordens de serviço", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 8))

    # --- FILTROS DE PESQUISA E COBRANÇA ---
    f_filtros = tk.LabelFrame(frame_principal, text=" Filtros de clientes, serviços e cobrança ", font=("Arial", 9, "bold"), padx=10, pady=8)
    f_filtros.pack(fill="x", pady=(0, 8))

    f_l1 = tk.Frame(f_filtros)
    f_l1.pack(fill="x", pady=(0, 4))

    tk.Label(f_l1, text="Tipo de Cliente:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    combo_tipo_cliente = ttk.Combobox(f_l1, values=["Todos", "Particular", "Prefeitura"], width=13, state="readonly")
    combo_tipo_cliente.set("Todos")
    combo_tipo_cliente.pack(side="left", padx=(0, 12))

    tk.Label(f_l1, text="Busca:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_busca_livre = tk.Entry(f_l1, font=("Arial", 9), width=22)
    entry_busca_livre.pack(side="left", padx=(0, 12))

    tk.Label(f_l1, text="Status:", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    combo_filtro_status = ttk.Combobox(f_l1, values=["Todos", "Aberta", "Em Andamento", "Concluída", "Faturada", "Cancelada"], width=13, state="readonly")
    combo_filtro_status.set("Todos")
    combo_filtro_status.pack(side="left", padx=(0, 12))

    tk.Label(f_l1, text="Acréscimo (%):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 4))
    entry_porcentagem = tk.Entry(f_l1, font=("Arial", 9), width=6)
    entry_porcentagem.pack(side="left", padx=(0, 5))
    entry_porcentagem.insert(0, "0")

    # --- TABELA DE ATENDIMENTOS CONSOLIDADA POR OS ---
    frame_tabela = tk.Frame(frame_principal)
    frame_tabela.pack(fill="both", expand=True, pady=(0, 8))

    colunas = ("OS", "Data", "Cliente", "TipoCliente", "Status", "ValorTotal", "Usuario")
    tabela_previa = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=12)
    
    tabela_previa.heading("OS", text="Nº OS"); tabela_previa.column("OS", width=100, anchor="center")
    tabela_previa.heading("Data", text="Data"); tabela_previa.column("Data", width=100, anchor="center")
    tabela_previa.heading("Cliente", text="Cliente / Setor"); tabela_previa.column("Cliente", width=280, anchor="w")
    tabela_previa.heading("TipoCliente", text="Tipo"); tabela_previa.column("TipoCliente", width=110, anchor="center")
    tabela_previa.heading("Status", text="Status OS"); tabela_previa.column("Status", width=120, anchor="center")
    tabela_previa.heading("ValorTotal", text="Valor Total (R$)"); tabela_previa.column("ValorTotal", width=140, anchor="center")
    tabela_previa.heading("Usuario", text="Registrado por"); tabela_previa.column("Usuario", width=130, anchor="center")

    scrollbar_prev = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela_previa.yview)
    tabela_previa.configure(yscrollcommand=scrollbar_prev.set)
    tabela_previa.pack(side="left", fill="both", expand=True)
    scrollbar_prev.pack(side="right", fill="y")

    def carregar_dados_filtrados():
        for i in tabela_previa.get_children():
            tabela_previa.delete(i)

        f_tipo_cli = combo_tipo_cliente.get()
        f_termo = entry_busca_livre.get().strip().lower()
        f_status = combo_filtro_status.get()
        
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

            # Busca todos os registros da tabela uso e agrupa por Nº da OS no dicionário
            cursor.execute("SELECT id, data, local_setor, nome_equipamento, quantidade_usada, observacao, usuario, status FROM uso ORDER BY id DESC;")
            
            oss_agrupadas = {}
            for row_id, data, setor, tipo_item, qtd, obs, usuario, status_db in cursor.fetchall():
                if not data or not obs:
                    continue

                num_os_str = extrair_numero_os(obs)

                if num_os_str not in oss_agrupadas:
                    status_atual = status_db if status_db else "Aberta"
                    tipo_cliente_detectado = "Particular"
                    if setor and "prefeitura" in str(setor).lower():
                        tipo_cliente_detectado = "Prefeitura"
                    elif setor and "particular" in str(setor).lower():
                        tipo_cliente_detectado = "Particular"

                    oss_agrupadas[num_os_str] = {
                        "data": data,
                        "setor": setor or "-",
                        "tipo_cliente": tipo_cliente_detectado,
                        "status": status_atual,
                        "usuario": usuario or "-",
                        "itens": [],
                        "obs_completa": obs
                    }

                quantidade = int(qtd or 0)
                val_unitario = precos_tabela.get(str(tipo_item).strip().lower(), 0.0)
                oss_agrupadas[num_os_str]["itens"].append({
                    "equipamento": tipo_item or "-",
                    "qtd": quantidade,
                    "val_unit": val_unitario
                })

            cursor.close()
            conn.close()

            # Aplica filtros e insere na tabela de forma consolidada
            for num_os, dados in oss_agrupadas.items():
                if f_status != "Todos" and f_status.lower() != dados["status"].lower():
                    continue
                if f_tipo_cli != "Todos" and f_tipo_cli.lower() != dados["tipo_cliente"].lower():
                    continue

                # Calcula o valor total da OS (soma dos equipamentos + mão de obra se houver na obs)
                valor_base_itens = sum(it["qtd"] * it["val_unit"] for it in dados["itens"])
                
                # Tenta extrair valor de mão de obra da observação se estiver cadastrado
                val_mao_obra = 0.0
                if "Mão de Obra: R$" in dados["obs_completa"]:
                    try:
                        val_mao_obra = extrair_valor_mao_obra(dados["obs_completa"])
                    except:
                        pass

                valor_total_base = valor_base_itens + val_mao_obra
                valor_com_acrescimo = valor_total_base * (1 + (percentual / 100.0))

                texto_geral = f"{num_os} {dados['setor']} {dados['usuario']} {dados['status']} {dados['obs_completa']}".lower()
                if f_termo and f_termo not in texto_geral:
                    continue

                tabela_previa.insert("", "end", values=(
                    formatar_numero_os(num_os),
                    dados["data"],
                    dados["setor"],
                    dados["tipo_cliente"],
                    dados["status"],
                    f"R$ {valor_com_acrescimo:.2f}".replace('.', ','),
                    dados["usuario"]
                ), tags=(dados["obs_completa"],))

        except Exception as e:
            print("Erro ao carregar relatório consolidado:", e)

    carregar_dados_filtrados()

    def abrir_janela_detalhes_os():
        selecao = tabela_previa.selection()
        if not selecao:
            messagebox.showwarning("Atenção", "Selecione uma Ordem de Serviço na tabela para ver os detalhes!", parent=janela_principal)
            return

        item_dados = tabela_previa.item(selecao[0])
        tags = item_dados.get("tags")
        vals = item_dados.get("values")
        
        if not tags:
            return

        obs_completa = tags[0]
        num_os_exibicao = formatar_numero_os(vals[0])
        num_os_busca = extrair_numero_os(obs_completa)

        # Cria janela flutuante centralizada com os detalhes completos
        top_detalhes = tk.Toplevel(janela_principal)
        top_detalhes.title(f"Detalhes Completos — {num_os_exibicao}")
        top_detalhes.geometry("600x480")
        top_detalhes.resizable(False, False)
        top_detalhes.grab_set()
        top_detalhes.update_idletasks()
        pos_x = janela_principal.winfo_rootx() + (janela_principal.winfo_width() - top_detalhes.winfo_width()) // 2
        pos_y = janela_principal.winfo_rooty() + (janela_principal.winfo_height() - top_detalhes.winfo_height()) // 2
        top_detalhes.geometry(f"600x480+{max(pos_x, 0)}+{max(pos_y, 0)}")

        f_det = tk.Frame(top_detalhes, padx=15, pady=15)
        f_det.pack(fill="both", expand=True)

        tk.Label(f_det, text=f"🔍 Detalhamento Completo da Ordem de Serviço {num_os_exibicao}", font=("Arial", 13, "bold"), fg="#1F4E79").pack(anchor="w", pady=(0, 10))

        txt_det = tk.Text(f_det, font=("Arial", 10), height=18, wrap="word", bg="#F8F9FA")
        txt_det.pack(fill="both", expand=True, pady=(0, 10))
        txt_det.insert("1.0", obs_completa)
        txt_det.config(state="disabled")

        def gerar_pdf_desta_os():
            conn = config.obter_conexao_banco()
            if not conn:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome_equipamento, quantidade_usada, observacao, descricao_servico, status FROM uso WHERE observacao ILIKE %s ORDER BY id ASC;", (f"%{num_os_busca}%",))
                registros = cursor.fetchall()
                if not registros:
                    raise ValueError("Nenhum registro foi encontrado para esta OS.")
                codigo_cliente = ""
                nome_cliente = ""
                for parte in str(registros[0][3] or "").split("|"):
                    if "Cód.Cli:" in parte:
                        codigo_cliente = parte.split(":", 1)[1].strip()
                    if "Cliente:" in parte:
                        nome_cliente = parte.split("Cliente:", 1)[1].strip()
                if nome_cliente:
                    nome_cliente = nome_cliente.split("(", 1)[0].strip()
                dados = {"num_os": num_os_exibicao, "status": registros[0][5] or "Aberta", "descricao": registros[0][4] or "", "itens": []}
                cliente = None
                if codigo_cliente:
                    cursor.execute("""SELECT codigo, nome, tipo, documento, cep, rua, numero, bairro, cidade,
                                      contato, email, modelo_central, modulo, mac_address, operadora, linha_numero, iccid,
                                      data_atualizacao FROM clientes WHERE codigo = %s;""", (codigo_cliente,))
                    cliente = cursor.fetchone()
                    if cliente:
                        dados.update({"cod_cliente": cliente[0], "cliente": cliente[1], "tipo": cliente[2], "documento": cliente[3], "cep": cliente[4], "rua": cliente[5], "numero": cliente[6], "bairro": cliente[7], "cidade": cliente[8], "contato": cliente[9], "email": cliente[10], "central": cliente[11], "modulo": cliente[12], "mac": cliente[13], "operadora": cliente[14], "linha": cliente[15], "iccid": cliente[16], "data_atualizacao": cliente[17]})
                if not cliente and nome_cliente:
                    cursor.execute("""SELECT codigo, nome, tipo, documento, cep, rua, numero, bairro, cidade,
                                      contato, email, modelo_central, modulo, mac_address, operadora, linha_numero, iccid,
                                      data_atualizacao FROM clientes WHERE nome ILIKE %s ORDER BY id DESC LIMIT 1;""", (nome_cliente,))
                    cliente = cursor.fetchone()
                    if cliente:
                        dados.update({"cod_cliente": cliente[0], "cliente": cliente[1], "tipo": cliente[2], "documento": cliente[3], "cep": cliente[4], "rua": cliente[5], "numero": cliente[6], "bairro": cliente[7], "cidade": cliente[8], "contato": cliente[9], "email": cliente[10], "central": cliente[11], "modulo": cliente[12], "mac": cliente[13], "operadora": cliente[14], "linha": cliente[15], "iccid": cliente[16], "data_atualizacao": cliente[17]})
                if not cliente and nome_cliente:
                    dados.update({"cliente": nome_cliente})
                valor_mao_obra = 0.0
                for registro_id, nome_item, quantidade, observacao, descricao, status in registros:
                    if nome_item and "Nenhum (Ajuste / Suporte)" not in nome_item:
                        cursor.execute("SELECT cod, valor_unitario FROM estoque WHERE tipo = %s LIMIT 1;", (nome_item,))
                        item_banco = cursor.fetchone()
                        dados["itens"].append({"cod": item_banco[0] if item_banco else "-", "nome": nome_item, "qtd": quantidade or 0, "valor_unitario": float(item_banco[1] or 0) if item_banco else 0, "obs": "-"})
                    if observacao and "Mão de Obra: R$" in observacao:
                        valor_mao_obra = extrair_valor_mao_obra(observacao)
                    if descricao:
                        dados["descricao"] = descricao
                dados["valor_mao_obra"] = valor_mao_obra
                cursor.close(); conn.close()
                import modulo_pdf
                modulo_pdf.gerar_pdf_ordem_servico_detalhada(dados, top_detalhes)
            except Exception as e:
                conn.close()
                messagebox.showerror("Erro", f"Não foi possível gerar o PDF da OS: {e}", parent=top_detalhes)

        f_acoes_detalhes = tk.Frame(f_det)
        f_acoes_detalhes.pack(fill="x")
        tk.Button(f_acoes_detalhes, text="📄 Gerar PDF da OS", command=gerar_pdf_desta_os, bg="#1F4E79", fg="white", font=("Arial", 10, "bold"), width=22, height=2).pack(side="left")
        tk.Button(f_acoes_detalhes, text="Fechar", command=top_detalhes.destroy, bg="#595959", fg="white", font=("Arial", 10, "bold"), width=15, height=2).pack(side="right")

    def alterar_status_os_selecionada():
        selecao = tabela_previa.selection()
        if not selecao:
            messagebox.showwarning("Atenção", "Selecione uma Ordem de Serviço na tabela para alterar o status!", parent=janela_principal)
            return

        item_vals = tabela_previa.item(selecao[0], "values")
        tags_os = tabela_previa.item(selecao[0], "tags")
        num_os = formatar_numero_os(item_vals[0])
        num_os_busca = extrair_numero_os(tags_os[0] if tags_os else item_vals[0])
        status_atual = item_vals[4]

        top_status = tk.Toplevel(janela_principal)
        top_status.title(f"Alterar Status — {num_os}")
        top_status.geometry("340x220")
        top_status.resizable(False, False)
        top_status.grab_set()

        tk.Label(top_status, text=f"Gerenciar Status da {num_os}", font=("Arial", 10, "bold")).pack(pady=(12, 6))
        tk.Label(top_status, text=f"Status Atual: {status_atual}", font=("Arial", 9, "italic"), fg="#555555").pack(pady=(0, 10))

        tk.Label(top_status, text="Novo Status:", font=("Arial", 9, "bold")).pack(anchor="w", padx=25)
        combo_novo_status = ttk.Combobox(top_status, values=["Aberta", "Em Andamento", "Concluída", "Faturada", "Cancelada"], width=25, state="readonly")
        combo_novo_status.set(status_atual)
        combo_novo_status.pack(pady=(2, 15))

        def confirmar_alteracao():
            novo_st = combo_novo_status.get().strip()
            if novo_st in ["Concluída", "Faturada", "Cancelada"]:
                if not messagebox.askyesno("Confirmação", f"Definir {num_os} como '{novo_st}'? Prosseguir?", parent=top_status):
                    return

            conn = config.obter_conexao_banco()
            if not conn:
                return

            try:
                cursor = conn.cursor()
                # Atualiza todas as linhas daquela OS na tabela uso
                cursor.execute("UPDATE uso SET status = %s WHERE observacao ILIKE %s;", (novo_st, f"%{num_os_busca}%"))
                conn.commit()
                cursor.close()
                conn.close()

                messagebox.showinfo("Sucesso", f"Status da {num_os} atualizado para '{novo_st}'!", parent=top_status)
                top_status.destroy()
                carregar_dados_filtrados()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar status: {e}", parent=top_status)

        tk.Button(top_status, text="💾 Salvar Novo Status", command=confirmar_alteracao, bg="#38761D", fg="white", font=("Arial", 9, "bold"), width=22, height=2).pack()

    # --- BOTÕES DE AÇÃO ---
    f_botoes = tk.Frame(frame_principal)
    f_botoes.pack(fill="x", pady=(4, 0))

    tk.Button(f_botoes, text="🔍 Filtrar", command=carregar_dados_filtrados, bg="#1F4E79", fg="white", font=("Arial", 9, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 4))
    tk.Button(f_botoes, text="📋 Ver Detalhes da OS", command=abrir_janela_detalhes_os, bg="#2F5597", fg="white", font=("Arial", 9, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 4))
    tk.Button(f_botoes, text="⚙️ Alterar Status", command=alterar_status_os_selecionada, bg="#B45F06", fg="white", font=("Arial", 9, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 4))

    def gerar_relatorio_final_excel():
        try:
            wb_rel = openpyxl.Workbook()
            ws = wb_rel.active
            ws.title = "Relatorio_Atendimentos_Detalhado"

            ws.append(["Nº OS", "Data", "Cliente / Setor", "Tipo de Cliente", "Status OS", "Valor Total (R$)", f"Valor com Acréscimo ({entry_porcentagem.get().strip()}%)", "Registrado por", "Detalhes Completos da OS & Serviços"])

            for item_id in tabela_previa.get_children():
                vals = tabela_previa.item(item_id, "values")
                obs_tag = tabela_previa.item(item_id, "tags")[0] if tabela_previa.item(item_id, "tags") else ""
                ws.append(list(vals) + [obs_tag])

            nome_arquivo = os.path.join(config.obter_pasta_saida('relatorios'), f"Relatorio_Atendimentos_Detalhado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            wb_rel.save(nome_arquivo)
            wb_rel.close()

            abrir = messagebox.askyesno("Relatório gerado", f"Relatório gerado com sucesso:\n{nome_arquivo}\n\nDeseja abrir agora?", parent=janela_principal)
            if abrir:
                os.startfile(nome_arquivo)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório em Excel: {e}", parent=janela_principal)

    tk.Button(f_botoes, text="📥 Excel Detalhado", command=gerar_relatorio_final_excel, bg="#38761D", fg="white", font=("Arial", 9, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 4))
    tk.Button(frame_principal, text="⬅ Voltar ao Menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 10), height=1).pack(fill="x", pady=(5, 0))
