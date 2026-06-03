import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database.models.notifications import Notification
from database.db import db
import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')

# ── Configuración SMTP (Outlook) ──────────────────────────────
MAIL_SERVER  = os.environ.get('MAIL_SERVER',   'smtp.office365.com')
MAIL_PORT    = int(os.environ.get('MAIL_PORT', 587))
MAIL_USER    = os.environ.get('MAIL_USERNAME', '')
MAIL_PASS    = os.environ.get('MAIL_PASSWORD', '')
MAIL_FROM    = os.environ.get('MAIL_FROM',     MAIL_USER)  # nombre/correo remitente


def _send_smtp(to_email: str, subject: str, html_body: str) -> tuple[bool, str]:
    """Envía el email por SMTP y retorna (éxito, mensaje_error)."""
    if not MAIL_USER or not MAIL_PASS:
        return False, 'MAIL_USERNAME o MAIL_PASSWORD no configurados en variables de entorno.'
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Body-Fit Gym <{MAIL_FROM}>'
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(MAIL_USER, MAIL_PASS)
            server.sendmail(MAIL_USER, to_email, msg.as_string())
        return True, ''
    except Exception as exc:
        return False, str(exc)[:200]


def _log_notification(client_id, channel, message, success, error=''):
    status = 'enviado' if success else f'error: {error[:100]}'
    notif = Notification(
        client_id=client_id,
        channel=channel,
        message=message[:255],
        status=status,
        sent_at=datetime.now(BOGOTA) if success else None,
    )
    db.session.add(notif)
    db.session.commit()
    return success


# ── Templates de email ────────────────────────────────────────

def _base_template(titulo: str, contenido: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0;">
        <tr><td align="center">
          <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
            <!-- Header -->
            <tr>
              <td style="background:#1a1a2e;padding:24px 32px;">
                <h1 style="margin:0;color:#ffffff;font-size:22px;letter-spacing:1px;">
                  💪 BODY-FIT GYM
                </h1>
              </td>
            </tr>
            <!-- Título -->
            <tr>
              <td style="background:#e63946;padding:16px 32px;">
                <h2 style="margin:0;color:#ffffff;font-size:18px;">{titulo}</h2>
              </td>
            </tr>
            <!-- Contenido -->
            <tr>
              <td style="padding:32px;">
                {contenido}
              </td>
            </tr>
            <!-- Footer -->
            <tr>
              <td style="background:#f8f8f8;padding:16px 32px;border-top:1px solid #eeeeee;">
                <p style="margin:0;color:#999999;font-size:12px;text-align:center;">
                  Este es un mensaje automático de Body-Fit Gym.<br>
                  Por favor no respondas a este correo.
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


class NotificationService:

    # ── 1. Bienvenida al registrarse ──────────────────────────
    @staticmethod
    def send_welcome(client):
        """Llama esto justo después de crear el cliente en la BD."""
        if not client.email:
            return False

        contenido = f"""
        <p style="color:#333;font-size:16px;">Hola <strong>{client.full_name}</strong>,</p>
        <p style="color:#555;">¡Bienvenido(a) a <strong>Body-Fit Gym</strong>! 🎉</p>
        <p style="color:#555;">Tu registro ha sido completado exitosamente.</p>
        <table style="background:#f8f8f8;border-radius:6px;padding:16px;width:100%;margin:16px 0;">
          <tr><td style="color:#666;padding:4px 0;"><strong>Nombre:</strong></td><td style="color:#333;">{client.full_name}</td></tr>
          <tr><td style="color:#666;padding:4px 0;"><strong>Documento:</strong></td><td style="color:#333;">{client.document_type} {client.document_number}</td></tr>
          <tr><td style="color:#666;padding:4px 0;"><strong>Teléfono:</strong></td><td style="color:#333;">{client.phone or '—'}</td></tr>
        </table>
        <p style="color:#555;">Ya puedes acercarte al gimnasio y hablar con nuestro equipo para activar tu membresía.</p>
        <p style="color:#555;">¡Nos vemos en el gym! 💪</p>
        """

        html = _base_template('¡Bienvenido a Body-Fit!', contenido)
        ok, err = _send_smtp(client.email, '¡Bienvenido a Body-Fit Gym! 💪', html)
        return _log_notification(client.id, 'email', f'Bienvenida: {client.full_name}', ok, err)

    # ── 2. Confirmación de pago / membresía activada ──────────
    @staticmethod
    def send_payment_confirmation(payment):
        """Llama esto justo después de registrar un pago."""
        client = payment.client
        if not client or not client.email:
            return False

        contenido = f"""
        <p style="color:#333;font-size:16px;">Hola <strong>{client.full_name}</strong>,</p>
        <p style="color:#555;">Tu pago ha sido registrado correctamente. ¡Tu membresía está activa! ✅</p>
        <table style="background:#f8f8f8;border-radius:6px;padding:16px;width:100%;margin:16px 0;">
          <tr><td style="color:#666;padding:4px 0;"><strong>Plan:</strong></td><td style="color:#333;">{payment.membership.name}</td></tr>
          <tr><td style="color:#666;padding:4px 0;"><strong>Monto pagado:</strong></td><td style="color:#333;font-weight:bold;">${'{:,.0f}'.format(payment.amount)} COP</td></tr>
          <tr><td style="color:#666;padding:4px 0;"><strong>Método:</strong></td><td style="color:#333;">{payment.payment_method}</td></tr>
          <tr><td style="color:#666;padding:4px 0;"><strong>Válido desde:</strong></td><td style="color:#333;">{payment.start_date.strftime('%d/%m/%Y')}</td></tr>
          <tr><td style="color:#666;padding:4px 0;"><strong>Vence el:</strong></td><td style="color:#e63946;font-weight:bold;">{payment.end_date.strftime('%d/%m/%Y')}</td></tr>
        </table>
        <p style="color:#555;">¡Entrena duro y alcanza tus metas! 🏋️</p>
        """

        html = _base_template('Pago Confirmado ✅', contenido)
        ok, err = _send_smtp(client.email, f'Pago confirmado — {payment.membership.name}', html)
        return _log_notification(client.id, 'email', f'Pago confirmado: ${payment.amount}', ok, err)

    # ── 3. Aviso de vencimiento próximo ───────────────────────
    @staticmethod
    def send_expiry_warning(payment, days_left: int):
        """Llama esto desde el job diario de vencimientos."""
        client = payment.client
        if not client or not client.email:
            return False

        emoji = '⚠️' if days_left <= 1 else '🔔'
        dias_texto = 'mañana' if days_left == 1 else f'en {days_left} días'

        contenido = f"""
        <p style="color:#333;font-size:16px;">Hola <strong>{client.full_name}</strong>,</p>
        <p style="color:#555;">{emoji} Tu membresía en <strong>Body-Fit Gym</strong> vence <strong>{dias_texto}</strong>.</p>
        <table style="background:#fff3cd;border-radius:6px;padding:16px;width:100%;margin:16px 0;border-left:4px solid #ffc107;">
          <tr><td style="color:#666;padding:4px 0;"><strong>Plan:</strong></td><td style="color:#333;">{payment.membership.name}</td></tr>
          <tr><td style="color:#666;padding:4px 0;"><strong>Fecha de vencimiento:</strong></td><td style="color:#e63946;font-weight:bold;">{payment.end_date.strftime('%d/%m/%Y')}</td></tr>
        </table>
        <p style="color:#555;">Renueva tu membresía antes de que venza para no perder ni un día de entrenamiento.</p>
        <p style="color:#555;">Acércate al gimnasio o comunícate con nosotros para renovar. 💪</p>
        """

        html = _base_template(f'Tu membresía vence {dias_texto} {emoji}', contenido)
        ok, err = _send_smtp(client.email, f'{emoji} Tu membresía vence {dias_texto} — Body-Fit', html)
        return _log_notification(client.id, 'email', f'Aviso vencimiento: {days_left} días', ok, err)

    # ── 4. Membresía expirada ─────────────────────────────────
    @staticmethod
    def send_expired_notice(payment):
        """Llama esto cuando la membresía ya expiró."""
        client = payment.client
        if not client or not client.email:
            return False

        contenido = f"""
        <p style="color:#333;font-size:16px;">Hola <strong>{client.full_name}</strong>,</p>
        <p style="color:#555;">Tu membresía en <strong>Body-Fit Gym</strong> ha vencido el <strong>{payment.end_date.strftime('%d/%m/%Y')}</strong>. 😢</p>
        <p style="color:#555;">Para seguir disfrutando de nuestras instalaciones, renueva tu plan.</p>
        <table style="background:#f8d7da;border-radius:6px;padding:16px;width:100%;margin:16px 0;border-left:4px solid #e63946;">
          <tr><td style="color:#666;padding:4px 0;"><strong>Plan vencido:</strong></td><td style="color:#333;">{payment.membership.name}</td></tr>
          <tr><td style="color:#666;padding:4px 0;"><strong>Venció el:</strong></td><td style="color:#e63946;font-weight:bold;">{payment.end_date.strftime('%d/%m/%Y')}</td></tr>
        </table>
        <p style="color:#555;">¡Te esperamos de vuelta! No dejes que el esfuerzo se pierda. 💪</p>
        """

        html = _base_template('Tu membresía ha vencido ❌', contenido)
        ok, err = _send_smtp(client.email, '❌ Tu membresía en Body-Fit ha vencido — ¡Renueva!', html)
        return _log_notification(client.id, 'email', f'Membresía expirada: {payment.end_date}', ok, err)

    # ── Genérico (para recuperación de contraseña, etc.) ──────
    @staticmethod
    def send_email(to_email, subject, body, client_id=None):
        html = _base_template(subject, f'<p style="color:#555;">{body}</p>')
        ok, err = _send_smtp(to_email, subject, html)
        return _log_notification(client_id, 'email', f'{subject[:100]}', ok, err)

    @staticmethod
    def send_password_reset(user):
        contenido = f"""
        <p style="color:#333;">Hola <strong>{user.full_name}</strong>,</p>
        <p style="color:#555;">Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>
        <p style="color:#555;">Si no realizaste esta solicitud, ignora este mensaje.</p>
        <p style="color:#555;">Para restablecer tu contraseña comunícate con el administrador del sistema.</p>
        """
        html = _base_template('Recuperación de Contraseña 🔐', contenido)
        ok, err = _send_smtp(user.email, 'Recuperación de contraseña — Body-Fit', html)
        return _log_notification(None, 'email', f'Reset password: {user.email}', ok, err)
