from database.models.sales import Sale, SaleItem
from database.models.inventory import Product
from database.db import db
from services.inventory_service import InventoryService

class SalesService:
    @staticmethod
    def create_sale(client_id, items_data, payment_method, notes=None):
        total = 0
        sale = Sale(client_id=client_id, payment_method=payment_method, notes=notes, total=0)
        db.session.add(sale)
        db.session.flush()
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
            InventoryService.remove_stock(product.id, item['quantity'], 'Venta')
        sale.total = total
        db.session.commit()
        return sale
