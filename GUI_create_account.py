from classes import Bank, BankAccount, setup_test_data
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QComboBox, QMessageBox)
from  database.database import init_db, save_account_to_db, get_db_path
import sys
    
class CreateAccountWindow(QWidget): # дает классу функции, чтобы он функционировал как элемент графического интерфейса
    def __init__(self, banks):
        super().__init__()
        self.banks = banks

        self.setWindowTitle("Создание банковского счета")
        self.resize(300, 300)
        self.name = QLineEdit() # поле для ввода одной строки текста
        self.surname = QLineEdit() 
        self.patronymic = QLineEdit()
        self.age = QLineEdit()
        self.name.setPlaceholderText("Имя") # создание подсказки для поля ввода
        self.surname.setPlaceholderText("Фамилия")
        self.patronymic.setPlaceholderText("Отчество")
        self.age.setPlaceholderText("Возраст")

        self.account_balance = QLineEdit()
        self.account_balance.setPlaceholderText("Баланс")

        self.bank_box = QComboBox()
        for bank in banks:
            self.bank_box.addItem(bank.bank_name)

        self.btn_create = QPushButton("Создать счет") 
        self.btn_create.clicked.connect(self.create_account) # привязка кнопки к методу

        layout = QVBoxLayout() # определение вертикального менеджера компоновки
        layout.addWidget(QLabel("Владелец"))

        layout.addWidget(self.name)
        layout.addWidget(self.surname)
        layout.addWidget(self.patronymic)
        layout.addWidget(self.age)
        layout.addWidget(QLabel("Баланс"))
        layout.addWidget(self.account_balance)
        layout.addWidget(QLabel("Банк"))
        layout.addWidget(self.bank_box)
        layout.addWidget(self.btn_create)

        self.setLayout(layout) # соединяет окно приложения с логикой размещения элементов внутри него.
    
    def create_account(self):
        surname = self.surname.text().strip()
        name = self.name.text().strip()
        patronymic = self.patronymic.text().strip()
        if not all([surname, name, patronymic, self.age.text(), self.account_balance.text()]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
        full_name = f"{surname.title()} {name.title()} {patronymic.title()}"
        bank_name = self.bank_box.currentText()

        try:
            balance=float(self.account_balance.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Баланс должен быть числом")
            return
        try:
            age=int(self.age.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Возраст должен быть числом")
            return
        account = None
        for bank in self.banks:
            if bank.bank_name == bank_name:
                account = bank.create_account(full_name, age, balance)
                break # Нашли банк — выходим из цикла
        # Если пробежали весь цикл, но объект аккаунта так и не создался
        if account is None:
            QMessageBox.warning(self, "Ошибка", "Выбранный банк не найден в системе!")
            return # Останавливаем функцию, не давая программе упасть ниже
        db_id = save_account_to_db(account)
        account.account_number = db_id
        QMessageBox.information(self, "Успех", f"Счет {account.account_number} создан!") # появляется после нажатия на кнопку "создать счет"     
        self.name.clear()
        self.surname.clear()
        self.patronymic.clear()
        self.age.clear()
        self.account_balance.clear()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv) # cоздание объекта приложения
    # получаем банки с уже вписанными счетами из первого файла
    banks_list = setup_test_data()
    window = CreateAccountWindow(banks_list) # добавление списка банков
    window.show() # показ окна на экране
    sys.exit(app.exec_()) # закрытие программы, если пользователь нажмет крестик

