from flask import Blueprint, render_template, redirect, url_for, flash
from services.backup_service import BackupService
from utils.security import login_required, role_required

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')

@backup_bp.route('/')
@login_required
@role_required('admin')
def index():
    try:
        backups = BackupService.list_backups()
    except Exception:
        backups = []
    return render_template('backups/backups.html', backups=backups)

@backup_bp.route('/create', methods=['POST'])
@login_required
@role_required('admin')
def create():
    try:
        BackupService.create_backup()
        flash('Respaldo creado.', 'success')
    except Exception as e:
        flash(f'Error al crear respaldo: {e}', 'danger')
    return redirect(url_for('backup.index'))
