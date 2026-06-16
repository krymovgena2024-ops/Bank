import sqlite3
import os


def get_db_path():
    # находим папку, где лежит database.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "list_of_accounts.db")


def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Обновленная старая таблица (без balance)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS list_of_accounts (
        id INTEGER PRIMARY KEY,
        owner_name TEXT,
        age INTEGER,
        bank_name TEXT
    )""")
    
    # 2. Новая таблица кошельков
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_balances (
        id INTEGER PRIMARY KEY,
        account_id INTEGER,
        currency TEXT,
        balance REAL,
        FOREIGN KEY (account_id) REFERENCES list_of_accounts(id) ON DELETE CASCADE
    )""")
    
    conn.commit()
    conn.close()


def save_account_to_db(account):
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Проверяем, существует ли уже этот человек в ЭТОМ ЖЕ банке
        cursor.execute("""
            SELECT id FROM list_of_accounts 
            WHERE owner_name = ? AND bank_name = ?
        """, (account.owner_name, account.bank_name))
        
        row = cursor.fetchone()
        
        if row:
            # Если пользователь уже зарегистрирован в этом банке,
            # мы берем его существующий ID для связывания валют
            user_id = row[0]
        else:
            # Если это совершенно новый пользователь для данного банка,
            # создаем для него запись в list_of_accounts
            cursor.execute("""
                INSERT INTO list_of_accounts (owner_name, age, bank_name, account_number) 
                VALUES (?, ?, ?, ?)
            """, (account.owner_name, account.age, account.bank_name, account.account_number))
            
            # Получаем автоматически сгенерированный ID новой записи пользователя
            user_id = cursor.lastrowid
        
        # 2. Проверяем, нет ли уже у этого конкретного user_id базовой валюты UAH
        cursor.execute("""
            SELECT id FROM users_balances 
            WHERE account_id = ? AND currency = 'UAH'
        """, (user_id,))
        
        if not cursor.fetchone():
            # Привязываем стартовый баланс UAH строго к ID владельца счета
            cursor.execute("""
                INSERT INTO users_balances (account_id, currency, balance) 
                VALUES (?, ?, ?)
            """, (user_id, "UAH", 0.0))
            
        conn.commit()
        return user_id