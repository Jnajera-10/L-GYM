from flask import Blueprint, render_template, session, redirect, url_for, send_file, request
from services.report_service import ReportService
from services.export_service import ExportService
from utils.pdf_generator import generate_report_pdf
from database.models.payment import Payment
from database.models.sales import Sale
from database.models.attendance import Attendance
from database.models.client import Client

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    clients = ReportService.clients_report()
    return render_template('reports/reports.html', clients=clients)

@reports_bp.route('/excel/clients')
def excel_clients():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    clients = Client.query.filter_by(is_active=True).all()
    buf = ExportService.export_clients_excel(clients)
    return send_file(buf, as_attachment=True, download_name='clientes.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@reports_bp.route('/excel/payments')
def excel_payments():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    payments = Payment.query.filter_by(is_deleted=False).all()
    buf = ExportService.export_payments_excel(payments)
    return send_file(buf, as_attachment=True, download_name='pagos.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@reports_bp.route('/excel/sales')
def excel_sales():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    sales = Sale.query.filter_by(is_deleted=False).all()
    buf = ExportService.export_sales_excel(sales)
    return send_file(buf, as_attachment=True, download_name='ventas.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@reports_bp.route('/pdf/clients')
def pdf_clients():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    clients = Client.query.filter_by(is_active=True).all()
    buf = generate_report_pdf('clientes', clients)
    return send_file(buf, as_attachment=True, download_name='clientes.pdf', mimetype='application/pdf')

@reports_bp.route('/pdf/payments')
def pdf_payments():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    payments = Payment.query.filter_by(is_deleted=False).all()
    buf = generate_report_pdf('pagos', payments)
    return send_file(buf, as_attachment=True, download_name='pagos.pdf', mimetype='application/pdf')

@reports_bp.route('/pdf/sales')
def pdf_sales():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    sales = Sale.query.filter_by(is_deleted=False).all()
    buf = generate_report_pdf('ventas', sales)
    return send_file(buf, as_attachment=True, download_name='ventas.pdf', mimetype='application/pdf')
