import json
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import pandas as pd
from tqdm import tqdm

from concurrent.futures import ThreadPoolExecutor


class Scraper:
    def __init__(self):
        self.res = {'data': []}
        self.url = 'https://www.eautotools.com/category-s/1748.htm'

        self.headers = {"Accept-Language": "en-US, en;q=0.5"}

    def getURLS(self) -> 'store json':
        url = {}
        response = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")

        categories = soup.findAll('li', class_='nav')

        for cat in categories:
            url[cat.a.text] = cat.a['href']

        with open('../data/URL.json', 'w') as fp:
            json.dump(url, fp, indent=4)

    def scrapSite(self) -> 'store csv':
        with open('../data/URL.json', 'r') as fp:
            urls = json.load(fp)
        idx = 0
        for cat in urls.keys():
            if idx == 2:
                break
            idx += 1
            productsList = self.scrapCategory(category=cat, url=urls[cat])
            self.res['data'] += productsList

        df = pd.json_normalize(self.res['data'], max_level=0)
        print(df)
        # pprint(self.res)
        df.to_csv('../data/TEMP.csv', index=False)

    def scrap(self):
        res = requests.get('https://www.eautotools.com/Come-Alongs-Chain-Hoists-s/498.htm', headers=self.headers)
        soup = BeautifulSoup(res.text, "lxml")
        self.scrapCategory('Come-Alongs-Chain-Hoists')

        res = requests.get('https://www.eautotools.com/Autel-ADAS-s/2478.htm', headers=self.headers)
        soup = BeautifulSoup(res.text, "lxml")
        self.scrapCategory('ADAS')

        df = pd.json_normalize(self.res['data'], max_level=0)
        print(df)
        df.to_csv('../data/TEMP.csv', index=False)

    def productPage(self, url) -> 'tuple':
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

        return code, str(desc), imgURL

    def scrapCategory(self, url, category) -> 'list of json':

        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")

        productContainer = soup.findAll('div', class_='v-product')
        print(len(productContainer))

        products = []
        for one in tqdm(productContainer):
            a = one.find('a', class_='v-product__img')
            productURL = a['href']

            code, desc, imgURL = self.productPage(productURL)
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

            products.append(r)
        return products


if __name__ == '__main__':
    s = Scraper()
    # s.scrap()
    s.scrapSite()
