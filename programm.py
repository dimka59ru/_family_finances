# from PyQt4 import QtGui
from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QMainWindow, QApplication, \
    QLabel, QWidget, QAction, qApp, QAbstractItemView, QTableWidgetItem
# from mainwindow import Ui_MainWindow
from PyQt5.uic import loadUi
import sqlite3
import datetime
import time


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
            # self.showMaximized()
            self.show()

            self.about_action.setIcon(QIcon('resources/Help.png'))
            self.about_action.triggered.connect(self.about)

            self.quit_action.setIcon(QIcon('resources/Exit.png'))
            # self.quit_action.setIcon(QIcon(qApp.style().standardIcon(QStyle.SP_DialogCancelButton)))
            self.quit_action.setShortcut('Ctrl+Q')
            self.quit_action.triggered.connect(qApp.quit)

            # Подключение к базе
            self.conn = sqlite3.connect('family_finances.db')
            # Создание курсора
            self.cur_db = self.conn.cursor()

            # Инициализация таблицы статей доходов
            self.init_table_incomes()

            # Вывод статей дохода в таблицу
            self.get_row_table_incomes()

            # Нажатие кнопки добавления статьи доходов
            self.button_add_item_income.clicked.connect(self.press_button_add_item_income)

            #  Установим в поле с датой действия дату + год вперед
            self.date_edit_add_item_income.setDate(datetime.date.today() + datetime.timedelta(365))
            self.date_edit_add_item_income.setEnabled(False)

            # Статус чекбокса
            self.check_box_add_item_income.stateChanged.connect(self.check_box_add_item_income_state_changed)



        except FileNotFoundError:
            QMessageBox.warning(
                self, 'Error', ' File form.ui not found!')
            # self.ui = Ui_MainWindow()
            # self.ui.setupUi(self)

    def check_box_add_item_income_state_changed(self):
        if self.check_box_add_item_income.isChecked():
            self.date_edit_add_item_income.setEnabled(True)
        else:
            self.date_edit_add_item_income.setEnabled(False)

    # Функция при нажатии кнопки добавления статьи доходов
    def press_button_add_item_income(self):
        item_income = self.line_edit_add_item_income.text()
        item_income = " ".join(item_income.split())  # Удалим лишние пробелы

        if self.check_box_add_item_income.isChecked():
            date = self.get_unix_time(self.date_edit_add_item_income.date().toPyDate())
        else:
            date = 0

        if not item_income:
            QMessageBox.warning(
                self, 'Error', 'Не заполнено наименование!')
        else:
            try:
                self.add_item_income(item_income, date)
            except Exception as e:
                print(e)
            else:
                self.get_row_table_incomes()

        self.line_edit_add_item_income.clear()

    # Функция добавления статьи доходов в БД
    def add_item_income(self, name, expiration_date):
        try:
            self.cur_db.execute(
                "INSERT INTO incomes (name, expiration_date) VALUES ('{}','{}')".format(name, expiration_date))
        except sqlite3.DatabaseError as err:
            QMessageBox.warning(
                self, 'Error', ' Error: {}'.format(err))
        else:
            self.conn.commit()

    # Функция инициализации таблицы статей доходов
    def init_table_incomes(self):
        column_name = ["Статья дохода", "Действительна до"]
        row_count = 3
        self.table_incomes.horizontalHeader().setStretchLastSection(True)
        # self.table_incomes.setRowCount(row_count)  # Устанавливаем количество строк
        self.table_incomes.setColumnCount(len(column_name))  # Устанавливаем количество столбцов
        # self.table_incomes.horizontalHeader().resizeSection(0, 1000)  # Ширина столбцов

        self.table_incomes.setHorizontalHeaderLabels(column_name)  # Именуем столбцы таблицы
        self.table_incomes.verticalHeader().setDefaultSectionSize(22)  # Устанавливаем высоту строк
        self.table_incomes.setSelectionBehavior(QAbstractItemView.SelectRows)  # Выделяем только строки
        self.table_incomes.setSelectionMode(QAbstractItemView.SingleSelection)  # Выделяем только одну строку
        self.table_incomes.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Запрет редактирования таблицы

    # Функция вывода записей в таблице статей доходов
    def get_row_table_incomes(self):
        self.table_incomes.clearContents()
        self.table_incomes.setRowCount(0)

        self.cur_db.execute('SELECT * FROM incomes')
        all_data = self.cur_db.fetchall()
        for row in all_data:
            inx = all_data.index(row)
            self.table_incomes.insertRow(inx)
            self.table_incomes.setItem(inx, 0, QTableWidgetItem(str(row[1])))
            self.table_incomes.setItem(inx, 1, QTableWidgetItem(str(self.convert_date(row[2]))))

    def convert_date(self, unixtime):
        return datetime.datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')

    def get_unix_time(self, date):
        return int(time.mktime(date.timetuple()))

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
