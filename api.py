import os
import time
from typing import List
from fastapi import FastAPI
from fastapi import Request
import requests
import json
import uvicorn
import os


app = FastAPI()
API_KEY = "63fb6587d72cd0ad68bb5598be9adcfa"
LINK = "https://api.openweathermap.org/data/2.5/weather"
cache_lifetime = int(os.environ.get('CACHE_LIFETIME', 1800))


def get_weather_info_from_cache(city: str) -> dict:
    try:
        with open('cache.txt', 'r') as cache_txt:
            cache = cache_txt.read().split('\n')
        for line in cache:
            if f'"{city}"' in line:
                return json.loads(line)
        return dict()
    except Exception:
        return dict()


def change_info_in_cache(city: str, new_city_info: dict):
    old_cache_list = []
    old_cache = ""
    with open('cache.txt', 'r') as cache_txt:
        old_cache = cache_txt.read()
        old_cache_list = old_cache.split('\n')
    old_city_info = None
    for line in old_cache_list:
        if f'"{city}"' in line:
            old_city_info = line

    if old_city_info:
        with open('cache.txt', 'w') as cache_txt:
            new_city_info = new_city_info | {'time': time.time()}
            cache_txt.write(old_cache.replace(old_city_info, str(new_city_info).strip().replace("'", '"')))


def add_info_in_cache(new_city_info: dict):
    with open('cache.txt', 'a') as cache_txt:
        new_city_info = new_city_info | {'time': time.time()}
        cache_txt.write('\n' + str(new_city_info).strip().replace("'", '"'))


def get_weather_info_from_api(city: str) -> dict:
    try:
        return requests.get(LINK, {'q': city, 'appid': API_KEY, 'units': 'metric'}).json()
    except Exception:
        return ""


def get_weather_json_from_cache_or_api(city: str) -> dict:
    cache_weather = get_weather_info_from_cache(city)
    if cache_weather:
        if int(time.time() - cache_weather['time']) < cache_lifetime:
            if 'name' in cache_weather:
                return cache_weather
        else:
            api_weather = get_weather_info_from_api(city)
            if 'name' in api_weather.keys():
                change_info_in_cache(city, api_weather)
                return api_weather
            else:
                return cache_weather
    else:
        api_weather = get_weather_info_from_api(city)
        if api_weather:
            if 'name' in api_weather.keys():
                add_info_in_cache(api_weather)
            return api_weather
        else:
            return {'cod': -1, 'message': "weather server doesn't response"}


def generate_api_output(cities: List[str], params: List[str]) -> dict:
    allowed_params = ['temperature', 'feels', 'wind', 'visibility', 'humidity']
    cleared_params = []
    for param in params:
        if param.strip().lower() in allowed_params:
            cleared_params.append(param)

    if not cleared_params:
        cleared_params = allowed_params

    total_output_json = {}

    for city in cities:
        city_weather = get_weather_json_from_cache_or_api(city)
        if 'name' not in city_weather.keys():
            total_output_json[city] = city_weather
            continue

        city_weather_info_dict = {}
        for param in cleared_params:
            if param == 'temperature':
                city_weather_info_dict[param] = city_weather['main']['temp']
            elif param == 'feels':
                city_weather_info_dict[param] = city_weather['main']['feels_like']
            elif param == 'wind':
                city_weather_info_dict[param] = city_weather['wind']['speed']
            elif param == 'visibility':
                city_weather_info_dict[param] = city_weather['visibility']
            else:
                city_weather_info_dict[param] = city_weather['main']['humidity']

        total_output_json[city] = city_weather_info_dict

    return total_output_json


@app.get('/')
def get_weather_json_city(request: Request) -> dict:
    request_dict = request.query_params._dict
    params = []
    if 'params' in request_dict.keys():
        params = request_dict['params'].split()
    if 'city' in request_dict.keys():
        cities = [request_dict['city']] if request_dict['city'] else []
    elif 'cities' in request_dict.keys():
        cities = request_dict['cities'].split()

    if not cities:
        return {'cod': 0, 'message': 'city is not specified'}

    return generate_api_output(cities, params)


if __name__ == '__main__':
    print(f'cache_lifetime = {cache_lifetime}')
    uvicorn.run(app, host="0.0.0.0", port=8000)
