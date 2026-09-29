from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
login.login_message_category = 'info'
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.route('/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception:
            db_status = 'disconnected'
        return jsonify({'status': 'healthy', 'database': db_status}), 200


    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    csrf.init_app(app)

    @login.unauthorized_handler
    def unauthorized():
        if request.blueprint in ['api', 'paper_trade', 'screener', 'workspace']:
            return jsonify({'error': 'Unauthorized'}), 401
        from flask import flash
        flash(login.login_message, login.login_message_category)
        return redirect(url_for('auth.login', next=request.url))

    # Register blueprints
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.api.finance import bp as api_bp
    
    from app.api.paper_trading import bp as paper_trading_bp
    app.register_blueprint(paper_trading_bp, url_prefix='/api/paper-trade')
    
    from app.api.screener import bp as screener_bp
    app.register_blueprint(screener_bp, url_prefix='/api/screener')
    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.routes.admin_db import bp as admin_db_bp
    app.register_blueprint(admin_db_bp)
    
    from app.api.workspace import bp as workspace_bp
    app.register_blueprint(workspace_bp, url_prefix='/api/workspace')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Error handling
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
        
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template('errors/401.html'), 401
        
    @app.errorhandler(429)
    def ratelimit_error(error):
        return render_template('errors/429.html'), 429

    if not app.debug and not app.testing:
        # Vercel serverless compatibility: /tmp is the only writable directory
        is_vercel = os.environ.get('VERCEL') == '1'
        log_dir = '/tmp/logs' if is_vercel else 'logs'
        
        if not os.path.exists(log_dir):
            try:
                os.mkdir(log_dir)
            except OSError:
                pass # Fallback gracefully if even /tmp/logs fails

        log_file = os.path.join(log_dir, 'finance.log')
        try:
            file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        except OSError:
            # Fallback to console logging only if file logging is impossible
            pass
            
        app.logger.setLevel(logging.INFO)
        app.logger.info('Finance Insight Agent startup')

    if not app.testing:
        from app.scheduler import start_alert_scheduler
        start_alert_scheduler(app)

    from app.cli import make_admin_command
    app.cli.add_command(make_admin_command)

    return app
