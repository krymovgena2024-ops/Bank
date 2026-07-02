from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QComboBox)
from database.database import get_db_path, init_db
from classes import setup_test_data
import sys
import sqlite3
from PyQt5.QtCore import pyqtSignal


class ViewAccountDetails(QWidget):
    # Создаем сигнал для возврата в главное меню
    back_to_menu_requested = pyqtSignal()
    
    def __init__(self, banks_list):
        super().__init__() 
        self.banks = banks_list
        self.current_sender_id = None 
        self.current_bank_name = None 
        self.setWindowTitle("Узнать данные аккаунта")
        self.resize(340, 500) # Немного увеличим высоту окна под новые элементы
        
        self.account_number = QLineEdit()
        self.account_number.setPlaceholderText("Номер счёта человека которого надо найти.")
        
        self.btn_search = QPushButton("Посмотреть данные аккаунта")
        
        self.account_info = QLabel(f"Данные аккаунта:")
        self.balance_label = QLabel(f"")
        
        self.transfer_line = QLabel("Перевести деньги на счёт:")
        self.to_account_input = QLineEdit()
        self.to_account_input.setPlaceholderText("ID счета получателя")
        self.amount_line = QLineEdit()
        self.amount_line.setPlaceholderText("Сумма перевода")
        
        # === НОВЫЕ ЭЛЕМЕНТЫ ДЛЯ ВЫБОРА ВАЛЮТЫ ===
        available_currencies = ["UAH", "USD", "EUR", "TRY", "MDL"]
        
        self.currency_from_label = QLabel("Какую валюту списать у вас:")
        self.currency_from_select = QComboBox()
        self.currency_from_select.addItems(available_currencies)
        
        self.currency_to_label = QLabel("В какой валюте зачислить получателю:")
        self.currency_to_select = QComboBox()
        self.currency_to_select.addItems(available_currencies)
        # =======================================

        self.btn_transfer = QPushButton("Подтвердить перевод")
        self.btn_back = QPushButton("Назад в главное меню")
        
        # Расширяем список элементов второго экрана
        self.second_screen_elements = [
            self.account_info, self.balance_label, self.transfer_line,
            self.to_account_input, self.amount_line, 
            self.currency_from_label, self.currency_from_select, # Новые поля
            self.currency_to_label, self.currency_to_select,     # Новые поля
            self.btn_transfer
        ]
        
        for el in self.second_screen_elements:
            el.hide()
            
        layout = QVBoxLayout() 

        layout.addWidget(self.account_number)
        layout.addWidget(self.btn_search)

        for el in self.second_screen_elements:
            layout.addWidget(el)
            
        layout.addWidget(self.btn_back) 

        self.setLayout(layout)
        
        self.btn_search.clicked.connect(self.check_database) 
        self.btn_transfer.clicked.connect(self.process_transfer)
        self.btn_back.clicked.connect(self.show_search_fields)

    
    def check_database(self): 
        # 1. Получаем чистый текст из поля ввода QLineEdit
        account_num_text = self.account_number.text().strip()
        
        # Проверяем на наличие букв в строке
        if any(char.isalpha() for char in account_num_text):
            QMessageBox.warning(self, "Ошибка", "В номере счёта не должно быть букв!")
            return
            
        # Проверим на пустоту на всякий случай
        if not account_num_text:
            QMessageBox.warning(self, "Ошибка", "Введите номер счета!")
            return
        
        row = None
        with sqlite3.connect(get_db_path()) as conn:
            cursor = conn.cursor()
            
            # 2. ИСПРАВЛЕНО: Ищем строго по колонке account_number, а не по owner_name
            cursor.execute("SELECT * FROM list_of_accounts WHERE account_number = ?", (account_num_text,))
            row = cursor.fetchone()

        if row:
            # row[0] = id, row[1] = owner_name, row[2] = age, row[3] = bank_name, row[4] = account_number
            self.current_sender_id = row[0]  # ОСТАВЛЯЕМ ID (число 1, 2, 3...) для связи с балансами!
            self.current_bank_name = row[3] 
            self.current_sender_account_number = row[4] # А сюда сохраняем длинный номер счета
            
            # Теперь запрос балансов сработает идеально, так как мы передаем row[0]
            with sqlite3.connect(get_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT currency, balance FROM users_balances 
                    WHERE account_id = ?
                """, (self.current_sender_id,))
                balances_rows = cursor.fetchall()
            
            # Формируем строку со всеми кошельками
            balances_text = ""
            if balances_rows:
                for bal in balances_rows:
                    balances_text += f"• {bal[1]:.2f} {bal[0]}\n"
            else:
                balances_text = "   • Нет открытых счетов\n"

            # Скрываем кнопку поиска
            self.btn_search.hide()
            
            # Выводим полную информацию
            self.balance_label.setText(
                f"Владелец: {row[1]}\n"
                f"Возраст: {row[2]}\n"
                f"ID в системе: {row[0]}\n"
                f"Банк: {row[3]}\n"
                f"Номер счета: {row[4]}\n"  # Добавили вывод 16-значного номера для наглядности
                f"Доступные счета:\n{balances_text}"
            )
            
            # Показываем форму перевода
            for el in self.second_screen_elements:
                el.show()
        else:
            QMessageBox.warning(self, "Ошибка!", "Аккаунт с таким номером не найден")


    def process_transfer(self):
        to_acc = self.to_account_input.text().strip()
        amount_str = self.amount_line.text().strip()
        
        # Получаем выбранные пользователем валюты из выпадающих списков
        what_to_convert = self.currency_from_select.currentText()
        what_to_convert_into = self.currency_to_select.currentText()
        
        try:
            amount = float(amount_str)
            to_acc_id = int(to_acc)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректные числа и убедитесь что все поля заполнены.")
            return
            
        if not to_acc or not amount_str:
            QMessageBox.warning(self, "Ошибка", "Заполните данные для перевода")
            return

        if int(self.current_sender_account_number) == to_acc_id:
            QMessageBox.warning(self, "Ошибка", "Нельзя отправить деньги самому себе.")
            return
            
        active_bank = None
        for bank in self.banks:
            if bank.bank_name == self.current_bank_name:
                active_bank = bank
                break
            
        if active_bank:
            # ИСПРАВЛЕНО: передаем длинный номер счета отправителя вместо внутреннего ID
            success = active_bank.transfer(
                from_acc_num=self.current_sender_account_number, # Передаем 17-значный номер!
                to_acc_num=to_acc_id, 
                amount=amount, 
                what_to_convert=what_to_convert, 
                what_to_convert_into=what_to_convert_into
            )
            
            if success:
                QMessageBox.information(self, "Успех", f"Перевод выполнен. Конвертация: {what_to_convert} -> {what_to_convert_into}\n Комисия {success} {what_to_convert}")
                self.check_database() 
                self.to_account_input.clear()
                self.amount_line.clear()
            else:
                QMessageBox.warning(self, "Ошибка", "Перевод не удался. Проверьте балансы кошельков или ID получателя.")
        else:
            QMessageBox.warning(self, "Ошибка", "Банк отправителя не найден в системе.")
    
    
    def show_search_fields(self):
        # 1. ИСПРАВЛЕНО: Проверяем видимость актуального поля ввода номера счета
        if self.account_number.isVisible():
            # Если оно и так видно, значит пользователь на первом экране и хочет выйти в меню
            self.back_to_menu_requested.emit()
            self.close()
            return

        # Если поля поиска были скрыты (показывался экран перевода), возвращаем начальное состояние
        for el in self.second_screen_elements:
            el.hide()

        # 2. ИСПРАВЛЕНО: Показываем обратно поле ввода номера счета и кнопку поиска
        self.account_number.show()
        self.btn_search.show()

        # 3. ИСПРАВЛЕНО: Очищаем старый ввод в поле номера счета
        self.account_number.clear()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv) 
    banks_list = setup_test_data()
    window = ViewAccountDetails(banks_list)
    window.show()
    sys.exit(app.exec_())