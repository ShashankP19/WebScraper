
import argparse
import datetime
import locale
import logging
import re
import sys
import time
import os

import pandas as pd
from selenium import webdriver

URL_PATTERN = 'http(s)?:\/\/.?(www\.)?tripadvisor\.(in)\/Restaurant_Review.*'

class Review():
    def __init__(self, id, date, title, user, text, ratingValue):
        self.id = id
        self.date = date
        self.title = title
        self.user = user
        self.text = text
        self.ratingValue = ratingValue


class TripadvisorScraper():
    def __init__(self, engine='phantomjs'):
        self.language = 'en'
        self.locale_backup = locale.getlocale()[0]
        self.lookup = {}

        if engine == 'chrome':
            self.driver = webdriver.Chrome()
        elif engine == 'firefox':
            self.driver = webdriver.Firefox()
        elif engine == 'phantomjs':
            self.driver = webdriver.PhantomJS()
        else:
            logging.warning('Engine {} not supported. Defaulting to PhantomJS.'.format(engine))
            self.driver = webdriver.PhantomJS()


    def _parse_page(self):
        reviews = []

        time.sleep(2) 

        try:
           self.driver.find_element_by_class_name('reviewSelector').find_element_by_class_name('ulBlueLinks').click()
        except:
            pass        

        time.sleep(2)  

        review_elements = self.driver.find_elements_by_class_name('reviewSelector')
        for e in review_elements:
            try:
                id = e.get_attribute('id')
                date = e.find_element_by_class_name('ratingDate').get_attribute('title')
                date = datetime.datetime.strptime(date, '%d %B %Y')
                title = e.find_element_by_class_name('quote').find_element_by_tag_name('a').find_element_by_class_name('noQuotes').text

                try:
                    user = e.find_element_by_class_name('scrname').text
                except:
                    user = None
                text = e.find_element_by_class_name('partial_entry').text.replace('\n', ' ')

                rating_bubble_class = e.find_element_by_class_name('ui_bubble_rating').get_attribute('class')

                if 'bubble_10' in rating_bubble_class:
                    ratingValue = 1
                elif 'bubble_20' in rating_bubble_class:
                    ratingValue = 2
                elif 'bubble_30' in rating_bubble_class:
                    ratingValue = 3
                elif 'bubble_40' in rating_bubble_class:
                    ratingValue = 4
                elif 'bubble_50' in rating_bubble_class:
                    ratingValue = 5
                else:
                    ratingValue = 0
                    

                if id in self.lookup:
                    logging.warning('Fetched review {} twice.'.format(r.id))
                else:
                    self.lookup[id] = True
                    reviews.append(Review(id, date, title, user, text, ratingValue))
                #print(id)
            except:
                logging.warning('Couldn\'t fetch review.')
                pass

        return reviews


    def fetch_reviews(self, url, max_reviews=None, as_dataframe=True):
        self.lookup = {}
        reviews = []
        if not max_reviews: max_reviews = sys.maxsize
        
        self.driver.get(url)

        while len(reviews) < max_reviews:
            reviews += self._parse_page()
            logging.info('Fetched additional of {} reviews by now.'.format(len(reviews)))
            try:
                next_button_container = self.driver.find_element_by_class_name('next')
            except:
                break
            if 'disabled' in next_button_container.get_attribute('class'): break
            next_button_container.click()

        locale.setlocale(locale.LC_TIME, self.locale_backup)
        reviews = reviews[:max_reviews]
        if as_dataframe: return pd.DataFrame.from_records([r.__dict__ for r in reviews]).set_index('id', drop=True)
        return reviews
    
    def get_place_links(self, url):
        self.driver.get(url)
        links = []
        ul_list = self.driver.find_element_by_class_name('geoList')
        li_tags = ul_list.find_elements_by_tag_name('li')
        for li_tag in li_tags:
            links.append(li_tag.find_element_by_tag_name('a').get_attribute('href'))
        return links

    def get_restaurant_links(self):
        links = []
        restaurant_div = self.driver.find_elements_by_class_name('listing')
        time.sleep(2)
        for restaurant in restaurant_div:
            link = restaurant.find_element_by_class_name('property_title').get_attribute('href')
            links.append(link)
        return links

    def crawl_place(self, url):
        self.driver.get(url)
        time.sleep(2)
        restaurant_links = []
        while 1:
            restaurant_links += self.get_restaurant_links()
            #print(restaurant_links)
            logging.info('Fetched an additional of {} restaurant links by now.'.format(len(restaurant_links)))
            try:
                next_button_container = self.driver.find_element_by_class_name('nav next rndBtn ui_button primary taLnk')
            except:
                break
            if 'disabled' in next_button_container.get_attribute('class'): break
            next_button_container.click()   

        return restaurant_links



    def close(self):
        self.driver.quit()

def is_valid_url(url):
    return re.compile(URL_PATTERN).match(url)


def get_id_by_url(url):
    if not is_valid_url(url): return None
    match = re.compile('.*Restaurant_Review-g\d+-(d\d+).*').match(url)
    if match is None: return None
    return match.group(1)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape restaurant reviews from Tripadvisor (.com or .de).')
    parser.add_argument('url', help='URL to a Tripadvisor restaurant page')
    parser.add_argument('-o', '--out', dest='outfile', help='Path for output CSV file', default='reviews.csv')
    parser.add_argument('-n', dest='max', help='Maximum number of reviews to fetch', default=sys.maxsize, type=int)
    parser.add_argument('-e', '--engine', dest='engine', help='Driver to use', choices=['phantomjs', 'chrome', 'firefox'], default='phantomjs')
    args = parser.parse_args()

    scraper = TripadvisorScraper(engine=args.engine)

    place_links = scraper.get_place_links(args.url)
    #print(place_links)
    for place_url in place_links:
        restaurant_links = scraper.crawl_place(place_url)
        #print(restaurant_links)
        for restaurant_url in restaurant_links:
            df = scraper.fetch_reviews(restaurant_url, args.max)
            if os.path.exists('test_review.csv'):
                df.to_csv(args.outfile, mode='a', header=False)
            else:
                df.to_csv(args.outfile)
            print('Successfully fetched {} reviews.'.format(len(df.index)))
    
scraper.close()