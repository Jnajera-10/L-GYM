import os
import subprocess
from datetime import datetime
import pytz

BOGOTA = pytz.timezone('America/Bogota')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'backups')

class BackupService:
    @staticmethod
    def _backup_dir():
        path = os.path.abspath(BACKUP_DIR)
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def create_backup():
        """
        Genera un dump SQL de PostgreSQL usando pg_dump.
        Requiere que DATABASE_URL esté definida en el entorno.
        Compatible con Render + Neon.
        """
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            raise RuntimeError('DATABASE_URL no está configurada.')

        timestamp = datetime.now(BOGOTA).strftime('%Y%m%d_%H%M%S')
        backup_dir = BackupService._backup_dir()
        dest = os.path.join(backup_dir, f'backup_{timestamp}.sql')

        result = subprocess.run(
            ['pg_dump', '--no-password', '--format=plain', '--file', dest, db_url],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f'pg_dump falló: {result.stderr.strip()}')

        return dest

    @staticmethod
    def list_backups():
        backup_dir = BackupService._backup_dir()
        files = [f for f in os.listdir(backup_dir) if f.endswith('.sql')]
        return sorted(files, reverse=True)

    @staticmethod
    def restore_backup(filename):
        """Restaurar un backup SQL — usar con precaución en producción."""
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            raise RuntimeError('DATABASE_URL no está configurada.')

        backup_dir = BackupService._backup_dir()
        src = os.path.join(backup_dir, filename)
        if not os.path.exists(src):
            raise FileNotFoundError(f'Archivo de backup no encontrado: {filename}')

        result = subprocess.run(
            ['psql', '--no-password', db_url, '--file', src],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f'psql falló: {result.stderr.strip()}')
