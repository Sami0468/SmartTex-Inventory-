"""
SmartTex Inventory - Application Factory
"""
import os
from flask import Flask, render_template
from app.extensions import db, login_manager, csrf
from app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # Register blueprints
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.dashboard.routes import dashboard_bp
    from app.blueprints.fabrics.routes import fabrics_bp
    from app.blueprints.suppliers.routes import suppliers_bp
    from app.blueprints.warehouses.routes import warehouses_bp
    from app.blueprints.production.routes import production_bp
    from app.blueprints.workers.routes import workers_bp
    from app.blueprints.customers.routes import customers_bp
    from app.blueprints.sales.routes import sales_bp
    from app.blueprints.reports.routes import reports_bp
    from app.blueprints.notifications.routes import notifications_bp
    from app.blueprints.audit.routes import audit_bp
    from app.blueprints.ai_assistant.routes import ai_bp
    from app.blueprints.messages.routes import messages_bp
    from app.blueprints.history.routes import history_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(fabrics_bp, url_prefix="/fabrics")
    app.register_blueprint(suppliers_bp, url_prefix="/suppliers")
    app.register_blueprint(warehouses_bp, url_prefix="/warehouses")
    app.register_blueprint(production_bp, url_prefix="/production")
    app.register_blueprint(workers_bp, url_prefix="/workers")
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(sales_bp, url_prefix="/sales")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(audit_bp, url_prefix="/audit")
    app.register_blueprint(ai_bp, url_prefix="/ai")
    app.register_blueprint(messages_bp, url_prefix="/team-chat")
    app.register_blueprint(history_bp, url_prefix="/history")

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.errorhandler(400)
    def bad_request(e):
        from flask import flash, redirect, request
        from flask_wtf.csrf import CSRFError
        if isinstance(e, CSRFError) or "CSRF" in str(getattr(e, "description", "")):
            flash("Your session changed since this page was loaded (e.g. you logged in again, "
                  "or it sat open a while). Please refresh the page and try again.", "warning")
            referrer = request.referrer or "/"
            return redirect(referrer)
        return render_template("errors/500.html"), 400

    # Context processor - inject notifications count globally
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        unread_count = 0
        if current_user.is_authenticated:
            from app.models.notification import Notification
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
        return dict(unread_notifications=unread_count)

    # CLI command to seed database
    @app.cli.command("seed-db")
    def seed_db():
        from app.utils.seed import seed_database
        seed_database()
        print("Database seeded successfully.")

    @app.cli.command("init-db")
    def init_db():
        with app.app_context():
            db.create_all()
        print("Database tables created.")

    return app
