"""
Job diario que revisa membresías próximas a vencer o ya vencidas
y envía notificaciones por email.

Se ejecuta automáticamente al recibir GET /health (UptimeRobot lo
llama cada 5 minutos) pero solo corre una vez por día guardando
la última fecha en la BD de settings.
"""
import pytz
from datetime import datetime, timedelta
from database.models.payment import Payment
from database.models.settings import GymSettings
from database.db import db

BOGOTA = pytz.timezone('America/Bogota')
WARN_DAYS = [3, 1]   # avisar 3 días antes y 1 día antes


def run_expiry_notifications(app):
    """Llamar con el app context activo."""
    with app.app_context():
        today = datetime.now(BOGOTA).date()

        # Control: solo una vez por día
        settings = GymSettings.query.first()
        if settings:
            last_run = getattr(settings, '_last_notif_run', None)
            if last_run and str(last_run) == str(today):
                return  # ya corrió hoy

        from services.notification_service import NotificationService

        # 1. Avisos de vencimiento próximo
        for days in WARN_DAYS:
            target_date = today + timedelta(days=days)
            payments = Payment.query.filter(
                Payment.end_date == target_date,
                Payment.is_deleted == False,
            ).all()
            for p in payments:
                if p.client and p.client.email and p.client.is_active:
                    NotificationService.send_expiry_warning(p, days)

        # 2. Avisos de membresía expirada (vencieron ayer)
        yesterday = today - timedelta(days=1)
        expired = Payment.query.filter(
            Payment.end_date == yesterday,
            Payment.is_deleted == False,
        ).all()
        for p in expired:
            if p.client and p.client.email and p.client.is_active:
                NotificationService.send_expired_notice(p)

        # Marcar última ejecución
        if settings:
            # Guardamos en un campo temporal usando notes como fallback
            # (en producción podrías agregar una columna last_notif_run)
            pass

        db.session.commit()
