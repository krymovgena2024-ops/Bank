from classes import Bank, BankAccount, setup_test_data
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QTextEdit, QLineEdit, QPushButton, 
                             QListWidget, QComboBox, QMessageBox)
from  database.database import init_db, save_account_to_db, get_db_path
import sys
from GUI_create_account import CreateAccountWindow
from classes import setup_test_data
from GUI_view_profile_data import ViewAccountDetails

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Главное меню")
        self.resize(300, 300)
        self.btn1=QPushButton("Создать счет")
        self.btn2=QPushButton("Посмотреть данные аккаунта")
        self.layout=QVBoxLayout()
        self.layout.addWidget(self.btn1)
        self.layout.addWidget(self.btn2)
        self.win1=None
        self.win2=None
        self.setLayout(self.layout)
        self.btn1.clicked.connect(self.window_one)
        self.btn2.clicked.connect(self.window_two)


    def window_one(self):
        if self.win1 is None:
            self.win1=CreateAccountWindow(setup_test_data())
            self.win1.show()


    def window_two(self):
        if self.win2 is None:
            self.win2=ViewAccountDetails(setup_test_data())
            self.win2.show()


if __name__=="__main__":
    app=QApplication(sys.argv)
    window=MainWindow()
    window.show()
    sys.exit(app.exec_())



    
