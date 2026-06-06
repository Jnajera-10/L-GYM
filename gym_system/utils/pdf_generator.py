from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

DARK   = colors.HexColor('#1a1a2e')
ACCENT = colors.HexColor('#e94560')
RED    = colors.HexColor('#FFCCCC')
YELLOW = colors.HexColor('#FFF3CD')


def _fmt_date(value, fmt='%d/%m/%Y'):
    if value is None:
        return 'N/A'
    try:
        if hasattr(value, 'strftime'):
            return value.strftime(fmt)
        return str(value)[:10]
    except Exception:
        return str(value)


def _fmt_money(value):
    try:
        return f'${float(value):,.0f}'
    except (TypeError, ValueError):
        return 'N/A'


def generate_receipt_pdf(payment):
    buf  = BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=letter)
    styles   = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph('Body-Fit', ParagraphStyle('title', fontSize=20, textColor=DARK, spaceAfter=4)))
    elements.append(Paragraph('RECIBO DE PAGO', styles['Title']))
    elements.append(Spacer(1, 12))
    data = [
        ['Cliente:',      payment.client.full_name    if payment.client     else 'N/A'],
        ['Membresía:',    payment.membership.name     if payment.membership else 'N/A'],
        ['Monto:',        _fmt_money(payment.amount)],
        ['Fecha de pago:',_fmt_date(payment.payment_date)],
        ['Vencimiento:',  _fmt_date(payment.end_date)],
        ['Método:',       payment.payment_method or 'N/A'],
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


def generate_report_pdf(tipo, data, start=None, end=None, today=None):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.5*inch, rightMargin=0.5*inch,
        topMargin=0.5*inch,  bottomMargin=0.5*inch,
    )
    styles   = getSampleStyleSheet()
    elements = []

    # ── Encabezado ───────────────────────────────────────────────
    titulo_map = {
        'clientes':   'Clientes Activos',
        'pagos':      'Ingresos / Pagos',
        'ventas':     'Ventas de Productos',
        'vencidos':   'Membresías Vencidas',
        'por_vencer': 'Membresías por Vencer (≤3 días)',
    }
    titulo = titulo_map.get(tipo, tipo.capitalize())
    elements.append(Paragraph('Body-Fit', ParagraphStyle('brand', fontSize=18, textColor=DARK, spaceAfter=2)))
    now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f'Reporte: {titulo} — {now_str}', styles['Normal']))

    if start and end:
        elements.append(Paragraph(
            f'Período: {_fmt_date(start)} al {_fmt_date(end)}',
            styles['Normal']
        ))

    elements.append(Spacer(1, 14))

    # ── Tabla según tipo ─────────────────────────────────────────
    row_colors = []  # para colorear filas de vencidos

    if tipo == 'clientes':
        table_data = [['Nombre', 'Documento', 'Email', 'Teléfono', 'Inscripción']]
        for c in data:
            table_data.append([
                c.full_name      or '',
                c.document_number or '',
                c.email          or '',
                c.phone          or '',
                _fmt_date(c.enrollment_date),
            ])
        col_widths = [170, 90, 130, 85, 70]

    elif tipo == 'pagos':
        table_data = [['Cliente', 'Plan', 'Monto', 'Fecha Pago', 'Método']]
        total = 0
        for p in data:
            table_data.append([
                p.client.full_name    if p.client     else 'N/A',
                p.membership.name     if p.membership else 'N/A',
                _fmt_money(p.amount),
                _fmt_date(p.payment_date),
                p.payment_method      or '',
            ])
            total += p.amount or 0
        table_data.append(['', '', _fmt_money(total), 'TOTAL', ''])
        col_widths = [160, 110, 75, 80, 75]

    elif tipo == 'ventas':
        table_data = [['Cliente', 'Total', 'Método', 'Fecha']]
        for s in data:
            table_data.append([
                s.client.full_name if s.client else 'General',
                _fmt_money(s.total),
                s.payment_method or '',
                _fmt_date(s.sale_date, '%d/%m/%Y %H:%M'),
            ])
        col_widths = [200, 80, 90, 130]

    elif tipo in ('vencidos', 'por_vencer'):
        table_data = [['Cliente', 'Teléfono', 'Email', 'Plan', 'Venció / Vence', 'Días']]
        ref = today or datetime.now().date()
        for p in data:
            dias = (p.end_date - ref).days
            table_data.append([
                p.client.full_name if p.client else 'N/A',
                p.client.phone     if p.client else '',
                p.client.email     if p.client else '',
                p.membership.name  if p.membership else 'N/A',
                _fmt_date(p.end_date),
                str(dias),
            ])
            row_colors.append(RED if dias < 0 else YELLOW)
        col_widths = [130, 75, 120, 90, 75, 40]

    else:
        table_data = [['Sin datos']]
        col_widths = [500]

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Estilo base
    style_cmds = [
        ('BACKGROUND',  (0, 0),  (-1, 0),  DARK),
        ('TEXTCOLOR',   (0, 0),  (-1, 0),  colors.white),
        ('FONTNAME',    (0, 0),  (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0),  (-1, -1), 8),
        ('GRID',        (0, 0),  (-1, -1), 0.3, colors.lightgrey),
        ('PADDING',     (0, 0),  (-1, -1), 5),
        ('ALIGN',       (0, 0),  (-1, -1), 'LEFT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]

    # Colorear filas individuales para vencidos
    for i, fill in enumerate(row_colors, start=1):
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), fill))

    table.setStyle(TableStyle(style_cmds))
    elements.append(table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f'Total de registros: {len(data)}', styles['Normal']))

    doc.build(elements)
    buf.seek(0)
    return buf
