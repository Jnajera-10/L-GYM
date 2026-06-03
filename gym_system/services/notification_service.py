import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database.models.notifications import Notification
from database.db import db
import pytz
import requests
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')


class NotificationService:

    @staticmethod
    def send_email(to_email, subject, body, client_id=None):
        """
        Envía un email real por SMTP y registra el resultado en la BD.
        Requiere MAIL_USERNAME y MAIL_PASSWORD en las variables de entorno.
        Si no están configuradas, guarda el registro como 'pendiente' sin fallar.
        """
        mail_user = os.environ.get('MAIL_USERNAME', '').strip()
        mail_pass = os.environ.get('MAIL_PASSWORD', '').strip()
        mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.environ.get('MAIL_PORT', 587))

        status = 'pendiente'
        if mail_user and mail_pass:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = mail_user
                msg['To'] = to_email
                msg.attach(MIMEText(body, 'html', 'utf-8'))

                with smtplib.SMTP(mail_server, mail_port, timeout=10) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(mail_user, mail_pass)
                    server.sendmail(mail_user, to_email, msg.as_string())

                status = 'enviado'
            except Exception as exc:
                status = f'error: {str(exc)[:120]}'

        notif = Notification(
            client_id=client_id,
            channel='email',
            message=f'{subject}: {body[:200]}',
            status=status,
            sent_at=datetime.now(BOGOTA) if status == 'enviado' else None,
        )
        db.session.add(notif)
        db.session.commit()
        return status == 'enviado'

    @staticmethod
    def send_whatsapp(phone, message, client_id=None):
        api_url = os.environ.get('WHATSAPP_API_URL', '').strip()
        token = os.environ.get('WHATSAPP_TOKEN', '').strip()

        status = 'pendiente'
        if api_url and token:
            try:
                resp = requests.post(
                    api_url,
                    json={'phone': phone, 'message': message},
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=10,
                )
                status = 'enviado' if resp.ok else f'error: {resp.status_code}'
            except Exception as exc:
                status = f'error: {str(exc)[:120]}'

        notif = Notification(
            client_id=client_id,
            channel='whatsapp',
            message=message[:200],
            status=status,
            sent_at=datetime.now(BOGOTA) if status == 'enviado' else None,
        )
        db.session.add(notif)
        db.session.commit()
        return status == 'enviado'

    @staticmethod
    def send_password_reset(user):
        subject = 'Recuperación de contraseña — Body-Fit'
        body = f"""
        <p>Hola <strong>{user.full_name}</strong>,</p>
        <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en Body-Fit.</p>
        <p>Si no realizaste esta solicitud, puedes ignorar este mensaje.</p>
        <p>Para restablecer tu contraseña comunícate con el administrador del sistema.</p>
        <br><p>— Equipo Body-Fit</p>
        """
        return NotificationService.send_email(user.email, subject, body)
