import sqlite3
import os

db_path = os.path.join('instance', 'finance.db')
conn = sqlite3.connect(db_path)
conn.execute("DELETE FROM alembic_version")
conn.execute("INSERT INTO alembic_version (version_num) VALUES ('fbcd1f41a016')")
conn.execute("DROP TABLE IF EXISTS portfolio_transaction")
conn.execute("DROP TABLE IF EXISTS alert")
conn.commit()
conn.close()
