import os
import sqlite3
import telebot
import datetime
import re

from typing import Optional
from loguru import logger
from decouple import config
from telebot import types
from urllib.parse import urljoin
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from botrequests.lowprice import get_list_offers, get_data_photo, get_destination
from botrequests.bestdeal import get_list_offers_bestdeal
from botrequests.sqlite_my import creation, get_command_bd, init_request, get_history_bd, set_distance_bd, \
    set_min_max_price_bd, set_history_bd, get_info_request_bd, set_num_photo_bd, set_photo_bd, set_num_offers_bd,\
    get_city_id_bd, set_city_id_bd, set_city_bd, get_date_input, set_date_output, set_date_input


KEY = config('KEY')
PATH_BD = os.path.join('simply_bd.bd')

bot = telebot.TeleBot(KEY)


markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
itembtn1 = types.KeyboardButton('/lowprice')
itembtn2 = types.KeyboardButton('/highprice')
itembtn3 = types.KeyboardButton('/bestdeal')
itembtn4 = types.KeyboardButton('/history')
itembtn5 = types.KeyboardButton('/help')
markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5)


@logger.catch
def city_name(message: types.Message) -> None:
    """
    Функция получает название города проверяет его на валидность?
    проверяет на существование в  БД (если есть, запрос на API не делается),
    запрашивает  количество отелей для поиска
    :param message: Сообщение пользователя
    """
    text_mes = message.text
    pattern = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ\s]+', text_mes)

    try:
        if pattern:
            city_bd_id = get_city_id_bd(text=pattern[0])
            if len(city_bd_id) != 0:
                set_city_id_bd(chat_id=message.chat.id, city_id=city_bd_id[0][0])
                set_date_in(message)
            else:
                destination_id = get_destination(city=pattern[0])
                if destination_id == '00':
                    bot.send_message(message.chat.id, f'Сервак одел деревянный бушлат,'
                                                      '\nповторите запрос через недельку'
                                                      '\nВведите название отеля')
                    bot.register_next_step_handler(message, city_name)

                elif destination_id == "response error":
                    raise ValueError

                else:
                    set_city_bd(text=pattern[0], destination=int(destination_id))
                    set_city_id_bd(chat_id=message.chat.id, city_id=int(destination_id))
                    set_date_in(message)

        else:
            raise ValueError

    except ValueError:
        bot.send_message(message.chat.id, 'В названии  города только буквы и пробел.'
                                          '\nПопробуйте еще разок, вводите данные рукой.')
        bot.register_next_step_handler(message, city_name)


def set_date_in(message: types.Message):
    """
    Функция вызова даты въезда
    :param message: Сообщение пользователя
    """
    text = "Выберите дату заезда"
    bot.send_message(message.from_user.id, text)
    date = datetime.date.today()
    calendar, step = DetailedTelegramCalendar(calendar_id=1, locale='ru', min_date=date).build()
    bot.send_message(message.chat.id, f"Выберите {LSTEP[step]}", reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal(callback_query: types.CallbackQuery) -> None:
    """
    Функция обработчик календаря, выводит клавиатуру с календарем и ожидает ответ,
    передает ответ в БД,
    и переходит к следующему шагу
    :param callback_query: запрос обраатного вызова с сообщением

    """
    date = datetime.date.today()
    result, key, step = DetailedTelegramCalendar(calendar_id=1, locale='ru', min_date=date).process(callback_query.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}",
                              callback_query.message.chat.id,
                              callback_query.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Вы выбрали {result}",
                              callback_query.message.chat.id,
                              callback_query.message.message_id)
        set_date_input(chat_id=callback_query.message.chat.id, date_in=str(result))
        date_out(callback_query.message.chat.id)


def date_out(chat_id: int) -> None:
    """
    Функция вызова даты въезда
    :param chat_id: ID чата
    """
    date_today = (datetime.datetime.strptime(get_date_input(chat_id=chat_id),
                                             "%Y-%m-%d") + datetime.timedelta(days=1)).date()
    text = "Выберите дату выезда"
    bot.send_message(chat_id, text)
    calendar, step = DetailedTelegramCalendar(calendar_id=2, locale='ru', min_date=date_today).build()
    bot.send_message(chat_id, f"Выберите {LSTEP[step]}", reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal(callback_query: types.CallbackQuery) -> None:
    """
    Функция обработчик календаря, выводит клавиатуру с календарем и ожидает ответ,
    передает ответ в БД,
    и переходит к следующему шагу
    :param callback_query: запрос обратного вызова с сообщением
    """
    date_today = (datetime.datetime.strptime(get_date_input(chat_id=callback_query.message.chat.id),
                                             "%Y-%m-%d") + datetime.timedelta(days=1)).date()

    result, key, step = DetailedTelegramCalendar(calendar_id=2, locale='ru',
                                                 min_date=date_today).process(callback_query.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}",
                              callback_query.message.chat.id,
                              callback_query.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Вы выбрали {result}",
                              callback_query.message.chat.id,
                              callback_query.message.message_id)
        set_date_output(chat_id=callback_query.message.chat.id, date_out=str(result))
        selection_next_step(callback_query.message)


def selection_next_step(message: types.Message) -> None:
    """
    Функция обработки выбора следующего шага.
    В зависимости от команды переключает на получение цен или количество отелей
    :param message: сообщение
    """
    command = get_command_bd(chat_id=message.chat.id)
    if command == 'bestdeal':
        bot.send_message(message.chat.id, "Введите диапазон цен для поиска (2 целых числа 'от' 'до')")
        bot.register_next_step_handler(message, request_for_prices)

    else:
        bot.send_message(message.chat.id, "Введите количество отелей (число от 1 до 5)")
        bot.register_next_step_handler(message, get_offers)


@logger.catch
def get_offers(message: types.Message) -> None:
    """
    Функция обрабатывает количество отелей для вывода и записывает информацию в БД
    :param message: Сообщение от пользователя.
    """
    num = message.text
    try:
        if num.isdigit() and (0 < int(num) <= 5):
            set_num_offers_bd(chat_id=message.chat.id, nums=int(num))
            bot.send_message(message.chat.id, 'Нужно вывести фото отелей? (Да, Нет?)')
            bot.register_next_step_handler(message, request_photo)

        else:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, 'АХТУНГ!\nБез гравицапы не полетим\nВведите количество отелей,'
                                          ' которые необходимо вывести (от 1 до 5)')
        bot.register_next_step_handler(message, get_offers)


@logger.catch
def request_photo(message: types.Message) -> None:
    """ Функция обрабатывает запрос на вывод фотографий отелей
        заносит флаг ответа в БД
    :param message сообщение от пользователя
    """
    try:
        answer = message.text.title()

        if answer == "Да":
            set_photo_bd(chat_id=message.chat.id, flag=1)
            bot.send_message(message.chat.id, 'Введите количество фотографий для каждого отеля \n(число от 1 до 5)')
            bot.register_next_step_handler(message, check_num_photo)

        elif answer == "Нет":
            set_photo_bd(chat_id=message.chat.id, flag=0)
            answer_out(message)

        else:
            raise ValueError('Ошибка при запросе необходимости вывода фотографий')
    except ValueError:
        bot.send_message(message.chat.id, 'Ввод не верный, \nНужно вывести фото отелей? (Да, Нет)')
        bot.register_next_step_handler(message, request_photo)


@logger.catch
def check_num_photo(message: types.Message) -> None:
    """
    Функция обрабатывает запрос на количество фотографий отелей и вносит информацию в БД.
    :param message: Сообщение пользователя
    """
    nums_photo = int(message.text)
    try:
        if 0 < nums_photo <= 5:
            set_num_photo_bd(chat_id=message.chat.id, nums=nums_photo)
            answer_out(message=message)

        else:
            raise ValueError('Ошибка при запросе выбора фотографий')
    except ValueError:
        bot.send_message(message.chat.id, 'Ввод не верный, Введите число от 1 до 5')
        bot.register_next_step_handler(message, check_num_photo)


@logger.catch
def answer_out(message: types.Message) -> None:
    """
    Функция обработчик вывода данных пользователю.
    получает id чата для ответа, обращается в БД таблица request
    формирует и выводит ответ пользователю
    :param message: сообщение пользователя
    """
    list_hotels: list = []
    chat_id: int = message.chat.id
    response_bd = get_info_request_bd(chat_id=chat_id)

    command, num_hotels = response_bd[0], response_bd[1]
    flag_photo, num_photos = response_bd[2], response_bd[3]
    city_id, date_cur = response_bd[4], response_bd[5]

    bot.send_message(chat_id, 'Теперь недельку подождите, \nхромая чюрюпаха уже в пути.')

    if (command == 'lowprice') or (command == 'highprice'):
        if command == 'lowprice':
            list_hotels = get_list_offers(chat_id=chat_id, city_id=city_id,
                                          nums=str(num_hotels), sort='PRICE')

        elif command == 'highprice':
            list_hotels = get_list_offers(chat_id=chat_id, city_id=city_id,
                                          nums=str(num_hotels), sort='PRICE_HIGHEST_FIRST')

        if len(list_hotels) != 0:
            try:
                for i_hotel in list_hotels:
                    text = re.findall(r'\b[^\'\"]+', i_hotel["name"])
                    string_info = '\nНазвание: {name}' \
                                  '\nАдрес: {address}' \
                                  '\nСсылка: {url_hotel}' \
                                  '\nЦена: {price}'.format(
                                        name=text[0],
                                        address=i_hotel["address"]["streetAddress"],
                                        url_hotel=url_hotels(id_hotel=i_hotel['id']),
                                        price=i_hotel["ratePlan"]["price"]["exactCurrent"])
                    set_history_bd(chat_id=chat_id, command=command, date=date_cur, string=string_info)
                    if flag_photo == 1:
                        bot.send_message(chat_id, f'Фотографии отеля {string_info}', disable_web_page_preview=True)
                        if num_photos != 0:
                            out_photo(chat_id=chat_id, num_photos=num_photos, hotel=i_hotel)

                        else:
                            bot.send_message(chat_id, 'Фотографии нет')

                    else:
                        bot.send_message(chat_id=chat_id, text=string_info, disable_web_page_preview=True)
            except KeyError:
                KeyError('Нет адреса')
                bot.send_message(chat_id, 'Нет адреса, Невозможно сформировать строку вывода')

        else:
            bot.send_message(chat_id, 'Отелей по вашему запросу в базе нет')

    else:
        out_info_bestdeal(chat_id)


def out_info_bestdeal(chat_id: int) -> None:
    """
    Функция вывода информации пользователю каманда bestdeal
    :param chat_id: id чата
    """
    response_bd = get_info_request_bd(chat_id=chat_id)

    command, num_hotels = response_bd[0], response_bd[1]
    flag_photo, num_photos = response_bd[2], response_bd[3]
    city_id, date_cur = response_bd[4], response_bd[5]
    mini, maxi = response_bd[6], response_bd[7]
    distance_hotels = response_bd[8]

    list_hotels = get_list_offers_bestdeal(chat_id=chat_id, city_id=city_id, nums=num_hotels,
                                           distance_ldk=distance_hotels, min_p=mini, max_p=maxi)
    try:
        if len(list_hotels) != 0:
            for i_hotel in list_hotels:
                text = re.findall(r'\b[^\'\"]+', i_hotel["name"])
                string_info = """Название: {name} 
                                 \nАдрес: {address} 
                                 \nСсылка: {url_hotel}
                                 \nЦена: {price} 
                                 \nУдаленность от центра {distanc}""".format(
                                    name=text[0],
                                    address=i_hotel["address"]["streetAddress"],
                                    url_hotel=url_hotels(id_hotel=i_hotel['id']),
                                    price=i_hotel["ratePlan"]["price"]["exactCurrent"],
                                    distanc=i_hotel["landmarks"][0]["distance"])
                set_history_bd(chat_id=chat_id, command=command, date=date_cur, string=string_info)
                if flag_photo == 1:
                    bot.send_message(chat_id, f'Фотографии отеля {string_info}', disable_web_page_preview=True)
                    if num_photos == 1:
                        out_photo(chat_id=chat_id, num_photos=num_photos, hotel=i_hotel)

                    else:
                        bot.send_message(chat_id, 'Фотографии отсутствуют')

                else:
                    bot.send_message(chat_id=chat_id, text=string_info, disable_web_page_preview=True)

        else:
            bot.send_message(chat_id, 'По вашему запросу ничего не найдено')

    except KeyError:
        KeyError('Нет адреса')
        bot.send_message(chat_id, 'Нет адреса, Невозможно сформировать строку вывода')
    except sqlite3.OperationalError:
        sqlite3.OperationalError("Ошибка данных от сервера")
        bot.send_message(chat_id, 'Ошибка данных от сервера. Невозможно сформировать строку вывода')


def out_photo(chat_id: int, num_photos: int, hotel: dict) -> None:
    """
    Функция выводит фотографии пользователю
    :param chat_id: id чата
    :param num_photos: кол-во фотографий
    :param hotel: словарь информации об отеле
    """
    try:
        bot.send_media_group(chat_id, [types.InputMediaPhoto(get_photos(hotels_id=hotel['id'], num_photos=i_photo))
                                       for i_photo in range(num_photos)])
    except Exception:
        Exception("Вывод фотографии неудачный")
        bot.send_message(chat_id, 'Не хватило денег на фотоаппарат')


@logger.catch
def get_photos(hotels_id: int, num_photos: int) -> Optional[str]:
    """
    Функция получает адрес фотографии из запроса к API
    :param hotels_id: Id отеля для запроса
    :param num_photos номер фотографии для поиска и вывода
    :return url_photo or None возвращаем адрес фотки, а если не найдена, возвращаем None
    """
    data_photos = get_data_photo(id_hotels=hotels_id)

    if len(data_photos) != 0:
        url_photo = data_photos["hotelImages"][num_photos]["baseUrl"].format(
            size=data_photos["hotelImages"][num_photos]["sizes"][0]["suffix"])

        return url_photo
    return None


@logger.catch
def request_for_prices(message: types.Message) -> None:
    """
    Функция обрабатывает ответ на запрос о ценах и запрашивает удаленность от центра
    :param message: сообщение от пользователя
    """
    try:
        pattern_price = re.findall(r'([0-9]+)', message.text)
        min_price = int(pattern_price[0])
        max_price = int(pattern_price[1])
        if min_price < max_price:
            set_min_max_price_bd(chat_id=message.chat.id, min_p=min_price, max_p=max_price)
            bot.send_message(message.chat.id, 'Введите удаленность от центра в метрах, число до 5000')
            bot.register_next_step_handler(message, request_distance_of_landmark)

        elif min_price > max_price:
            set_min_max_price_bd(chat_id=message.chat.id, min_p=max_price, max_p=min_price)
            bot.send_message(message.chat.id, 'Введите удаленность от центра в метрах, число до 5000')
            bot.register_next_step_handler(message, request_distance_of_landmark)

        else:
            raise ValueError

    except IndexError:
        IndexError('Неверный ввод цен')
        bot.send_message(message.chat.id, "Ввод неверный, \nпопробуйте нажимать кнопки руками")
        bot.register_next_step_handler(message, request_for_prices)
    except ValueError:
        ValueError('неверный диапазон цен')
        bot.send_message(message.chat.id, "Ввод неверный, \nпопробуйте нажимать кнопки руками")
        bot.register_next_step_handler(message, request_for_prices)


@logger.catch
def request_distance_of_landmark(message: types.Message) -> None:
    """
    Функция обрабатывает расстояние до центра и запрашивает число отелей
    :param message: сообщение от пользователя
    """
    try:
        pattern_distance = re.findall(r'([0-9]+)', message.text)
        if (int(pattern_distance[0]) >= 1) and (int(pattern_distance[0])) <= 5000:
            set_distance_bd(chat_id=message.chat.id, distance=int(pattern_distance[0]))
            bot.send_message(message.chat.id, 'Введите количество отелей(число от 1 до 5)')
            bot.register_next_step_handler(message, get_offers)

        else:
            raise ValueError

    except ValueError:
        bot.send_message(message.chat.id, 'Введите дистанцию в метрах заново \n(целое целое число min 1 max 5000)')
        bot.register_next_step_handler(message, request_distance_of_landmark)


def url_hotels(id_hotel: int) -> str:
    """
    Функция создает адрес отеля
    :param id_hotel: id отеля
    :return: final_url строка с адресом
    """
    base_url = "https://ru.hotels.com/"
    first = "ho" + str(id_hotel)
    final_url = urljoin(base_url, first)
    return final_url


@bot.message_handler(commands=['start'])
@logger.catch
def get_text_messages(message: types.Message) -> None:
    """Функция выводит начальную портянку при старте Привет, блаблаблабла"""
    text = "Список команд\n" \
           "Введите команду или выберите ее в меню\n" \
           "/help - вывести все команды.\n" \
           "/lowprice - минимальные цены\n" \
           "/highprice - максимальные цены\n" \
           "/bestdeal - предложения от min до max при заданной удаленности\n" \
           "/history - вывод 5 последних запросов"
    bot.send_message(message.from_user.id, text, reply_markup=markup)


@bot.message_handler(commands=['help'])
@logger.catch
def process_help_command(message: types.Message) -> None:
    """
    Функция ожидает ввода команды  help  и выводит все команды
    :param message: сообщение от пользователя (с командой)
    """
    text = "/help - вывести все команды.\n" \
           "/lowprice - предложения для бомжей\n" \
           "/highprice - предложения для миллионеров\n" \
           "/bestdeal - предложения для всех остальных\n" \
           "/history - вывод 5 последних запросов"
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['lowprice'])
@logger.catch
def command_lowprice(message: types.Message) -> None:
    """
    Функция ожидает ввода команды lowprice, создает БД, создает запись в базе данных о времени
    ввода команды и название команды.
    :param message: сообщение от пользователя (с командой)
    """
    creation(PATH_BD)
    cur_date = datetime.datetime.now()
    date = cur_date.strftime('%d-%m-%Y %H:%M:%S')
    init_request(chat_id=message.chat.id, command='lowprice', date=date)
    bot.send_message(message.chat.id, 'Введите название города для поиска')
    bot.register_next_step_handler(message, city_name)


@bot.message_handler(commands=['highprice'])
@logger.catch
def command_highprice(message: types.Message) -> None:
    """
    Функция ожидает ввода команды highprice
    :param message: сообщение от пользователя (с командой)
    """
    creation(PATH_BD)
    cur_date = datetime.datetime.now()
    date = cur_date.strftime('%d-%m-%Y %H:%M:%S')
    init_request(chat_id=message.chat.id, command='highprice', date=date)
    bot.send_message(message.chat.id, 'Введите название города для поиска')
    bot.register_next_step_handler(message, city_name)


@bot.message_handler(commands=['bestdeal'])
@logger.catch
def command_bestdeal(message: types.Message) -> None:
    """
    Функция обработки команды bestdeal
    :param message: сообщение
    """
    creation(PATH_BD)
    cur_date = datetime.datetime.now()
    date = cur_date.strftime('%d-%m-%Y %H:%M:%S')
    init_request(chat_id=message.chat.id, command='bestdeal', date=date)
    bot.send_message(message.chat.id, 'Введите название города для поиска')
    bot.register_next_step_handler(message, city_name)


@bot.message_handler(commands=['history'])
@logger.catch
def command_help(message: types.Message) -> None:
    """
    Функция выводит историю запросов
    Выводит последние 5 запросов
    :param message: сообщение от пользователя (с командой)
    """
    list_history = get_history_bd(chat_id=message.chat.id)
    if list_history:
        for i_rec in list_history:
            text = f"'{i_rec[2]}'\n'{i_rec[3]}'\n'{i_rec[4]}'"
            bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "Список пуст")


@bot.message_handler(content_types=['text'])
@logger.catch
def get_text_messages(message: types.Message) -> None:
    """
    Функция выводит текст при вводе слова 'Привет'
    :param message: сообщение от пользователя с текстом
    """
    if message.text.title() == 'Привет':
        text = 'Введите команду, или выберите ее в меню'
        bot.send_message(message.from_user.id, text)


if __name__ == '__main__':
    bot.infinity_polling(timeout=10)
