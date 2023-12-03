import logging

from lxml import etree
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
from urllib.parse import urlparse

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


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def validate_xpath(xpath):
    try:
        etree.XPath(xpath)
        return True
    except etree.XPathSyntaxError:
        return False


def create_link(data: List) -> bool:
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
        logging.ERROR(e)
        return False


Base.metadata.create_all(bind=engine)
