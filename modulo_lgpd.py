"""Ferramentas locais de privacidade e atendimento aos direitos do titular.

As rotinas deste arquivo são chamadas pelo login, pelo cadastro de clientes e
pela aba LGPD em main.py. Elas apoiam o Controlador; não substituem análise
jurídica, controles operacionais ou procedimentos externos ao banco de dados.
"""

import csv
import json
import os
import re
import socket
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk
import tkinter as tk

import config


VERSAO_TERMOS = "2026-09-25.1"
PRAZO_SESSAO_MS = 15 * 60 * 1000
DOCUMENTO_ANONIMIZADO = "000.000.000-00"


def _executar(cursor, sql, parametros=()):
    """Executa SQL usando a conexão selecionada em `config.py`.

    O restante deste módulo escreve consultas com `?`, que é o marcador do
    SQLite. Esta função troca o marcador pelo formato configurado para o banco
    ativo e encaminha os valores separadamente, evitando concatenar dados do
    usuário dentro da consulta.
    """
    cursor.execute(sql.replace("?", config.PLACEHOLDER_SQL), parametros)


def _ip_local():
    """Retorna o endereço de rede local que será anexado ao aceite.

    Como o login roda neste aplicativo desktop, não há uma API web que observe
    o IP público do usuário. O valor vem do próprio computador e pode ser um IP
    privado da rede da oficina; em falha, registra-se um texto explicativo.
    """
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "indisponível"


def usuario_aceitou_termo_atual(usuario_id):
    """Verifica se o usuário já aceitou a versão atual dos termos.

    `main.py:fazer_login` chama esta função antes de abrir o menu. A consulta
    cruza o ID autenticado com `VERSAO_TERMOS`, então publicar uma versão nova
    volta a solicitar o aceite sem apagar o histórico anterior.
    Retorna `False` também se o banco estiver indisponível, bloqueando o acesso.
    """
    conn = config.obter_conexao_banco()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        _executar(cursor,
            "SELECT id FROM termos_aceites_log WHERE usuario_id = ? AND versao_termo = ? LIMIT 1;",
            (usuario_id, VERSAO_TERMOS)
        )
        aceitou = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return aceitou
    except Exception:
        conn.close()
        return False


def _registrar_aceite(usuario_id, username):
    """Insere a evidência do aceite na tabela `termos_aceites_log`.

    É chamada pelo botão "Aceito" de `exigir_aceite_termos`. A gravação inclui
    o ID e nome do usuário autenticado, horário com fuso, versão do documento
    e IP local. Só confirma a transação depois de o banco aceitar todos os dados.
    """
    conn = config.obter_conexao_banco()
    if not conn:
        raise RuntimeError("Não foi possível acessar o banco para registrar o aceite.")
    try:
        cursor = conn.cursor()
        _executar(cursor,
            "INSERT INTO termos_aceites_log (usu  ario_id, username, data_hora, versao_termo, endereco_ip) "
            "VALUES (?, ?, ?, ?, ?);",
            (usuario_id, username, datetime.now().astimezone().isoformat(timespec="seconds"), VERSAO_TERMOS, _ip_local())
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        conn.rollback()
        conn.close()
        raise


def exigir_aceite_termos(janela, usuario_id, username):
    """Mostra os termos no login e impede o menu sem aceite explícito.

    `main.py:fazer_login` chama esta função após validar as credenciais. Se o
    aceite desta versão já existir, retorna imediatamente `True`; caso contrário,
    abre uma janela modal. O botão de recusa e o X fecham sem gravar e retornam
    `False`, fazendo o chamador voltar à tela de login.
    """
    if usuario_aceitou_termo_atual(usuario_id):
        return True

    resultado = {"aceitou": False}
    dialogo = tk.Toplevel(janela)
    dialogo.title("Termos de Uso e Privacidade")
    largura = min(720, janela.winfo_screenwidth() - 40)
    altura = min(560, janela.winfo_screenheight() - 80)
    dialogo.geometry(f"{largura}x{altura}")
    dialogo.minsize(min(520, largura), min(420, altura))
    dialogo.transient(janela)
    dialogo.update_idletasks()
    pos_x = (janela.winfo_screenwidth() - largura) // 2
    pos_y = (janela.winfo_screenheight() - altura) // 2
    dialogo.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
    dialogo.grab_set()
    dialogo.protocol("WM_DELETE_WINDOW", dialogo.destroy)

    # Só a linha do texto recebe espaço extra; o rodapé fica sempre visível.
    dialogo.grid_columnconfigure(0, weight=1)
    dialogo.grid_rowconfigure(2, weight=1)
    tk.Label(dialogo, text="Termos de Uso e Política de Privacidade", font=("Arial", 14, "bold")).grid(
        row=0, column=0, sticky="w", padx=16, pady=(16, 6)
    )
    tk.Label(dialogo, text=f"Versão {VERSAO_TERMOS}", font=("Arial", 9, "italic")).grid(
        row=1, column=0, sticky="w", padx=16
    )

    quadro_texto = tk.Frame(dialogo)
    quadro_texto.grid(row=2, column=0, sticky="nsew", padx=16, pady=12)
    quadro_texto.grid_rowconfigure(0, weight=1)
    quadro_texto.grid_columnconfigure(0, weight=1)
    texto = tk.Text(quadro_texto, wrap="word", height=20, padx=10, pady=8)
    barra = ttk.Scrollbar(quadro_texto, orient="vertical", command=texto.yview)
    texto.configure(yscrollcommand=barra.set)
    texto.grid(row=0, column=0, sticky="nsew")
    barra.grid(row=0, column=1, sticky="ns")
    texto.insert("1.0", (
        "1. Papéis e finalidade\n"
        "O cliente da oficina atua como Controlador dos dados dos consumidores. "
        "Este software é uma ferramenta de apoio operada pelo fornecedor do sistema. "
        "O Controlador deve definir a finalidade e a base legal de cada tratamento.\n\n"
        "2. Uso dos dados\n"
        "Os dados cadastrados devem ser limitados ao atendimento automotivo, à "
        "execução de ordens de serviço, à comunicação solicitada e às obrigações legais. "
        "O consentimento para mensagens promocionais é opcional e separado do serviço.\n\n"
        "3. Acesso e segurança\n"
        "Cada usuário deve proteger suas credenciais, bloquear o computador quando "
        "se afastar e acessar apenas os dados necessários às suas tarefas. O sistema "
        "encerra a sessão após 15 minutos sem atividade.\n\n"
        "4. Direitos dos titulares\n"
        "O Controlador deve receber e avaliar solicitações de acesso, correção, "
        "portabilidade, oposição ou eliminação. O menu LGPD permite localizar, exportar "
        "e anonimizar dados mantidos neste banco, preservando referências financeiras.\n\n"
        "5. Limites e responsabilidade\n"
        "A ferramenta não determina a base legal, prazos legais de guarda, resposta a "
        "incidentes nem validade jurídica de documentos. O Controlador deve revisar "
        "estes termos, sua política própria e seus procedimentos com assessoria adequada.\n\n"
        "O aceite registra o usuário, a versão, o horário e o endereço IP local disponível "
        "neste computador. Esta versão é um texto inicial de produto e precisa ser ajustada "
        "à operação real antes de ser usada como instrumento jurídico."
    ))
    texto.configure(state="disabled")

    botoes = tk.Frame(dialogo)
    botoes.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))

    def aceitar():
        """Grava o aceite e fecha a janela somente se a gravação funcionar."""
        try:
            _registrar_aceite(usuario_id, username)
            resultado["aceitou"] = True
            dialogo.destroy()
        except Exception as erro:
            messagebox.showerror("Falha no registro", str(erro), parent=dialogo)

    tk.Button(botoes, text="Não aceito", command=dialogo.destroy, width=18).pack(side="left")
    tk.Button(botoes, text="Aceito", command=aceitar, width=18).pack(side="right")
    janela.wait_window(dialogo)
    return resultado["aceitou"]


def mascarar_documento(documento):
    """Mascara CPF/CNPJ antes de apresentá-lo em tabelas da interface.

    É reutilizada tanto pela lista de clientes em `modulo_financeiro.py` quanto
    pelo painel LGPD abaixo. A busca ainda consulta o valor original no banco;
    esta função afeta apenas o texto exibido, não altera o dado persistido.
    """
    digitos = re.sub(r"\D", "", str(documento or ""))
    if len(digitos) == 11:
        return f"***.{digitos[3:6]}.{digitos[6:9]}-**"
    if len(digitos) == 14:
        return f"**.***.{digitos[5:8]}/****-**"
    if len(digitos) > 4:
        return "*" * (len(digitos) - 4) + digitos[-4:]
    return "***"


def _registrar_evento(cursor, codigo, acao):
    """Adiciona uma ação de privacidade à tabela `lgpd_eventos`.

    Os callbacks do painel usam esta função após exportar, revelar/ocultar ou
    anonimizar. Guarda referência pelo código do cliente, usuário conectado e
    horário, sem copiar nome, documento ou contato para a própria auditoria.
    O chamador controla a transação e deve executar `commit()`.
    """
    _executar(cursor,
        "INSERT INTO lgpd_eventos (codigo_cliente, acao, usuario, data_hora) VALUES (?, ?, ?, ?);",
        (codigo, acao, config.usuario_logado, datetime.now().astimezone().isoformat(timespec="seconds"))
    )


def _converter_registro(cursor, linha):
    """Associa os nomes das colunas SQL aos valores retornados pelo cursor.

    O resultado permite que o CSV seja organizado por nomes de campo, mesmo
    quando o esquema ganha colunas. É usado por `_dados_titular`, que agrega
    registros de várias tabelas para a exportação.
    """
    return dict(zip((coluna[0] for coluna in cursor.description), linha))


def _json_para_csv(valor):
    """Normaliza valores JSONB/JSON para que possam ser serializados no CSV.

    PostgreSQL pode devolver JSONB como `dict` ou `list`; SQLite normalmente
    devolve o JSON armazenado como texto. Este adaptador transforma apenas os
    primeiros em texto JSON e deixa os demais valores como vieram do banco.
    """
    if isinstance(valor, (dict, list)):
        return json.dumps(valor, ensure_ascii=False, default=str)
    return valor


def _dados_titular(codigo):
    """Reúne os dados associados ao código do cliente para a exportação.

    `exportar_dados`, callback do painel LGPD, consome o dicionário retornado.
    A consulta inclui cadastro, orçamentos, ordens de serviço e histórico. Novas
    ordens são ligadas por `uso.codigo_cliente`; registros legados sem esse campo
    também são encontrados pelo nome enquanto o cadastro ainda o possui.
    """
    conn = config.obter_conexao_banco()
    if not conn:
        raise RuntimeError("Não foi possível conectar ao banco de dados.")
    try:
        cursor = conn.cursor()
        _executar(cursor, "SELECT * FROM clientes WHERE codigo = ?;", (codigo,))
        linha_cliente = cursor.fetchone()
        if not linha_cliente:
            raise LookupError("O cliente não foi encontrado.")
        cliente = _converter_registro(cursor, linha_cliente)

        _executar(cursor,
            "SELECT numero_os, codigo_cliente, data, dados_cliente, itens, descricao, valor_mao_obra, status, usuario "
            "FROM orcamentos WHERE codigo_cliente = ? ORDER BY numero_os;",
            (codigo,)
        )
        orcamentos = [_converter_registro(cursor, linha) for linha in cursor.fetchall()]
        for orcamento in orcamentos:
            orcamento["dados_cliente"] = _json_para_csv(orcamento.get("dados_cliente"))
            orcamento["itens"] = _json_para_csv(orcamento.get("itens"))

        nome = str(cliente.get("nome") or "")
        _executar(cursor,
            "SELECT data, local_setor, nome_equipamento, quantidade_usada, observacao, usuario, status, descricao_servico "
            "FROM uso WHERE codigo_cliente = ? OR (? <> ? AND (local_setor LIKE ? OR observacao LIKE ? OR descricao_servico LIKE ?)) ORDER BY id;",
            (codigo, nome, "Cliente Excluído", f"%{nome}%", f"%{nome}%", f"%{nome}%")
        )
        ordens = [_converter_registro(cursor, linha) for linha in cursor.fetchall()] if nome else []

        _executar(cursor,
            "SELECT data, num_conta, descricao_log, item, quantidade, usuario FROM atualizacoes WHERE num_conta = ? ORDER BY id;",
            (codigo,)
        )
        atualizacoes = [_converter_registro(cursor, linha) for linha in cursor.fetchall()]
        cursor.close()
        conn.close()
        return {"cliente": cliente, "orcamentos": orcamentos, "ordens_de_servico": ordens, "historico": atualizacoes}
    except Exception:
        conn.close()
        raise


def _substituir_pii(valor, dados_pessoais):
    """Substitui identificadores conhecidos dentro de textos livres.

    O nome é tratado como palavra para não remover partes de outras palavras;
    números/endereço só são trocados quando têm pelo menos seis caracteres,
    evitando alterar acidentalmente valores curtos como quantidade ou preço.
    O chamador passa os dados que acabou de ler da linha `clientes`.
    """
    texto = str(valor or "")
    for indice, dado in enumerate(dados_pessoais):
        if dado:
            if indice == 0:
                texto = re.sub(
                    rf"(?<!\w){re.escape(dado)}(?!\w)", "Cliente Excluído", texto, flags=re.IGNORECASE
                )
            elif len(dado) >= 6:
                texto = texto.replace(dado, "Cliente Excluído")
    return texto


def _anonimizar_json(valor, dados_pessoais):
    """Percorre dicionários/listas de JSON e remove campos pessoais conhecidos.

    É usada para limpar `orcamentos.dados_cliente`, que guarda uma cópia dos
    dados usados na emissão do orçamento. Campos financeiros e itens continuam
    no JSON; campos de identificação listados abaixo são apagados ou recebem
    o marcador "Cliente Excluído".
    """
    campos_pessoais = {
        "cliente", "documento", "cep", "rua", "numero", "bairro", "cidade",
        "contato", "email", "central", "modulo", "mac", "operadora", "linha",
        "iccid", "data_atualizacao"
    }
    if isinstance(valor, dict):
        resultado = {}
        for chave, conteudo in valor.items():
            if str(chave).lower() in campos_pessoais:
                resultado[chave] = "Cliente Excluído" if str(chave).lower() == "cliente" else None
            else:
                resultado[chave] = _anonimizar_json(conteudo, dados_pessoais)
        return resultado
    if isinstance(valor, list):
        return [_anonimizar_json(item, dados_pessoais) for item in valor]
    if isinstance(valor, str):
        return _substituir_pii(valor, dados_pessoais)
    return valor


def anonimizar_cliente(codigo, parent):
    """Anonimiza o cadastro e as cópias conhecidas sem apagar valores financeiros.

    `esquecer_cliente`, no painel abaixo, chama esta função após confirmação do
    código. Primeiro lê os identificadores, depois atualiza `clientes`, `orcamentos`,
    `uso` e `atualizacoes` dentro da mesma transação. O código e os valores das
    compras/serviços permanecem para que relatórios e conciliações continuem
    funcionando. Em qualquer falha, `rollback()` desfaz o conjunto inteiro.
    `parent` é mantido na assinatura para receber a janela da tela chamadora.
    """
    conn = config.obter_conexao_banco()
    if not conn:
        raise RuntimeError("Não foi possível conectar ao banco de dados.")
    try:
        cursor = conn.cursor()
        _executar(cursor, "SELECT nome, documento, contato, email, cep, rua, numero, bairro, cidade FROM clientes WHERE codigo = ?;", (codigo,))
        cliente = cursor.fetchone()
        if not cliente:
            raise LookupError("O cliente não foi encontrado.")
        nome = str(cliente[0] or "")
        dados_pessoais = ([nome] if nome else []) + [
            str(valor) for valor in cliente[1:] if valor and len(str(valor).strip()) >= 6
        ]

        # O UPDATE substitui a identidade, limpa contatos/dados técnicos e revoga
        # consentimentos; o código permanece como chave dos registros financeiros.
        _executar(cursor,
            "UPDATE clientes SET nome = ?, documento = ?, cep = NULL, rua = NULL, numero = NULL, bairro = NULL, "
            "cidade = NULL, contato = NULL, email = NULL, modelo_central = NULL, modulo = NULL, mac_address = NULL, "
            "operadora = NULL, linha_numero = NULL, iccid = NULL, consentimento_email = ?, "
            "consentimento_whatsapp = ?, consentimento_atualizado_em = ?, data_atualizacao = ? WHERE codigo = ?;",
            ("Cliente Excluído", DOCUMENTO_ANONIMIZADO, False, False,
             datetime.now().astimezone().isoformat(timespec="seconds"), datetime.now().strftime("%d/%m/%Y"), codigo)
        )

        # Orçamentos guardam um retrato do cliente em JSON; limpar só `clientes`
        # deixaria uma cópia identificável acessível no histórico da OS.
        _executar(cursor, "SELECT numero_os, dados_cliente, descricao FROM orcamentos WHERE codigo_cliente = ?;", (codigo,))
        for numero_os, dados_cliente, descricao in cursor.fetchall():
            if isinstance(dados_cliente, str):
                try:
                    dados_cliente = json.loads(dados_cliente)
                except json.JSONDecodeError:
                    dados_cliente = _substituir_pii(dados_cliente, dados_pessoais)
            dados_limpos = _anonimizar_json(dados_cliente, dados_pessoais)
            descricao_limpa = _substituir_pii(descricao, dados_pessoais)
            if config.DATABASE_URL:
                _executar(cursor,
                    "UPDATE orcamentos SET dados_cliente = ?::jsonb, descricao = ? WHERE numero_os = ?;",
                    (json.dumps(dados_limpos, ensure_ascii=False), descricao_limpa, numero_os)
                )
            else:
                _executar(cursor,
                    "UPDATE orcamentos SET dados_cliente = ?, descricao = ? WHERE numero_os = ?;",
                    (json.dumps(dados_limpos, ensure_ascii=False), descricao_limpa, numero_os)
                )

        # O código identifica ordens novas com precisão. A busca pelo nome cobre
        # ordens antigas criadas antes de `uso.codigo_cliente` existir.
        _executar(cursor,
            "SELECT id, local_setor, observacao, descricao_servico FROM uso "
            "WHERE codigo_cliente = ? OR (? <> ? AND (local_setor LIKE ? OR observacao LIKE ? OR descricao_servico LIKE ?));",
            (codigo, nome, "Cliente Excluído", f"%{nome}%", f"%{nome}%", f"%{nome}%")
        )
        for ordem_id, local_setor, observacao, descricao_servico in cursor.fetchall():
            setor_limpo = _substituir_pii(local_setor, dados_pessoais)
            observacao_limpa = _substituir_pii(observacao, dados_pessoais)
            servico_limpo = _substituir_pii(descricao_servico, dados_pessoais)
            _executar(cursor,
                "UPDATE uso SET local_setor = ?, observacao = ?, descricao_servico = ? WHERE id = ?;",
                (setor_limpo, observacao_limpa, servico_limpo, ordem_id)
            )

        _executar(cursor, "SELECT id, descricao_log, item FROM atualizacoes WHERE num_conta = ?;", (codigo,))
        for log_id, descricao_log, item in cursor.fetchall():
            _executar(cursor,
                "UPDATE atualizacoes SET descricao_log = ?, item = ? WHERE id = ?;",
                (_substituir_pii(descricao_log, dados_pessoais), _substituir_pii(item, dados_pessoais), log_id)
            )

        _registrar_evento(cursor, codigo, "ANONIMIZACAO")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        conn.rollback()
        conn.close()
        raise


def mostrar_painel_lgpd(janela_principal, limpar_tela, centralizar_janela, voltar_menu_callback):
    """Monta a tela LGPD e conecta os botões às consultas e rotinas de privacidade.

    `main.py:mostrar_menu_principal` abre esta tela pela aba Privacidade/LGPD.
    Os callbacks internos compartilham a tabela visual e o código selecionado:
    pesquisar preenche a lista; exportar_dados gera CSV; esquecer_cliente chama
    `anonimizar_cliente`; revelar_documentos aplica a permissão e registra auditoria.
    Ao sair, `voltar_menu_callback` retorna à aba do menu que chamou esta tela.
    """
    limpar_tela(janela_principal)
    centralizar_janela(janela_principal, config.LARGURA_PADRAO, config.ALTURA_PADRAO)
    frame = tk.Frame(janela_principal, padx=18, pady=14)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Privacidade e dados do titular", font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 8))
    filtros = tk.Frame(frame)
    filtros.pack(fill="x", pady=(0, 8))
    tk.Label(filtros, text="Buscar por nome, código ou CPF:").pack(side="left", padx=(0, 6))
    busca = tk.Entry(filtros, width=42)
    busca.pack(side="left", padx=(0, 8))

    tabela = ttk.Treeview(frame, columns=("codigo", "nome", "documento"), show="headings", height=15)
    tabela.heading("codigo", text="Código")
    tabela.heading("nome", text="Nome")
    tabela.heading("documento", text="CPF / CNPJ mascarado")
    tabela.column("codigo", width=100, anchor="center")
    tabela.column("nome", width=360, anchor="w")
    tabela.column("documento", width=210, anchor="center")
    tabela.pack(fill="both", expand=True, pady=(0, 8))
    estado = {"documentos": {}, "revelado": False}

    def pesquisar(event=None):
        """Filtra clientes no banco e redesenha a lista com documentos mascarados."""
        for item in tabela.get_children():
            tabela.delete(item)
        termo = busca.get().strip()
        conn = config.obter_conexao_banco()
        if not conn:
            messagebox.showerror("Banco indisponível", "Não foi possível conectar ao banco.", parent=janela_principal)
            return
        try:
            cursor = conn.cursor()
            parte = f"%{termo}%"
            _executar(cursor,
                "SELECT codigo, nome, documento FROM clientes WHERE nome LIKE ? OR codigo LIKE ? OR documento LIKE ? ORDER BY nome;",
                (parte, parte, parte)
            )
            estado["documentos"] = {}
            for codigo, nome, documento in cursor.fetchall():
                estado["documentos"][codigo] = documento
                tabela.insert("", "end", iid=str(codigo), values=(codigo, nome or "", mascarar_documento(documento)))
            cursor.close()
            conn.close()
        except Exception as erro:
            conn.close()
            messagebox.showerror("Erro na pesquisa", str(erro), parent=janela_principal)

    def codigo_selecionado():
        """Retorna o código da linha selecionada, usado como chave nas ações."""
        selecao = tabela.selection()
        return tabela.item(selecao[0], "values")[0] if selecao else None

    def revelar_documentos():
        """Alterna a exibição do documento e registra quem revelou/ocultou."""
        if config.usuario_nivel_logado not in ("admin", "gerente"):
            messagebox.showwarning("Acesso restrito", "Somente usuários com nível de gerente podem revelar documentos.", parent=janela_principal)
            return
        estado["revelado"] = not estado["revelado"]
        for codigo, documento in estado["documentos"].items():
            if tabela.exists(str(codigo)):
                valores = list(tabela.item(str(codigo), "values"))
                valores[2] = str(documento or "") if estado["revelado"] else mascarar_documento(documento)
                tabela.item(str(codigo), values=valores)
        conn = config.obter_conexao_banco()
        if conn:
            try:
                cursor = conn.cursor()
                _registrar_evento(cursor, codigo_selecionado(), "REVELACAO_DOCUMENTO" if estado["revelado"] else "OCULTACAO_DOCUMENTO")
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                conn.rollback()
                conn.close()
        botao_revelar.configure(text="Ocultar documentos" if estado["revelado"] else "Revelar documentos")

    def exportar_dados():
        """Gera um CSV do titular selecionado e registra a exportação."""
        codigo = codigo_selecionado()
        if not codigo:
            messagebox.showwarning("Selecione um titular", "Selecione um cliente antes de exportar.", parent=janela_principal)
            return
        try:
            dados = _dados_titular(codigo)
        except Exception as erro:
            messagebox.showerror("Falha na exportação", str(erro), parent=janela_principal)
            return
        caminho = filedialog.asksaveasfilename(
            parent=janela_principal, title="Exportar dados do titular", defaultextension=".csv",
            initialfile=f"dados_titular_{codigo}.csv", filetypes=[("Arquivo CSV", "*.csv")]
        )
        if not caminho:
            return
        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.writer(arquivo)
                escritor.writerow(("categoria", "registro_json"))
                for categoria, registros in dados.items():
                    conjunto = registros if isinstance(registros, list) else [registros]
                    for registro in conjunto:
                        escritor.writerow((categoria, json.dumps(registro, ensure_ascii=False, default=str)))
            conn = config.obter_conexao_banco()
            if conn:
                cursor = conn.cursor()
                _registrar_evento(cursor, codigo, "EXPORTACAO_CSV")
                conn.commit()
                cursor.close()
                conn.close()
            messagebox.showinfo("Exportação concluída", f"Arquivo gerado em:\n{caminho}", parent=janela_principal)
        except Exception as erro:
            messagebox.showerror("Falha ao gravar CSV", str(erro), parent=janela_principal)

    def esquecer_cliente():
        """Confirma a ação irreversível e chama a anonimização transacional."""
        codigo = codigo_selecionado()
        if not codigo:
            messagebox.showwarning("Selecione um titular", "Selecione um cliente antes de anonimizar.", parent=janela_principal)
            return
        confirmado = simpledialog.askstring(
            "Confirmar anonimização", f"Esta ação remove identificadores e não pode ser desfeita.\nDigite o código {codigo} para confirmar:",
            parent=janela_principal
        )
        if confirmado != str(codigo):
            return
        try:
            anonimizar_cliente(codigo, janela_principal)
            messagebox.showinfo("Anonimização concluída", "Os identificadores foram removidos. Os registros e valores financeiros foram preservados.", parent=janela_principal)
            pesquisar()
        except Exception as erro:
            messagebox.showerror("Falha na anonimização", str(erro), parent=janela_principal)

    tk.Button(filtros, text="Pesquisar", command=pesquisar).pack(side="left")
    busca.bind("<Return>", pesquisar)
    botoes = tk.Frame(frame)
    botoes.pack(fill="x", pady=(0, 8))
    tk.Button(botoes, text="Exportar dados CSV", command=exportar_dados, bg="#2F5597", fg="white", font=("Arial", 10, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 5))
    tk.Button(botoes, text="Esquecer", command=esquecer_cliente, bg="#B45F06", fg="white", font=("Arial", 10, "bold"), height=2).pack(side="left", fill="x", expand=True, padx=(0, 5))
    botao_revelar = tk.Button(botoes, text="Revelar documentos", command=revelar_documentos, bg="#38761D", fg="white", font=("Arial", 10, "bold"), height=2)
    botao_revelar.pack(side="left", fill="x", expand=True, padx=(0, 5))
    tk.Button(frame, text="Voltar ao menu", command=voltar_menu_callback, bg="#595959", fg="white", font=("Arial", 9), height=1).pack(fill="x", pady=(2, 0))