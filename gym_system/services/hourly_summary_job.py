"""
Job horario que junta todos los eventos acumulados (pagos, ventas,
eliminaciones, cobros pendientes) y envía UN solo mensaje de WhatsApp
al dueño con el resumen, en vez de un mensaje por cada evento.

Se dispara desde /health (igual que daily_report_job), pero corre
como máximo 1 vez por hora, y SOLO entre las 5:00am y las 10:00pm
(hora Bogotá). Fuera de ese rango los eventos quedan en la cola sin
enviarse, y se incluyen en el primer resumen del día (a las 5am).

Si no hubo ningún evento en la hora correspondiente, no envía nada
(para no gastar mensajes sin necesidad).
"""
import pytz
import logging
from datetime import datetime
from services.notification_queue import pop_all

BOGOTA = pytz.timezone('America/Bogota')
logger = logging.getLogger(__name__)

HORA_INICIO = 5    # 5:00 am
HORA_FIN    = 22   # 10:00 pm (no se envía después de esta hora)

_last_run_hour_key = None  # ej. "2026-06-29-14"

ICONOS = {
    'pago': '💪',
    'pago_pendiente': '⏳',
    'pago_eliminado': '🗑️',
    'venta': '🛒',
    'venta_pendiente': '⏳',
    'venta_cobrada': '✅',
}

TITULOS = {
    'pago': 'Pagos nuevos',
    'pago_pendiente': 'Pagos pendientes',
    'pago_eliminado': 'Pagos eliminados',
    'venta': 'Ventas (inventario)',
    'venta_pendiente': 'Ventas pendientes',
    'venta_cobrada': 'Ventas cobradas',
}


def run_hourly_summary(app):
    global _last_run_hour_key

    with app.app_context():
        now = datetime.now(BOGOTA)
        hour_key = now.strftime('%Y-%m-%d-%H')

        # Fuera del horario 5am-10pm: no enviar, dejar acumulando en la cola
        if now.hour < HORA_INICIO or now.hour >= HORA_FIN:
            return

        # Ya corrió esta hora
        if _last_run_hour_key == hour_key:
            return

        _last_run_hour_key = hour_key

        try:
            eventos = pop_all()
            if not eventos:
                logger.info(f'[hourly_summary] {hour_key} — sin eventos, no se envía nada.')
                return

            # Agrupar por tipo
            grupos = {}
            for ev in eventos:
                grupos.setdefault(ev['tipo'], []).append(ev['texto'])

            fecha_str = now.strftime('%d/%m/%Y')
            hora_str = now.strftime('%H:%M')

            bloques = []
            for tipo, textos in grupos.items():
                icono = ICONOS.get(tipo, '•')
                titulo = TITULOS.get(tipo, tipo)
                lineas = "\n".join(f"  • {t}" for t in textos)
                bloques.append(f"{icono} *{titulo}* ({len(textos)})\n{lineas}")

            cuerpo = "\n\n".join(bloques)

            mensaje = (
                f"📊 *RESUMEN L-GYM*\n"
                f"📅 {fecha_str} — {hora_str}\n"
                f"{'-'*28}\n"
                f"{cuerpo}\n"
                f"{'-'*28}\n"
                f"Total eventos: {len(eventos)}"
            )

            from services.notification_service import send_whatsapp_owner
            send_whatsapp_owner(mensaje)
            logger.info(f'[hourly_summary] {hour_key} — resumen enviado ({len(eventos)} eventos).')

        except Exception as exc:
            logger.error(f'[hourly_summary] Error generando resumen: {exc}', exc_info=True)
