from classes import setup_test_data
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QComboBox, QMessageBox)
from PyQt5.QtCore import pyqtSignal  # ИМПОРТИРУЕМ СИГНАЛЫ
from database.database import init_db, save_account_to_db, get_db_path
import sys
    
class CreateAccountWindow(QWidget): 
    # Создаем сигнал, который будет сообщать главному меню о возврате
    account_created = pyqtSignal()

    def __init__(self, banks):
        super().__init__()
        self.banks = banks

        self.setWindowTitle("Создание банковского счета")
        self.resize(300, 350) # Немного увеличили высоту для новой кнопки
        self.name = QLineEdit() 
        self.surname = QLineEdit() 
        self.patronymic = QLineEdit()
        self.age = QLineEdit()
        self.name.setPlaceholderText("Имя") 
        self.surname.setPlaceholderText("Фамилия")
        self.patronymic.setPlaceholderText("Отчество")
        self.age.setPlaceholderText("Возраст")

        self.account_balance = QLineEdit()
        self.account_balance.setPlaceholderText("Баланс")

        self.bank_box = QComboBox()
        for bank in banks:
            self.bank_box.addItem(bank.bank_name)

        self.btn_create = QPushButton("Создать счет") 
        self.btn_create.clicked.connect(self.create_account) 

        # ДОБАВЛЯЕМ КНОПКУ «НАЗАД»
        self.btn_back = QPushButton("Назад в главное меню")
        self.btn_back.clicked.connect(self.go_back)

        layout = QVBoxLayout() 
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
        layout.addWidget(self.btn_back) # Добавили кнопку назад в разметку

        self.setLayout(layout) 
    
    def create_account(self):
        surname = self.surname.text().strip()
        name = self.name.text().strip()
        patronymic = self.patronymic.text().strip()
        
        # 1. Проверяем заполнение всех полей
        if not all([surname, name, patronymic, self.age.text(), self.account_balance.text()]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
            
        # 2. Проверяем, чтобы в ФИО не закрались цифры
        if any(char.isdigit() for char in surname + name + patronymic):
            QMessageBox.warning(self, "Ошибка", "В Фамилии, Имени или Отчестве не должно быть цифр!")
            return
            
        full_name = f"{name.title()} {surname.title()} {patronymic.title()}"
        bank_name = self.bank_box.currentText()

        try:
            balance = float(self.account_balance.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Баланс должен быть числом")
            return
        try:
            age = int(self.age.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Возраст должен быть числом")
            return

        # 3. НОВАЯ ПРОВЕРКА: Проверяем в БД, нет ли уже у этого человека аккаунта в ЭТОМ ЖЕ банке
        import sqlite3
        try:
            with sqlite3.connect(get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM list_of_accounts 
                    WHERE owner_name = ? AND bank_name = ?
                """, (full_name, bank_name))
                if cursor.fetchone():
                    QMessageBox.warning(
                        self, "Ошибка", 
                        f"Пользователь {full_name} уже зарегистрирован в банке {bank_name}!\n"
                        f"Если хотите открыть счет в другой валюте, используйте окно 'Открыть валютный счет'."
                    )
                    return
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось проверить существование аккаунта: {e}")
            return

        account = None
        for bank in self.banks:
            if bank.bank_name == bank_name:
                account = bank.create_account(full_name, age, balance)
                break 

        if account is None:
            QMessageBox.warning(self, "Ошибка", "Выбранный банк не найден в системе!")
            return 
            
        save_account_to_db(account)
        # db_id по-прежнему нужен системе для связей таблиц, 
        # но пользователю мы теперь показываем настоящий 16-значный номер!
        QMessageBox.information(
            self, "Успех", 
            f"Аккаунт успешно создан!\nНомер счета: {account.account_number}"
        )      
        
        self.name.clear()
        self.surname.clear()
        self.patronymic.clear()
        self.age.clear()
        self.account_balance.clear()

        # Автоматически возвращаемся назад после успешного создания
        self.go_back()

    # Метод для возврата назад
    def go_back(self):
        self.account_created.emit() # Отправляем сигнал главному меню
        self.close() # Закрываем текущее окно создания аккаунта


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv) 
    banks_list = setup_test_data()
    window = CreateAccountWindow(banks_list) 
    window.show() 
    sys.exit(app.exec_())