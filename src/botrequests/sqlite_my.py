import os
import sqlite3
from typing import List, Tuple
from sqlite3 import Error
from loguru import logger

PATH_BD = os.path.join('simply_bd.bd')


@logger.catch
def creation(path: str) -> None:
    """
    Функия создает таблицу БЛ
    :param path: - путь создания
    """
    connection = None

    try:
        connection = sqlite3.connect(path)
    except Error as err:
        logger.exception(err)

    cursor = connection.cursor()
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS request(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_chat INTEGER NOT NULL UNIQUE ON CONFLICT REPLACE,
                        command TEXT,
                        city_id INTEGER,
                        date_cur TEXT,
                        date_in TEXT,
                        date_out TEXT,
                        num_hotels INTEGER,
                        num_photo INTEGER,
                        flag_photo INTEGER,
                        min_price TEXT,
                        max_price TEXT,
                        distance INTEGER
                        );""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS city (
                        id_city INTEGER PRIMARY KEY AUTOINCREMENT,
                        city_name TEXT,
                        city_id INTEGER
                        );""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS history (
                        id_history INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        command TEXT,
                        data_cur TEXT,
                        response TEXT
                        );""")
        connection.commit()

    except Error as err:
        logger.exception(err)
    connection.close()


@logger.catch
def add_info_bd(path: str, request_sql: str) -> None:
    """Функция добавляет информацию в БД
    :param request_sql: строка запроса
    :param path: путь до файла БД
    """
    connection = None

    try:
        connection = sqlite3.connect(path)
    except Error as err:
        logger.exception(err)
    cursor = connection.cursor()
    try:
        cursor.execute(request_sql)
        connection.commit()
    except Error as err:
        logger.exception(err)
    connection.close()


@logger.catch
def get_info_bd(path: str, request_sql: str) -> List[tuple]:
    """Функция вывода информации из БД
    :param path:
    :param request_sql:
    :return: result: кортеж значений
    """
    connection = None
    result = []

    try:
        connection = sqlite3.connect(path)
    except Error as err:
        logger.exception(err)
    cursor = connection.cursor()
    try:
        cursor.execute(request_sql)
        result = cursor.fetchall()
    except Error as err:
        logger.exception(err)
    connection.close()
    return result


def init_request(chat_id: int, command: str, date: str) -> None:
    """
    Функция создает запись  БД при вводе команды
    :param chat_id: id чата
    :param command: команда
    :param date: дата и время
    """
    request = f"INSERT INTO request(id_chat, command, date_cur) " \
              f"VALUES({chat_id}, '{command}', '{date}');"
    add_info_bd(PATH_BD, request_sql=request)


def get_city_id_bd(text: str) -> List[tuple]:
    """
    Функция получает название города и ищет в базе его ID
    :param text: название города
    :return: ID города
    """
    request = f' SELECT city_id ' \
              f'FROM city ' \
              f'WHERE city_name = "{text}";'
    city_id = get_info_bd(PATH_BD, request_sql=request)
    return city_id


def set_city_id_bd(chat_id: int, city_id: int) -> None:
    """
    Функция добавляет в БД ID города
    :param chat_id: id чата
    :param city_id: ID города
    """
    request_bd = f"UPDATE request " \
                 f"SET city_id = {city_id} " \
                 f"WHERE  id_chat = {chat_id};"
    add_info_bd(PATH_BD, request_sql=request_bd)


def set_city_bd(text: str, destination: int) -> None:
    """
    Функция добавляет в БД, таблица городов, информацию о городе, его название и ID
    :param text: название города
    :param destination: ID города
    """
    request_ins = f"INSERT INTO city (city_name, city_id) " \
                  f"VALUES ('{text}', {destination});"
    add_info_bd(PATH_BD, request_sql=request_ins)


def get_history_bd(chat_id: int) -> List[tuple]:
    """
    Функция получения истории по id чата
    :param chat_id: id чата
    :return: выводит кортеж значений истории, последние 5 записей
    """
    request = f"SELECT * FROM history " \
              f"WHERE chat_id = {chat_id} " \
              f"ORDER BY id_history DESC LIMIT 5"
    list_history = get_info_bd(PATH_BD, request)
    return list_history


def set_history_bd(chat_id: int, command: str, date: str, string: str) -> None:
    """
    Функция записывает историю в файл БД
    :param chat_id: id чата
    :param command: команда
    :param date: дата, время вызова команды
    :param string: строка с информацией об отеле
    """
    request_history = f"INSERT INTO history(chat_id, command, data_cur, response)" \
                      f" VALUES({chat_id}, '{command}', '{date}', '{string}');"
    add_info_bd(PATH_BD, request_history)


def get_command_bd(chat_id: int) -> str:
    """
    Функция поиска и вывода вывода  команды из БД
    :param chat_id: id чата
    :return command: str  выводит команду из кортежа
    """
    request_command = f"SELECT command " \
                      f"FROM request " \
                      f" WHERE id_chat= {chat_id};"
    command = get_info_bd(PATH_BD, request_sql=request_command)
    return command[0][0]


def set_distance_bd(chat_id: int, distance: int) -> None:
    """
    Функция добавляет в БД расстояние от центра
    :param chat_id: id чата
    :param distance: расстояние до центра города
    """
    request_upd = f"UPDATE request " \
                  f"SET distance = {distance} " \
                  f" WHERE id_chat = {chat_id};"
    add_info_bd(PATH_BD, request_sql=request_upd)


def set_min_max_price_bd(chat_id: int, min_p: int, max_p: int) -> None:
    """
    Функция добавляет данные о минимальной и максимальной цене
    :param chat_id:id чата
    :param min_p: минимальная цена
    :param max_p: максимальная цена
    """
    request_upd = f"UPDATE request " \
                  f"SET min_price = '{str(min_p)}', max_price= '{str(max_p)}' " \
                  f" WHERE  id_chat = {chat_id};"
    add_info_bd(PATH_BD, request_sql=request_upd)


def set_num_offers_bd(chat_id: int, nums: int) -> None:
    """
    Функция добавляет данные о количестве отелей в БД
    :param chat_id: id чата
    :param nums: количество необходимых для поиска отелей
    """
    request_num = f"UPDATE request " \
                  f"SET num_hotels = {nums} " \
                  f" WHERE  id_chat = {chat_id};"
    add_info_bd(PATH_BD, request_sql=request_num)


def set_photo_bd(chat_id: int, flag: int) -> None:
    """
    Функция добавляет состояние флага необходимости вывода фотографий
    :param chat_id: id чата
    :param flag: флаг состояния 0-1
    """
    request_num = f"UPDATE request " \
                  f"SET flag_photo = {flag} " \
                  f" WHERE  id_chat = {chat_id};"
    add_info_bd(PATH_BD, request_sql=request_num)


def set_num_photo_bd(chat_id: int, nums: int) -> None:
    """
    Функция добавляет данные о количестве фотографий в БД
    :param chat_id: id чата
    :param nums: количество фотографий
    """
    request_num = f"UPDATE request " \
                  f"SET num_photo = {nums} " \
                  f" WHERE id_chat = {chat_id};"
    add_info_bd(PATH_BD, request_sql=request_num)


def get_info_request_bd(chat_id: int) -> Tuple:
    """
    Функция ищет и выводит всю информацию по конкретному запросу
    :param chat_id: id чата для поиска
    """
    request = f"SELECT command, num_hotels, flag_photo, num_photo, city_id," \
              f" date_cur, min_price, max_price, distance " \
              f" FROM request " \
              f" WHERE id_chat = {chat_id};"
    response = get_info_bd(PATH_BD, request_sql=request)
    return response[0]


def set_date_input(chat_id: int, date_in: str) -> None:
    """
    Функция записи даты въезда
    :param chat_id: id чата
    :param date_in: Дата въезда
    """
    request_date = f"UPDATE request " \
                   f"SET date_in = '{date_in}' " \
                   f" WHERE id_chat = {chat_id};"
    add_info_bd(PATH_BD, request_sql=request_date)


def get_date_input(chat_id: int) -> str:
    """
    Функция получения даты въезда
    :param chat_id: id чата
    :return: дата въезда
    """

    request_date = f"SELECT date_in" \
                   f" FROM request " \
                   f" WHERE id_chat = {chat_id};"
    response = get_info_bd(PATH_BD, request_sql=request_date)
    return response[0][0]


def set_date_output(chat_id: int, date_out: str) -> None:
    """
    Функция записи даты въезда
    :param chat_id: id чата
    :param date_out: Дата выезда
    """
    request_date = f"UPDATE request " \
                   f"SET date_out = '{date_out}' " \
                   f" WHERE id_chat = {chat_id};"
    add_info_bd(PATH_BD, request_sql=request_date)


def get_date_output(chat_id: int) -> str:
    """
    Функция получения даты выезда
    :param chat_id: id чата
    :return: дата выезда
    """
    request_date = f"SELECT date_out" \
                   f" FROM request " \
                   f" WHERE id_chat = {chat_id};"
    response = get_info_bd(PATH_BD, request_sql=request_date)
    return response[0][0]
