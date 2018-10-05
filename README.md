# WebScraper

### Dependencies
- python
- pandas
- selenium

### To get urls of all restaurants in a city
Execution command
```
python get_rest_links.py -o <output txt filename> -e <browser ('firefox', 'chrome')> <url>

```
For example, to get urls of all restaurants in city of Agra
```
python get_rest_links.py -o 'agra_rest_urls.txt' -e 'firefox' 'https://www.tripadvisor.in/Restaurants-g297683-Agra_Agra_District_Uttar_Pradesh.html'

```
The urls will be stored in `agra_rest_links.txt`

### To scrape urls stored in a text file

Execution command
```
python scrape.py -o <output csv filename> -l <input urls text file> -e <browser ('firefox', 'chrome')> -n <max no. of reviews per restaurant> 

```

For example, to scrape a max. of 100 reviews from restaurants in agra
 ```
 python scrape.py -o 'agra.csv' -l 'agra_rest_urls.txt' -e 'firefox' -n 100
 ```

- If file with the given output csv filename already exists, then data is appended to the same file.
- Tip: If scraper stops abruptly, but if you want to continue from where you left off, manually remove the urls from the text file which have already been scraped.   
- Has been tested with firefox only
