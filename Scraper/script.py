import requests
import re
import json
from bs4 import BeautifulSoup
from pprint import pprint
import pandas as pd
from tqdm import tqdm


class Scraper:
    def __init__(self):
        self.res = {}
        self.url = 'https://www.eautotools.com/Come-Alongs-Chain-Hoists-s/498.htm'
        self.count = 0

        self.headers = {"Accept-Language": "en-US, en;q=0.5"}
        res = requests.get(self.url, headers=self.headers)

        self.soup = BeautifulSoup(res.text, "lxml")

    def scrap(self):
        res = requests.get(self.url, headers=self.headers)
        self.soup = BeautifulSoup(res.text, "lxml")
        self.scrapPage('Come-Alongs-Chain-Hoists')

        res = requests.get('https://www.eautotools.com/Autel-ADAS-s/2478.htm', headers=self.headers)
        self.soup = BeautifulSoup(res.text, "lxml")
        self.scrapPage('ADAS')

        df = pd.DataFrame(self.res).T.reset_index(drop=True)
        print(df)
        df.to_csv('../sampleFinal.csv', index=False)

    def description(self, url):
        res = requests.get(url, headers=self.headers)

        x = BeautifulSoup(res.text, "lxml")

        for tag in x.find_all('strong'):

            if tag.text.lower() == 'features and benefits:':
                tag.extract()

        desc = x.find('div', id='ProductDetail_ProductDetails_div')

        code = x.find('span', class_='product_code').text

        zoomPhoto = x.find('a', id='product_photo_zoom_url2')
        if zoomPhoto:
            imgURL = 'https:' + zoomPhoto['href']
        else:
            imgURL = 'https:' + x.find('img', id='product_photo')['src']

        return code, desc, imgURL

    def scrapPage(self, category):
        productContainer = self.soup.findAll('div', class_='v-product')
        print(len(productContainer))
        r = {}
        for one in tqdm(productContainer):
            a = one.find('a', class_='v-product__img')
            descURL = a['href']

            code, desc, imgURL = self.description(descURL)
            productName = a.img['title']
            productBrand = productName.split(' ')[0]
            price = one.find('div', class_='product_productprice').b.text.split(" ")[2]

            r = {
                'product-code': code,
                'product-category': category,
                'ProductName': productName,
                'price': price,
                'brand': productBrand,
                'Description': desc,
                'ImageURL': imgURL
            }
            self.count += 1

            self.res[self.count] = r


if __name__ == '__main__':
    s = Scraper()
    s.scrap()
