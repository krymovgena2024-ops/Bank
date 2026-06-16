from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
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
        self.current_sender_id = None # здесь хранится ID отправителя
        self.current_bank_name = None # здесь хранится название банка владельца счета
        self.setWindowTitle("Узнать данные аккаунта")
        self.resize(320, 420) # Немного увеличили высоту под раздельные поля ФИО
        
        # Раздельные поля ввода ФИО вместо одного owner_name
        self.surname = QLineEdit()
        self.surname.setPlaceholderText("Фамилия")
        self.name = QLineEdit()
        self.name.setPlaceholderText("Имя")
        self.patronymic = QLineEdit()
        self.patronymic.setPlaceholderText("Отчество")
        
        self.btn_search = QPushButton("Посмотреть данные аккаунта")
        
        # элементы результата (скрыты изначально)
        self.account_info = QLabel(f"Данные аккаунта:")
        self.balance_label = QLabel(f"")
        
        # поля для совершения перевода
        self.transfer_line = QLabel("Перевести деньги со счета:")
        self.to_account_input = QLineEdit()
        self.to_account_input.setPlaceholderText("ID счета получателя")
        self.amount_line = QLineEdit()
        self.amount_line.setPlaceholderText("Сумма перевода")
        self.btn_transfer = QPushButton("Подтвердить перевод")
        
        # Кнопка НАЗАД теперь всегда видима изначально!
        self.btn_back = QPushButton("Назад в главное меню")
        
        # Исходный список скрываемых элементов второго экрана
        self.second_screen_elements = [
            self.account_info, self.balance_label, self.transfer_line,
            self.to_account_input, self.amount_line, self.btn_transfer
        ]
        
        # Скрываем только элементы второго экрана
        for el in self.second_screen_elements:
            el.hide()
            
        layout = QVBoxLayout() 

        # 1. Добавляем раздельные элементы поиска (первый экран)
        layout.addWidget(self.name)
        layout.addWidget(self.surname)
        layout.addWidget(self.patronymic)
        layout.addWidget(self.btn_search)

        # 2. Добавляем скрытые элементы второго экрана (результаты и перевод)
        for el in self.second_screen_elements:
            layout.addWidget(el)
            
        # 3. Добавляем кнопку "Назад" в самый низ, чтобы она была видна всегда
        layout.addWidget(self.btn_back) 

        self.setLayout(layout)
        
        self.btn_search.clicked.connect(self.check_database) 
        self.btn_transfer.clicked.connect(self.process_transfer)
        self.btn_back.clicked.connect(self.show_search_fields)

    
    def check_database(self): 
        # Считываем данные и чистим пробелы
        s_name = self.name.text().strip()
        s_surname = self.surname.text().strip()
        s_patronymic = self.patronymic.text().strip()

        # Проверяем, заполнил ли пользователь все 3 поля
        if not all([s_surname, s_name, s_patronymic]):
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните полностью Фамилию, Имя и Отчество!")
            return

        # Проверяем на наличие цифр в полях ввода
        if any(char.isdigit() for char in s_surname + s_name + s_patronymic):
            QMessageBox.warning(self, "Ошибка", "В Фамилии, Имени или Отчестве не должно быть цифр!")
            return

        # Формируем красивую искомую строку
        search_name = f"{s_surname.title()} {s_name.title()} {s_patronymic.title()}"
        
        with sqlite3.connect(get_db_path()) as conn:
            cursor = conn.cursor()
            
            # Получаем основные данные пользователя
            cursor.execute("SELECT * FROM list_of_accounts WHERE owner_name = ?", (search_name,))
            row = cursor.fetchone()

        if row:
            # row[0] = id, row[1] = owner_name, row[2] = age, row[3] = bank_name
            self.current_sender_id = row[0]  
            self.current_bank_name = row[3] 
            
            # Запрашиваем балансы пользователя из актуальной таблицы users_balances
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
                    balances_text += f"   • {bal[1]} {bal[0]}\n"
            else:
                balances_text = "   • Нет открытых счетов\n"

            # Скрываем все три поля ввода поиска и кнопку поиска
            self.surname.hide()
            self.name.hide()
            self.patronymic.hide()
            self.btn_search.hide()
            
            # Выводим полную информацию
            self.balance_label.setText(
                f"Владелец: {row[1]}\n"
                f"Возраст: {row[2]}\n"
                f"ID счета: {row[0]}\n"
                f"Банк: {row[3]}\n"
                f"Доступные счета:\n{balances_text}"
            )
            
            # Показываем форму перевода
            for el in self.second_screen_elements:
                el.show()
        else:
            QMessageBox.warning(self, "Ошибка!", "Аккаунт не найден")


    def process_transfer(self):
        to_acc = self.to_account_input.text().strip()
        amount_str = self.amount_line.text().strip()
        try:
            amount = float(amount_str)
            to_acc_id = int(to_acc)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректные числа")
            return
            
        if not to_acc or not amount_str:
            QMessageBox.warning(self, "Ошибка", "Заполните данные для перевода")
            return

        if int(self.current_sender_id) == to_acc_id:
            QMessageBox.warning(self, "Ошибка", "Нельзя отправить деньги самому себе.")
            return
            
        active_bank = None
        for bank in self.banks:
            if bank.bank_name == self.current_bank_name:
                active_bank = bank
                break
            
        if active_bank:
            success = active_bank.transfer(self.current_sender_id, to_acc_id, amount, currency="UAH")
            
            if success:
                QMessageBox.information(self, "Успех", "Перевод выполнен")
                self.check_database() # Обновляем экран с балансами
                self.to_account_input.clear()
                self.amount_line.clear()
            else:
                QMessageBox.warning(self, "Ошибка", "Перевод не удался. Проверьте баланс UAH или ID получателя.")
        else:
            QMessageBox.warning(self, "Ошибка", "Банк отправителя не найден в системе.")
    
    
    def show_search_fields(self): 
        # Если поля ввода видны, значит пользователь на первом экране и хочет выйти в меню
        if self.name.isVisible():
            self.back_to_menu_requested.emit()
            self.close()
            return

        # Если поля поиска были скрыты, возвращаем состояние к начальному поиску
        for el in self.second_screen_elements:
            el.hide()
            
        # Показываем все три поля ФИО и кнопку заново
        self.surname.show()
        self.name.show()
        self.patronymic.show()
        self.btn_search.show()
        
        # Очищаем старый ввод
        self.surname.clear()
        self.name.clear()
        self.patronymic.clear()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv) 
    banks_list = setup_test_data()
    window = ViewAccountDetails(banks_list)
    window.show()
    sys.exit(app.exec_())