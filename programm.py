import hashlib
import os

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QMainWindow, QApplication,
                             QLabel, qApp, QAbstractItemView, QTableWidgetItem, QMenu, QFileDialog)

from PyQt5.uic import loadUi
import sqlite3
import datetime
import time
import xlsxwriter


class CreateUser(QDialog):
    def __init__(self, db_file, parent=None):
        super(CreateUser, self).__init__(parent)
        self.setWindowTitle('Create User')
        self.setWindowIcon(QtGui.QIcon('resources/Accounting.png'))

        self.text_name = QLineEdit(self)
        self.text_pass = QLineEdit(self)

        self.label_name = QLabel(self)
        self.label_pass = QLabel(self)
        self.label_name.setText('login:')
        self.label_pass.setText('pass:')

        self.button_login = QPushButton('Create', self)

        self.button_login.clicked.connect(self.create_user)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label_name)
        layout.addWidget(self.text_name)
        layout.addWidget(self.label_pass)
        layout.addWidget(self.text_pass)
        layout.addWidget(self.button_login)

        # Подключение к базе SQLite
        try:
            self.conn = sqlite3.connect(db_file)
            self.cur_db = self.conn.cursor()
        except sqlite3.DatabaseError as err:
            print(err)

    def create_user(self):
        try:
            self.cur_db.execute(
                "INSERT INTO users (name, pass) VALUES (?, ?)", (
                    self.text_name.text(), self.computeMD5hash(self.text_pass.text())))
        except sqlite3.DatabaseError as err:
            print(err)
        else:
            self.conn.commit()

        self.cur_db.close()
        self.conn.close()
        self.accept()

    def computeMD5hash(self, string):
        m = hashlib.md5()
        m.update(string.encode('utf-8'))
        return m.hexdigest()


class Login(QDialog):
    def __init__(self, db_file, parent=None):
        super(Login, self).__init__(parent)
        self.setWindowTitle('Login')
        self.setWindowIcon(QtGui.QIcon('resources/Accounting.png'))

        self.text_name = QLineEdit(self)
        self.text_pass = QLineEdit(self)
        self.text_pass.setEchoMode(QLineEdit.Password)

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

        # Подключение к базе SQLite
        try:
            self.conn = sqlite3.connect(db_file)
            self.cur_db = self.conn.cursor()
        except sqlite3.DatabaseError as err:
            print(err)

        self.login, self.password = self.get_user()

    ## Проверка логина и пароля
    def handle_login(self):
        if (self.text_name.text() == self.login and
                    self.computeMD5hash(self.text_pass.text()) == self.password):

            self.cur_db.close()
            self.conn.close()
            self.accept()
        else:
            QMessageBox.warning(
                self, 'Error', 'Bad user or password')

    def get_user(self):
        try:
            self.cur_db.execute('SELECT * FROM users')
            return self.cur_db.fetchone()
        except sqlite3.DatabaseError as err:
            print(err)

    def computeMD5hash(self, string):
        m = hashlib.md5()
        m.update(string.encode('utf-8'))
        return m.hexdigest()


class Window(QMainWindow):
    def __init__(self, db_file, parent=None):
        super(Window, self).__init__(parent)

        try:
            loadUi("resources/window.ui", self)
            self.setWindowIcon(QtGui.QIcon('resources/Accounting.png'))
            # self.showMaximized()
            self.show()

            self.about_action.setIcon(QtGui.QIcon('resources/Help.png'))
            self.about_action.triggered.connect(self.about)

            self.quit_action.setIcon(QtGui.QIcon('resources/Exit.png'))
            # self.quit_action.setIcon(QIcon(qApp.style().standardIcon(QStyle.SP_DialogCancelButton)))
            self.quit_action.setShortcut('Ctrl+Q')
            self.quit_action.triggered.connect(qApp.quit)

            self.save_action.setIcon(QtGui.QIcon('resources/Save.png'))
            self.save_action.setShortcut('Ctrl+S')
            self.save_action.triggered.connect(self.save_report)

            # Фильтр для вывода записей по умолчанию
            self.filter_date = [self.utc_date_to_unix_time(datetime.date.today() + datetime.timedelta(1)),
                                self.utc_date_to_unix_time(datetime.date.today() - datetime.timedelta(30))]

            self.date_edit_start.setDate(datetime.date.today() - datetime.timedelta(30))
            self.date_edit_end.setDate(datetime.date.today())

            self.button_filter.clicked.connect(self.press_button_filter)

            # Подключение к базе SQLite
            self.db_file = db_file
            try:
                self.conn = sqlite3.connect(self.db_file)
            except sqlite3.DatabaseError as err:
                QMessageBox.warning(
                    self, 'Error', '#1 Error db: {}'.format(err))

            # Создание курсора
            self.cur_db = self.conn.cursor()
            # self.init_db()

            # Инициализация таблиц
            self.column_name_income = ["Статья доходов", "Действительна до"]
            self.column_name_costs = ["Статья расходов", "Действительна до"]
            self.column_name_table_records = ["Дата занесения", "Статья", "Сумма"]
            # self.column_name_table_records_costs = ["Дата занесения", "Статья расхода", "Сумма"]
            self.init_table(self.table_incomes, self.column_name_income)
            self.init_table(self.table_costs, self.column_name_costs)
            self.init_table(self.table_records, self.column_name_table_records)
            # self.init_table(self.table_records_costs, self.column_name_table_records_costs)

            # Обновление информации в окне
            self.update_data_in_ui()

            # Нажатие кнопки добавления статьи доходов
            self.button_add_item_income.clicked.connect(self.press_button_add_item_income)
            self.button_add_item_costs.clicked.connect(self.press_button_add_item_costs)

            self.button_add_income.clicked.connect(self.press_button_add_income)
            self.button_add_cost.clicked.connect(self.press_button_add_cost)

            #  Установим в поле с датой действия дату + год вперед
            self.set_date_in_date_edit(self.date_edit_add_item_income)
            self.set_date_in_date_edit(self.date_edit_add_item_costs)

            self.date_edit_add_item_income.setEnabled(False)
            self.date_edit_add_item_costs.setEnabled(False)

            # Статус времени при отметке чекбокса
            self.checkbox_add_item_income.stateChanged.connect(self.changed_state_date_edit_income)
            self.checkbox_add_item_costs.stateChanged.connect(self.changed_state_date_edit_costs)

            # self.get_data_records()

            validator = QtGui.QDoubleValidator(0.00, 999999.99, 2)
            validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
            self.line_sum_incomes.setValidator(validator)
            self.line_sum_costs.setValidator(validator)

            # self.setContextMenuPolicy(Qt.ActionsContextMenu)
            self.table_records.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table_records.customContextMenuRequested.connect(self.open_menu)


        except FileNotFoundError:
            QMessageBox.warning(
                self, 'Error', ' File form.ui not found!')
            # self.ui = Ui_MainWindow()
            # self.ui.setupUi(self)

    def save_report(self):

        try:
            options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
            directory = QFileDialog.getExistingDirectory(self, "", "", options=options)

            all = self.sum_all_data()

            if directory:

                workbook = xlsxwriter.Workbook('{}/report_{}.xlsx'.format(
                    directory, datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
                worksheet = workbook.add_worksheet()
                bold = workbook.add_format({'bold': True, 'bg_color': '#CCCCCC', 'border': 1})
                red = workbook.add_format({'bg_color': '#FFC7CE', 'border': 1})
                green = workbook.add_format({'bg_color': '#e5fbe5', 'border': 1})

                worksheet.write(0, 1, "Сводный отчет за период")

                worksheet.set_column('B:E', 25)

                worksheet.write('B2', self.column_name_table_records[0], bold)
                worksheet.write('C2', self.column_name_table_records[1], bold)
                worksheet.write('D2', self.column_name_table_records[2], bold)

                i = 2
                for row in all:
                    bgcolor = green if row[0] == 1 else red

                    if row[0] == 1:
                        for row2 in self.data_incomes:
                            if row[1][3] == row2[0]:
                                worksheet.write(i, 2, row2[1], bgcolor)  # Статья

                    elif row[0] == 2:
                        for row2 in self.data_costs:
                            if row[1][3] == row2[0]:
                                worksheet.write(i, 2, row2[1], bgcolor)  # Статья

                    worksheet.write(i, 1, self.unix_time_to_datetime_utc(row[1][1]), bgcolor)  # Дата

                    worksheet.write_number(i, 3, float(str(row[1][2]).replace(",", ".")), bgcolor)  # Сумма
                    i += 1

                workbook.close()


        except Exception as err:
            QMessageBox.warning(
                self, 'Error', ' Error save: {}'.format(err))

    def press_button_filter(self):
        date_start = self.utc_date_to_unix_time(self.date_edit_start.date().toPyDate())
        date_end = self.utc_date_to_unix_time(self.date_edit_end.date().toPyDate() + datetime.timedelta(1))
        self.filter_date = [date_end, date_start]
        self.update_data_in_ui()

    def open_menu(self, position):
        indexes = self.table_records.selectionModel().selectedRows()
        if indexes:
            row = indexes[0].row()

            menu = QMenu(self)
            quitAction = menu.addAction("Удалить")
            action = menu.exec_(self.table_records.viewport().mapToGlobal(position))

            if action == quitAction:
                date_time = self.table_records.item(row, 0).text()
                unixtime = self.utc_datetime_to_unix_time(datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S'))
                item = self.table_records.item(row, 1).text()
                summ = self.table_records.item(row, 2).text()

                flag = True
                for row in self.data_incomes:
                    if item == row[1]:
                        flag = False

                try:
                    if flag:
                        self.cur_db.execute(
                            "UPDATE costs_records SET del=? WHERE datetime=? AND sum=?", (
                                1, unixtime, summ
                            ))
                    else:
                        self.cur_db.execute(
                            "UPDATE income_records SET del=? WHERE datetime=? AND sum=?", (
                                1, unixtime, summ
                            ))
                except sqlite3.DatabaseError as err:
                    QMessageBox.warning(
                        self, 'Error', '#9 Error db: {}'.format(err))
                else:
                    self.conn.commit()
                    self.update_data_in_ui()

    def update_data_in_ui(self):
        # Получим список статей дохода
        self.data_incomes = self.get_data_incomes()
        self.data_costs = self.get_data_costs()
        # self.all_data = self.sum_all_data(self.data_incomes, self.data_costs)

        self.income_records, self.costs_records = self.get_data_records(self.filter_date)

        # Вывод статей в таблицы
        self.write_in_table(self.data_incomes, self.table_incomes)
        self.write_in_table(self.data_costs, self.table_costs)

        self.write_in_table_records(self.table_records)

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
            date = self.utc_date_to_unix_time(self.date_edit_add_item_income.date().toPyDate())
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
            date = self.utc_date_to_unix_time(self.date_edit_add_item_costs.date().toPyDate())
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

    def press_button_add_income(self):

        if not self.line_sum_incomes.text():
            QMessageBox.warning(
                self, 'Error', 'Не заполнена сумма дохода!')
        else:
            datetime_now = self.utc_datetime_to_unix_time(datetime.datetime.now())
            for row in self.data_incomes:
                if row[1] == self.combobox_incomes.currentText():
                    id_item = row[0]
                    self.add_incomes(datetime_now, self.line_sum_incomes.text(), id_item)

        self.update_data_in_ui()
        self.line_sum_incomes.clear()

    def press_button_add_cost(self):

        if not self.line_sum_costs.text():
            QMessageBox.warning(
                self, 'Error', 'Не заполнена сумма расхода!')
        else:
            datetime_now = self.utc_datetime_to_unix_time(datetime.datetime.now())
            for row in self.data_costs:
                if row[1] == self.combobox_costs.currentText():
                    id_item = row[0]
                    self.add_costs(datetime_now, self.line_sum_costs.text(), id_item)

        self.update_data_in_ui()
        self.line_sum_costs.clear()

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

    # Функция добавления доходов
    def add_incomes(self, datetime_now, summ, id_item):
        try:
            self.cur_db.execute(
                "INSERT INTO income_records (datetime, sum, id_item) VALUES (?, ?, ?)",
                (datetime_now, summ, id_item))
        except sqlite3.DatabaseError as err:
            QMessageBox.warning(
                self, 'Error', '#7 Error db: {}'.format(err))
        else:
            self.conn.commit()

    # Функция добавления расходов
    def add_costs(self, datetime_now, summ, id_item):
        try:
            self.cur_db.execute(
                "INSERT INTO costs_records (datetime, sum, id_item) VALUES (?, ?, ?)",
                (datetime_now, summ, id_item))
        except sqlite3.DatabaseError as err:
            QMessageBox.warning(
                self, 'Error', '#8 Error db: {}'.format(err))
        else:
            self.conn.commit()

    # Функция инициализации таблиц
    def init_table(self, table, column_name):
        table.horizontalHeader().setStretchLastSection(True)
        # table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        table.setColumnCount(len(column_name))  # Устанавливаем количество столбцов
        table.setHorizontalHeaderLabels(column_name)  # Именуем столбцы таблицы
        table.verticalHeader().setDefaultSectionSize(22)  # Устанавливаем высоту строк
        table.setSelectionBehavior(QAbstractItemView.SelectRows)  # Выделяем только строки
        table.setSelectionMode(QAbstractItemView.SingleSelection)  # Выделяем только одну строку
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Запрет редактирования таблицы


        # table.setAlternatingRowColors(True)
        # table.setStyleSheet("alternate-background-color: yellow; background-color: red;");

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

    def get_data_records(self, filter_date):
        try:
            self.cur_db.execute('SELECT * FROM income_records WHERE del=0 and datetime <= ? and datetime >= ?',
                                (filter_date[0], filter_date[1]))
            income_records = self.cur_db.fetchall()

            self.cur_db.execute('SELECT * FROM costs_records WHERE del=0 and datetime <= ? and datetime >= ?',
                                (filter_date[0], filter_date[1]))
            costs_records = self.cur_db.fetchall()

            return income_records, costs_records

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
                table.setItem(inx, 1, QTableWidgetItem(str(self.unix_time_to_datetime_utc(row[2]))))

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def sum_all_data(self):
        all = []
        for row in self.income_records:
            temp = []
            temp.append(1)
            temp.append(row)
            all.append(temp)

        for row in self.costs_records:
            temp = []
            temp.append(2)
            temp.append(row)
            all.append(temp)

        all.sort(key=self.sort_by_date, reverse=True)

        return all

    def write_in_table_records(self, table):
        table.clearContents()
        table.setRowCount(0)
        all = self.sum_all_data()

        for inx, row in enumerate(all):
            table.insertRow(inx)
            table.setItem(inx, 0, QTableWidgetItem(str(self.unix_time_to_datetime_utc(row[1][1]))))

            table.setItem(inx, 2, QTableWidgetItem(str(row[1][2])))
            table.setItem(inx, 1, QTableWidgetItem("Статья отсутствует"))

            # table.setItem(inx, 1, QTableWidgetItem(str(row[0])))

            if row[0] == 1:
                for row2 in self.data_incomes:
                    if row[1][3] == row2[0]:
                        table.setItem(inx, 1, QTableWidgetItem(str(row2[1])))
                        self.set_color(table, "#e5fbe5", inx)


            elif row[0] == 2:
                for row2 in self.data_costs:
                    if row[1][3] == row2[0]:
                        table.setItem(inx, 1, QTableWidgetItem(str(row2[1])))
                        self.set_color(table, "#ffd8d8", inx)

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def sort_by_date(self, key):
        return key[1][1]

    def set_color(self, table, color, inx):

        for i, c in enumerate(self.column_name_table_records):
            table.item(inx, i).setBackground(QtGui.QColor(color))

            # Функция вывода записей в комбобоксы

    def write_in_combobox(self, data, combobox):
        combobox.clear()

        datetime_now = self.utc_datetime_to_unix_time(datetime.datetime.now())

        for row in data:
            if (datetime_now < row[2]) or (row[2] == 0):
                combobox.addItem(str(row[1]))

    def unix_time_to_datetime_utc(self, unixtime):
        return datetime.datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')

    def utc_date_to_unix_time(self, date):
        return int(time.mktime(date.timetuple()))

    def utc_datetime_to_unix_time(self, datetime):
        return int(time.mktime(datetime.timetuple()))

    def about(self):
        QMessageBox.about(self, "О программе",
                          "<strong>Домашняя бухгалтерия</strong>"
                          "<br/>Суворов Дмитрий<br/>"
                          "dimka59ru@gmail.com")

    # Функция, вызываемая при закрытии окна
    def closeEvent(self, event):
        # закрываем соединение с базой
        self.cur_db.close()
        self.conn.close()
        event.accept()


def init_db(cur_db):
    sql_create_costs_table = """ CREATE TABLE IF NOT EXISTS `costs` (
                                    `id`	INTEGER PRIMARY KEY AUTOINCREMENT,
                                    `name`	TEXT NOT NULL UNIQUE,
                                    `expiration_date`	INTEGER,
                                    `visible`	INTEGER NOT NULL DEFAULT 1
                                );"""

    sql_create_incomes_table = """ CREATE TABLE IF NOT EXISTS `incomes` (
                                            `id`	INTEGER,
                                            `name`	TEXT NOT NULL UNIQUE,
                                            `expiration_date`	INTEGER,
                                            `visible`	INTEGER NOT NULL DEFAULT 1,
                                            PRIMARY KEY(`id`)
                                        );"""

    sql_create_costs_records_table = """ CREATE TABLE IF NOT EXISTS `costs_records` (
                                            `id`	INTEGER,
                                            `datetime`	INTEGER NOT NULL,
                                            `sum`	INTEGER NOT NULL,
                                            `id_item`	INTEGER NOT NULL,
                                            `del`	INTEGER NOT NULL DEFAULT 0,
                                            PRIMARY KEY(`id`),
                                            FOREIGN KEY(`id_item`) REFERENCES `costs`(`id`)
                                        );"""

    sql_create_income_records_table = """ CREATE TABLE IF NOT EXISTS `income_records` (
                                            `id`	INTEGER PRIMARY KEY AUTOINCREMENT,
                                            `datetime`	INTEGER NOT NULL,
                                            `sum`	INTEGER NOT NULL,
                                            `id_item`	INTEGER NOT NULL,
                                            `del`	INTEGER NOT NULL DEFAULT 0,
                                            FOREIGN KEY(`id_item`) REFERENCES `incomes`(`id`)
                                        );"""

    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS `users` (                                                        
                                                    `name`	TEXT NOT NULL,
                                                    `pass`	TEXT NOT NULL                                                        
                                                );"""

    try:
        cur_db.execute(sql_create_costs_table)
        cur_db.execute(sql_create_incomes_table)
        cur_db.execute(sql_create_costs_records_table)
        cur_db.execute(sql_create_income_records_table)
        cur_db.execute(sql_create_users_table)

    except Exception as err:
        print(err)


if __name__ == '__main__':

    import sys
    from os.path import expanduser

    app = QApplication(sys.argv)
    app.setStyle("fusion")
    p = QtGui.QPalette
    p = qApp.palette()
    p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(77, 98, 120))
    qApp.setPalette(p)

    home = expanduser("~")
    db_file = "{}/family_finances.db".format(home)
    # Подключение к базе SQLite
    try:
        conn = sqlite3.connect(db_file)
        cur_db = conn.cursor()
        init_db(cur_db)
        cur_db.execute('SELECT * FROM users')
        result = cur_db.fetchone()

        if not result:
            create_user = CreateUser(db_file)
            if create_user.exec_() == QDialog.Accepted:
                login = Login(db_file)

    except sqlite3.DatabaseError as err:
        print("#1 - {}".format(err))

    login = Login(db_file)

    if login.exec_() == QDialog.Accepted:
        window = Window(db_file)
        # window.showMaximized()
        # window.show()
        sys.exit(app.exec_())
