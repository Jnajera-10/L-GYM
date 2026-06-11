from database.models.payment import Payment
from database.db import db
import pytz
from datetime import datetime, timedelta

BOGOTA = pytz.timezone('America/Bogota')
EXPIRY_WARN_DAYS = 3

class MembershipService:
    @staticmethod
    def count_active():
        from database.models.membership import Membership
        today = datetime.now(BOGOTA).date()
        # Cuenta clientes únicos con membresía vigente, excluyendo plan diario
        return db.session.query(Payment.client_id).join(
            Membership, Payment.membership_id == Membership.id
        ).filter(
            Payment.end_date >= today,
            Payment.is_deleted == False,
            Membership.membership_type != 'diario',
        ).distinct().count()

    @staticmethod
    def count_expiring_soon():
        today = datetime.now(BOGOTA).date()
        soon = today + timedelta(days=EXPIRY_WARN_DAYS)
        return Payment.query.filter(
            Payment.end_date >= today,
            Payment.end_date <= soon,
            Payment.is_deleted == False
        ).count()

    @staticmethod
    def count_expired():
        today = datetime.now(BOGOTA).date()
        return Payment.query.filter(
            Payment.end_date < today,
            Payment.is_deleted == False
        ).count()

    @staticmethod
    def get_active_memberships():
        today = datetime.now(BOGOTA).date()
        return Payment.query.filter(
            Payment.end_date >= today,
            Payment.is_deleted == False
        ).all()
