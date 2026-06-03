from flask import request, redirect, url_for, flash, render_template
from database.models.payment import Payment
from database.models.client import Client
from database.models.membership import Membership
from database.db import db
from services.payment_service import PaymentService
from services.audit_service import AuditService

class PaymentsController:
    @staticmethod
    def index():
        payments = Payment.query.filter_by(is_deleted=False).order_by(Payment.payment_date.desc()).all()
        return render_template('payments/payments.html', payments=payments)

    @staticmethod
    def create():
        clients = Client.query.filter_by(is_active=True).all()
        memberships = Membership.query.filter_by(is_active=True).all()
        if request.method == 'POST':
            payment = PaymentService.register_payment(request.form)
            if payment:
                AuditService.log('create', 'payments', payment.id, None, str(payment.amount))
                flash('Pago registrado correctamente.', 'success')
                return redirect(url_for('payments.receipt', payment_id=payment.id))
        return render_template('payments/create_payment.html', clients=clients, memberships=memberships)

    @staticmethod
    def receipt(payment_id):
        payment = Payment.query.get_or_404(payment_id)
        return render_template('payments/receipt.html', payment=payment)

    @staticmethod
    def delete(payment_id):
        payment = Payment.query.get_or_404(payment_id)
        payment.is_deleted = True
        db.session.commit()
        flash('Pago eliminado.', 'warning')
        return redirect(url_for('payments.index'))
