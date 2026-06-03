from flask import Blueprint
from controllers.payments_controller import PaymentsController

payment_bp = Blueprint('payments', __name__, url_prefix='/payments')

payment_bp.add_url_rule('/', 'index', PaymentsController.index)
payment_bp.add_url_rule('/create', 'create', PaymentsController.create, methods=['GET', 'POST'])
payment_bp.add_url_rule('/<int:payment_id>/receipt', 'receipt', PaymentsController.receipt)
payment_bp.add_url_rule('/<int:payment_id>/delete', 'delete', PaymentsController.delete, methods=['POST'])
