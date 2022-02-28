import itertools
import json
import re
import time
import scrapy
from scrapyselenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.exceptions import CloseSpider


def input_list(keyword, location):
    k = keyword.replace('\n', '').split('#')
    l = location.replace('\n', '').split('#')
    return list(itertools.product(k, l))


class YpAuSpider(scrapy.Spider):
    name = 'yp_au'
    allowed_domains = ['yellowpages.com.au']
    previous = ''
    page_status = False

    def __init__(self, kword, location='', *args, **kwargs):
        self.k = kword
        self.l = location

    def start_requests(self):
        q = input_list(self.k, self.l)

        req = SeleniumRequest(
            url='https://www.yellowpages.com.au',
            wait_time=60,
            callback=self.parse,
            dont_filter=True,
            meta={'page': None, 'q': q, 'k': None, 'l': None}

        )
        req.headers['Cookie'] = 'js_enabled=true; is_cookie_active=true;'
        yield req

    def parse(self, response):
        driver = response.meta['driver']
        query = response.meta['q']
        keyword, location = query[0]
        if len(query)<=0:
            raise CloseSpider('The process has been completed')
        if self.previous not in query:
            self.previous = (keyword, location)
            try:

                print(f'Keyword:{keyword}')
                print(f'Locaton:{location}')

                driver.get('https://www.yellowpages.com.au')
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'clue'))).send_keys(keyword)

                time.sleep(3)
                if location:
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'where'))).send_keys(
                        location)

                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'button-search'))).click()

            except:
                pass
        WebDriverWait(driver, 1200).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.MuiToggleButton-label')))
        time.sleep(5)
        result = driver.page_source
        pattren = re.compile(r'\bwindow\.__INITIAL_STATE__\s*=\s*(\{.*?\};)\s*', re.DOTALL | re.MULTILINE)
        json_data = pattren.findall(result)
        final_result = json.loads(json_data[0][:-1])
        next_page = final_result.get('model').get('pagination').get('nextPageLink', None)
        print(next_page)
        if next_page is None:
            query.remove((keyword, location))
        result_items = final_result.get('model').get('inAreaResultViews')
        for item in result_items:
            address = None
            if item.get('name'):
                try:
                    addressView = item.get('addressView', None)
                    if addressView:
                        street = addressView.get('addressLine')
                        post_code = addressView.get('postCode')
                        state = addressView.get('state')
                        suburb = addressView.get('suburb')
                        address = f'{street}, {suburb} {state} {post_code}'

                    yield {
                        'Search Term': keyword,
                        'Search Area': location,
                        'Business Name': item.get('name'),
                        "Business Description": item.get('longDescriptor'),
                        'Email': item.get('primaryEmail'),
                        'Website': item.get('website'),
                        'phone': item.get('callContactNumber').get('displayValue'),
                        'Address': address if address else "",

                    }
                except:
                    pass

        if next_page:
            req = SeleniumRequest(
                url=response.urljoin(next_page),
                wait_time=60,
                callback=self.parse,
                dont_filter=True,
                meta={'q': query}

            )
            req.headers['Cookie'] = 'js_enabled=true; is_cookie_active=true;'
            yield req
        else:
            req = SeleniumRequest(
                url='https://www.yellowpages.com.au',
                wait_time=60,
                callback=self.parse,
                dont_filter=True,
                meta={'q': query}

            )
            req.headers['Cookie'] = 'js_enabled=true; is_cookie_active=true;'
            yield req
