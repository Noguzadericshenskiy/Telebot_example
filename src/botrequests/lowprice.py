import datetime
import json
import requests
from loguru import logger
from decouple import config
from typing import Any, List, Dict, Optional
from urllib.parse import urljoin
from .sqlite_my import get_date_input, get_date_output


KEY_HOTELS = config('KEY_HOTEL')

headers = {
        'x-rapidapi-host': 'hotels4.p.rapidapi.com',
        'x-rapidapi-key': KEY_HOTELS
                }

url_first = "https://hotels4.p.rapidapi.com"

logger.add('logs/logs.log', level='DEBUG', retention='30 days')


@logger.catch
def get_destination(city: str) -> Any:
    """
    Функцмя запрашивает id города по названию
    :param city: город для поиска
    :return: destination_id
    """
    try:
        query_city = {"query": city, "locale": "ru_RU"}
        response = requests.request("GET", urljoin(url_first, "locations/v2/search"),
                                    headers=headers, params=query_city, timeout=20)
        data = json.loads(response.text)
        destination_id = data['suggestions'][0]["entities"][0]["destinationId"]

        return destination_id

    except requests.exceptions.ReadTimeout:
        logger.info("Timeout Error")
        return "00"

    except ConnectionError:
        logger.info("Response error")
        return "response error"

    except IndexError:
        logger.info("Response error")
        return "response error"


@logger.catch
def get_list_offers(chat_id: int , city_id: int, nums: str, sort: str) -> List[Optional[dict]]:
    """
        Функция получения списка ID отелей
        :param nums: количество отелей для вывода
        :param city_id: id чата
        :param sort: параметр сортировки
        :return list_hotels  список данных об отелях
        """

    date_in = get_date_input(chat_id=chat_id)
    date_out = get_date_output(chat_id=chat_id)

    querystring_param = {"destinationId": city_id,
                         "pageNumber": "1",
                         "pageSize": nums,
                         "checkIn": date_in,
                         "checkOut": date_out,
                         "adults1": "1",
                         "sortOrder": sort,
                         "locale": "ru_RU",
                         "currency": "RUB"
                         }

    try:
        response = requests.request("GET", urljoin(url_first, "properties/list"),
                                    headers=headers, params=querystring_param, timeout=20)
        data_1 = json.loads(response.text)
        list_hotels = data_1['data']['body']['searchResults']['results']
        return list_hotels

    except ConnectionError:
        logger.info("response error")
        return []

    except requests.exceptions.ReadTimeout:
        logger.info("Timeout Error")
        return []


@logger.catch
def get_data_photo(id_hotels: int) -> Dict:
    """
    Функция делает запрос к API Hotels и возвращает информацию о запрошенной фотографии отеля
    :param id_hotels: Id отеля для запроса
    :return: информация о фотографии
    """

    try:
        querystring_photo = {"id": str(id_hotels)}
        response = requests.request("GET", urljoin(url_first, "properties/get-hotel-photos"),
                                    headers=headers, params=querystring_photo, timeout=20)
        data_photos = json.loads(response.text)

        return data_photos

    except ConnectionError:
        logger.info("response error")
        return {}

    except requests.exceptions.ReadTimeout:
        logger.info("response error")
        return {}
