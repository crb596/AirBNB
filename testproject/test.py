import requests
from scrapy.selector import Selector

# Prepare url
city     = 'Toronto'
main_url = 'https://www.airbnb.com'
city_url = f'{main_url}/s/{city}/homes/'

# Create selector
html = requests.get(city_url).content
sel  = Selector(text=html)

# Get hotels
hotels = sel.css('div._8ssblpx')
print('Number of hotels:', len(hotels))

# Find the next page url
next_page = sel.css('a._za9j7e ::attr(href)').extract_first()
print('Next page:', '\n', next_page)