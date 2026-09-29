import os

with open('app/__init__.py', 'r') as f:
    content = f.read()

if 'from app.api.screener import bp as screener_bp' not in content:
    target = "app.register_blueprint(paper_trading_bp, url_prefix='/api/paper-trade')"
    replacement = target + "\n    \n    from app.api.screener import bp as screener_bp\n    app.register_blueprint(screener_bp, url_prefix='/api/screener')"
    
    content = content.replace(target, replacement)
    
    # Also fix unauthorized_handler
    auth_target = "if request.blueprint in ['api', 'paper_trade']:"
    auth_replacement = "if request.blueprint in ['api', 'paper_trade', 'screener']:"
    content = content.replace(auth_target, auth_replacement)
    
    with open('app/__init__.py', 'w') as f:
        f.write(content)
    print("Registered screener blueprint")
else:
    print("Blueprint already registered")
