import datetime
import sqlite3
import os, random
from database.database import get_db_path

class BankAccount:
    def __init__(self, account_number, owner_name, age, bank_name, initial_balance=0.0):
        self.account_number = account_number
        self.owner_name = owner_name
        self.age = age
        self.bank_name = bank_name
        self.account_number = "".join([str(random.randint(0, 9)) for _ in range(17)])


class Bank:
    def __init__(self, bank_name):
        self.bank_name = bank_name.title()


    def transfer(self, from_acc_num, to_acc_num, amount):
        # поиск счетов
        sender = self.find_account(from_acc_num)
        receiver = self.find_account(to_acc_num)
        # проверки на существование счетов
        if sender is None:
            print(f"Ошибка: Счет отправителя '{from_acc_num}' не найден.")
            return False
        if receiver is None:
            print(f"Ошибка: Счет получателя '{to_acc_num}' не найден.")
            return False
        # расчет комиссии и общей суммы
        comission = 0
        if sender.bank_name != receiver.bank_name:
            comission = amount * 0.01
        total_amount = amount + comission
        # проверка баланса
        if sender.balance < total_amount:
            print(f"Недостаточно средств. Требуется: {total_amount}, на счету: {sender.balance}")
            return False
        # выполнение перевода
        sender.balance -= total_amount
        receiver.balance += amount
        # обновление в базе данных
        try:
            db_path = get_db_path()
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                # обновляем баланс отправителя (списываем total_amount с учетом комиссии)
                cursor.execute("""
                UPDATE list_of_accounts 
                SET balance = ? 
                WHERE id = ?
            """, (sender.balance, from_acc_num))
                # обновляем баланс получателя (зачисляем сумму amount)
                cursor.execute("""
                UPDATE list_of_accounts 
                SET balance = ? 
                WHERE id = ?
            """, (receiver.balance, to_acc_num))
                # фиксация изменений в файле базы даных
                conn.commit()
                print(f"Перевод выполнен успешно. Списано: {total_amount} UAH (Комиссия: {comission})")
                return True
        except Exception as e:
            # если произошла ошибка базы данных, возвращаем балансы объектов в исходное состояние
            sender.balance += total_amount
            receiver.balance -= amount
            print(f"Ошибка базы данных при переводе: {e}")
            return False
    
    
    def create_account(self, owner_name, age, balance):
        # Просто создаем объект в памяти и возвращаем его в GUI
        return BankAccount(
            account_number=None,  # ID пока нет, его присвоит GUI после сохранения
            owner_name=owner_name,
            age=age,
            bank_name=self.bank_name,
            initial_balance=balance  # Передаем введенный баланс сюда
        )
    

    def find_account(self, account_number):
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # ищем строку по account_number
        cursor.execute("SELECT * FROM list_of_accounts WHERE id = ?", (account_number,))
        row = cursor.fetchone()
        if row:
        # Если запись найдена, создаем объект BankAccount
            found_account = BankAccount(
            account_number=row[0],
            owner_name=row[1],
            age=row[2],
            bank_name=row[3])
            return found_account
        return None


    def create_new_score_on_exists_account_with_new_currrency(self, owner_name, new_currency):
        db_path = get_db_path()
        search_name = owner_name.strip().title()
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # 1. Находим числовой id пользователя по ФИО И НАЗВАНИЮ БАНКА (self.bank_name)
                cursor.execute("""
                    SELECT id FROM list_of_accounts 
                    WHERE owner_name = ? AND bank_name = ?
                """, (search_name, self.bank_name))
                row = cursor.fetchone()
                
                if not row:
                    print(f"Ошибка: Пользователь '{search_name}' не найден в банке {self.bank_name}!")
                    return False
                
                account_id = row[0] # Теперь мы гарантированно получили ID нужного банка (например, 2 для Monobank)
                
                # 2. Проверяем, нет ли у этого конкретного ID счета в этой валюте
                cursor.execute("""
                    SELECT id FROM users_balances 
                    WHERE account_id = ? AND currency = ?
                """, (account_id, new_currency.upper()))
                
                if cursor.fetchone():
                    print(f"У аккаунта {search_name} в банке {self.bank_name} уже есть счет в валюте {new_currency.upper()}!")
                    return False
                
                # 3. Создаем новый валютный кошелек со стартовым балансом 0.0
                cursor.execute("""
                    INSERT INTO users_balances (account_id, currency, balance)
                    VALUES (?, ?, ?)
                """, (account_id, new_currency.upper(), 0.0))
                
                conn.commit()
                print(f"Успешно открыт счет в валюте {new_currency.upper()} для {search_name} в {self.bank_name}.")
                return True
                
        except Exception as e:
            print(f"Ошибка при создании валютного счета: {e}")
            return False


# функция создания начальных банков и счетов, чтобы счета, созданные здесь, были доступны в файле GUI_create_account
def setup_test_data():
    privat_bank = Bank("Privat Bank")
    monobank = Bank("Monobank")
    abank = Bank("А-Bank")
    sense_bank = Bank("Sense Bank")
    return [privat_bank, monobank, abank, sense_bank]