from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

def generate_receipt_pdf(payment):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph('RECIBO DE PAGO', styles['Title']))
    data = [
        ['Cliente:', payment.client.full_name],
        ['Membresía:', payment.membership.name],
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
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf
