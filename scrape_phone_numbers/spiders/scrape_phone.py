# -*- coding: utf-8 -*-
import scrapy
import re

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError


class ScrapePhoneNumbersItem(scrapy.Item):
    phone = scrapy.Field()
    source = scrapy.Field()


class ScrapePhoneSpider(scrapy.Spider):

    name = 'scrape_phone'

    bad_url = 'not_working_url.csv'
    dns_error = 'dns_error.csv'
    found_url = 'working_url.csv'

    not_found_url = 'not_found_url_2.csv'
    redirected_urls = 'redirected_urls_2.csv'
    internal_server_error = 'internal_err_2.csv'
    timeout_error = 'timeout.csv'

    def start_requests(self):
        with open('urls_to_scrape_full_urls.csv','r') as read_file:
            for u in read_file.readlines():
                yield scrapy.Request(u.strip(), callback=self.parse_httpbin, errback=self.errback_httpbin, dont_filter=True)

    def parse_httpbin(self, response):

        self.handle_status_codes(response)

        numitems = []

        self.removeNode(response.selector, response.xpath('//style'))
        self.removeNode(response.selector, response.xpath('//script'))

        print('BODY', response.body)
        selector = response.xpath('string(//body)').extract()  # returns a list
        print('PARSED BODY', selector)
        sanitized = ''.join([re.sub(r'[^\+a-zA-Z\d+\-]+', '', item) for item in selector])  # remove alphanumeric characters, making a list comprehension
        print('SANITIZED BODY',sanitized)

        pattern = re.compile('[\d+\-]{9,12}')

        numbers = pattern.findall(sanitized)
        print('SCRAPED NUMBERS',numbers)

        v = set(numbers)
        for number in zip(v):
            numitem = ScrapePhoneNumbersItem()
            numitem['phone'] = number
            numitem['source'] = response.url
            numitems.append(numitem)

        return numitems

            # yield {'number':number, 'url':response.url}

    def removeNode(self, context, nodeToRemove):
        for element in nodeToRemove:
            contentToRemove = element.root # .root returns a html element
            contentToRemove.getparent().remove(contentToRemove) # .getparent() gets parent element of style/script, then removes it

        return context.extract()

    def handle_status_codes(self, response):

        if response.status in range(200, 299) :
            self.append(self.found_url, response.url)

        elif response.status in range(300, 399):
            self.append(self.redirected_urls, response.url)

        elif response.status == 404:
            self.append(self.not_found_url, response.url)

        elif response.status in range(400, 499):
            self.append(self.not_found_url, response.url)

        elif response.status in range(500, 599):
            self.append(self.internal_server_error, response.url)

        else:
            self.append(self.bad_url, response.url)


    def errback_httpbin(self, failure):
        # log all errback failures,
        # in case you want to do something special for some errors,
        # you may need the failure's type
        self.logger.error(repr(failure))

        # if isinstance(failure.value, HttpError):
        if failure.check(HttpError):
            # you can get the response
            response = failure.value.response
            # self.logger.error('HttpError on %s', response.url)
            self.append(self.bad_url, response.url)

        # elif isinstance(failure.value, DNSLookupError):
        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            # self.logger.error('DNSLookupError on %s', request.url)
            self.append(self.dns_error, request.url)

        # elif isinstance(failure.value, TimeoutError):
        elif failure.check(TimeoutError):
            request = failure.request
            # self.logger.error('TimeoutError on %s', request.url)
            self.append(self.dns_error, request.url)

        else:
            self.append(self.bad_url, failure.request.url)

    def append(self, file, string):
        file = open(file, 'a')
        file.write(string + "\n")
        file.close()
