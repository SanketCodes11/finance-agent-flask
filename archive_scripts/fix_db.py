import sqlite3
import os

db_path = os.path.join('instance', 'finance.db')
conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))")
conn.execute("INSERT OR REPLACE INTO alembic_version (version_num) VALUES ('fbcd1f41a016')")
conn.commit()
conn.close()
