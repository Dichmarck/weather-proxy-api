Прокси приложение, взаимодействующее с API openweathermap.org 

Команда для клонирования образа docker:
docker pull dichmarck/weather-proxy-api:latest
Запуск через команду docker run -e CACHE_LIFETIME=10 -p 8000:8000 dichmarck/weather-proxy-api
Адрес: localhost:8000
CACHE_LIFETIME - время действия кэша в секундах. По стандарту 1800с.
