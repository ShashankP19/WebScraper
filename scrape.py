
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
    def __init__(self, id, date, title, text, ratingValue, restaurant_details):
        self.id = id
        self.date = date
        self.title = title
        #self.user = user
        self.text = text
        self.restaurant_rating_food = restaurant_details['rating_summary']['food']
        self.restaurant_rating_service = restaurant_details['rating_summary']['service']
        self.restaurant_rating_value = restaurant_details['rating_summary']['value']
        self.restaurant_rating_atmosphere = restaurant_details['rating_summary']['atmosphere']
        self.restaurant_average_prices = restaurant_details['average_prices']
        self.restaurant_cuisine = restaurant_details['cuisine']
        self.restaurant_meals = restaurant_details['meals']
        self.restaurant_features = restaurant_details['restaurant_features']
        self.restaurant_good_for = restaurant_details['good_for']
        self.restaurant_open_hours_sunday = restaurant_details['open_hours']['sunday']
        self.restaurant_open_hours_monday = restaurant_details['open_hours']['monday']
        self.restaurant_open_hours_tuesday = restaurant_details['open_hours']['tuesday']
        self.restaurant_open_hours_wednesday = restaurant_details['open_hours']['wednesday']
        self.restaurant_open_hours_thursday = restaurant_details['open_hours']['thursday']
        self.restaurant_open_hours_friday = restaurant_details['open_hours']['friday']
        self.restaurant_open_hours_saturday = restaurant_details['open_hours']['saturday'] 
        self.ratingValue_target = ratingValue


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

        self.driver.implicitly_wait(5)


    def _parse_page(self, restaurant_details):
        reviews = []

        time.sleep(3) 

        try:
           #self.driver.find_element_by_class_name('reviewSelector').find_element_by_class_name('ulBlueLinks').click()
           self.driver.find_element_by_class_name('ulBlueLinks').click()
        except:
            pass        

        time.sleep(2)  

        review_elements = self.driver.find_elements_by_class_name('reviewSelector')
        for e in review_elements:
            try:
                id = 'NULL'
                date = 'NULL'
                title = 'NULL'
                text = 'NULL'
                user = 'NULL'
                ratingValue = 'NULL'

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
                    reviews.append(Review(id, date, title, text, ratingValue, restaurant_details))
                #print(id)
            except:
                logging.warning('Couldn\'t fetch review.')
                pass

        return reviews

    # function to get all reviews of a restaurant
    def fetch_restaurant_reviews(self, url, max_reviews=None, as_dataframe=True):
        self.lookup = {}
        reviews = []
        if not max_reviews: max_reviews = sys.maxsize
        
        self.driver.get(url)

        restaurant_details = self.get_restaurant_details()


        while len(reviews) < max_reviews:
            reviews += self._parse_page(restaurant_details)
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
    

    # function to get restaurant specific features
    def get_restaurant_details(self):
        
        restaurant_details = {
            'rating_summary': {
                'food': 'NULL',
                'service': 'NULL',
                'value': 'NULL',
                'atmosphere': 'NULL'
            },
            'average_prices': 'NULL',
            'cuisine': 'NULL',
            'meals': 'NULL',
            'restaurant_features': 'NULL',
            'good_for': 'NULL',
            'open_hours': {
                'sunday': 'NULL',
                'monday': 'NULL',
                'tuesday': 'NULL',
                'wednesday': 'NULL',
                'thursday': 'NULL',
                'friday': 'NULL',
                'saturday': 'NULL',
            }
        }

        # Get restaurant's ratings' summary 
        try:
            bar_chart = self.driver.find_element_by_class_name('barChart')
            rating_rows = bar_chart.find_elements_by_class_name('ratingRow')
            for rating_row in rating_rows:
                text = rating_row.find_element_by_class_name('text').text
                rating_bubbles_class = rating_row.find_element_by_class_name('ui_bubble_rating').get_attribute('alt')
                rating = rating_bubbles_class.partition(' ')[0]
                if(text == 'Food'):
                    restaurant_details['rating_summary']['food'] = rating
                elif(text == 'Service'):
                    restaurant_details['rating_summary']['service'] = rating
                elif(text == 'Value'):
                    restaurant_details['rating_summary']['value'] = rating
                elif(text == 'Atmosphere'):
                    restaurant_details['rating_summary']['atmosphere'] = rating
        except:
            pass

        # Get features - price, meals, restaurant features, good for 
        restaurant_details_table = self.driver.find_element_by_class_name('table_section')
        restaurant_details_row = restaurant_details_table.find_elements_by_class_name('row')
        for row in restaurant_details_row:
            try:
                title = row.find_element_by_class_name('title')
                content = row.find_element_by_class_name('content')
            except:
                continue 
            
            if title.text == 'Average prices':
                restaurant_details['average_prices'] = content.text
            
            elif title.text == 'Cuisine':
                restaurant_details['cuisine'] = content.text
            
            elif title.text == 'Meals':
                restaurant_details['meals'] = content.text
            
            elif title.text == 'Restaurant features':
                restaurant_details['restaurant_features'] = content.text
            
            elif title.text == 'Good for':
                restaurant_details['good_for'] = content.text
        
        # Get restaurant open hours 
        try:
            open_hours = self.driver.find_elements_by_class_name('hours')[1]
            open_hours_details = open_hours.find_elements_by_class_name('detail')
            for detail in open_hours_details:
                try:
                    day = detail.find_element_by_class_name('day').text
                    timings = detail.find_element_by_class_name('hours').text.replace('\n', ', ')
                    if day == 'Sunday':
                        restaurant_details['open_hours']['sunday'] = timings
                    elif day == 'Monday':
                        restaurant_details['open_hours']['monday'] = timings
                    elif day == 'Tuesday':
                        restaurant_details['open_hours']['tuesday'] = timings
                    elif day == 'Wednesday':
                        restaurant_details['open_hours']['wednesday'] = timings
                    elif day == 'Thursday':
                        restaurant_details['open_hours']['thursday'] = timings
                    elif day == 'Friday':
                        restaurant_details['open_hours']['friday'] = timings
                    elif day == 'Saturday':
                        restaurant_details['open_hours']['saturday'] = timings
                except:
                    pass
                
        except: 
            pass
        
        return restaurant_details


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
    parser.add_argument('-l', '--links', dest='rest_links', help='Path of text file containing restaurant links')
    parser.add_argument('-o', '--out', dest='outfile', help='Path for output CSV file', default='reviews.csv')
    parser.add_argument('-n', dest='max', help='Maximum number of reviews to fetch', default=sys.maxsize, type=int)
    parser.add_argument('-e', '--engine', dest='engine', help='Driver to use', choices=['phantomjs', 'chrome', 'firefox'], default='phantomjs')
    args = parser.parse_args()

    scraper = TripadvisorScraper(engine=args.engine)

    with open(args.rest_links) as f:
        restaurant_links = f.readlines()

    print('Found {} restaurant urls\n'.format(len(restaurant_links)))

    rest_num = 1
    for restaurant_url in restaurant_links:
        df = scraper.fetch_restaurant_reviews(restaurant_url, args.max)
        if os.path.exists(args.outfile):
            df.to_csv(args.outfile, mode='a', header=False)
        else:
            df.to_csv(args.outfile)
        print('{}) Successfully fetched {} reviews from {}.'.format(rest_num, len(df.index), restaurant_url))
        rest_num += 1
    
scraper.close()