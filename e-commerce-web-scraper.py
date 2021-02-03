from bs4 import BeautifulSoup
import json
import numpy as np
import requests
import csv

HM_URL = 'https://www2.hm.com'

ITEMS_URL = {
    'shorts': r'https://www2.hm.com/en_us/women/products/shorts.html?sort=stock&image-size=small&image=model&offset=0&page-size=72',

}

COLUMN_HEADERS = [
    'name',
    'description',
    'image',
    'color',
    'price',
    'category'
]

agent = {
    "User-Agent": 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}


def findGoodImage(soupPageContent, color):
    """
    Function finds link to product image instead of model image

    :param soupPageContent: BeautifulSoup object with specific product page content
    :param color: color version of product
    :return: link to product image
    """

    re = soupPageContent.find('div', class_="catalogwarning parbase")
    res = re.find_next('script')

    res = str(res)
    ind = res.find(color)
    a = res[ind:].find(r"images':[")
    b = res[ind:].find(r"video':")
    images = res[ind + a:ind + b]

    temp = images.find('DESCRIPTIVESTILLLIFE')
    x = images[temp:].find(r"image': isDesktop ?")
    y = images[temp:].find(r"file:/product/main")

    link = images[x + temp + 21:y + temp + len(r"file:/product/main]")]

    return link


def getNewItem(url, category):
    """
    Function returns json product based on H&M page

    :param url: product url
    :param category: product category
    :return: new product schema
    """

    itemPage = requests.get(url, headers=agent)
    productSoup = BeautifulSoup(itemPage.content, 'lxml')

    result = productSoup.find(id="product-schema")

    if result is not None:

        # find the product schema on the H&M product page
        result = result.find_all(text=True, recursive=False)
        result = str(result)
        result = result.replace(r'\r\n', ' ')
        result = result.replace(r'[{', '')
        result = result[:result.find(r'"brand')] + result[result.find(r'"url"'):]

        hmProductSchema = json.loads(result[2:-5])

        # if main image is model image find product image
        if hmProductSchema['image'].find('DESCRIPTIVESTILLLIFE') == -1:
            hmProductSchema['image'] = findGoodImage(productSoup, hmProductSchema['color'])

        newItem = [
                 hmProductSchema['name'],
                 hmProductSchema['description'],
                 hmProductSchema['image'],
                 hmProductSchema['color'],
                 float(hmProductSchema['price']),
                 category
        ]

        return newItem



def saveDataToCSV(URL, category):
    """
    Function inserts items to CSV file if the product does not exist

    :param URL: URL of specific product
    :param category: category of product
    """
    page = requests.get(URL, headers=agent)

    soup = BeautifulSoup(page.content, 'html.parser')

    if soup:
        print("Received HTML document!")
    else:
        print("Could not receive HTML document!")

    results = soup.find_all('div', class_="image-container")

    if results:
        print("Found image-container!")

        items = []
        for el in results:
            link = el.find('a')
            items.append(getNewItem(HM_URL + link.get('href'), category))

        with open('items.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(COLUMN_HEADERS)
            writer.writerows(items)
    else:
        print("Could not find image-container!")


def main():
    for link in ITEMS_URL:
        saveDataToCSV(ITEMS_URL[link], link)


if __name__ == "__main__":
    main()
