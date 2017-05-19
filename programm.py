# from PyQt4 import QtGui
from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QColor
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
        self.setWindowIcon(QIcon('resources/Accounting.png'))

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
            self.setWindowIcon(QIcon('resources/Accounting.png'))
            # self.showMaximized()
            self.show()

            self.about_action.setIcon(QIcon('resources/Help.png'))
            self.about_action.triggered.connect(self.about)

            self.quit_action.setIcon(QIcon('resources/Exit.png'))
            # self.quit_action.setIcon(QIcon(qApp.style().standardIcon(QStyle.SP_DialogCancelButton)))
            self.quit_action.setShortcut('Ctrl+Q')
            self.quit_action.triggered.connect(qApp.quit)

            # Подключение к базе SQLite
            try:
                self.conn = sqlite3.connect('family_finances.db')
            except sqlite3.DatabaseError as err:
                QMessageBox.warning(
                    self, 'Error', '#1 Error db: {}'.format(err))

            # Создание курсора
            self.cur_db = self.conn.cursor()



            # Инициализация таблиц
            self.column_name_income = ["Статья доходов", "Действительна до"]
            self.column_name_costs = ["Статья расходов", "Действительна до"]
            self.column_name_table_records_incomes = ["Дата занесения", "Статья дохода", "Сумма"]
            self.column_name_table_records_costs = ["Дата занесения", "Статья расхода", "Сумма"]
            self.init_table(self.table_incomes, self.column_name_income)
            self.init_table(self.table_costs, self.column_name_costs)
            self.init_table(self.table_records_incomes, self.column_name_table_records_incomes)
            self.init_table(self.table_records_costs, self.column_name_table_records_costs)

            # Получение данных из БД
            self.update_data_in_ui()


            # Нажатие кнопки добавления статьи доходов
            self.button_add_item_income.clicked.connect(self.press_button_add_item_income)
            self.button_add_item_costs.clicked.connect(self.press_button_add_item_costs)

            #  Установим в поле с датой действия дату + год вперед
            self.set_date_in_date_edit(self.date_edit_add_item_income)
            self.set_date_in_date_edit(self.date_edit_add_item_costs)

            self.date_edit_add_item_income.setEnabled(False)
            self.date_edit_add_item_costs.setEnabled(False)

            # Статус времени при отметке чекбокса
            self.checkbox_add_item_income.stateChanged.connect(self.changed_state_date_edit_income)
            self.checkbox_add_item_costs.stateChanged.connect(self.changed_state_date_edit_costs)

            self.get_data_records()


        except FileNotFoundError:
            QMessageBox.warning(
                self, 'Error', ' File form.ui not found!')
            # self.ui = Ui_MainWindow()
            # self.ui.setupUi(self)

    def update_data_in_ui(self):
        # Получим список статей дохода
        self.data_incomes = self.get_data_incomes()
        self.data_costs = self.get_data_costs()

        self.data_records = self.get_data_records()

        # Вывод статей в таблицы
        self.write_in_table(self.data_incomes, self.table_incomes)
        self.write_in_table(self.data_costs, self.table_costs)

        self.write_in_table_records(self.data_records, self.table_records_incomes)

        # Заполнение выпадающих списков статей
        self.write_in_combobox(self.data_incomes, self.combobox_incomes)
        self.write_in_combobox(self.data_costs, self.combobox_costs)



    def set_date_in_date_edit(self, date_edit):
        """ Установит в поле с датой действия дату + год вперед """
        date_edit.setDate(datetime.date.today() + datetime.timedelta(365))

    def changed_state_date_edit_income(self):
        if self.checkbox_add_item_income.isChecked():
            self.date_edit_add_item_income.setEnabled(True)
        else:
            self.date_edit_add_item_income.setEnabled(False)

    def changed_state_date_edit_costs(self):
        if self.checkbox_add_item_costs.isChecked():
            self.date_edit_add_item_costs.setEnabled(True)
        else:
            self.date_edit_add_item_costs.setEnabled(False)

    # Функция при нажатии кнопки добавления статьи доходов
    def press_button_add_item_income(self):
        text = self.line_edit_add_item_income.text()
        text = " ".join(text.split())  # Удалим лишние пробелы

        if self.checkbox_add_item_income.isChecked():
            date = self.get_unix_time(self.date_edit_add_item_income.date().toPyDate())
        else:
            date = 0

        if not text:
            QMessageBox.warning(
                self, 'Error', 'Не заполнено наименование!')
        else:
            try:
                self.add_item_income(text, date)
            except Exception as e:
                print(e)
            else:
                self.update_data_in_ui()

        self.line_edit_add_item_income.clear()

    def press_button_add_item_costs(self):
        text = self.line_edit_add_item_costs.text()
        text = " ".join(text.split())  # Удалим лишние пробелы

        if self.checkbox_add_item_costs.isChecked():
            date = self.get_unix_time(self.date_edit_add_item_costs.date().toPyDate())
        else:
            date = 0

        if not text:
            QMessageBox.warning(
                self, 'Error', 'Не заполнено наименование!')
        else:
            try:
                self.add_item_costs(text, date)
            except Exception as e:
                print(e)
            else:
                self.update_data_in_ui()
        self.line_edit_add_item_costs.clear()

    # Функция добавления статьи доходов в БД
    def add_item_income(self, name, expiration_date):
        try:
            self.cur_db.execute(
                "INSERT INTO incomes (name, expiration_date) VALUES (?, ?)", (name, expiration_date))
        except sqlite3.DatabaseError as err:
            QMessageBox.warning(
                self, 'Error', '#2 Error db: {}'.format(err))
        else:
            self.conn.commit()

    # Функция добавления статьи расходов в БД
    def add_item_costs(self, name, expiration_date):
        try:
            self.cur_db.execute(
                "INSERT INTO costs (name, expiration_date) VALUES (?, ?)", (name, expiration_date))
        except sqlite3.DatabaseError as err:
            QMessageBox.warning(
                self, 'Error', '#3 Error db: {}'.format(err))
        else:
            self.conn.commit()

    # Функция инициализации таблиц
    def init_table(self, table, column_name):
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnCount(len(column_name))  # Устанавливаем количество столбцов
        table.setHorizontalHeaderLabels(column_name)  # Именуем столбцы таблицы
        table.verticalHeader().setDefaultSectionSize(22)  # Устанавливаем высоту строк
        table.setSelectionBehavior(QAbstractItemView.SelectRows)  # Выделяем только строки
        table.setSelectionMode(QAbstractItemView.SingleSelection)  # Выделяем только одну строку
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Запрет редактирования таблицы

    def get_data_incomes(self):
        try:
            self.cur_db.execute('SELECT * FROM incomes')
            return self.cur_db.fetchall()
        except sqlite3.DatabaseError as err:
            QMessageBox.warning(
                self, 'Error', '#4 Error db: {}'.format(err))

    def get_data_costs(self):
        try:
            self.cur_db.execute('SELECT * FROM costs')
            return self.cur_db.fetchall()
        except sqlite3.DatabaseError as err:
            QMessageBox.warning(
                self, 'Error', '#5 Error db: {}'.format(err))

    def get_data_records(self):
        try:
            self.cur_db.execute('SELECT * FROM financial_records')
            return self.cur_db.fetchall()
            # print(self.cur_db.fetchall())
        except sqlite3.DatabaseError as err:
            QMessageBox.warning(
                self, 'Error', '#6 Error db: {}'.format(err))


    # Функция вывода записей в таблице статей доходов/расходов
    def write_in_table(self, data, table):
        table.clearContents()
        table.setRowCount(0)
        for row in data:
            inx = data.index(row)
            table.insertRow(inx)
            table.setItem(inx, 0, QTableWidgetItem(str(row[1])))
            if row[2] == 0:
                table.setItem(inx, 1, QTableWidgetItem("Бессрочно"))
            else:
                table.setItem(inx, 1, QTableWidgetItem(str(self.convert_date(row[2]))))

    def write_in_table_records(self, data, table):
        table.clearContents()
        table.setRowCount(0)
        for row in data:
            inx = data.index(row)
            table.insertRow(inx)
            table.setItem(inx, 0, QTableWidgetItem(str(row[1])))
            table.setItem(inx, 1, QTableWidgetItem(str(row[4])))
            table.setItem(inx, 2, QTableWidgetItem(str(row[3])))


    # Функция вывода записей в комбобоксы
    def write_in_combobox(self, data, combobox):
        combobox.clear()
        for row in data:
            combobox.addItem(str(row[1]))

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
    app.setStyle("fusion")
    p = QPalette
    p = qApp.palette()
    p.setColor(QPalette.Highlight, QColor(77, 98, 120))
    qApp.setPalette(p)
    login = Login()

    if login.exec_() == QDialog.Accepted:
        window = Window()
        # window.showMaximized()
        # window.show()
        sys.exit(app.exec_())
