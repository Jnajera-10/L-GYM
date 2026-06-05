from flask import render_template
from database.models.client import Client
from database.models.attendance import Attendance
from database.models.inventory import Product
from database.models.payment import Payment
from services.membership_service import MembershipService
from services.payment_service import PaymentService
import pytz
from datetime import datetime, timedelta

BOGOTA = pytz.timezone('America/Bogota')


class DashboardController:
    @staticmethod
    def index():
        now   = datetime.now(BOGOTA)
        today = now.date()

        # Inicio del día con timezone explícita — evita TypeError al comparar
        start_of_day = BOGOTA.localize(datetime(today.year, today.month, today.day, 0, 0, 0))

        # ── Estadísticas generales ────────────────────────────────────
        stats = {
            'total_clients':      Client.query.filter_by(is_active=True).count(),
            'active_memberships': MembershipService.count_active(),
            'expiring_soon':      MembershipService.count_expiring_soon(),
            'expired':            MembershipService.count_expired(),
            'today_income':       PaymentService.today_income(),
            'month_income':       PaymentService.month_income(),
            'today_attendance':   Attendance.query.filter(
                                      Attendance.check_in >= start_of_day
                                  ).count(),
            'low_stock':          Product.query.filter(
                                      Product.quantity <= Product.min_stock,
                                      Product.is_active == True,
                                  ).count(),
        }

        # ── Alertas accionables: próximas a vencer (≤3 días) ─────────
        warn_limit = today + timedelta(days=3)
        expiring_payments = (
            Payment.query
            .filter(
                Payment.end_date >= today,
                Payment.end_date <= warn_limit,
                Payment.is_deleted == False,
            )
            .order_by(Payment.end_date.asc())
            .all()
        )

        # ── Alertas accionables: ya vencidas (ayer y anteriores) ─────
        expired_payments = (
            Payment.query
            .filter(
                Payment.end_date < today,
                Payment.is_deleted == False,
            )
            .order_by(Payment.end_date.desc())
            .limit(10)          # máximo 10 para no saturar el dashboard
            .all()
        )

        # ── Caja del día: desglose por método de pago ─────────────────
        today_payments = Payment.query.filter(
            Payment.payment_date == today,
            Payment.is_deleted   == False,
        ).all()

        cash_breakdown = {}
        for p in today_payments:
            method = p.payment_method or 'otro'
            cash_breakdown[method] = cash_breakdown.get(method, 0) + p.amount

        # También calcular ingresos del mes por método
        month_payments = PaymentService.month_payments_raw()
        month_breakdown = {}
        for p in month_payments:
            method = p.payment_method or 'otro'
            month_breakdown[method] = month_breakdown.get(method, 0) + p.amount

        return render_template(
            'dashboard/dashboard.html',
            stats            = stats,
            today            = today,
            expiring_payments= expiring_payments,
            expired_payments = expired_payments,
            cash_breakdown   = cash_breakdown,
            month_breakdown  = month_breakdown,
        )
