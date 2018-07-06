# -*- coding: utf-8 -*-
import scrapy
from bs4 import BeautifulSoup


class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ['fydok.nl']
    start_urls = ['http://Fydok.nl']

    def parse(self, response):
        res = response.body
        soup = BeautifulSoup(res, 'lxml')
        print(soup)
