import os

file_path = "app/models/finance.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

model_code = """
class PlatformSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maintenance_mode = db.Column(db.Boolean, default=False, nullable=False)
    ai_analyst_enabled = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @classmethod
    def get_settings(cls):
        settings = cls.query.get(1)
        if not settings:
            settings = cls(id=1)
            db.session.add(settings)
            db.session.commit()
        return settings
"""

if "class PlatformSetting(db.Model):" not in content:
    content += "\n" + model_code + "\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Added PlatformSetting to models.")
else:
    print("PlatformSetting already exists.")
