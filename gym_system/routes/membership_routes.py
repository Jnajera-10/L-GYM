from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models.membership import Membership
from database.db import db
from utils.security import login_required, role_required

membership_bp = Blueprint('membership', __name__, url_prefix='/membership')


@membership_bp.route('/')
@login_required
def index():
    # Solo membresías activas
    memberships = Membership.query.filter_by(is_active=True).order_by(Membership.name).all()
    return render_template('memberships/memberships.html', memberships=memberships)


@membership_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    if request.method == 'POST':
        m = Membership(
            name=request.form['name'],
            duration_days=int(request.form['duration_days']),
            price=float(request.form['price']),
        )
        db.session.add(m)
        db.session.commit()
        flash('Membresía creada.', 'success')
        return redirect(url_for('membership.index'))
    return render_template('memberships/create_membership.html')


@membership_bp.route('/<int:mid>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(mid):
    m = Membership.query.get_or_404(mid)
    if request.method == 'POST':
        m.name = request.form['name']
        m.duration_days = int(request.form['duration_days'])
        m.price = float(request.form['price'])
        db.session.commit()
        flash('Membresía actualizada.', 'success')
        return redirect(url_for('membership.index'))
    return render_template('memberships/create_membership.html', membership=m)


@membership_bp.route('/<int:mid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete(mid):
    m = Membership.query.get_or_404(mid)
    m.is_active = False
    db.session.commit()
    flash('Membresía desactivada.', 'warning')
    return redirect(url_for('membership.index'))
