with open('app/__init__.py', 'r') as f:
    content = f.read()

if 'workspace_bp' not in content:
    content = content.replace(
        "app.register_blueprint(screener_bp, url_prefix='/api/screener')",
        "app.register_blueprint(screener_bp, url_prefix='/api/screener')\n    from app.api.workspace import bp as workspace_bp\n    app.register_blueprint(workspace_bp, url_prefix='/api/workspace')"
    )
    content = content.replace("['api', 'paper_trade', 'screener']", "['api', 'paper_trade', 'screener', 'workspace']")
    with open('app/__init__.py', 'w') as f:
        f.write(content)
