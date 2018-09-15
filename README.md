# WebScraper

### Web scraper for getting customer reviews of restaurants from tripadvisor.in

Execution command
```
python scrape.py -o <output filename> -e <browser ('firefox', 'chrome')> -n <max no. of reviews per restaurant> <url>

```
- Has been tested only with firefox
- If file with the given output filename already exists, then data is appended to the same file.

#### Examples

- To scrape second page of restaurant list : https://www.tripadvisor.in/Restaurants-g293860-oa20-India.html#LOCATION_LIST
```
python scrape.py -o 'reviews.csv' -e 'firefox' 'https://www.tripadvisor.in/Restaurants-g293860-oa20-India.html#LOCATION_LIST'

```

- To scrape third page of restaurant list : https://www.tripadvisor.in/Restaurants-g293860-oa40-India.html#LOCATION_LIST
```
python scrape.py -o 'reviews.csv' -e 'firefox' 'https://www.tripadvisor.in/Restaurants-g293860-oa40-India.html#LOCATION_LIST'

```
