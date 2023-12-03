import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

raw_price = "12  23  ,  45"
print(float((re.sub(r'[^\d.,]', '', raw_price).replace(",", "."))))

url = "https://auto.ru/cars/new/group/toyota/land_cruiser/22905534/23504067/1121311614-587ce411/"
xpath = "//*[@id='app']/div/div[2]/div[3]/div/div[2]/div/div[2]/div/div[2]/div[1]/div[1]/div[2]/div/div[2]/div"
site = urlparse(url).netloc
print(site)

service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get(url)
try:
    price_element = driver.find_element(By.XPATH, xpath)
    if price_element:
        raw_price = price_element.text.strip()
        print(float((re.sub(r'[^\d.,]', '', raw_price).replace(",", "."))))
except Exception as e:
    print(f'Ошибка {url}: {e}')

driver.quit()
