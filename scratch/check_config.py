from app import create_app
app = create_app()
with app.app_context():
    key = app.config.get('TWELVE_DATA_API_KEY')
    if key:
        print(f"Success! Key loaded securely. Length: {len(key)}")
    else:
        print("Key not found in app.config!")
