with open('app/__init__.py', 'r') as f:
    content = f.read()

if '/health' not in content:
    target = 'app.config.from_object(config_class)'
    replacement = '''app.config.from_object(config_class)

    @app.route('/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception:
            db_status = 'disconnected'
        return jsonify({'status': 'healthy', 'database': db_status}), 200
'''
    content = content.replace(target, replacement)
    
    with open('app/__init__.py', 'w') as f:
        f.write(content)
