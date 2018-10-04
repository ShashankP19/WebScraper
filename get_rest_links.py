
import argparse
import locale
import logging
import re
import sys
import time
import os

from selenium import webdriver

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
         
        self.driver.implicitly_wait(10)

    # function to get links of all restaurant in a webpage
    def get_restaurant_links_per_page(self, links_file):
        time.sleep(2)
        restaurant_div = self.driver.find_elements_by_class_name('listing')
        for restaurant in restaurant_div:
            link = restaurant.find_element_by_class_name('property_title').get_attribute('href')
            links_file.write(link + os.linesep)
        return 

    # function to get links of all restaurant in a city
    def get_restaurant_links_of_city(self, url, links_file):
        print('....Collecting urls of restaurants from city - ', url)
        self.driver.get(url)
        page_no = 1
        while 1:
            time.sleep(2)
            self.get_restaurant_links_per_page(links_file)
            print('In page ', page_no)
            page_no += 1
            try:
                next_button_container = self.driver.find_element_by_class_name('next') 
            except:
                break
            if 'disabled' in next_button_container.get_attribute('class'): 
                break
            next_button_container.click()   

        return 



    def close(self):
        self.driver.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape restaurant reviews from Tripadvisor (.com).')
    parser.add_argument('url', help='URL to a Tripadvisor city page')
    parser.add_argument('-o', '--out', dest='outfile', help='Path for output text file', default='links.txt')
    parser.add_argument('-e', '--engine', dest='engine', help='Driver to use', choices=['phantomjs', 'chrome', 'firefox'], default='phantomjs')
    args = parser.parse_args()

    scraper = TripadvisorScraper(engine=args.engine)

    links_file = open(args.outfile, 'w')

    scraper.get_restaurant_links_of_city(args.url, links_file)
    
    links_file.close()
    
    scraper.close()