import os
import subprocess
from datetime import datetime
from tkinter import messagebox
import config
from xml.sax.saxutils import escape

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    pass


def preparar_caminho_pdf(tipo, nome):
    return os.path.join(config.obter_pasta_saida(tipo), nome)


def informar_arquivo_gerado(titulo, caminho, janela_pai):
    abrir = messagebox.askyesno(titulo, f"Arquivo gerado com sucesso:\n{caminho}\n\nDeseja abrir agora?", parent=janela_pai)
    if abrir:
        try:
            os.startfile(caminho)
        except Exception as erro:
            messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{erro}", parent=janela_pai)


def gerar_pdf_ordem_servico(num_os, nome_cliente, tipo_cliente, itens_os, valor_mao_obra, janela_pai):
    """Gera um PDF formatado para a Ordem de Serviço (OS)"""
    try:
        nome_arquivo = preparar_caminho_pdf('ordens_servico', f"OS_{num_os.replace('/', '-')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elementos = []
        
        styles = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1F4E79'), alignment=1, spaceAfter=10)
        estilo_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#555555'), spaceAfter=15)
        estilo_corpo = ParagraphStyle('Corpo', parent=styles['Normal'], fontSize=10, textColor=colors.black, spaceAfter=6)
        
        # Cabeçalho do Documento
        elementos.append(Paragraph(f"<b>ORDEM DE SERVIÇO - {num_os}</b>", estilo_titulo))
        elementos.append(Paragraph(f"<b>Data de Emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>Emitido por:</b> {config.usuario_logado}", estilo_sub))
        elementos.append(Spacer(1, 10))
        
        # Dados do Cliente
        elementos.append(Paragraph(f"<b>Cliente:</b> {nome_cliente} ({tipo_cliente})", estilo_corpo))
        elementos.append(Spacer(1, 10))
        
        # Tabela de Itens da OS
        dados_tabela = [["Cód.", "Equipamento / Item", "Qtd", "Observação"]]
        for item in itens_os:
            dados_tabela.append([str(item.get('cod', '-')), str(item.get('nome', '-')), str(item.get('qtd', 0)), str(item.get('obs', '-'))])
            
        tabela = Table(dados_tabela, colWidths=[70, 220, 50, 190])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        elementos.append(tabela)
        elementos.append(Spacer(1, 15))
        
        # Resumo Financeiro (Mão de Obra)
        if valor_mao_obra > 0:
            elementos.append(Paragraph(f"<b>Valor da Mão de Obra:</b> R$ {valor_mao_obra:.2f}".replace('.', ','), estilo_corpo))
            
        doc.build(elementos)
        informar_arquivo_gerado("Ordem de serviço", nome_arquivo, janela_pai)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível gerar o PDF da OS: {e}", parent=janela_pai)


def gerar_pdf_ordem_compra(num_oc, fornecedor, itens_oc, janela_pai):
    """Gera um PDF formatado para a Ordem de Compra (OC)"""
    try:
        nome_arquivo = preparar_caminho_pdf('ordens_compra', f"OC_{num_oc.replace('/', '-')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elementos = []
        
        styles = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#38761D'), alignment=1, spaceAfter=10)
        estilo_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#555555'), spaceAfter=15)
        estilo_corpo = ParagraphStyle('Corpo', parent=styles['Normal'], fontSize=10, textColor=colors.black, spaceAfter=6)
        
        elementos.append(Paragraph(f"<b>ORDEM DE COMPRA - {num_oc}</b>", estilo_titulo))
        elementos.append(Paragraph(f"<b>Data de Emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>Solicitante:</b> {config.usuario_logado}", estilo_sub))
        elementos.append(Spacer(1, 10))
        
        elementos.append(Paragraph(f"<b>Fornecedor / Descrição:</b> {fornecedor}", estilo_corpo))
        elementos.append(Spacer(1, 10))
        
        dados_tabela = [["Nome do Item / Equipamento", "Quantidade"]]
        for item in itens_oc:
            dados_tabela.append([str(item.get('nome', '-')), str(item.get('qtd', 0))])
            
        tabela = Table(dados_tabela, colWidths=[380, 150])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#38761D')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        elementos.append(tabela)
        doc.build(elementos)
        informar_arquivo_gerado("Ordem de compra", nome_arquivo, janela_pai)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível gerar o PDF da OC: {e}", parent=janela_pai)


def gerar_pdf_ordem_servico_tecnico(dados_os, janela_pai):
    """Gera o PDF da Ordem de Serviço em branco/pré-preenchida para o técnico com logo e 5 linhas de serviço"""
    try:
        num_os = dados_os.get('num_os', 'OS-00000')
        nome_arquivo = preparar_caminho_pdf('ordens_servico', f"OS_Tecnico_{num_os.replace('/', '-')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
        elementos = []
        
        styles = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle('TituloOS', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#1F4E79'), alignment=0, spaceAfter=2)
        estilo_sub = ParagraphStyle('SubOS', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#555555'), spaceAfter=8)
        estilo_corpo = ParagraphStyle('CorpoOS', parent=styles['Normal'], fontSize=9, textColor=colors.black, spaceAfter=4)
        
        # Tentativa de carregar a logo do ícone para o canto superior esquerdo
        cabecalho_tabela_dados = []
        # Caminho seguro para localizar o ícone na mesma pasta do projeto
        caminho_icone = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icone.ico')
        
        texto_cabecalho = [
            Paragraph("<b>MAYER'S CARTCH - OFICINA ESPECIALIZADA</b>", estilo_titulo),
            Paragraph("<b>Orçamento</b>", ParagraphStyle('SubTit', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#333333'), spaceAfter=4)),
            Paragraph(f"<b>Nº da OS:</b> {num_os} | <b>Data de Emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>Emitido por:</b> {config.usuario_logado}", estilo_sub)
        ]

        if os.path.exists(caminho_icone):
            try:
                from reportlab.platypus import Image
                # Redimensiona o ícone para caber perfeitamente no cabeçalho
                logo = Image(caminho_icone, width=45, height=45)
                cabecalho_tabela_dados = [[logo, texto_cabecalho]]
                t_cabecalho = Table(cabecalho_tabela_dados, colWidths=[55, 485])
                t_cabecalho.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ]))
                elementos.append(t_cabecalho)
            except Exception:
                elementos.extend(texto_cabecalho)
        else:
            elementos.extend(texto_cabecalho)
            
        elementos.append(Spacer(1, 4))
        
        # Bloco de Informações Cadastrais e Técnicas
        tabela_dados = [
            [Paragraph(f"<b>Cliente:</b> {dados_os.get('cliente', '-')}", estilo_corpo), Paragraph(f"<b>Cód. Cliente:</b> {dados_os.get('cod_cliente', '-')}", estilo_corpo)],
            [Paragraph(f"<b>Endereço:</b> {dados_os.get('rua', '-')}, nº {dados_os.get('numero', '-')}", estilo_corpo), Paragraph(f"<b>Contrato / Tipo:</b> {dados_os.get('tipo', '-')}", estilo_corpo)],
            [Paragraph(f"<b>Bairro:</b> {dados_os.get('bairro', '-')}", estilo_corpo), Paragraph(f"<b>Cidade:</b> {dados_os.get('cidade', '-')}", estilo_corpo)],
            [Paragraph(f"<b>Central de Alarme:</b> {dados_os.get('central', '-')}", estilo_corpo), Paragraph(f"<b>Módulo:</b> {dados_os.get('modulo', '-')}", estilo_corpo)],
            [Paragraph(f"<b>Operadora / Linha:</b> {dados_os.get('operadora', '-')} ({dados_os.get('linha', '-')})", estilo_corpo), Paragraph(f"<b>ICCID:</b> {dados_os.get('iccid', '-')}", estilo_corpo)],
            [Paragraph(f"<b>Mac Address:</b> {dados_os.get('mac', '-')}", estilo_corpo), Paragraph(f"<b>Contato:</b> {dados_os.get('contato', '-')}", estilo_corpo)]
        ]
        
        t_cad = Table(tabela_dados, colWidths=[310, 230])
        t_cad.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E0E0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        
        elementos.append(t_cad)
        elementos.append(Spacer(1, 6))
        
        # Solicitação do Serviço
        solicitacao_txt = dados_os.get('solicitacao', 'Manutenção preventiva / Corretiva de alarme.')
        t_sol = Table([[Paragraph(f"<b>Solicitação / Descrição do Chamado:</b><br/>{solicitacao_txt}", estilo_corpo)]], colWidths=[540])
        t_sol.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#1F4E79')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EBF1F5')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]))
        elementos.append(t_sol)
        elementos.append(Spacer(1, 8))
        
        # Bloco de Relatório Técnico (Exatamente 5 linhas bem espaçadas e centralizadas)
        estilo_linha = ParagraphStyle('LinhaEscrita', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#777777'), alignment=1, spaceBefore=8, spaceAfter=8)
        
        t_campo = Table([
            [Paragraph("<b>Relatório do Técnico / Serviço Executado:</b>", estilo_corpo)],
            [Paragraph("________________________________________________________________________________________________", estilo_linha)],
            [Paragraph("________________________________________________________________________________________________", estilo_linha)],
            [Paragraph("________________________________________________________________________________________________", estilo_linha)],
            [Paragraph("________________________________________________________________________________________________", estilo_linha)],
            [Paragraph("________________________________________________________________________________________________", estilo_linha)],
            [Paragraph("<b>Materiais Utilizados em Campo:</b>", estilo_corpo)],
            [Paragraph("________________________________________________________________________________________________", estilo_linha)],
            [Paragraph("________________________________________________________________________________________________", estilo_linha)]
        ], colWidths=[540])
        
        t_campo.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        elementos.append(t_campo)
        elementos.append(Spacer(1, 10))
        
        # Assinaturas centralizadas nas colunas
        t_ass = Table([
            [Paragraph("________________________________________<br/>Assinatura do Técnico", estilo_corpo),
             Paragraph("________________________________________<br/>Assinatura / Carimbo do Cliente", estilo_corpo)]
        ], colWidths=[270, 270])
        t_ass.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
        ]))
        elementos.append(t_ass)
        
        doc.build(elementos)
        informar_arquivo_gerado("Ordem de serviço", nome_arquivo, janela_pai)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível gerar o PDF da OS para o técnico: {e}", parent=janela_pai)


def gerar_pdf_orcamento(dados_orcamento, janela_pai):
    """Gera uma solicitação de orçamento com aparência documental e resumo financeiro."""
    try:
        numero = str(dados_orcamento.get('num_orcamento', 'ORC-00000')).replace('/', '-')
        nome_arquivo = preparar_caminho_pdf('orcamentos', f"Orcamento_{numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=30, bottomMargin=30)
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle('TituloOrcamento', parent=estilos['Heading1'], fontSize=16, textColor=colors.HexColor('#1F4E79'), alignment=1, spaceAfter=3)
        subtitulo = ParagraphStyle('SubtituloOrcamento', parent=estilos['Normal'], fontSize=9, textColor=colors.HexColor('#555555'), alignment=1, spaceAfter=10)
        corpo = ParagraphStyle('CorpoOrcamento', parent=estilos['Normal'], fontSize=8.5, leading=11, textColor=colors.black)
        pequeno = ParagraphStyle('PequenoOrcamento', parent=corpo, fontSize=8, leading=10)
        direita = ParagraphStyle('DireitaOrcamento', parent=corpo, alignment=2)

        def texto(valor):
            return escape(str(valor or '-'))

        itens = dados_orcamento.get('itens_orcamento', [])
        valor_mao_obra = float(dados_orcamento.get('valor_mao_obra', 0) or 0)
        total_itens = sum(float(item.get('qtd', 0)) * float(item.get('valor_unitario', 0) or 0) for item in itens)
        total_geral = total_itens + valor_mao_obra

        elementos = []
        caminho_icone = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icone.ico')
        cabecalho = [
            Paragraph('<b>MAYER\'S CARTCH - OFICINA ESPECIALIZADA</b>', titulo),
            Paragraph('<b>SOLICITAÇÃO DE ORÇAMENTO</b>', ParagraphStyle('TipoOrcamento', parent=estilos['Heading2'], fontSize=11, alignment=1, textColor=colors.HexColor('#333333'))),
            Paragraph(f"<b>Nº do Orçamento:</b> {texto(dados_orcamento.get('num_orcamento'))} | <b>Emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>Responsável:</b> {texto(config.usuario_logado)}", subtitulo)
        ]
        if os.path.exists(caminho_icone):
            try:
                from reportlab.platypus import Image
                logo = Image(caminho_icone, width=42, height=42)
                topo = Table([[logo, cabecalho]], colWidths=[55, 485])
                topo.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#B7C9D6')), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F7FA'))]))
                elementos.append(topo)
            except Exception:
                elementos.extend(cabecalho)
        else:
            elementos.extend(cabecalho)
        elementos.append(Spacer(1, 8))

        cliente = [
            [Paragraph(f"<b>Cliente:</b> {texto(dados_orcamento.get('cliente'))}", corpo), Paragraph(f"<b>Código:</b> {texto(dados_orcamento.get('cod_cliente'))}", corpo)],
            [Paragraph(f"<b>Tipo:</b> {texto(dados_orcamento.get('tipo'))} | <b>CPF/CNPJ:</b> {texto(dados_orcamento.get('documento'))}", pequeno), Paragraph(f"<b>Contato:</b> {texto(dados_orcamento.get('contato'))}", pequeno)],
            [Paragraph(f"<b>Endereço:</b> {texto(dados_orcamento.get('rua'))}, nº {texto(dados_orcamento.get('numero'))} - {texto(dados_orcamento.get('bairro'))}", pequeno), Paragraph(f"<b>Cidade:</b> {texto(dados_orcamento.get('cidade'))} - <b>CEP:</b> {texto(dados_orcamento.get('cep'))}", pequeno)],
            [Paragraph(f"<b>E-mail:</b> {texto(dados_orcamento.get('email'))}", pequeno), Paragraph(f"<b>Atualização cadastral:</b> {texto(dados_orcamento.get('data_atualizacao'))}", pequeno)],
               [Paragraph(f"<b>Marca:</b> {texto(dados_orcamento.get('central'))}", pequeno), Paragraph(f"<b>Linha:</b> {texto(dados_orcamento.get('modulo'))}", pequeno)],
            [Paragraph(f"<b>Ano:</b> {texto(dados_orcamento.get('operadora'))} | <b>Combustível:</b> {texto(dados_orcamento.get('linha'))}", pequeno), Paragraph(f"<b>Modelo:</b> {texto(dados_orcamento.get('mac'))}", pequeno)]
        ]
        tabela_cliente = Table(cliente, colWidths=[310, 230])
        tabela_cliente.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')), ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#B7C9D6')), ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#D9E2E8')), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('LEFTPADDING', (0, 0), (-1, -1), 7)]))
        elementos.append(tabela_cliente)
        elementos.append(Spacer(1, 8))

        solicitacao = texto(dados_orcamento.get('solicitacao'))
        elementos.append(Table([[Paragraph(f"<b>Descrição da solicitação:</b><br/>{solicitacao}", corpo)]], colWidths=[540], style=TableStyle([('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#1F4E79')), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EBF1F5')), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('LEFTPADDING', (0, 0), (-1, -1), 8)])))
        elementos.append(Spacer(1, 8))

        linhas = [[Paragraph('<b>Código</b>', pequeno), Paragraph('<b>Item / Serviço</b>', pequeno), Paragraph('<b>Qtd.</b>', pequeno), Paragraph('<b>Valor unitário</b>', pequeno), Paragraph('<b>Total</b>', pequeno), Paragraph('<b>Observação</b>', pequeno)]]
        for item in itens:
            qtd = float(item.get('qtd', 0) or 0)
            unitario = float(item.get('valor_unitario', 0) or 0)
            linhas.append([Paragraph(texto(item.get('cod')), pequeno), Paragraph(texto(item.get('nome')), pequeno), Paragraph(f'{qtd:g}', direita), Paragraph(f'R$ {unitario:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), direita), Paragraph(f'R$ {qtd * unitario:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), direita), Paragraph(texto(item.get('obs')), pequeno)])
        linhas.append([Paragraph('', pequeno), Paragraph('<b>Prestação de serviço / mão de obra</b>', pequeno), Paragraph('1', direita), Paragraph(f'R$ {valor_mao_obra:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), direita), Paragraph(f'R$ {valor_mao_obra:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), direita), Paragraph('', pequeno)])
        tabela_itens = Table(linhas, colWidths=[65, 190, 40, 85, 85, 75], repeatRows=1)
        tabela_itens.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B7C9D6')), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (2, 1), (4, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
        elementos.append(tabela_itens)
        elementos.append(Spacer(1, 8))

        total_formatado = f'R$ {total_geral:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        resumo = Table([[Paragraph('<b>TOTAL DO ORÇAMENTO</b>', corpo), Paragraph(f'<b>{total_formatado}</b>', ParagraphStyle("Total", parent=corpo, alignment=2, fontSize=12, textColor=colors.HexColor('#1F4E79')))]], colWidths=[400, 140])
        resumo.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EAF2F8')), ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1F4E79')), ('TOPPADDING', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 9), ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8)]))
        elementos.append(resumo)
        elementos.append(Spacer(1, 12))
        elementos.append(Paragraph('Este documento é uma solicitação de orçamento e não representa uma nota fiscal eletrônica.', ParagraphStyle('Aviso', parent=pequeno, alignment=1, textColor=colors.HexColor('#666666'))))

        doc.build(elementos)
        informar_arquivo_gerado("Orçamento", nome_arquivo, janela_pai)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível gerar o orçamento: {e}", parent=janela_pai)


def gerar_pdf_ordem_servico_detalhada(dados_os, janela_pai):
    """Gera a ordem de serviço definitiva a partir dos dados registrados."""
    try:
        numero = str(dados_os.get('num_os', 'OS-00000')).replace('/', '-')
        nome_arquivo = preparar_caminho_pdf('ordens_servico', f"OrdemServico_{numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        doc = SimpleDocTemplate(nome_arquivo, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=30, bottomMargin=30)
        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle('TituloOSFinal', parent=estilos['Heading1'], fontSize=16, textColor=colors.HexColor('#1F4E79'), alignment=1, spaceAfter=3)
        corpo = ParagraphStyle('CorpoOSFinal', parent=estilos['Normal'], fontSize=8.5, leading=11)
        pequeno = ParagraphStyle('PequenoOSFinal', parent=corpo, fontSize=8)
        direita = ParagraphStyle('DireitaOSFinal', parent=corpo, alignment=2)

        def texto(valor):
            return escape(str(valor or '-'))

        itens = dados_os.get('itens', [])
        mao_obra = float(dados_os.get('valor_mao_obra', 0) or 0)
        total_itens = sum(float(item.get('qtd', 0)) * float(item.get('valor_unitario', 0) or 0) for item in itens)
        total = total_itens + mao_obra
        moeda = lambda valor: f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        elementos = []
        caminho_icone = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icone.ico')
        cabecalho = [
            Paragraph("<b>MAYER'S CARTCH - OFICINA ESPECIALIZADA</b>", titulo),
            Paragraph(f"<b>ORDEM DE SERVIÇO</b> - {texto(dados_os.get('num_os'))}", ParagraphStyle('TipoOSFinal', parent=estilos['Heading2'], fontSize=11, alignment=1)),
            Paragraph(f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | <b>Status:</b> {texto(dados_os.get('status', 'Aberta'))} | <b>Responsável:</b> {texto(config.usuario_logado)}", pequeno)
        ]
        if os.path.exists(caminho_icone):
            try:
                from reportlab.platypus import Image
                logo = Image(caminho_icone, width=42, height=42)
                topo = Table([[logo, cabecalho]], colWidths=[55, 485])
                topo.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#B7C9D6')), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F7FA'))]))
                elementos.append(topo)
            except Exception:
                elementos.extend(cabecalho)
        else:
            elementos.extend(cabecalho)
        elementos.append(Spacer(1, 8))
        cliente = [
            [Paragraph(f"<b>Cliente:</b> {texto(dados_os.get('cliente'))}", corpo), Paragraph(f"<b>Código:</b> {texto(dados_os.get('cod_cliente'))}", corpo)],
            [Paragraph(f"<b>CPF/CNPJ:</b> {texto(dados_os.get('documento'))}", pequeno), Paragraph(f"<b>Contato:</b> {texto(dados_os.get('contato'))}", pequeno)],
            [Paragraph(f"<b>Endereço:</b> {texto(dados_os.get('rua'))}, nº {texto(dados_os.get('numero'))} - {texto(dados_os.get('bairro'))}", pequeno), Paragraph(f"<b>Cidade:</b> {texto(dados_os.get('cidade'))} - <b>CEP:</b> {texto(dados_os.get('cep'))}", pequeno)],
            [Paragraph(f"<b>Marca:</b> {texto(dados_os.get('central'))}", pequeno), Paragraph(f"<b>Linha:</b> {texto(dados_os.get('modulo'))}", pequeno)],
            [Paragraph(f"<b>Ano:</b> {texto(dados_os.get('operadora'))} | <b>Combustível:</b> {texto(dados_os.get('linha'))}", pequeno), Paragraph(f"<b>Modelo:</b> {texto(dados_os.get('mac'))}", pequeno)]
        ]
        tabela_cliente = Table(cliente, colWidths=[310, 230])
        tabela_cliente.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')), ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#B7C9D6')), ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#D9E2E8')), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5), ('LEFTPADDING', (0, 0), (-1, -1), 7)]))
        elementos.extend([tabela_cliente, Spacer(1, 8)])
        elementos.append(Table([[Paragraph(f"<b>Serviço executado:</b><br/>{texto(dados_os.get('descricao'))}", corpo)]], colWidths=[540], style=TableStyle([('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#1F4E79')), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EBF1F5')), ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7), ('LEFTPADDING', (0, 0), (-1, -1), 8)])))
        elementos.append(Spacer(1, 8))
        linhas = [[Paragraph('<b>Código</b>', pequeno), Paragraph('<b>Peça / serviço</b>', pequeno), Paragraph('<b>Qtd.</b>', pequeno), Paragraph('<b>Unitário</b>', pequeno), Paragraph('<b>Total</b>', pequeno), Paragraph('<b>Observação</b>', pequeno)]]
        for item in itens:
            qtd = float(item.get('qtd', 0) or 0); unitario = float(item.get('valor_unitario', 0) or 0)
            linhas.append([Paragraph(texto(item.get('cod')), pequeno), Paragraph(texto(item.get('nome')), pequeno), Paragraph(f'{qtd:g}', direita), Paragraph(moeda(unitario), direita), Paragraph(moeda(qtd * unitario), direita), Paragraph(texto(item.get('obs')), pequeno)])
        linhas.append([Paragraph('', pequeno), Paragraph('<b>Mão de obra</b>', pequeno), Paragraph('1', direita), Paragraph(moeda(mao_obra), direita), Paragraph(moeda(mao_obra), direita), Paragraph('', pequeno)])
        tabela_itens = Table(linhas, colWidths=[65, 190, 40, 85, 85, 75], repeatRows=1)
        tabela_itens.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B7C9D6')), ('ALIGN', (2, 1), (4, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
        elementos.extend([tabela_itens, Spacer(1, 8)])
        resumo = Table([[Paragraph('<b>TOTAL DA ORDEM DE SERVIÇO</b>', corpo), Paragraph(f'<b>{moeda(total)}</b>', ParagraphStyle('TotalOSFinal', parent=corpo, alignment=2, fontSize=12, textColor=colors.HexColor('#1F4E79')))]], colWidths=[400, 140])
        resumo.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EAF2F8')), ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1F4E79')), ('TOPPADDING', (0, 0), (-1, -1), 9), ('BOTTOMPADDING', (0, 0), (-1, -1), 9)]))
        elementos.append(resumo)
        doc.build(elementos)
        informar_arquivo_gerado("Ordem de serviço", nome_arquivo, janela_pai)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível gerar o PDF da ordem de serviço: {e}", parent=janela_pai)
