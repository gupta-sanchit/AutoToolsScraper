import re
import json
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

from Scraper.script import Scraper


class URLS(Scraper):
    def __init__(self):
        self.data = {}
        super().__init__()

    def getURLS(self):
        response = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")

        categories = soup.findAll('li', class_='nav')

        with ThreadPoolExecutor(max_workers=20) as executor:
            threads = []
            for i in categories:
                threads.append(executor.submit(self.category, cat=i))

            for thread in tqdm(as_completed(threads), total=len(threads)):
                data, cat = thread.result()
                self.data[cat] = data
        with open('../data/URL.json', 'w') as fp:
            json.dump(self.data, fp, indent=4)

    def category(self, cat) -> 'store json':

        catName = cat.a.text
        BASE_URL = cat.a['href']
        subCatUrls = self.check_subCat(BASE_URL=BASE_URL)
        # self.data[catName] = {}
        if subCatUrls:
            catData = {}
            for subcat in subCatUrls.keys():
                BASE_URL = subCatUrls[subcat]
                lastPage = self.number_of_pages(url=BASE_URL)
                catUrlList = []
                if lastPage != 0:
                    for i in range(1, lastPage + 1):
                        URL = BASE_URL + f"?searching=Y&sort=1&cat=1&page={i}"
                        catUrlList.append(URL)
                    catData[subcat] = catUrlList
                    # self.data[catName][subcat] = catUrlList
        else:
            catData = []
            lastPage = self.number_of_pages(url=BASE_URL)
            catUrlList = []
            if lastPage != 0:
                for i in range(1, lastPage + 1):
                    URL = BASE_URL + f"?searching=Y&sort=1&cat=1&page={i}"
                    catUrlList.append(URL)
                catData = catUrlList
                # self.data[catName] = catUrlList

        return catData, catName

    def check_subCat(self, BASE_URL):

        response = requests.get(BASE_URL, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")

        subCat = soup.findAll('a', class_='subcategory_link')

        urls = {}
        if len(subCat) == 0: return urls

        for i in subCat:
            name = i.span.text
            urls[name] = i['href']

        return urls

    def number_of_pages(self, url) -> 'int':
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")

        x = soup.find('input', title='Go to page')

        if x is None: return 0

        lastPage = x.parent.text.strip()
        lastPage = re.findall(r'\d+', lastPage)
        lastPage = list(map(int, lastPage))

        return lastPage[len(lastPage) - 1]


if __name__ == '__main__':
    u = URLS()
    u.getURLS()
