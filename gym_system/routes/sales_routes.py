from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models.sales import Sale
from database.models.inventory import Product
from database.models.client import Client
from database.db import db
from services.sales_service import SalesService
from utils.security import login_required

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')
PER_PAGE = 30


@sales_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    pagination = (
        Sale.query
        .filter_by(is_deleted=False)
        .order_by(Sale.sale_date.desc())
        .paginate(page=page, per_page=PER_PAGE, error_out=False)
    )
    return render_template('sales/sales.html', sales=pagination.items, pagination=pagination)


@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    products = Product.query.filter_by(is_active=True).all()
    clients = Client.query.filter_by(is_active=True).order_by(Client.full_name).all()
    if request.method == 'POST':
        client_id = request.form.get('client_id') or None
        payment_method = request.form.get('payment_method', 'efectivo')
        product_ids = request.form.getlist('product_id')
        quantities = request.form.getlist('quantity')
        items = [
            {'product_id': int(pid), 'quantity': int(qty)}
            for pid, qty in zip(product_ids, quantities)
            if int(qty) > 0
        ]
        if not items:
            flash('Agrega al menos un producto.', 'danger')
        else:
            try:
                SalesService.create_sale(client_id, items, payment_method)
                flash('Venta registrada.', 'success')
                return redirect(url_for('sales.index'))
            except ValueError as e:
                flash(str(e), 'danger')
    return render_template('sales/new_sale.html', products=products, clients=clients)


@sales_bp.route('/<int:sid>/delete', methods=['POST'])
@login_required
def delete(sid):
    sale = Sale.query.get_or_404(sid)
    sale.is_deleted = True
    db.session.commit()
    flash('Venta eliminada.', 'warning')
    return redirect(url_for('sales.index'))


@sales_bp.route('/<int:sid>/invoice')
@login_required
def invoice(sid):
    from database.models.sales import Sale
    sale = Sale.query.get_or_404(sid)
    return render_template('sales/invoice.html', sale=sale)
