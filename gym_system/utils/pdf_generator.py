from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

DARK = colors.HexColor('#1a1a2e')
ACCENT = colors.HexColor('#e94560')

def generate_receipt_pdf(payment):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph('Body-Fit', ParagraphStyle('title', fontSize=20, textColor=DARK, spaceAfter=4)))
    elements.append(Paragraph('RECIBO DE PAGO', styles['Title']))
    elements.append(Spacer(1, 12))
    data = [
        ['Cliente:', payment.client.full_name if payment.client else 'N/A'],
        ['Membresía:', payment.membership.name if payment.membership else 'N/A'],
        ['Monto:', f'${payment.amount:,.0f}'],
        ['Fecha de pago:', str(payment.payment_date)],
        ['Vencimiento:', str(payment.end_date)],
        ['Método:', payment.payment_method],
    ]
    table = Table(data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf

def generate_report_pdf(tipo, data):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.5*inch, rightMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph('Body-Fit', ParagraphStyle('brand', fontSize=18, textColor=DARK, spaceAfter=2)))
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f'Reporte de {tipo.capitalize()} — Generado: {now}', styles['Normal']))
    elements.append(Spacer(1, 16))

    if tipo == 'clientes':
        table_data = [['ID', 'Nombre', 'Documento', 'Email', 'Celular', 'Estado']]
        for c in data:
            table_data.append([c.id, c.full_name, c.document_number or '', c.email or '', c.phone or '',
                                'Activo' if c.is_active else 'Inactivo'])
        col_widths = [35, 150, 90, 130, 85, 55]

    elif tipo == 'pagos':
        table_data = [['ID', 'Cliente', 'Membresía', 'Monto', 'Fecha', 'Método']]
        for p in data:
            table_data.append([p.id,
                                p.client.full_name if p.client else 'N/A',
                                p.membership.name if p.membership else 'N/A',
                                f'${p.amount:,.0f}',
                                str(p.payment_date)[:10],
                                p.payment_method])
        col_widths = [35, 140, 100, 70, 80, 70]

    elif tipo == 'ventas':
        table_data = [['ID', 'Cliente', 'Total', 'Método', 'Fecha', 'Productos']]
        for s in data:
            table_data.append([s.id,
                                s.client.full_name if s.client else 'General',
                                f'${s.total:,.0f}',
                                s.payment_method,
                                s.sale_date.strftime('%d/%m/%Y'),
                                len(s.items)])
        col_widths = [35, 150, 80, 80, 90, 60]
    else:
        table_data = [['Sin datos']]
        col_widths = [500]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f'Total de registros: {len(data)}', styles['Normal']))
    doc.build(elements)
    buf.seek(0)
    return buf
