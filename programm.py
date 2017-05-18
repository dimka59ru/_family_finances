# from PyQt4 import QtGui
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QMainWindow, QApplication, \
    QLabel, QWidget, QAction, qApp
# from mainwindow import Ui_MainWindow
from PyQt5.uic import loadUi
import sqlite3


class Login(QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.setWindowTitle('Login')

        self.text_name = QLineEdit(self)
        self.text_pass = QLineEdit(self)

        self.label_name = QLabel(self)
        self.label_pass = QLabel(self)
        self.label_name.setText('login:')
        self.label_pass.setText('pass:')

        self.button_login = QPushButton('Login', self)

        self.button_login.clicked.connect(self.handle_login)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.label_name)
        layout.addWidget(self.text_name)
        layout.addWidget(self.label_pass)
        layout.addWidget(self.text_pass)
        layout.addWidget(self.button_login)

    ## Проверка логина и пароля
    def handle_login(self):
        if (self.text_name.text() == 'foo' and
            self.text_pass.text() == 'bar'):
            self.accept()
        else:
            QMessageBox.warning(
                self, 'Error', 'Bad user or password')

class Window(QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        try:
            loadUi("resources/window.ui", self)
            self.showMaximized()

            self.about_action.setIcon(QIcon('resources/Help.png'))
            self.about_action.triggered.connect(self.about)

            self.quit_action.setIcon(QIcon('resources/Exit.png'))
            # self.quit_action.setIcon(QIcon(qApp.style().standardIcon(QStyle.SP_DialogCancelButton)))
            self.quit_action.setShortcut('Ctrl+Q')
            self.quit_action.triggered.connect(qApp.quit)

            # Подключение к базе
            conn = sqlite3.connect('family_finances.db')
            # Создание курсора
            self.cur_db = conn.cursor()

            self.read_incomes_table(self.cur_db)



        except FileNotFoundError:
            QMessageBox.warning(
                self, 'Error', ' File form.ui not found!')
        # self.ui = Ui_MainWindow()
        # self.ui.setupUi(self)

    ## Создание вкладки со справочником
    # def new_tab(self):
    #     self.tab = QWidget()
    #     self.tab_widget.addTab(self.tab, "Text Tab")

    def read_incomes_table(self, cur_db):
        import datetime
        print('read incomes table')
        cur_db.execute('SELECT * FROM incomes')
        row = cur_db.fetchone()
        while row is not None:
            print(row)
            date_end = datetime.datetime.fromtimestamp(row[2]).strftime('%Y-%m-%d %H:%M:%S')
            date_add = datetime.datetime.fromtimestamp(row[3]).strftime('%Y-%m-%d %H:%M:%S')
            print(date_end)
            print(date_add)

            row = cur_db.fetchone()



    def about(self):
        QMessageBox.about(self, "О программе",
                          "<strong>Домашняя бухгалтерия</strong>"
                          "<br/>Суворов Дмитрий<br/>"
                          "dimka59ru@gmail.com")





if __name__ == '__main__':

    import sys
    app = QApplication(sys.argv)
    login = Login()

    if login.exec_() == QDialog.Accepted:
        window = Window()
        # window.showMaximized()
        # window.show()
        sys.exit(app.exec_())