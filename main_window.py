from classes import Bank, BankAccount, setup_test_data
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QTextEdit, QLineEdit, QPushButton, 
                             QListWidget, QComboBox, QMessageBox)
from  database.database import init_db, save_account_to_db, get_db_path
import sys
from GUI_create_account import CreateAccountWindow
from classes import setup_test_data
from GUI_view_profile_data import ViewAccountDetails
from GUI_create_currency_account import CreateCurrencyAccountWindow


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное меню")
        self.resize(300, 300)
        self.btn1=QPushButton("Создать счет в Украинской гривне")
        self.btn2=QPushButton("Посмотреть данные аккаунта")
        self.layout=QVBoxLayout()
        self.layout.addWidget(self.btn1)
        self.layout.addWidget(self.btn2)
        self.win1=None
        self.win2=None
        self.setLayout(self.layout)
        self.btn1.clicked.connect(self.window_one)
        self.btn2.clicked.connect(self.window_two)
        self.btn3 = QPushButton("Создать счет в другой валюте")
        self.layout.addWidget(self.btn3) # Добавляем кнопку в твой layout

        self.win3 = None # Заготовка под новое окно

        # Привязываем нажатие кнопки к методу открытия окна
        self.btn3.clicked.connect(self.window_three)


    def window_one(self):
        if self.win1 is None:
            self.win1 = CreateAccountWindow(setup_test_data())
            # Подключаем наш сигнал к восстановлению главного меню:
            self.win1.account_created.connect(self.show)
            
        self.win1.show()
        self.hide() # Прячем главное меню, чтобы на экране осталась только форма создания


    def window_two(self):
        if self.win2 is None:
            self.win2 = ViewAccountDetails(setup_test_data())
            # Подключаем сигнал кнопки "Назад" к показу Главного меню:
            self.win2.back_to_menu_requested.connect(self.show)
            
        self.win2.show()
        self.hide() # Прячем главное меню


    def window_three(self):
        if self.win3 is None:
            self.win3 = CreateCurrencyAccountWindow(setup_test_data())
            # Подключаем сигнал кнопки "Назад" к восстановлению Главного меню
            self.win3.back_to_menu_requested.connect(self.show)

        self.win3.show()
        self.hide() # Прячем главное меню


if __name__=="__main__":
    app=QApplication(sys.argv)
    window=MainWindow()
    window.show()
    sys.exit(app.exec_())



    
