"""
Migración: agrega columna customer_name a la tabla sales.
Ejecutar una sola vez: python migrate_customer_name.py
"""
from app import application
from database.db import db
from sqlalchemy import text

with application.app_context():
    with db.engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE sales ADD COLUMN IF NOT EXISTS customer_name VARCHAR(150)"
        ))
        conn.commit()
    print("✅ Columna customer_name agregada a sales.")
