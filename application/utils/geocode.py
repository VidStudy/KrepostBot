from math import radians, cos, sin, asin, sqrt
from yandex_geocoder import Client
from typing import Optional, AnyStr

import json
import urllib

def distance_between_two_points(first_coordinates: tuple, second_coordinates: tuple) -> tuple:
    lat1, lon1 = first_coordinates
    lat2, lon2 = second_coordinates
    try:
        url = 'https://api.routing.yandex.net/v2/distancematrix?origins={},{}&destinations={},{}&apikey={}'.format(
            lat1, lon1, lat2, lon2, '424e9981-9ff1-44c3-ba6e-60c7669b25f3')
        r = urllib.request.urlopen(url)
        data = json.loads(r.read().decode('utf-8'))
        km = data['rows'][0]['elements'][0]['distance']['value'] / 1000.0
        return round(km, 1), 'км'
    except: # fallback
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # Haversina formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        # Radius of Earth in kilometers is 6731
        km = 6371 * c
        return round(km, 1), 'км'

def get_address_by_coordinates(coordinates: tuple) -> Optional[AnyStr]:
    """
    Return address string value by coordinates
    :param coordinates: Coordinates (latitude, longitude)
    :return: string value
    """
    client = Client('4d16304f-12ba-4134-ac9b-f0da5028a1f4')
    latitude = coordinates[0]
    longitude = coordinates[1]
    location = client.address(longitude, latitude)
    return location
