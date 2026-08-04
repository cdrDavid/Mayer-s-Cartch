import os
from datetime import datetime
from tkinter import messagebox
import config

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    pass

def gerar_pdf_ordem_servico(num_os, nome_cliente, tipo_cliente, itens_os, valor_mao_obra, janela_pai):
    """Gera um PDF formatado para a Ordem de Serviço (OS)"""
    try:
        nome_arquivo = f"OS_{num_os.replace('/', '-')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
        messagebox.showinfo("Sucesso", f"PDF da Ordem de Serviço gerado com sucesso!\nSalvo como: {nome_arquivo}", parent=janela_pai)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível gerar o PDF da OS: {e}", parent=janela_pai)


def gerar_pdf_ordem_compra(num_oc, fornecedor, itens_oc, janela_pai):
    """Gera um PDF formatado para a Ordem de Compra (OC)"""
    try:
        nome_arquivo = f"OC_{num_oc.replace('/', '-')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
        messagebox.showinfo("Sucesso", f"PDF da Ordem de Compra gerado com sucesso!\nSalvo como: {nome_arquivo}", parent=janela_pai)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível gerar o PDF da OC: {e}", parent=janela_pai)