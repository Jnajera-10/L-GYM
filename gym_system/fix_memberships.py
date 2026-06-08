"""
fix_memberships.py
==================
1. Crea todas las membresías del gimnasio en la tabla memberships
2. Actualiza los pagos importados del Excel con el plan y monto correcto
3. Actualiza los montos de los 40 pagos de junio con el precio real

Ejecutar desde gym_system/:
    python fix_memberships.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

import openpyxl
from datetime import date, datetime
from app import application
from database.db import db
from database.models.membership import Membership
from database.models.payment import Payment
from database.models.client import Client

# ── Catálogo completo de membresías ───────────────────────────────────
CATALOG = [
    {'name': 'Diario',        'membership_type': 'diario',        'duration_days': 1,   'price': 5000,   'max_members': 1},
    {'name': 'Semanal',       'membership_type': 'semanal',       'duration_days': 7,   'price': 20000,  'max_members': 1},
    {'name': 'Quincenal',     'membership_type': 'quincenal',     'duration_days': 15,  'price': 35000,  'max_members': 1},
    {'name': 'Mensual',       'membership_type': 'mensual',       'duration_days': 30,  'price': 60000,  'max_members': 1},
    {'name': 'Trimestral',    'membership_type': 'trimestral',    'duration_days': 90,  'price': 170000, 'max_members': 1},
    {'name': 'Semestral',     'membership_type': 'semestral',     'duration_days': 180, 'price': 300000, 'max_members': 1},
    {'name': 'Anual',         'membership_type': 'anual',         'duration_days': 365, 'price': 550000, 'max_members': 1},
    {'name': 'Plan Pareja',   'membership_type': 'pareja',        'duration_days': 30,  'price': 110000, 'max_members': 2},
    {'name': 'Plan Familiar', 'membership_type': 'familiar',      'duration_days': 30,  'price': 50000,  'max_members': 10},
    {'name': 'Estudiantil',   'membership_type': 'estudiantil',   'duration_days': 30,  'price': 50000,  'max_members': 1, 'requires_student': True},
]

# Mapeo de texto del Excel → membership_type del catálogo
PLAN_MAP = {
    'mensual':    'mensual',
    'quincenal':  'quincenal',
    'semana':     'semanal',
    'semanal':    'semanal',
    'trimestre':  'trimestral',
    'trimestral': 'trimestral',
    'semestre':   'semestral',
    'semestral':  'semestral',
    'anual':      'anual',
    'diario':     'diario',
    'pareja':     'pareja',
    'familiar':   'familiar',
    'estudiantil':'estudiantil',
}

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'REGISTRO DIARIO BODYFIT JUNIO.xlsx')
# Si no está en la ruta de arriba, busca en Downloads
if not os.path.exists(EXCEL_PATH):
    EXCEL_PATH = os.path.expanduser(r'~\Downloads\REGISTRO DIARIO BODYFIT JUNIO.xlsx')


def get_or_create_membership(session, mtype):
    """Devuelve la membresía por tipo."""
    return session.query(Membership).filter_by(membership_type=mtype).first()


with application.app_context():

    # ── 1. Crear membresías del catálogo ─────────────────────────────
    print("\n📋 Creando/verificando membresías del catálogo...")
    for cfg in CATALOG:
        existing = Membership.query.filter_by(membership_type=cfg['membership_type']).first()
        if existing:
            # Actualizar precio y datos
            existing.name          = cfg['name']
            existing.duration_days = cfg['duration_days']
            existing.price         = cfg['price']
            existing.max_members   = cfg.get('max_members', 1)
            existing.requires_student = cfg.get('requires_student', False)
            existing.is_active     = True
            print(f"  [✓] Actualizado: {cfg['name']} — ${cfg['price']:,.0f}")
        else:
            m = Membership(
                name             = cfg['name'],
                membership_type  = cfg['membership_type'],
                duration_days    = cfg['duration_days'],
                price            = cfg['price'],
                max_members      = cfg.get('max_members', 1),
                requires_student = cfg.get('requires_student', False),
                is_active        = True,
            )
            db.session.add(m)
            print(f"  [+] Creado: {cfg['name']} — ${cfg['price']:,.0f}")

    db.session.commit()
    print("  ✅ Membresías listas\n")

    # ── 2. Leer Excel y actualizar pagos ─────────────────────────────
    print("📂 Leyendo Excel...")
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb['REGISTRO']

    actualizados = 0
    no_encontrado = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        nombre_raw = row[0]
        if not nombre_raw or not str(nombre_raw).strip():
            continue

        nombre  = str(nombre_raw).strip()
        plan_ex = str(row[3]).strip().lower() if row[3] else 'mensual'
        val     = row[2]

        if isinstance(val, datetime): fecha_insc = val.date()
        elif isinstance(val, date):   fecha_insc = val
        else:                         fecha_insc = None

        mtype = PLAN_MAP.get(plan_ex, 'mensual')

        # Buscar cliente en BD
        cliente = Client.query.filter(
            db.func.lower(Client.full_name) == nombre.lower()
        ).first()
        if not cliente:
            no_encontrado += 1
            continue

        # Buscar membresía correcta
        membresia = Membership.query.filter_by(membership_type=mtype).first()
        if not membresia:
            continue

        # Actualizar todos los pagos de este cliente
        pagos = Payment.query.filter_by(client_id=cliente.id, is_deleted=False).all()
        for pago in pagos:
            pago.membership_id = membresia.id
            pago.amount        = membresia.price
        actualizados += len(pagos)

    db.session.commit()

    print(f"  ✅ Pagos actualizados: {actualizados}")
    if no_encontrado:
        print(f"  ⚠️  Clientes no encontrados en BD: {no_encontrado}")

    # ── 3. Resumen final ─────────────────────────────────────────────
    print("\n📊 Resumen de membresías en BD:")
    for cfg in CATALOG:
        m = Membership.query.filter_by(membership_type=cfg['membership_type']).first()
        if m:
            total_pagos = Payment.query.filter_by(membership_id=m.id, is_deleted=False).count()
            print(f"  {m.name:<20} — {total_pagos} pagos — ${m.price:,.0f}")

    print("\n✅ Todo listo\n")
