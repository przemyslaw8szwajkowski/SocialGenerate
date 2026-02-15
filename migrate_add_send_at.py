import sqlite3

def migrate_add_send_at(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE post ADD COLUMN send_at DATETIME")
        print("Kolumna send_at dodana.")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Kolumna send_at już istnieje.")
        else:
            print("Błąd migracji:", e)
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate_add_send_at('users.db')
