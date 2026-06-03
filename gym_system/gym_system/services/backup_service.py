import shutil, os
from datetime import datetime
import pytz

BOGOTA = pytz.timezone('America/Bogota')
DB_PATH = 'database/database.db'
BACKUP_DIR = 'backups'

class BackupService:
    @staticmethod
    def create_backup():
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now(BOGOTA).strftime('%Y%m%d_%H%M%S')
        dest = os.path.join(BACKUP_DIR, f'backup_{timestamp}.db')
        shutil.copy2(DB_PATH, dest)
        return dest

    @staticmethod
    def list_backups():
        return sorted(os.listdir(BACKUP_DIR), reverse=True)

    @staticmethod
    def restore_backup(filename):
        src = os.path.join(BACKUP_DIR, filename)
        shutil.copy2(src, DB_PATH)
