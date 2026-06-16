import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QMessageBox)
from PyQt5.QtCore import pyqtSignal
from database.database import get_db_path, init_db
from classes import setup_test_data

class CreateCurrencyAccountWindow(QWidget):
    back_to_menu_requested = pyqtSignal()

    def __init__(self, banks_list):
        super().__init__()
        self.banks = banks_list
        
        self.setWindowTitle("Открыть валютный счет")
        self.resize(320, 360)

        # Раздельные поля ввода ФИО
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя")
        
        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("Фамилия")
        
        self.patronymic_input = QLineEdit()
        self.patronymic_input.setPlaceholderText("Отчество")
        
        # Выбор банка
        self.bank_box = QComboBox()
        for bank in self.banks:
            self.bank_box.addItem(bank.bank_name)
            
        # Выбор валюты
        self.currency_box = QComboBox()
        self.currencies = {
            "USD (Американский доллар)": "USD",
            "EUR (Евро)": "EUR",
            "TRY (Турецкая лира)": "TRY",
            "MDL (Молдавский лей)": "MDL"
        }
        for curr_name in self.currencies.keys():
            self.currency_box.addItem(curr_name)

        self.btn_create = QPushButton("Открыть счет")
        self.btn_back = QPushButton("Назад в главное меню")

        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Владелец аккаунта:"))
        layout.addWidget(self.name_input)
        layout.addWidget(self.surname_input)
        layout.addWidget(self.patronymic_input)
        
        layout.addWidget(QLabel("Выберите банк:"))
        layout.addWidget(self.bank_box)
        
        layout.addWidget(QLabel("Выберите валюту нового счета:"))
        layout.addWidget(self.currency_box)
        
        layout.addWidget(self.btn_create)
        layout.addWidget(self.btn_back)

        self.setLayout(layout)

        self.btn_create.clicked.connect(self.handle_create_account)
        self.btn_back.clicked.connect(self.handle_back)

    def handle_create_account(self):
        name = self.name_input.text().strip()
        surname = self.surname_input.text().strip()
        patronymic = self.patronymic_input.text().strip()
        
        selected_bank_name = self.bank_box.currentText()
        selected_display_curr = self.currency_box.currentText()
        currency_code = self.currencies[selected_display_curr]

        if not all([surname, name, patronymic]):
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните полностью Имя, Фамилию и Отчество!")
            return

        if any(char.isdigit() for char in surname + name + patronymic):
            QMessageBox.warning(self, "Ошибка", "В Имени, Фамилии или Отчестве не должно быть цифр!")
            return

        full_name = f"{name.title()} {surname.title()} {patronymic.title()}"

        active_bank = None
        for bank in self.banks:
            if bank.bank_name == selected_bank_name:
                active_bank = bank
                break

        if active_bank:
            # ТЕПЕРЬ метод внутри класса Bank (classes.py) найдет ID пользователя 
            # именно для выбранного банка, и создаст там счет в выбранной валюте!
            success = active_bank.create_new_score_on_exists_account_with_new_currrency(full_name, currency_code)
            
            if success:
                QMessageBox.information(
                    self, "Успех", 
                    f"В банке {selected_bank_name} для пользователя {full_name} успешно открыт счет в валюте {currency_code}!"
                )
                self.surname_input.clear()
                self.name_input.clear()
                self.patronymic_input.clear()
            else:
                QMessageBox.warning(
                    self, "Ошибка", 
                    f"Не удалось открыть счет. Возможно, у {full_name} в банке {selected_bank_name} уже есть счет в валюте {currency_code} или аккаунт в этом банке еще не создан через меню 'Создать счет'."
                )
        else:
            QMessageBox.warning(self, "Ошибка", "Выбранный банк не найден в системе.")

    def handle_back(self):
        self.back_to_menu_requested.emit()
        self.close()

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    banks_list = setup_test_data()
    window = CreateCurrencyAccountWindow(banks_list)
    window.show()
    sys.exit(app.exec_())