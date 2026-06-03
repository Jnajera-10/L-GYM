from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.models.inventory import Product, StockMovement
from database.db import db
from services.inventory_service import InventoryService

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    products = Product.query.filter_by(is_active=True).all()
    low_stock = InventoryService.low_stock()
    return render_template('inventory/products.html', products=products, low_stock=low_stock)

@inventory_bp.route('/create', methods=['GET', 'POST'])
def create():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        p = Product(
            name=request.form['name'],
            category=request.form.get('category'),
            brand=request.form.get('brand'),
            quantity=int(request.form.get('quantity', 0)),
            purchase_price=float(request.form['purchase_price']),
            sale_price=float(request.form['sale_price']),
            min_stock=int(request.form.get('min_stock', 5))
        )
        db.session.add(p)
        db.session.commit()
        flash('Producto creado.', 'success')
        return redirect(url_for('inventory.index'))
    return render_template('inventory/products.html', products=Product.query.filter_by(is_active=True).all())

@inventory_bp.route('/<int:pid>/add-stock', methods=['POST'])
def add_stock(pid):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    qty = int(request.form.get('quantity', 0))
    InventoryService.add_stock(pid, qty)
    flash('Stock agregado.', 'success')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/<int:pid>/edit', methods=['POST'])
def edit(pid):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    p = Product.query.get_or_404(pid)
    p.name = request.form['name']
    p.category = request.form.get('category')
    p.brand = request.form.get('brand')
    p.purchase_price = float(request.form['purchase_price'])
    p.sale_price = float(request.form['sale_price'])
    p.min_stock = int(request.form.get('min_stock', 5))
    p.quantity = int(request.form.get('quantity', p.quantity))
    db.session.commit()
    flash('Producto actualizado.', 'success')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/<int:pid>/delete', methods=['POST'])
def delete(pid):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    p = Product.query.get_or_404(pid)
    p.is_active = False
    db.session.commit()
    flash('Producto eliminado.', 'warning')
    return redirect(url_for('inventory.index'))
