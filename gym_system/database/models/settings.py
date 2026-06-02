from database.db import db
from datetime import datetime
import pytz

BOGOTA = pytz.timezone('America/Bogota')

class GymSettings(db.Model):
    __tablename__ = 'gym_settings'
    id = db.Column(db.Integer, primary_key=True)
    gym_name = db.Column(db.String(150), default='Mi Gimnasio')
    logo_path = db.Column(db.String(255))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    instagram = db.Column(db.String(100))
    facebook = db.Column(db.String(100))
    whatsapp = db.Column(db.String(20))
    days_before_expiry = db.Column(db.Integer, default=3)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(BOGOTA))
