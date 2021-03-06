import json
import pandas as pd
from time import time
from tqdm import tqdm
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession
from requests.packages.urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed


class Scraper:
    def __init__(self):
        self.res = {'data': []}
        self.url = 'https://www.eautotools.com/category-s/1748.htm'
        self.headers = {"Accept-Language": "en-US, en;q=0.5"}

        self.session = FuturesSession(executor=ThreadPoolExecutor())
        retry = Retry(connect=5, backoff_factor=2, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def scrapSite(self) -> 'store csv':
        with open('../data/URL.json', 'r') as fp:
            urls = json.load(fp)

        with ThreadPoolExecutor() as executor:
            threads = []
            # idx = 0
            for cat in urls.keys():
                # if idx == 11: break
                # idx += 1
                x = urls[cat]
                if isinstance(x, dict):
                    for subcat in x.keys():
                        for url in x[subcat]:
                            threads.append(executor.submit(self.scrapCategory, url=url, category=cat, subcat=subcat))
                else:
                    for url in x:
                        threads.append(executor.submit(self.scrapCategory, url=url, category=cat))
            for thread in tqdm(as_completed(threads), total=len(threads)):
                category, productList = thread.result()
                self.res['data'] += productList
                print(f"\nCOMPLETED ==> {category}", end='\n')
        try:
            with open('../data/products.json', 'w') as fp:
                json.dump(self.res, fp, indent=4)
        except BaseException as e:
            print(e)

        df = pd.json_normalize(self.res['data'], max_level=0)
        print(df)
        df.to_csv('../data/Site.csv', index=False)

    def handleCategory(self, category, url_List):

        catProductList = []
        with ThreadPoolExecutor() as executor:
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
        specs = x.find('div', id='ProductDetail_TechSpecs_div')

        specs = specs if specs else ''

        code = x.find('span', class_='product_code').text

        zoomPhoto = x.find('a', id='product_photo_zoom_url2')

        brand = x.find('meta', itemprop='manufacturer')['content']

        listPriceDiv = x.find('div', class_='product_listprice')
        listPrice = listPriceDiv.b.text.split(" ")[2] if listPriceDiv else 'NA'

        catContainer = x.find('td', class_='vCSS_breadcrumb_td')

        cats = catContainer.findAll('a')

        cat = ''
        for i in range(2, len(cats)):
            cat += cats[i].text + ' >' if i != len(cats) - 1 else cats[i].text

        cat = cat.strip()
        cat = cat.replace(',', '-')
        cat = cat.replace('/', '-')
        if zoomPhoto:
            imgURL = 'https:' + zoomPhoto['href']
        else:
            try:
                imgURL = 'https:' + x.find('img', id='product_photo')['src']
            except TypeError as e:
                print(e, url)
                imgURL = x.find('a', id='product_photo_zoom_url')['href']
        return code, str(desc), imgURL, brand, listPrice, cat, str(specs)

    def scrapCategory(self, url, category, subcat=None) -> 'tuple':
        response = self.getResponse(url)
        soup = BeautifulSoup(response.text, "lxml")

        productContainer = soup.findAll('div', class_='v-product')
        products = []
        for one in productContainer:
            a = one.find('a', class_='v-product__img')
            productURL = a['href']

            code, desc, imgURL, productBrand, listPrice, cat, specs = self.productPage(productURL)
            productName = one.find('a', class_='v-product__title').text.strip()
            yourPrice = one.find('div', class_='product_productprice').b.text.split(" ")[2]
            r = {
                'product-code': code,
                'product-category': cat,
                'ProductName': productName,
                'list-price': listPrice,
                'your-price': yourPrice,
                'brand': productBrand,
                'Description': desc,
                'Specifications': specs,
                'ImageURL': imgURL
            }

            products.append(r)
        return category, products

    def getResponse(self, url):
        response = self.session.get(url, headers=self.headers)
        return response.result()


if __name__ == '__main__':
    start = time()

    s = Scraper()
    s.scrapSite()

    print(f'TIME TAKEN ==> {time() - start}')
