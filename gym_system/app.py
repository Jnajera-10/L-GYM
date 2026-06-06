import os
from flask import Flask
from config import Config
from database.db import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp
    from routes.client_routes import client_bp
    from routes.membership_routes import membership_bp
    from routes.payment_routes import payment_bp
    from routes.attendance_routes import attendance_bp
    from routes.inventory_routes import inventory_bp
    from routes.sales_routes import sales_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.reports_routes import reports_bp
    from routes.notification_routes import notification_bp
    from routes.settings_routes import settings_bp
    from routes.backup_routes import backup_bp
    from routes.audit_routes import audit_bp
    from routes.health_routes import health_bp
    from routes.profile_routes import profile_bp

    for bp in [auth_bp, user_bp, client_bp, membership_bp, payment_bp,
               attendance_bp, inventory_bp, sales_bp, dashboard_bp,
               reports_bp, notification_bp, settings_bp, backup_bp, audit_bp,
               health_bp, profile_bp]:
        app.register_blueprint(bp)

    # El módulo de prueba de emails solo se activa si ENABLE_EMAIL_TEST=true
    # en las variables de entorno de Render. En producción esta var NO existe,
    # así que la ruta /email-test queda completamente desregistrada.
    email_test_enabled = os.environ.get('ENABLE_EMAIL_TEST', '').lower() == 'true'
    if email_test_enabled:
        from routes.email_test_routes import email_test_bp
        app.register_blueprint(email_test_bp)

    # Inyectar email_test_enabled en todos los templates (para el sidebar)
    @app.context_processor
    def inject_globals():
        return {'email_test_enabled': email_test_enabled}

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    with app.app_context():
        db.create_all()

    return app

application = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=False)
