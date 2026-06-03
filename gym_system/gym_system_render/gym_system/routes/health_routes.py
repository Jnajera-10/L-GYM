from flask import Blueprint, jsonify
import pytz
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health():
    bogota = pytz.timezone('America/Bogota')
    return jsonify({
        'status': 'ok',
        'time_bogota': datetime.now(bogota).isoformat()
    })
