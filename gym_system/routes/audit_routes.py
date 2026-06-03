from flask import Blueprint, render_template
from database.models.audit import AuditLog
from utils.security import login_required, role_required

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
@role_required('admin')
def index():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template('audit/audit.html', logs=logs)
