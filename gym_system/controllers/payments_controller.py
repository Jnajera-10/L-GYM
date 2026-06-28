from datetime import datetime
import pytz
BOGOTA = pytz.timezone("America/Bogota")

from flask import request, redirect, url_for, flash, render_template
from database.models.payment import Payment, SHIFT_MORNING, SHIFT_AFTERNOON, _get_shift
from database.models.client import Client
from database.models.membership import Membership
from database.models.cash_register import CashRegister
from database.db import db
from services.payment_service import PaymentService
from services.audit_service import AuditService
import logging


def _fmt(value):
    """Formatea número con puntos como separador de miles (estilo colombiano)."""
    try:
        return f"{int(value):,}".replace(',', '.')
    except (ValueError, TypeError):
        return '0'


logger = logging.getLogger(__name__)
PER_PAGE = 30


class PaymentsController:

    @staticmethod
    def index():
        page   = request.args.get('page', 1, type=int)
        q           = request.args.get('q', '').strip()
        plan_filter = request.args.get('plan', '').strip()
        method      = request.args.get('method', '').strip()
        date_from   = request.args.get('date_from', '').strip()
        date_to     = request.args.get('date_to', '').strip()
        shift       = request.args.get('shift', '').strip()

        hoy_str = datetime.now(BOGOTA).strftime('%Y-%m-%d')

        no_filters = not any([q, plan_filter, method, date_from, date_to, shift])
        if no_filters:
            date_from = hoy_str

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
            query = query.filter(Payment.payment_method.ilike(f'%{method}%'))

        if shift:
            query = query.filter(
                Payment.shift.isnot(None),
                Payment.shift == shift
            )

        hoy_date = datetime.now(BOGOTA).date()

        if date_from:
            try:
                query = query.filter(Payment.payment_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
            except ValueError:
                query = query.filter(Payment.payment_date >= hoy_date)
        elif shift:
            query = query.filter(Payment.payment_date >= hoy_date)

        if date_to:
            try:
                query = query.filter(Payment.payment_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
            except ValueError:
                pass
        elif shift and not date_from:
            query = query.filter(Payment.payment_date <= hoy_date)

        pagination = query.order_by(Payment.payment_date.desc()).paginate(
            page=page, per_page=PER_PAGE, error_out=False
        )

        memberships = Membership.query.filter_by(is_active=True).order_by(Membership.name).all()
        today = datetime.now(BOGOTA).date()

        from database.models.membership import Membership as Memb
        daily_count_today = (
            Payment.query
            .join(Memb, Payment.membership_id == Memb.id)
            .filter(
                Payment.payment_date == today,
                Payment.is_deleted   == False,
                Memb.membership_type == 'diario',
            )
            .count()
        )

        return render_template(
            'payments/payments.html',
            payments          = pagination.items,
            pagination        = pagination,
            memberships       = memberships,
            today             = today,
            q                 = q,
            plan_filter       = plan_filter,
            shift             = shift,
            method            = method,
            date_from         = date_from or hoy_str,
            date_to           = date_to,
            daily_count_today = daily_count_today,
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

                if partner_payment:
                    AuditService.log('create', 'payments', partner_payment.id, None, 'Plan Pareja (espejo)')
                    _send_couple_email(partner_payment, payment.client)
                    flash('✅ Membresía activada también para el segundo cliente del Plan Pareja.', 'info')

                flash('Pago registrado correctamente.', 'success')
                return redirect(url_for('payments.receipt', payment_id=payment.id))
            else:
                flash('No se pudo registrar el pago.', 'danger')

        today_date = datetime.now(BOGOTA).date()
        daily_count_today = (
            Payment.query
            .join(Membership, Payment.membership_id == Membership.id)
            .filter(
                Payment.payment_date == today_date,
                Payment.is_deleted   == False,
                Membership.membership_type == 'diario',
            )
            .count()
        )

        from database.models.inventory import Product
        products = Product.query.filter_by(is_active=True).filter(Product.quantity > 0).order_by(Product.name).all()
        return render_template(
            'payments/create_payment.html',
            clients           = clients,
            memberships       = memberships,
            current_shift     = _get_shift(),
            today             = datetime.now(BOGOTA).strftime('%Y-%m-%d'),
            daily_count_today = daily_count_today,
            products          = products,
        )

    @staticmethod
    def renew():
        today = datetime.now(BOGOTA).date()

        if request.method == 'POST':
            payment, partner_payment, error = PaymentService.register_payment(request.form)
            if error:
                flash(error, 'danger')
                client_id     = request.form.get('client_id')
                membership_id = request.form.get('membership_id')
                return redirect(url_for(
                    'payments.renew',
                    client_id=client_id,
                    membership_id=membership_id,
                ))
            elif payment:
                AuditService.log(
                    'renew', 'payments', payment.id,
                    f'{payment.client.full_name} — {payment.membership.name}',
                    f'${_fmt(payment.amount)} | {payment.start_date} → {payment.end_date}'
                )
                _send_payment_email(payment)
                if partner_payment:
                    AuditService.log(
                        'renew', 'payments', partner_payment.id,
                        f'{partner_payment.client.full_name} — {partner_payment.membership.name}',
                        'Plan Pareja (espejo)'
                    )
                    _send_couple_email(partner_payment, payment.client)
                    flash('✅ Membresía activada también para el segundo cliente del Plan Pareja.', 'info')
                flash('Renovación registrada correctamente.', 'success')
                return redirect(url_for('payments.receipt', payment_id=payment.id))
            else:
                flash('No se pudo registrar la renovación.', 'danger')

        client_id     = request.args.get('client_id', type=int)
        membership_id = request.args.get('membership_id', type=int)

        client     = Client.query.get_or_404(client_id) if client_id else None
        membership = Membership.query.get(membership_id) if membership_id else None

        suggested_start = today
        if client and membership:
            last_payment = (
                Payment.query
                .filter(
                    Payment.client_id     == client.id,
                    Payment.membership_id == membership.id,
                    Payment.is_deleted    == False,
                )
                .order_by(Payment.end_date.desc())
                .first()
            )
            if last_payment and last_payment.end_date >= today:
                from datetime import timedelta
                suggested_start = last_payment.end_date + timedelta(days=1)

        clients     = Client.query.filter_by(is_active=True).order_by(Client.full_name).all()
        memberships = Membership.query.filter_by(is_active=True).order_by(Membership.name).all()

        return render_template(
            'payments/renew_payment.html',
            clients              = clients,
            memberships          = memberships,
            preselect_client     = client,
            preselect_membership = membership,
            suggested_start      = suggested_start,
            today                = today,
        )

    @staticmethod
    def receipt(payment_id):
        payment = Payment.query.get_or_404(payment_id)

        daily_count = None
        if payment.membership and payment.membership.membership_type == 'diario':
            daily_count = (
                Payment.query
                .join(Membership, Payment.membership_id == Membership.id)
                .filter(
                    Payment.payment_date == payment.payment_date,
                    Payment.is_deleted   == False,
                    Membership.membership_type == 'diario',
                )
                .count()
            )

        return render_template('payments/receipt.html', payment=payment, daily_count=daily_count)

    @staticmethod
    def delete(payment_id):
        payment = Payment.query.get_or_404(payment_id)
        client  = payment.client
        mirror  = PaymentService.soft_delete_payment(payment)
        db.session.commit()
        AuditService.log('delete', 'payments', payment.id, str(payment.amount), 'eliminado')
        if mirror:
            AuditService.log(
                'delete', 'payments', mirror.id,
                str(mirror.amount),
                f'eliminado (espejo Plan Pareja del pago #{payment.id})',
            )

        try:
            from services.notification_service import send_whatsapp_owner
            hora = datetime.now(BOGOTA).strftime('%H:%M')
            msg = (
                f"🗑️ *L-GYM - Pago Eliminado*\n"
                f"{'-'*28}\n"
                f"👤 *Cliente:* {client.full_name if client else '-'}\n"
                f"📋 *Plan:* {payment.membership.name if payment.membership else '-'}\n"
                f"💰 *Monto:* ${_fmt(payment.amount)} COP\n"
                f"💳 *Metodo:* {payment.payment_method or '-'}\n"
                f"📅 *Fecha pago:* {payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else '-'}\n"
                f"🔖 *Recibo N.:* {payment.id}\n"
                f"🕑 *Hora eliminacion:* {hora}\n"
                f"{'-'*28}\n"
                f"⚠️ Este pago fue eliminado del sistema."
                + (f"\n♻️ Tambien se elimino el espejo Plan Pareja #{mirror.id}." if mirror else "")
            )
            send_whatsapp_owner(msg)
        except Exception as exc:
            logger.error(f'[WHATSAPP] Error notificando eliminación: {exc}')

        if mirror:
            flash('Pago eliminado (incluyendo el registro espejo del Plan Pareja).', 'warning')
        else:
            flash('Pago eliminado.', 'warning')
        return redirect(url_for('payments.index'))

    @staticmethod
    def extend_days(payment_id):
        from datetime import timedelta
        payment = Payment.query.get_or_404(payment_id)
        try:
            days = int(request.form.get('days', 0))
        except (ValueError, TypeError):
            flash('Número de días inválido.', 'danger')
            return redirect(url_for('clients.detail', client_id=payment.client_id))

        if days == 0:
            flash('Ingresa un número de días distinto de cero.', 'warning')
            return redirect(url_for('clients.detail', client_id=payment.client_id))

        old_end = payment.end_date
        payment.end_date = payment.end_date + timedelta(days=days)
        db.session.commit()
        AuditService.log(
            'update', 'payments', payment.id,
            str(old_end),
            f'end_date → {payment.end_date} ({days:+d} días)',
        )
        accion = f'agregaron {days}' if days > 0 else f'quitaron {abs(days)}'
        flash(f'✅ Se {accion} días a {payment.client.full_name}. Nuevo vencimiento: {payment.end_date.strftime("%d/%m/%Y")}.', 'success')
        return redirect(url_for('clients.detail', client_id=payment.client_id))

    @staticmethod
    def mark_paid(payment_id):
        """Marca un pago pendiente como pagado."""
        payment = Payment.query.get_or_404(payment_id)
        changed = PaymentService.mark_as_paid(payment)
        if changed:
            AuditService.log('update', 'payments', payment.id, 'pendiente', 'pagado')
            try:
                from services.notification_service import send_whatsapp_owner
                hora = datetime.now(BOGOTA).strftime('%H:%M')
                msg = (
                    f"✅ *L-GYM - Pago Confirmado*\n"
                    f"{'-'*28}\n"
                    f"👤 *Cliente:* {payment.client.full_name if payment.client else '-'}\n"
                    f"📋 *Plan:* {payment.membership.name if payment.membership else '-'}\n"
                    f"💰 *Monto:* ${_fmt(payment.amount)} COP\n"
                    f"💳 *Metodo:* {payment.payment_method or '-'}\n"
                    f"📅 *Fecha:* {payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else '-'}\n"
                    f"🕑 *Hora:* {hora}\n"
                    f"🔖 *Recibo N.:* {payment.id}\n"
                    f"{'-'*28}\n"
                    f"💵 El cliente saldó su deuda pendiente."
                )
                send_whatsapp_owner(msg)
            except Exception as exc:
                logger.error(f'[WHATSAPP] Error notificando pago confirmado: {exc}')
            flash(f'✅ Pago #{payment.id} marcado como pagado.', 'success')
        else:
            flash('Este pago ya estaba marcado como pagado.', 'info')
        return redirect(url_for('payments.index'))


# ──────────────────────────────────────────────────────────────────────
# Helpers de email
# ──────────────────────────────────────────────────────────────────────
def _send_payment_email(payment):
    try:
        client = payment.client
        if not client:
            return

        try:
            from services.notification_service import send_whatsapp_owner
            from utils.helpers import parse_payment_split
            hora = datetime.now(BOGOTA).strftime('%H:%M')
            turno = payment.shift or '—'

            metodos = parse_payment_split(payment.payment_method, payment.amount)
            metodo_str = ' + '.join(
                f"{m.capitalize()} ${_fmt(v)}" if v is not None else m.capitalize()
                for m, v in metodos
            )

            is_pending = getattr(payment, 'payment_status', 'pagado') == 'pendiente'
            daily_qty = getattr(payment, 'daily_quantity', 1) or 1
            daily_str = f" ({daily_qty} personas)" if payment.membership and payment.membership.membership_type == 'diario' and daily_qty > 1 else ""

            # Líneas de productos si hay
            items_lines = ""
            if hasattr(payment, 'items') and payment.items:
                lines = [f"  • {i.product.name} x{i.quantity} = ${_fmt(i.subtotal)}" for i in payment.items if i.product]
                items_lines = "\n🛍️ *Productos:*\n" + "\n".join(lines) + "\n"

            if is_pending:
                msg = (
                    f"⏳ *L-GYM - PAGO PENDIENTE*\n"
                    f"{'-'*28}\n"
                    f"👤 *Cliente:* {client.full_name}\n"
                    f"📋 *Plan:* {payment.membership.name}{daily_str}\n"
                    f"{items_lines}"
                    f"💰 *TOTAL:* ${_fmt(payment.amount)} COP\n"
                    f"📅 *Fecha pago:* {payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else '-'}\n"
                    f"✅ *Valido desde:* {payment.start_date.strftime('%d/%m/%Y')}\n"
                    f"⏳ *Vence:* {payment.end_date.strftime('%d/%m/%Y')}\n"
                    f"🕐 *Turno:* {turno}\n"
                    f"🕑 *Hora:* {hora}\n"
                    f"🔖 *Recibo N.:* {payment.id}\n"
                    f"{'-'*28}\n"
                    f"⚠️ *ESTE CLIENTE AÚN NO HA PAGADO — ESTÁ EN DEUDA.*\n"
                    f"📝 *Obs:* {payment.notes or 'Sin observaciones'}"
                )
            else:
                msg = (
                    f"💪 *L-GYM - Nuevo Pago*\n"
                    f"{'-'*28}\n"
                    f"👤 *Cliente:* {client.full_name}\n"
                    f"📋 *Plan:* {payment.membership.name}{daily_str}\n"
                    f"💳 *Metodo:* {metodo_str}\n"
                    f"{items_lines}"
                    f"💰 *TOTAL:* ${_fmt(payment.amount)} COP\n"
                    f"📅 *Fecha pago:* {payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else '-'}\n"
                    f"✅ *Valido desde:* {payment.start_date.strftime('%d/%m/%Y')}\n"
                    f"⏳ *Vence:* {payment.end_date.strftime('%d/%m/%Y')}\n"
                    f"🕐 *Turno:* {turno}\n"
                    f"🕑 *Hora:* {hora}\n"
                    f"🔖 *Recibo N.:* {payment.id}\n"
                    f"{'-'*28}\n"
                    f"📝 *Obs:* {payment.notes or 'Sin observaciones'}"
                )
            send_whatsapp_owner(msg)
        except Exception as exc:
            logger.error(f'[WHATSAPP] Error notificando al dueño: {exc}')

        if not client.email:
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
        flash('⚠️ Pago registrado, pero error al enviar email.', 'warning')


def _send_couple_email(partner_payment, main_client):
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
