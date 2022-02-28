# -*- coding: utf-8 -*-
import json
import scrapy
import string
from random import random
from requests_toolbelt import MultipartEncoder
from sys import maxsize
from scrapy.exceptions import CloseSpider
import itertools


def remove_tag(description):
    if description:
        description = description.strip()
        description = description.replace('\t', "")
        description = description.replace('\n', "")
        description = description.encode('ascii', 'ignore')
        description = description.decode()
        return description


def gen_boundary():
    alpha_numeric_encoding_map = \
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789AB'

    boundary = '----WebKitFormBoundary'

    for i in range(4):
        boundary += alpha_numeric_encoding_map[int(random() * (maxsize + 1)) >> 24 & 0x3F]
        boundary += alpha_numeric_encoding_map[int(random() * (maxsize + 1)) >> 16 & 0x3F]
        boundary += alpha_numeric_encoding_map[int(random() * (maxsize + 1)) >> 8 & 0x3F]
        boundary += alpha_numeric_encoding_map[int(random() * (maxsize + 1)) & 0x3F]

    return boundary


def input_list(keyword, location):
    k = keyword.replace('\n', '').split('#')
    l = location.replace('\n', '').split('#')
    return list(itertools.product(k, l))


class YlpSpider(scrapy.Spider):
    name = "german"
    allowed_domains = ["gelbeseiten.de"]
    alphabets = string.ascii_lowercase
    position = 0
    total_pages = 0

    # start_loading_index = 0

    # keyword = 'Restaurants'
    # location = '78120'
    def __init__(self, kword, location=None, distance='50000', *args, **kwargs):
        self.k = kword
        self.l = location
        self.dis = distance

    def start_requests(self):

        q = input_list(self.k, self.l)

        for i, query in enumerate(q):
            keyword, location = query
            distance =self.dis
            payload = {
                'umkreis': f'{distance}',
                'WAS': f'{keyword}',
                'position': '0',
                'WO': f'{location}',
                'sortierung': 'relevanz',

            }
            me = MultipartEncoder(fields=payload, boundary=gen_boundary())
            me_body = me.to_string()
            header = {'Content-Type': me.content_type,
                      'origin': "https://www.gelbeseiten.de",
                      'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30",
                      # 'referer': f'https://www.gelbeseiten.de/Suche/{keyword}/{location}?umkreis={distance}',
                      'Accept': '*/*',
                      # 'Accept-Encoding': 'gzip, deflate, sdch',
                      # 'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',

                      }
            yield scrapy.FormRequest(
                url='https://www.gelbeseiten.de/AjaxSuche',
                headers=header,
                body=me_body,
                callback=self.parse,
                method='POST',
                meta={'k': keyword, 'l': location, 'd': distance}
            )

    def parse(self, response, **kwargs):
        keyword = response.meta['k']
        location = response.meta['l']
        distance = response.meta['d']

        if len(response.text) <= 0:
            raise CloseSpider('Process Compelted')

        js = json.loads(response.text)

        if self.total_pages == 0:
            self.total_pages = int(js.get('gesamtanzahlTreffer'))
            self.position = int(js.get('anzahlTreffer')) + 1
        else:
            self.position += 10

        print('Total Records:{}'.format(self.total_pages))
        print('Search Term:{}'.format(keyword))
        print('Search Area:{}'.format(location))
        print('Current Postion:{}'.format(self.position))
        resp = scrapy.selector.Selector(text=js.get('html'))

        articless = resp.xpath('//article')
        print("Article Count", len(articless))
        for articles in articless:
            jd = articles.xpath('.//@data-lazyloaddata').get()
            if jd:
                company = json.loads(jd)
                url = company.get('detailseitenUrl')
                hit_btn_list = company.get('trefferButtonListList').get('trefferButtonListList')
                website = None
                email = None

                for item in hit_btn_list[0]:
                    if item.get('type') == "homepage":
                        website = item.get('gcLink').get('href', 'N/A')
                    if item.get('type') == "email":
                        email = item.get('gcLink').get('href')

                business_name = company.get('name')
                address = company.get('adresseKompakt')
                phone = address.get('telefonnummer', '')
                street_number = address.get('strasseHausnummer', '')
                postal_code = address.get('plzOrt', '')
                district = address.get('stadtteil', '')
                dis_km = address.get('entfernungText', '')
                address = f'{street_number if street_number else ""}{postal_code if postal_code else ""}{district if district else ""} {dis_km if dis_km else ""}'
                if email and email.startswith('mailto'):
                    email = email.split('?')[0].replace('mailto:', '')
                else:
                    email = 'n/a'
                yield {
                    'Search Area': remove_tag(location),
                    'Search Term': remove_tag(keyword),
                    'Business': remove_tag(business_name),
                    'Email': email,
                    'Website': website,
                    'Phone': phone,
                    'Address': remove_tag(address)

                }
            else:
                business_name = articles.xpath('.//h2/text()').get()
                street_number = articles.xpath('.//address/p[@class="Adresse"]/text()').get()
                postal_code = articles.xpath('.//address/p[@class="Adresse"]/span[@class="nobr"]/text()').get()
                dis_km = articles.xpath(
                    './/address/p[@class="Adresse"]/span[@class="mod-AdresseKompakt__entfernung"]/text()').get()
                address = f'{street_number if street_number else ""}{postal_code if postal_code else ""}{dis_km if dis_km else ""}'
                phone = articles.xpath('.//address/p[@class="mod-AdresseKompakt__phoneNumber"]/text()').get()
                website = articles.xpath(
                    '//div[contains(@class, "mod-Treffer__buttonleiste")]/div[@class="mod-GsSlider__slider"]/a[contains(@class,"contains-icon-homepage")]/@href').get()
                email = articles.xpath(
                    '//div[contains(@class, "mod-Treffer__buttonleiste")]/div[@class="mod-GsSlider__slider"]/a[contains(@class,"contains-icon-email")]/@href').get()
                if email and email.startswith('mailto'):
                    email = email.split('?')[0].replace('mailto:', '')
                else:
                    email = 'n/a'
                yield {
                    'Search Area': remove_tag(location),
                    'Search Term': remove_tag(keyword),
                    'Business': remove_tag(business_name),
                    'Email': email,
                    'Website': website,
                    'Phone': phone,
                    'Address': remove_tag(address)

                }

        if self.position < self.total_pages:
            payload = {
                'umkreis': f'{distance}',
                'WAS': f'{keyword}',
                'position': f'{self.position}',
                'WO': f'{location}',
                'anzahl': '10',
                'sortierung': 'relevanz',

            }

            me = MultipartEncoder(fields=payload, boundary=gen_boundary())
            me_body = me.to_string()
            header = {'Content-Type': me.content_type,
                      'origin': "https://www.gelbeseiten.de",
                      'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30",
                      'referer': f'https://www.gelbeseiten.de/Suche/{keyword}/{location}/?umkreis={distance}',
                      'Accept': 'application/json,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                      'Accept-Encoding': 'gzip, deflate, sdch',
                      'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',

                      }
            yield scrapy.Request(
                url='https://www.gelbeseiten.de/AjaxSuche',
                headers=header,
                body=me_body,
                callback=self.parse,
                method='POST',
                meta={'k': keyword, 'l': location, 'd': distance}

            )
