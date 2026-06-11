import sqlite3
import os


def get_db_path():
    # находим папку, где лежит database.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "list_of_accounts.db")


def init_db():
    db_path = get_db_path()
    conn=sqlite3.connect(db_path)
    cursor=conn.cursor()
    cursor.execute("""
CREATE TABLE IF NOT EXISTS list_of_accounts(id INTEGER PRIMARY KEY,
                   owner_name TEXT,
                   age INTEGER,
                   balance REAL,
                   bank_name TEXT)
""")
    conn.commit()
    conn.close()


def save_account_to_db(account):
    # используется with для автоматического закрытия
    db_path = get_db_path()
    print(f"Пытаюсь подключиться к базе по адресу: {os.path.abspath(db_path)}")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO list_of_accounts(owner_name, age, balance, bank_name)
            VALUES(?,?,?,?)
        """, (account.owner_name, account.age, account.balance, account.bank_name))
        new_id = cursor.lastrowid
        conn.commit()
        return new_id
    
    
