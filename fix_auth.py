import os

with open('app/__init__.py', 'r') as f:
    content = f.read()

content = content.replace("if request.blueprint == 'api':", "if request.blueprint in ['api', 'paper_trade']:")

with open('app/__init__.py', 'w') as f:
    f.write(content)
print("Fixed app/__init__.py")
