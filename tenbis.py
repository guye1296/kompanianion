import requests
import dataclasses
import typing
import uuid
import random
import functools


TENBIS_API_URL = "https://www.10bis.co.il/NextApi/{action}"


@dataclasses.dataclass
class Restaurant:
    name: str
    photo_url: str
    url: str
    distance: int


class Session:
    def __init__(self, address_key: str):
        city_id, street_id, house_number = address_key.split('-')
        self._params = {
            "addressKey": address_key,
            "cityId": city_id,
            "streetId": street_id,
            "houseNumber": house_number,
            "shoppingCartGuid": uuid.uuid4(),
        }

        self._restaurants = self._get_all_restaurants()

    def _send_api_request(self, action, **kwargs) -> dict:
        response = requests.get(
            TENBIS_API_URL.format(action=action),
            params=self._params,
        )

        response.raise_for_status()
        return response.json()

    def _get_all_restaurants(self) -> typing.List[Restaurant]:
        """
        get active restaurants
        :param location:
        :return:
        """
        response = self._send_api_request("searchRestaurants")

        if not response["Success"]:
            raise RuntimeError(f"API request failed :( {response}")

        restaurants = []
        raw_restaurants_list = response["Data"]["restaurantsList"]
        for raw_data in raw_restaurants_list:
            #if raw_data["isOpenNow"] and raw_data["isActive"] and raw_data["isDeliveryEnabled"]:
            if raw_data["isActive"] and raw_data["isDeliveryEnabled"]:
                restaurants.append(Restaurant(
                    name=raw_data["restaurantName"],
                    photo_url=raw_data["restaurantLogoUrl"],
                    distance=raw_data["distanceFromUser"],
                    url=f"https://www.10bis.co.il/next/restaurants/menu/delivery/{raw_data['restaurantId']}"
                ))

        return restaurants

    def get_random_restaurant(self) -> Restaurant:
        return random.choice(self._get_all_restaurants())

    @functools.lru_cache(16)
    def search_restaurant(self, name: str) -> Restaurant:
        """
        find first occurrence of 'name' in the restaurant list
        :return first restaurant match; None if not found
        """
        for restaurant in self._restaurants:
            if name in restaurant.name:
                return restaurant
