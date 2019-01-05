#!/usr/bin/env python3
import os
import re
import time
from termcolor import cprint
import requests
import json
import hashlib
import yaml
from bs4 import BeautifulSoup

from ipdb import set_trace

settings = "settings.yaml"

base_url = "https://www.ebay-kleinanzeigen.de{}"
product_search_url = "https://www.ebay-kleinanzeigen.de/s-suchanfrage.html?keywords={}&categoryId=&locationStr={}&locationId=&radius=0&sortingField=SORTING_DATE&adType=&posterType=&pageNum=1&action=find&maxPrice=&minPrice="

DATA_DIR = "data"
SEARCH_PAGES = 2


class Offer(object):

    def __init__(self, offer_html):
        bs = BeautifulSoup(offer_html, 'html.parser')
        self.title = bs.find("meta", {'property':"og:title"}).attrs['content']
        self.image_url = bs.find("meta", {'property':"og:image"}).attrs['content']
        self.description = bs.find("meta", {'property':"og:description"}).attrs['content']
        self.url = bs.find("meta", {'property':"og:url"}).attrs['content']
        self.locality = bs.find("meta", {'property':"og:locality"}).attrs['content']
        self.latitude = bs.find("meta", {'property':"og:latitude"}).attrs['content']
        self.longitude = bs.find("meta", {'property':"og:longitude"}).attrs['content']
        try:
            self.price = re.findall('\d+', re.findall(r'ExactPreis": "\d+"', offer_html)[0])[0]
        except:
            self.price = 0 


    def __repr__(self):
        return self.title

    
class EbayKleinanzeigen(object):


    def __init__(self):
        self.create_requests_session() 
        self.settings = yaml.safe_load(open(settings))
        self.notifications = []
        for search in self.settings.get('ebay-kleinanzeigen', []):
            cprint("Looking for '{}' in {}".format(search['product'], search['location']), 'magenta')
            self.search(search['product'], search['location'], search.get('max_price', -1))

    
    def create_requests_session(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ebay-kleinanzeigen bod'})


    def search(self, product, location, price):
        search_url = self.session.get(product_search_url.format(product, location)).url # follows a redirect
        offers = []
        for offer_html in self.get_offers_as_html(search_url, price, product):
            offer = Offer(offer_html)
            cprint("   Found: '{}'".format(offer.title), 'green')
            offers.append(offer)

        filename = os.path.join(DATA_DIR, "{}-{}.json".format(product, location))
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                json.dump([o.__dict__ for o in offers], f)
        self.find_new_offers(offers, filename)

    
    def get_offers_as_html(self, base_search_url, price, product):
        parts = base_search_url.split("/")
        if base_search_url.endswith("k0"): 
            # deutschland-weite Suche
            search_url = "https://www.ebay-kleinanzeigen.de/s-anzeige:angebote/seite:{}/preis:{}/%s/k0" % product
        else:
            search_url = "/".join(parts[:len(parts)-2]) + \
                         "/anzeige:angebote/" + \
                         "seite:{}/" + \
                         "preis::{}/" + \
                         "/".join(parts[len(parts)-2:])
        print(search_url)
        for i in range(1, SEARCH_PAGES+1):
            print(" Looking at result page {}".format(i))
            resp = self.session.get(search_url.format(i, price), allow_redirects=False)
            if "Es wurden keine Anzeigen für" in resp.text or resp.status_code == 302:
                print("  Nothing found here")
                return
            if "You look like a robot" in resp.text:
                cprint("Bot detection. What helped for me: use ipv4 instead of ipv6 (don't know why). Just put the ipv4 addresses for www.ebay-kleinanzeigen.de in /etc/hosts", "red")
                exit()
            relevant_html = resp.text.split("Alternative Anzeigen")[0]
            bs = BeautifulSoup(relevant_html, 'html.parser')
            offer_links = [x['data-href'] for x in bs.findAll('div', {'class': 'imagebox srpimagebox'})]
            for offer_url in offer_links:
                resp =  self.session.get(base_url.format(offer_url))
                if resp.status_code == 429:
                    cprint("Bot error: Too many requests \n{}\n{}".format(resp.headers, resp.text), 'red')
                    return
                yield resp.text
            self.create_requests_session() 



    def find_new_offers(self, offers, filename):
        print("Comparing the crawled offers with the last ones")
        offers_last_state = json.load(open(filename))
        offer_urls_last_time = [o['url'] for o in offers_last_state]
        for offer in offers:
            if offer.url not in offer_urls_last_time:
                self.notify_test(offer)
                self.notifications.append(offer)
        with open(filename, "w") as f:
            json.dump([o.__dict__ for o in offers], f)
    

    def notify_test(self, offer):
        cprint("   Found new offer: {}".format(offer.url), 'cyan')


if __name__ == '__main__':
    EbayKleinanzeigen()


def go():
    ebk = EbayKleinanzeigen()
    return ['Ebay Kleinanzeigen: {} für {} EUR {}'.format(x.title, x.price, x.url) for x in ebk.notifications]

