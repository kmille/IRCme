#!/usr/bin/env python3
from bs4 import BeautifulSoup
from ipdb import set_trace
import requests
import json
import hashlib
import os
import yaml
import re
from termcolor import cprint

settings = "settings.yaml"
base_url = "https://www.ebay-kleinanzeigen.de{}"
product_search_url = "https://www.ebay-kleinanzeigen.de/s-suchanfrage.html?keywords={}&categoryId=&locationStr={}&locationId=&radius=0&sortingField=SORTING_DATE&adType=&posterType=&pageNum=1&action=find&maxPrice=&minPrice="
data_dir = "data"

class Offer(object):

    def __init__(self, offer_html):
        bs = BeautifulSoup(offer_html, 'html.parser')
        self.image_url = bs.find("meta", {'property':"og:image"}).attrs['content']
        self.description = bs.find("meta", {'property':"og:description"}).attrs['content']
        self.title = bs.find("meta", {'property':"og:title"}).attrs['content']
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
        self.session = requests.Session()
        self.session.headers.update({'user-agent': 'ebay-kleinanzeigen bot'})
        
        self.settings = yaml.safe_load(open(settings))
        self.notifications = []
        for search in self.settings['searches']:
            cprint("Looking for '{}' in {}".format(search['product'], search['location']), 'magenta')
            self.search(search['product'], search['location'], search.get('max_price', -1))

    def search(self, product, location, price):
        search_url = self.session.get(product_search_url.format(product, location)).url
        offers = []
        for offer_html in self.get_offers_as_html(search_url, price):
            offer = Offer(offer_html)
            #cprint("   Found: '{}' for {} € in {}\n   url: {}".format(offer.title, offer.price, offer.locality, offer.url), 'green')
            offers.append(offer)

        filename = os.path.join(data_dir, "{}-{}.json".format(product, location))
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                json.dump([o.__dict__ for o in offers], f)
        self.find_new_offers(offers, filename)

    
    def get_offers_as_html(self, base_search_url, price):
        search_url = "/".join(base_search_url.split("/")[:4]) + \
                     "anzeige:angebote/" + \
                     "seite:{}/" + \
                     "preis::{}/" + \
                     "/".join(base_search_url.split("/")[4:])
        for i in range(1, 40):
            print(" Looking at result page {}".format(i))
            resp = self.session.get(search_url.format(i, price), allow_redirects=False)
            if "Es wurden keine Anzeigen für" in resp.text or resp.status_code == 302:
                print("  Nothing found here")
                return
            relevant_html = resp.text.split("Alternative Anzeigen")[0]
            bs = BeautifulSoup(relevant_html, 'html.parser')
            offer_links = [x['data-href'] for x in bs.findAll('div', {'class': 'imagebox srpimagebox'})]
            for offer_url in offer_links:
                yield self.session.get(base_url.format(offer_url)).text


    def find_new_offers(self, offers, filename):
        offers_last_state = json.load(open(filename))
        offer_urls_last_time = [o['url'] for o in offers_last_state]
        for offer in offers:
            if offer.url not in offer_urls_last_time:
                #self.notify_test(offer)
                self.notifications.append(offer)
        with open(filename, "w") as f:
            json.dump([o.__dict__ for o in offers], f)
    

    def notify_test(self, offer):
        cprint("   Found new offer: {}".format(offer.url), 'cyan')


def test_parse_offer_details():
    with open("html/details.html") as f:
        o = Offer(f.read())
    assert o.title == 'Glaskaraffe 900 mL NEU OVP'


if __name__ == '__main__':
    #test_parse_offer_details()
    EbayKleinanzeigen()


def go():
    ebk = EbayKleinanzeigen()
    return ['Ebay Kleinanzeigen: {} für {} EUR {}'.format(x.title, x.price, x.url) for x in ebk.notifications]

