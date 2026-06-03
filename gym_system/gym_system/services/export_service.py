import openpyxl
from io import BytesIO

class ExportService:
    @staticmethod
    def export_clients_excel(clients):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Clientes'
        headers = ['ID', 'Nombre', 'Documento', 'Email', 'Celular', 'Estado']
        ws.append(headers)
        for c in clients:
            ws.append([c.id, c.full_name, c.document_number, c.email, c.phone, 'Activo' if c.is_active else 'Inactivo'])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    @staticmethod
    def export_payments_excel(payments):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Pagos'
        ws.append(['ID', 'Cliente', 'Membresía', 'Monto', 'Fecha Pago', 'Vencimiento', 'Método'])
        for p in payments:
            ws.append([p.id, p.client.full_name, p.membership.name, p.amount, str(p.payment_date), str(p.end_date), p.payment_method])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf
