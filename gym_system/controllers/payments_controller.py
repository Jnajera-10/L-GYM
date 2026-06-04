from flask import request, redirect, url_for, flash, render_template
from database.models.payment import Payment
from database.models.client import Client
from database.models.membership import Membership
from database.db import db
from services.payment_service import PaymentService
from services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)
PER_PAGE = 30


class PaymentsController:

    @staticmethod
    def index():
        page = request.args.get('page', 1, type=int)
        pagination = (
            Payment.query
            .filter_by(is_deleted=False)
            .order_by(Payment.payment_date.desc())
            .paginate(page=page, per_page=PER_PAGE, error_out=False)
        )
        return render_template(
            'payments/payments.html',
            payments=pagination.items,
            pagination=pagination,
        )

    @staticmethod
    def create():
        clients = Client.query.filter_by(is_active=True).order_by(Client.full_name).all()
        memberships = Membership.query.filter_by(is_active=True).order_by(Membership.name).all()

        if request.method == 'POST':
            payment, error = PaymentService.register_payment(request.form)
            if error:
                flash(error, 'danger')
            elif payment:
                AuditService.log('create', 'payments', payment.id, None, str(payment.amount))
                _send_payment_email(payment)
                flash('Pago registrado correctamente.', 'success')
                return redirect(url_for('payments.receipt', payment_id=payment.id))
            else:
                flash('No se pudo registrar el pago.', 'danger')

        return render_template(
            'payments/create_payment.html',
            clients=clients,
            memberships=memberships,
        )

    @staticmethod
    def receipt(payment_id):
        payment = Payment.query.get_or_404(payment_id)
        return render_template('payments/receipt.html', payment=payment)

    @staticmethod
    def delete(payment_id):
        payment = Payment.query.get_or_404(payment_id)
        payment.is_deleted = True
        db.session.commit()
        AuditService.log('delete', 'payments', payment.id, str(payment.amount), 'eliminado')
        flash('Pago eliminado.', 'warning')
        return redirect(url_for('payments.index'))


def _send_payment_email(payment):
    """
    Envía el email de confirmación de pago.
    Separado para que cualquier error no bloquee el registro del pago.
    """
    try:
        client = payment.client
        membership = payment.membership

        if not client:
            flash('⚠️ Pago registrado, pero el cliente no se encontró para enviar el email.', 'warning')
            logger.error(f'[EMAIL] payment_id={payment.id} — client es None')
            return

        if not client.email:
            logger.info(f'[EMAIL] Cliente {client.full_name} no tiene email registrado, no se envía confirmación.')
            return

        if not membership:
            flash('⚠️ Pago registrado, pero la membresía no se encontró para enviar el email.', 'warning')
            logger.error(f'[EMAIL] payment_id={payment.id} — membership es None')
            return

        import os
        if not os.environ.get('BREVO_API_KEY'):
            flash('⚠️ Pago registrado. Email no enviado: falta BREVO_API_KEY en las variables de entorno de Render.', 'warning')
            logger.warning('[EMAIL] BREVO_API_KEY no definida')
            return

        if not os.environ.get('MAIL_FROM'):
            flash('⚠️ Pago registrado. Email no enviado: falta MAIL_FROM en las variables de entorno de Render.', 'warning')
            logger.warning('[EMAIL] MAIL_FROM no definida')
            return

        from services.notification_service import NotificationService
        ok = NotificationService.send_payment_confirmation(payment)

        if not ok:
            flash('⚠️ Pago registrado, pero el email de confirmación falló. '
                  'Revisa el módulo de Notificaciones para ver el error.', 'warning')
        else:
            flash(f'📧 Confirmación enviada a {client.email}', 'info')

    except Exception as exc:
        logger.error(f'[EMAIL] Error inesperado enviando email pago {payment.id}: {exc}', exc_info=True)
        flash(f'⚠️ Pago registrado, pero error al enviar email: {str(exc)[:120]}', 'warning')