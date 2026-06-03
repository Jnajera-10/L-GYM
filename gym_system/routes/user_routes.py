from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models.user import User
from database.db import db
from utils.security import hash_password, login_required, role_required

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/')
@login_required
@role_required('admin')
def index():
    users = User.query.all()
    return render_template('users/users.html', users=users)

@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            password_hash=hash_password(request.form['password']),
            full_name=request.form['full_name'],
            role=request.form['role']
        )
        db.session.add(user)
        db.session.commit()
        flash('Usuario creado.', 'success')
        return redirect(url_for('user.index'))
    return render_template('users/create_user.html')

@user_bp.route('/<int:user_id>/deactivate', methods=['POST'])
@login_required
@role_required('admin')
def deactivate(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    flash('Usuario desactivado.', 'warning')
    return redirect(url_for('user.index'))
