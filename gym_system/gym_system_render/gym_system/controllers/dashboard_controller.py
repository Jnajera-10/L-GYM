from flask import render_template
from database.models.client import Client
from database.models.attendance import Attendance
from database.models.inventory import Product
from database.models.payment import Payment
from database.models.sales import Sale
from services.membership_service import MembershipService
from services.payment_service import PaymentService
import pytz
from datetime import datetime, date

BOGOTA = pytz.timezone('America/Bogota')

class DashboardController:
    @staticmethod
    def index():
        today = datetime.now(BOGOTA).date()
        try:
            total_clients = Client.query.filter_by(is_active=True).count()
        except:
            total_clients = 0
        try:
            active_memberships = MembershipService.count_active()
        except:
            active_memberships = 0
        try:
            expiring_soon = MembershipService.count_expiring_soon()
        except:
            expiring_soon = 0
        try:
            expired = MembershipService.count_expired()
        except:
            expired = 0
        try:
            today_income = PaymentService.today_income()
        except:
            today_income = 0
        try:
            month_income = PaymentService.month_income()
        except:
            month_income = 0
        try:
            today_attendance = Attendance.query.filter(
                Attendance.check_in >= datetime(today.year, today.month, today.day)
            ).count()
        except:
            today_attendance = 0
        try:
            low_stock = Product.query.filter(Product.quantity <= Product.min_stock, Product.is_active == True).count()
        except:
            low_stock = 0

        stats = {
            'total_clients': total_clients,
            'active_memberships': active_memberships,
            'expiring_soon': expiring_soon,
            'expired': expired,
            'today_income': today_income,
            'month_income': month_income,
            'today_attendance': today_attendance,
            'low_stock': low_stock,
        }
        return render_template('dashboard/dashboard.html', stats=stats, today=today)
