from database.models.notifications import Notification
from database.db import db
import pytz, requests, os
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')

class NotificationService:
    @staticmethod
    def send_email(to_email, subject, body, client_id=None):
        notif = Notification(
            client_id=client_id,
            channel='email',
            message=f'{subject}: {body}',
            status='enviado',
            sent_at=datetime.now(BOGOTA)
        )
        db.session.add(notif)
        db.session.commit()

    @staticmethod
    def send_whatsapp(phone, message, client_id=None):
        notif = Notification(
            client_id=client_id,
            channel='whatsapp',
            message=message,
            status='enviado',
            sent_at=datetime.now(BOGOTA)
        )
        db.session.add(notif)
        db.session.commit()

    @staticmethod
    def send_password_reset(user):
        NotificationService.send_email(
            user.email,
            'Recuperación de contraseña',
            'Haz clic en el enlace para restablecer tu contraseña.'
        )
