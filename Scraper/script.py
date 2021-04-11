import re
import json
import requests
from pprint import pprint
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor


class Scraper:
    def __init__(self):
        self.res = {'data': []}
        self.url = 'https://www.eautotools.com/category-s/1748.htm'
        self.headers = {"Accept-Language": "en-US, en;q=0.5"}

    def scrapSite(self) -> 'store csv':
        with open('../data/URL1.json', 'r') as fp:
            urls = json.load(fp)

        with ThreadPoolExecutor(max_workers=20) as executor:
            threads = []
            idx = 0
            for cat in urls.keys():
                x = urls[cat]
                if isinstance(x, dict):
                    for subcat in x.keys():
                        for url in x[subcat]:
                            if idx == 50: break
                            idx += 1
                            threads.append(executor.submit(self.scrapCategory, url=url, category=cat, subcat=subcat))
                else:
                    for url in x:
                        if idx == 50: break
                        idx += 1
                        threads.append(executor.submit(self.scrapCategory, url=url, category=cat))
            for process in tqdm(as_completed(threads), total=len(threads)):
                category, productList = process.result()
                self.res['data'] += productList
                print(f"\nCOMPLETED ==> {category}", end='\n')
        try:
            with open('../data/products.json', 'w') as fp:
                json.dump(self.res, fp, indent=4)
        except BaseException as e:
            print(e)

        df = pd.json_normalize(self.res['data'], max_level=0)
        print(df)
        df.to_csv('../data/TEMP.csv', index=False)

    def handleCategory(self, category, url_List):

        catProductList = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            threads = []
            for url in url_List:
                threads.append(executor.submit(self.scrapCategory, category=category, url=url))
            for thread in as_completed(threads):
                catProductList += thread.result()

        return category, catProductList

    def productPage(self, url) -> 'tuple':
        res = self.getResponse(url)
        x = BeautifulSoup(res.text, "lxml")

        for tag in x.find_all('strong'):
            if tag.text.lower() == 'features and benefits:':
                tag.extract()

        desc = x.find('div', id='ProductDetail_ProductDetails_div')
        code = x.find('span', class_='product_code').text

        zoomPhoto = x.find('a', id='product_photo_zoom_url2')

        brand = x.find('meta', itemprop='manufacturer')['content']
        if zoomPhoto:
            imgURL = 'https:' + zoomPhoto['href']
        else:
            try:
                imgURL = 'https:' + x.find('img', id='product_photo')['src']
            except TypeError as e:
                print(e, url)
                imgURL = x.find('a', id='product_photo_zoom_url')['href']
        return code, str(desc), imgURL, brand

    def scrapCategory(self, url, category, subcat=None) -> 'tuple':
        response = self.getResponse(url)
        soup = BeautifulSoup(response.text, "lxml")

        productContainer = soup.findAll('div', class_='v-product')
        products = []
        for one in productContainer:
            a = one.find('a', class_='v-product__img')
            productURL = a['href']

            code, desc, imgURL, productBrand = self.productPage(productURL)
            productName = a.img['title']
            price = one.find('div', class_='product_productprice').b.text.split(" ")[2]
            categoryName = f"{category} > {subcat}" if subcat else category
            r = {
                'product-code': code,
                'product-category': categoryName,
                'ProductName': productName,
                'price': price,
                'brand': productBrand,
                'Description': desc,
                'ImageURL': imgURL
            }

            products.append(r)
        # print(category)
        return category, products

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
                    URL = BASE_URL + f"?searching=Y&sort=1&cat=1&page={i}"
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

    def getResponse(self, url):
        # session = requests.Session()
        # retry = Retry(connect=5, backoff_factor=2, status_forcelist=[502, 503, 504])
        # adapter = HTTPAdapter(max_retries=retry)
        # session.mount('http://', adapter)
        # session.mount('https://', adapter)
        response = requests.get(url, headers=self.headers)
        return response


if __name__ == '__main__':
    s = Scraper()
    # s.getURLS()
    s.scrapSite()
