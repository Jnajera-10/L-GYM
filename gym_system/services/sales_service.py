from database.models.sales import Sale, SaleItem
from database.models.inventory import Product
from database.db import db
from services.inventory_service import InventoryService
from services.audit_service import AuditService
from services.notification_service import send_whatsapp_owner
import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')


class SalesService:
    @staticmethod
    def create_sale(client_id, items_data, payment_method, notes=None):
        # Validar stock de todos los productos ANTES de escribir nada
        for item in items_data:
            product = Product.query.get(item['product_id'])
            if not product:
                raise ValueError(f'Producto {item["product_id"]} no encontrado.')
            if product.quantity < item['quantity']:
                raise ValueError(f'Stock insuficiente para "{product.name}". '
                                 f'Disponible: {product.quantity}, solicitado: {item["quantity"]}.')

        try:
            total = 0
            sale = Sale(client_id=client_id, payment_method=payment_method, notes=notes, total=0)
            db.session.add(sale)
            db.session.flush()

            lines_whatsapp = []  # Para armar el mensaje de WhatsApp
            lines_audit = []     # Para armar el detalle de auditoría

            for item in items_data:
                product = Product.query.get(item['product_id'])
                subtotal = product.sale_price * item['quantity']
                total += subtotal
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=item['quantity'],
                    unit_price=product.sale_price,
                    subtotal=subtotal
                )
                db.session.add(sale_item)
                # Descontar stock dentro de la misma sesión (sin commit interno)
                product.quantity -= item['quantity']
                mov_class = InventoryService.build_movement(product.id, item['quantity'], 'Venta')
                db.session.add(mov_class)

                lines_whatsapp.append(
                    f"  • {product.name} x{item['quantity']} = ${subtotal:,.0f}"
                )
                lines_audit.append(
                    f"{product.name} x{item['quantity']} (${subtotal:,.0f})"
                )

            sale.total = total
            db.session.commit()

            # ── WhatsApp al dueño ──────────────────────────────────────────
            try:
                now = datetime.now(BOGOTA).strftime('%d/%m/%Y %H:%M')
                productos_str = "\n".join(lines_whatsapp)
                msg = (
                    f"🛒 *VENTA REGISTRADA — L-GYM*\n"
                    f"📅 {now}\n"
                    f"💳 Pago: {payment_method}\n\n"
                    f"*Productos:*\n{productos_str}\n\n"
                    f"💰 *TOTAL: ${total:,.0f} COP*"
                )
                if notes:
                    msg += f"\n📝 Nota: {notes}"
                send_whatsapp_owner(msg)
            except Exception as wa_exc:
                # No bloquear la venta si WhatsApp falla
                print(f'[WHATSAPP] Error al enviar notificación de venta: {wa_exc}')

            # ── Auditoría ─────────────────────────────────────────────────
            try:
                detalle = " | ".join(lines_audit)
                AuditService.log(
                    action='VENTA',
                    table_name='sales',
                    record_id=sale.id,
                    old_value=None,
                    new_value=f"Total: ${total:,.0f} | Pago: {payment_method} | {detalle}"
                )
            except Exception as audit_exc:
                # No bloquear la venta si la auditoría falla
                print(f'[AUDIT] Error al registrar auditoría de venta: {audit_exc}')

            return sale

        except Exception:
            db.session.rollback()
            raise
