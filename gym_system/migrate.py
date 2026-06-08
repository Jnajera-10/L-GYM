from app import application
from database.db import db
from sqlalchemy import text

with application.app_context():
    with db.engine.connect() as conn:
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS shift VARCHAR(10) DEFAULT 'manana'"))
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS cash_received FLOAT"))
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS cash_change FLOAT"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS cash_registers (id SERIAL PRIMARY KEY, date DATE UNIQUE NOT NULL, opening_cash FLOAT NOT NULL DEFAULT 0, notes TEXT, created_at TIMESTAMP, updated_at TIMESTAMP)"))
        conn.commit()
    print("OK - columnas agregadas correctamente")
