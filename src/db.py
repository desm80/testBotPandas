import logging
import re
import time
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
from urllib.parse import urlparse
from webdriver_manager.chrome import ChromeDriverManager


DATABASE_URL = "sqlite:///links.db"
engine = create_engine(DATABASE_URL, echo=True)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class Link(Base):
    __tablename__ = 'links'

    id = Column(Integer,  primary_key=True)
    title = Column(String)
    url = Column(String)
    xpath = Column(String)

    def __repr__(self):
        return f"{self.title} - {self.url}"


def validate_url(url) -> bool:
    """
    Валидация ссылок.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def validate_xpath(xpath) -> bool:
    """
    Валидация локаторов XPATH.
    """
    try:
        etree.XPath(xpath)
        return True
    except etree.XPathSyntaxError:
        return False


def create_link(data: List) -> bool:
    """
    Функция создания и сохранения в БД объектов Link.
    """
    if not validate_url(data[1]):
        return False
    if not validate_xpath(data[2]):
        return False

    link = Link(
        title=data[0],
        url=data[1],
        xpath=data[2]
    )
    session.add(link)
    try:
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logging.error(e)
        return False


def parse_links():
    """
    Функция парсинга ссылок и получения цен по локаторам.
    :return: {
    site: string
    average price: float
    }
    """
    site_prices = {}
    links = session.query(Link).all()

    service = Service(executable_path=ChromeDriverManager().install())
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--disable-dev-shm-usage")

    time.sleep(2)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    for link in links:
        driver.get(link.url)
        try:
            price_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, link.xpath))
            )
            if price_element:
                raw_price = price_element.text.strip()
                cleaned_price = float((re.sub(r'[^\d.,]', '', raw_price).replace(",", ".")))
                site_key = urlparse(link.url).netloc
                if site_key not in site_prices:
                    site_prices[site_key] = {'total_price': 0, 'count': 0}
                site_prices[site_key]['total_price'] += cleaned_price
                site_prices[site_key]['count'] += 1
            else:
                logging.error(f'Ошибка парсинга цены по ссылке {link.url}')
        except Exception as e:
            logging.error(f'Ошибка парсинга цены по ссылке {link.url}: {e}')
        driver.quit()
        average_prices = {}
        for site_key, data in site_prices.items():
            average_prices[site_key] = data['total_price'] / data['count']
        return average_prices


Base.metadata.create_all(bind=engine)
