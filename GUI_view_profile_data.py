from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from database.database import get_db_path, init_db
from classes import setup_test_data
import sys
import sqlite3

class ViewAccountDetails(QWidget):
    def __init__(self, banks_list):
        super().__init__() 
        self.banks = banks_list
        self.current_sender_id = None # здесь хранится ID отправителя
        self.current_bank_name = None # здесь хранится имя банка владельца счета
        self.setWindowTitle("Узнать данные аккаунта")
        self.resize(300, 300)
        self.owner_name = QLineEdit()
        self.owner_name.setPlaceholderText("Имя")
        self.btn_search = QPushButton("Посмотреть данные аккаунта")
        
        
        # элементы результата (скрыты изначально)
        self.account_info=QLabel(f"Данные аккаунта:")
        self.balance_label=QLabel(f"")
        # поля для совершения перевода
        self.transfer_line = QLabel("Перевести деньги со счета:")
        self.to_account_input = QLineEdit()
        self.to_account_input.setPlaceholderText("ID счета получателя")
        self.amount_line = QLineEdit()
        self.amount_line.setPlaceholderText("Сумма перевода")
        self.btn_transfer = QPushButton("Подтвердить перевод")
        self.btn_back = QPushButton("Назад к поиску")
        self.second_screen_elements = [
            self.account_info, self.balance_label, self.transfer_line,
            self.to_account_input, self.amount_line, self.btn_transfer, self.btn_back]
        for el in self.second_screen_elements:
            el.hide()
        layout = QVBoxLayout() # определение вертикального менеджера компоновки
        
        # добавляем элементы первого экрана
        layout.addWidget(self.owner_name)
        layout.addWidget(self.btn_search)
        # добавляем скрытые элементы 
        for el in self.second_screen_elements:
            layout.addWidget(el)
            
        self.setLayout(layout) # соединяет окно приложения с логикой размещения элементов внутри него.
        self.btn_search.clicked.connect(self.check_database) # привязка кнопки к методу
        self.btn_transfer.clicked.connect(self.process_transfer)
        self.btn_back.clicked.connect(self.show_search_fields)

    
    def check_database(self): 
        search_name = self.owner_name.text().strip().title()
        with sqlite3.connect(get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM list_of_accounts WHERE owner_name = ?", (search_name,))
            row = cursor.fetchone()

        if row:
            # сохраняем ID найденного счета
            self.current_sender_id = row[0]  
            self.current_bank_name = row[4]
            # cкрываем поиск
            self.owner_name.hide()
            self.btn_search.hide()
            # показываем результат и форму перевода
            self.balance_label.setText(f"Владелец: {row[1]}\nID счета: {row[0]}\nБаланс: {row[3]} UAH\nБанк: {row[4]}")
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
        if int(self.current_sender_id)==to_acc:
            QMessageBox.warning(self, "Ошибка", "Нельзя отправить деньги самому себе.")
            return
        if not to_acc or not amount_str:
            QMessageBox.warning(self, "Ошибка", "Заполните данные для перевода")
            return
        
        
        active_bank = None
        for bank in self.banks:
            if bank.bank_name == self.current_bank_name:
                active_bank = bank
                break
            
        if active_bank:
            # вызываем метод перевода 
            active_bank.transfer(self.current_sender_id, to_acc_id, amount)
            QMessageBox.information(self, "Успех", "Перевод выполнен")
            # обновляем данные на экране (делаем повторный поиск, чтобы обновить баланс)
            self.check_database() 
            self.to_account_input.clear()
            self.amount_line.clear()
        else:
            QMessageBox.warning(self, "Ошибка", "Перевод не удался. Проверьте баланс и ID получателя.")
    
    
    def show_search_fields(self): # возвращает обратно к окну поиска
        # cкрываем информацию
        self.account_info.hide()
        self.balance_label.hide()
        self.btn_back.hide()
        # показываем поиск обратно
        self.owner_name.show()
        self.btn_search.show()
        self.owner_name.clear()


if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv) # cоздание объекта приложения
    banks_list = setup_test_data()
    window = ViewAccountDetails(banks_list)
    window.show()
    sys.exit(app.exec_()) # закрытие программы, если пользователь нажмет крестик


