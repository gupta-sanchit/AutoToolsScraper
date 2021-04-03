import re
import json
import requests
from bs4 import BeautifulSoup
from pprint import pprint
import pandas as pd
from tqdm import tqdm

from concurrent.futures import ThreadPoolExecutor, as_completed


class Scraper:
    def __init__(self):
        self.res = {'data': []}
        self.url = 'https://www.eautotools.com/category-s/1748.htm'

        self.headers = {"Accept-Language": "en-US, en;q=0.5"}

    def scrapSite(self) -> 'store csv':
        with open('../data/URL.json', 'r') as fp:
            urls = json.load(fp)

        with ThreadPoolExecutor(max_workers=20) as executor:
            threads = []
            for cat in urls.keys():
                for i in urls[cat]:
                    threads.append(executor.submit(self.scrapCategory, category=cat, url=i))
            for thread in tqdm(as_completed(threads), total=len(threads)):
                productsList = thread.result()
                self.res['data'] += productsList

        df = pd.json_normalize(self.res['data'], max_level=0)
        print(df)
        df.to_csv('../data/Site.csv', index=False)

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
            try:
                imgURL = 'https:' + x.find('img', id='product_photo')['src']
            except Exception as e:
                print(e, url)
                imgURL = x.find('a', id='product_photo_zoom_url')['href']
        return code, str(desc), imgURL

    def scrapCategory(self, url, category) -> 'list of json':
        response = requests.get(url, headers=self.headers)
        # print('*********************************************************************' + category)
        soup = BeautifulSoup(response.text, "lxml")

        productContainer = soup.findAll('div', class_='v-product')
        products = []
        for one in productContainer:
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
            # tqdm.write(f"\n{category} completed !!\n")
            # print(f"{category} ==> completed")
        return products

    def getURLS(self) -> 'store json':
        url = {}
        response = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")

        categories = soup.findAll('li', class_='nav')

        for cat in categories:
            catName = cat.a.text
            BASE_URL = cat.a['href']
            lastPage = self.number_of_pages(BASE_URL)

            catUrlList = []
            if lastPage == 0:
                sub_urls = self.check_subCat(BASE_URL)
                if len(sub_urls) != 0:
                    for i in sub_urls:
                        pCount = self.number_of_pages(i)
                        for j in range(1, pCount + 1):
                            URL = i + f"&page={j}"
                            catUrlList.append(URL)
                else:
                    pass
            else:
                for i in range(1, lastPage + 1):
                    URL = BASE_URL + f"&page={i}"
                    catUrlList.append(URL)
            url[catName] = catUrlList

        with open('../data/URL.json', 'w') as fp:
            json.dump(url, fp, indent=4)

    def check_subCat(self, BASE_URL):

        response = requests.get(BASE_URL, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")

        subCat = soup.findAll('a', class_='subcategory_link')

        urls = []
        if len(subCat) != 0:
            for i in subCat:
                urls.append(i['href'])
        return urls

    def number_of_pages(self, url) -> 'int':
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")

        x = soup.find('input', title='Go to page')

        if x is None:
            print(f"SubCat Check for URL ==> {url}")
            return 0

        lastPage = x.parent.text.strip()
        lastPage = re.findall(r'\d+', lastPage)
        lastPage = list(map(int, lastPage))

        return lastPage[len(lastPage) - 1]


if __name__ == '__main__':
    s = Scraper()
    # s.getURLS()
    s.scrapSite()
# 12 46