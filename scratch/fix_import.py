import re

file_path = "app/routes/admin.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add import at top
target = "from app.models.user import User, AdminAuditLog"
replace = "from app.models.user import User, AdminAuditLog\nfrom app.models.finance import PlatformSetting"

content = content.replace(target, replace)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Imported PlatformSetting in admin.py.")
