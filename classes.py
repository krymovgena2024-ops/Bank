import datetime
import sqlite3
import os
from database.database import get_db_path

class BankAccount:
    def __init__(self, account_number, owner_name, age, balance, bank_name):
        self.account_number = account_number
        self.owner_name = owner_name
        self.age = age
        self.balance = balance
        self.bank_name = bank_name
        self.account_history = [] # личный журнал транзакций
    
    def __repr__(self):
        # строка, которая должна выводится при печати списка счетов конкретного банка
        return f"(Owner: {self.owner_name}, Account number: {self.account_number}, Balance: {self.balance} UAH)"
    
    # def deposit (self, amount):
    #     self.balance += amount

    # def withdraw(self, suma):
    #     if self.balance >= suma:
    #         self.balance -= suma
    #         return True
    #     return False
    
    # def transfer(self, from_acc_num, to_acc_num, amount):
    #     comision = 0
    #     #якщо банк той самий — переказ без комісії
    #     if self.bank_name != from_acc_num.bank_name:
    #         comision = amount*0.01
    #     amount += comision
    #     sender = from_acc_num
    #     receiver = to_acc_num
    #     if sender.balance < amount: # проверяем баланс
    #         return False
    #     sender.balance -= amount # выполняем перевод
    #     receiver.balance += amount
    #     # функция вернет True, если общая сумма не превышает сумму на счете
    #     return True

class Transaction:
    def __init__(self, from_account_number, to_account_number, amount, comission, timestamp):
        self.from_acc = from_account_number
        self.to_acc = to_account_number
        self.amount = amount
        self.comission = comission
        self.timestamp = timestamp

    def __repr__(self):
        # делаем читабельное представление для журнала истории транзакций
        return f"Transaction(From: {self.from_acc} -> To: {self.to_acc}, Amount: {self.amount} UAH, Comission: {self.comission} UAH, Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
    

class Bank:
    bank_register = {} # Центральный регистр. Ключ = название банка, значение = список счетов
    #_next_account_number = 100 # используем атрибут класса для генерации уникальных номеров счетов
    def __init__(self, bank_name):
        self.bank_name = bank_name.title()
        #self.list_accounts = []
        #self.transaction_log = []
        # Автоматическая регистрация нового экземпляра банка. Когда создается monobank = Bank("monobank"), объект monobank автоматически попадает в Bank.bank_register
        #Bank.bank_register[bank_name] = self
    
    def __repr__(self):
        # возвращаем название банка и список счетов
        num_accounts = self.list_accounts
        return f"Bank({self.bank_name}, Accounts: {num_accounts})"

    def log_transaction(self, from_acc_num, to_acc_num, amount, comission):
        # создаем новый объект Transaction
        new_transaction = Transaction(
            from_account_number = from_acc_num,
            to_account_number = to_acc_num,
            amount = amount,
            comission = comission,
            timestamp = datetime.datetime.now()) # фиксируем текущее время
        # добавляем его в журнал
        self.transaction_log.append(new_transaction)
        return new_transaction


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
    
    
    def create_account(self, owner, age, initial_balance):
        # cоздаем экземпляр BankAccount, передавая все 4 аргумента
        new_account = BankAccount( 
            account_number=None, # теперь объект знает свой ID из базы
            owner_name=owner, 
            age=age,
            balance=initial_balance, 
            bank_name=self.bank_name)
        return new_account
    
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
            balance=row[3],
            bank_name=row[4])
            return found_account
        return None
        
    
    def total_assets(self):
        # используем встроенную функцию sum() с генераторным выражением:
        # проходимся по каждому 'account' в self.list_accounts
        # для каждого счета берем его account.balance
        # функция sum() добавляет эти значения
        total_assets = sum(account.balance for account in self.list_accounts)
        return total_assets

# функция создания начальных банков и счетов, чтобы счета, созданные здесь, были доступны в файле GUI_create_account
def setup_test_data():
    privat_bank = Bank("Privat Bank")
    monobank = Bank("Monobank")
    return [privat_bank, monobank]
    
    # этот блок сработает, только если запустить файл напрямую
if __name__ == "__main__":
    banks = setup_test_data()
#monobank.transfer(andrey_account.account_number, pavel_account.account_number, 500)
#monobank.transfer(viktor_account.account_number, anna_account.account_number, 400)
#privat_bank.transfer(oleg_account.account_number, viktor_account.account_number, 400)
#privat_bank.transfer(anna_account.account_number, pavel_account.account_number, 700)
#print(monobank.total_assets())
#print(privat_bank.total_assets())
#print(andrey_account.balance)
#print(monobank.transaction_log)
#print(privat_bank.transaction_log)
#print(monobank.list_accounts)


