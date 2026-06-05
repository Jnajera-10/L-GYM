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
        page   = request.args.get('page', 1, type=int)
        # ── Filtros ──────────────────────────────────────────────
        q           = request.args.get('q', '').strip()          # búsqueda por nombre/doc
        plan_filter = request.args.get('plan', '').strip()       # membresía id
        method      = request.args.get('method', '').strip()     # método de pago
        date_from   = request.args.get('date_from', '').strip()
        date_to     = request.args.get('date_to', '').strip()

        query = Payment.query.filter_by(is_deleted=False)

        if q:
            query = (
                query
                .join(Client, Payment.client_id == Client.id)
                .filter(
                    db.or_(
                        Client.full_name.ilike(f'%{q}%'),
                        Client.document_number.ilike(f'%{q}%'),
                    )
                )
            )

        if plan_filter:
            try:
                query = query.filter(Payment.membership_id == int(plan_filter))
            except ValueError:
                pass

        if method:
            query = query.filter(Payment.payment_method == method)

        if date_from:
            try:
                from datetime import datetime
                query = query.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
            except ValueError:
                pass

        if date_to:
            try:
                from datetime import datetime
                query = query.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
            except ValueError:
                pass

        pagination = query.order_by(Payment.payment_date.desc()).paginate(
            page=page, per_page=PER_PAGE, error_out=False
        )

        memberships = Membership.query.filter_by(is_active=True).order_by(Membership.name).all()

        return render_template(
            'payments/payments.html',
            payments    = pagination.items,
            pagination  = pagination,
            memberships = memberships,
            # devolver filtros al template para mantenerlos en el form
            q           = q,
            plan_filter = plan_filter,
            method      = method,
            date_from   = date_from,
            date_to     = date_to,
        )

    @staticmethod
    def create():
        clients     = Client.query.filter_by(is_active=True).order_by(Client.full_name).all()
        memberships = Membership.query.filter_by(is_active=True).order_by(Membership.name).all()

        if request.method == 'POST':
            payment, partner_payment, error = PaymentService.register_payment(request.form)
            if error:
                flash(error, 'danger')
            elif payment:
                AuditService.log('create', 'payments', payment.id, None, str(payment.amount))
                _send_payment_email(payment)

                # Plan Pareja: notificar también al segundo cliente
                if partner_payment:
                    AuditService.log('create', 'payments', partner_payment.id, None, 'Plan Pareja (espejo)')
                    _send_couple_email(partner_payment, payment.client)
                    flash(f'✅ Membresía activada también para el segundo cliente del Plan Pareja.', 'info')

                flash('Pago registrado correctamente.', 'success')
                return redirect(url_for('payments.receipt', payment_id=payment.id))
            else:
                flash('No se pudo registrar el pago.', 'danger')

        return render_template(
            'payments/create_payment.html',
            clients     = clients,
            memberships = memberships,
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


# ──────────────────────────────────────────────────────────────────────
# Helpers de email
# ──────────────────────────────────────────────────────────────────────
def _send_payment_email(payment):
    try:
        client = payment.client
        if not client or not client.email:
            return
        import os
        if not os.environ.get('BREVO_API_KEY') or not os.environ.get('MAIL_FROM'):
            flash('⚠️ Pago registrado. Email no enviado: revisa BREVO_API_KEY y MAIL_FROM en Render.', 'warning')
            return
        from services.notification_service import NotificationService
        ok = NotificationService.send_payment_confirmation(payment)
        if ok:
            flash(f'📧 Confirmación enviada a {client.email}', 'info')
        else:
            flash('⚠️ Pago registrado, pero el email de confirmación falló.', 'warning')
    except Exception as exc:
        logger.error(f'[EMAIL] Error pago {payment.id}: {exc}', exc_info=True)
        flash(f'⚠️ Pago registrado, pero error al enviar email.', 'warning')


def _send_couple_email(partner_payment, main_client):
    """Notifica al segundo cliente del Plan Pareja."""
    try:
        partner = partner_payment.client
        if not partner or not partner.email:
            return
        import os
        if not os.environ.get('BREVO_API_KEY') or not os.environ.get('MAIL_FROM'):
            return
        from services.notification_service import NotificationService
        NotificationService.send_couple_plan_notification(partner_payment, main_client)
    except Exception as exc:
        logger.error(f'[EMAIL] Error Plan Pareja notificación: {exc}', exc_info=True)
