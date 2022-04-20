from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
import time

def extract_soup_js(listing_url, waiting_time=[5, 1]):
    """Extracts HTML from JS pages: open, wait, click, wait, extract"""

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome('/Users/cole/Documents/AirBNBProject/Selenium_BS4/chromedriver', options=options)

    driver.get(listing_url)
    time.sleep(waiting_time[0])
    
    try:
        driver.find_element_by_class_name('_1kkx984').click()
    except:
        pass # next calander date
    
    time.sleep(waiting_time[1])
    detail_page = driver.page_source

    driver.quit()

    return BeautifulSoup(detail_page, features='html.parser')




url = 'https://www.airbnb.com/rooms/plus/22614911?adults=1'
data = extract_soup_js(url, waiting_time=[5, 1])

# Parse data

print(data)
