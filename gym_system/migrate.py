from app import application
from database.db import db
from sqlalchemy import text

with application.app_context():
    with db.engine.connect() as conn:
        # Migraciones previas (idempotentes)
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS shift VARCHAR(10) DEFAULT 'manana'"))
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS cash_received FLOAT"))
        conn.execute(text("ALTER TABLE payments ADD COLUMN IF NOT EXISTS cash_change FLOAT"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cash_registers (
                id SERIAL PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                opening_cash FLOAT NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))

        # Nueva tabla de egresos
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          SERIAL PRIMARY KEY,
                date        DATE NOT NULL,
                amount      FLOAT NOT NULL,
                description VARCHAR(255) NOT NULL,
                category    VARCHAR(80),
                created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at  TIMESTAMP
            )
        """))

        conn.commit()
    print("OK — migraciones aplicadas correctamente")
