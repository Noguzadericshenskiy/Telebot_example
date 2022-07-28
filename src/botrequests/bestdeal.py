import datetime
import json
import requests
import re
from loguru import logger
from decouple import config
from typing import List
from .sqlite_my import get_date_input, get_date_output


KEY_HOTELS = config('KEY_HOTEL')


url_prop = "https://hotels4.p.rapidapi.com/properties/list"
headers_prop = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': KEY_HOTELS
                }

logger.add('logs/logs.log', level='DEBUG', retention='30 days')


@logger.catch
def get_list_offers_bestdeal(chat_id: int, city_id: int, nums: int, min_p: str,
                             max_p: str, distance_ldk: int) -> List[dict]:
    """
        Функция получения списка ID отелей
        :param nums: количество отелей для вывода
        :param city_id: id чата
        :param min_p: минимальная цена поиска
        :param max_p: максимальная цена поиска
        :param distance_ldk: удаленность от центра
        :return list_hotels  список данных об отелях
        """
    list_hotels = []
    num_page_count = 1
    date_in = get_date_input(chat_id=chat_id)
    date_out = get_date_output(chat_id=chat_id)

    querystring_param = {"destinationId": city_id,
                         "pageNumber": num_page_count,
                         "pageSize": "25",
                         "checkIn": date_in,
                         "checkOut": date_out,
                         "adults1": "1",
                         "priceMin": min_p,
                         "priceMax": max_p,
                         "sortOrder": "DISTANCE_FROM_LANDMARK",
                         "locale": "ru_RU",
                         "currency": "RUB",
                         }

    try:
        while True:
            response = requests.request("GET", url_prop, headers=headers_prop, params=querystring_param, timeout=20)
            data_1 = json.loads(response.text)
            if data_1['data']['body']['searchResults']['results'] != 0:
                for i_hotel in data_1['data']['body']['searchResults']['results']:
                    try:
                        if (int(float(re.findall(r'\b[0-9.]+', i_hotel["landmarks"][0]["distance"])[0]) * 1000) <= distance_ldk)\
                                and i_hotel["address"]["streetAddress"]:
                            list_hotels.append(i_hotel)
                    except KeyError:
                        KeyError("Очередной косяк в недоапи")

                if len(list_hotels) >= nums:
                    return list_hotels[:nums]

                elif num_page_count == 26:
                    return list_hotels

                else:
                    num_page_count += 1

            else:
                return list_hotels

    except ConnectionError:
        logger.info("response error")
        return list_hotels

    except requests.exceptions.ReadTimeout:
        logger.info("Timeout Error")
        return list_hotels


