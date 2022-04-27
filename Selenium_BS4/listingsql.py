from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
import time
import json
import chompjs
import re
import urllib
import psycopg2

# Given a listing url (https://www.airbnb.com/rooms/plus/22614911?adults=1), return BS object
def extract_soup_js(listing_url, waiting_time=[5, 1]):
    """Extracts HTML from JS pages: open, wait, click, wait, extract"""

    print("Getting listing:" + listing_url)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome('/Users/cole/Documents/AirBNBProject/AirBNB/Selenium_BS4/chromedriver', options=options)

    driver.get(listing_url)
    time.sleep(waiting_time[0])
    
    try:
        # driver.find_element_by_class_name('_1kkx984').click()
        driver.soup.find_element(by=By.CLASS_NAME, value='_1kkx984').click()
    except:
        pass # next calander date
    
    time.sleep(waiting_time[1])
    detail_page = driver.page_source

    driver.quit()

    return BeautifulSoup(detail_page, features='html.parser')


# Given a listing BS object (for single listing), return JSON object with key values
def parse_listing(soup, outputfile):
    data = {} # create an obj to store the items
    

    # Get general listing information
    dataScript = soup.find("script", {"id": "data-deferred-state"})
    text = chompjs.parse_js_object(dataScript.text)
    metadata = text['niobeMinimalClientData'][0][1]['data']['presentation']['stayProductDetailPage']['sections']['metadata']
    sections = text['niobeMinimalClientData'][0][1]['data']['presentation']['stayProductDetailPage']['sections']['sections']

    data['lat'] = metadata['loggingContext']['eventDataLogging']['listingLat']
    data['lng'] = metadata['loggingContext']['eventDataLogging']['listingLng']
    data['superhost'] = metadata['loggingContext']['eventDataLogging']['isSuperhost']
    data['listing_id'] = metadata['loggingContext']['eventDataLogging']['listingId']
    data['roomType'] = metadata['loggingContext']['eventDataLogging']['roomType']
    data['pictureCount'] = metadata['loggingContext']['eventDataLogging']['pictureCount']
    data['amenities'] = metadata['loggingContext']['eventDataLogging']['amenities']
    data['accuracyRating'] = metadata['loggingContext']['eventDataLogging']['accuracyRating']
    data['checkinRating'] = metadata['loggingContext']['eventDataLogging']['checkinRating']
    data['cleanlinessRating'] = metadata['loggingContext']['eventDataLogging']['cleanlinessRating']
    data['communicationRating'] = metadata['loggingContext']['eventDataLogging']['communicationRating']
    data['locationRating'] = metadata['loggingContext']['eventDataLogging']['locationRating']
    data['valueRating'] = metadata['loggingContext']['eventDataLogging']['valueRating']
    data['guestSatisfactionOverall'] = metadata['loggingContext']['eventDataLogging']['guestSatisfactionOverall']
    data['reviewCount'] = metadata['loggingContext']['eventDataLogging']['visibleReviewCount']

    for SectionContainers in sections:
        if("OVERVIEW_DEFAULT" in SectionContainers['sectionId']):
            if "section" in SectionContainers and "detailItems" in SectionContainers["section"]:
                for info in SectionContainers['section']["detailItems"]:
                    if "guest" in info['title']:
                        data['guests'] = re.findall("\d+\.\d+|\d+", info['title'])[0]
                    if "room" in info['title']:
                        data['rooms'] = re.findall("\d+\.\d+|\d+", info['title'])[0]
                    if "bath" in info['title']:
                        data['baths'] = re.findall("\d+\.\d+|\d+", info['title'])[0]
                    if "bed" in info['title']:
                        data['beds'] = re.findall("\d+\.\d+|\d+", info['title'])[0]


    # Get days the listing is booked
    bookedDays = soup.findAll("div",{"data-is-day-blocked":"true"})
    freeDays = soup.findAll("div",{"data-is-day-blocked":"false"})
    data['bookings'] = []
    for container in bookedDays:
        booking = {}
        booking['id'] = container['data-testid']
        booking['booked'] = 'true'
        data['bookings'].append(booking) # add the item to the list
    
    for container in freeDays:
        item = {}
        item['id'] = container['data-testid']
        item['booked'] = 'false'
        data['bookings'].append(item) # add the item to the list
    # print(data)
    # Write out data to file TO DO: maybe use sqllite or something better suited for adding individual listings to obj, having to read in entire file to append each listing rn
    with open(outputfile, mode='r', encoding='utf-8') as f:
        feeds = json.load(f)
    with open(outputfile, mode='w', encoding='utf-8') as feedsjson:
        feeds.append(data)
        json.dump(feeds, feedsjson)

    return


# Given URL for map area, break down and get all listings, baseUrl = where search is starting from, waitingtime, used to delay searches to prevent blocking, listingsViewed = number of listings searched through recursivly this far, urls = array of all listings found through this search
def get_urls(baseUrl, waiting_time=[5, 1], listingsViewed = 0, urls=[]):
    # Fetch the first search page and get beatuful soup parsed results
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome('/Users/cole/Documents/AirBNBProject/AirBNB/Selenium_BS4/chromedriver', options=options)
    driver.get(baseUrl)
    time.sleep(waiting_time[0])
    detail_page = driver.page_source
    driver.quit()
    response = BeautifulSoup(detail_page, features='html.parser')
    urlArray = urls.copy()

    # Get data from script
    scripts = response.find("script", {"id": "data-deferred-state"}).text   #Get the text of target script
    data = chompjs.parse_js_object(scripts)
            
    # Go through listings for the page
    sections = data['niobeMinimalClientData'][0][1]['data']['presentation']['explore']['sections']['sections']
    resultCount = 0

    # Check to see how many listings were returned by the query
    if("EXPLORE_STRUCTURED_PAGE_TITLE" in sections[0]['sectionId']):
        resultCount = int(''.join(filter(str.isdigit, sections[0]['section']['structuredTitle'])))
    print("Found: " + str(resultCount) + " listings")
    # If there are not too many results, go through them
    if(resultCount < 300):
        for SectionContainers in sections:
            if("PAGINATED_HOMES" in SectionContainers['sectionId']):
                # Check to make sure has homes
                i = 0
                if "section" in SectionContainers and "child" in SectionContainers["section"] and "section" in SectionContainers["section"]["child"] and "items" in SectionContainers["section"]["child"]["section"]:
                    # For each listing
                    for listing in SectionContainers["section"]["child"]["section"]["items"]:
                        # Add to listing array
                        urlArray.append("https://www.airbnb.com/rooms/"+listing["listing"]["id"])
                        listingsViewed += 1

                        # Use the listing parser
                        # request = scrapy.Request("https://www.airbnb.com/rooms/"+listing["listing"]["id"],callback=self.parseListing)
                        # yield request

                # If there are more pages
                if listingsViewed < resultCount:
                    # Check to see if "&pagination_search=true&items_offset=20&section_offset=3" is already in the url
                    pos = baseUrl.find("&pagination_search=true&items_offset=")
                    if pos == -1:
                        newUrl = baseUrl + "&pagination_search=true&items_offset=" + str(listingsViewed) + "&section_offset=3"
                    else:
                        newUrl = baseUrl[0 : pos : ] + "&pagination_search=true&items_offset=" + str(listingsViewed) + "&section_offset=3"
                    
                    # Get next page
                    urlArray = get_urls(newUrl, waiting_time=[5, 1], listingsViewed = listingsViewed, urls = urlArray)

    # There are more than 300 listings
    else:
        print("Over 300 listings, splitting url")
        url = baseUrl

        # Get 4 borders
        urlObj = urllib.parse
        parsedUrl = urlObj.parse_qs(urllib.parse.urlparse(url).query)

        north = float(parsedUrl['ne_lat'][0])
        south = float(parsedUrl['sw_lat'][0])
        east = float(parsedUrl['ne_lng'][0])
        west = float(parsedUrl['sw_lng'][0])

        centerLat = (north + south) / 2
        centerLong = (east + west) / 2 


        # Create 4 new urls
        urlSouth = url.replace(str(north), str(centerLat))
        urlNorth = url.replace(str(south), str(centerLat))
        urlSouthWest = urlSouth.replace(str(east), str(centerLong))
        urlSouthEast = urlSouth.replace(str(west), str(centerLong))
        urlNorthWest = urlNorth.replace(str(east), str(centerLong))
        urlNorthEast = urlNorth.replace(str(west), str(centerLong))
                
        subdividedUrls = [urlSouthWest, urlSouthEast, urlNorthWest, urlNorthEast]

        # Recursivly search the 4 new urls
        # print(urlSouthWest)
        # print(urlSouthEast)
        # print(urlNorthWest)
        # print(urlNorthEast)
        urlsOne = get_urls(urlSouthWest, waiting_time=[5, 1], listingsViewed = 0, urls=[])
        print("Returned " + str(len(urlsOne)) + " urls from " + urlSouthWest)
        urlsTwo = get_urls(urlNorthWest, waiting_time=[5, 1], listingsViewed = 0, urls=[])
        print("Returned " + str(len(urlsTwo)) + " urls")
        urlsThree = get_urls(urlSouthEast, waiting_time=[5, 1], listingsViewed = 0, urls=[])
        print("Returned " + str(len(urlsThree)) + " urls")
        urlsFour = get_urls(urlNorthEast, waiting_time=[5, 1], listingsViewed = 0, urls=[])
        print("Returned " + str(len(urlsFour)) + " urls")
        # Append the fetched urls
        urlArray.extend(urlsOne)
        urlArray.extend(urlsTwo)
        urlArray.extend(urlsThree)
        urlArray.extend(urlsFour)

    return urlArray

#=== Running scraper ===

# 40 listings
baseUrl = 'https://www.airbnb.com/s/Broomfield--CO--United-States/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&date_picker_type=flexible_dates&query=Broomfield%2C%20CO%2C%20United%20States&place_id=ChIJO_iIW8yKa4cRsEK8kOiXBQc&adults=1&source=structured_search_input_header&search_type=user_map_move&ne_lat=39.9675166357289&ne_lng=-105.0067410973196&sw_lat=39.893933488186256&sw_lng=-105.14063697134304&zoom=13&search_by_map=true&flexible_trip_lengths%5B%5D=weekend_trip'

# Slightly over 300 (330ish)
# baseUrl = 'https://www.airbnb.com/s/Broomfield--CO--United-States/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&date_picker_type=flexible_dates&query=Broomfield%2C%20CO%2C%20United%20States&place_id=ChIJO_iIW8yKa4cRsEK8kOiXBQc&adults=1&source=structured_search_input_header&search_type=user_map_move&ne_lat=40.011513487136824&ne_lng=-104.9185071495657&sw_lat=39.841696123954954&sw_lng=-105.19110541616726&zoom=12&search_by_map=true&flexible_trip_lengths%5B%5D=weekend_trip'

# listingUrls = get_urls(baseUrl)
# print(listingUrls)
# print(len(listingUrls))

# Go through returned URL list for each listing

# Connect to postgres database
# DOOOOO NOT PUSH PASSWORD
# DONT PUSH THIS ANYWHEREEEEE

try:
    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(
        host="localhost",
        database="airbnb",
        user="postgres",
        password="Co!ebea5")
		
    # create a cursor
    cur = conn.cursor()
        
	# execute a statement
    print('PostgreSQL database version:')
    cur.execute('SELECT version()')

    # display the PostgreSQL database server version
    db_version = cur.fetchone()
    print(db_version)
       
	# close the communication with the PostgreSQL
    cur.close()
except (Exception, psycopg2.DatabaseError) as error:
    print(error)

# DATA_FILENAME = "outputdata.json"
# # Open the output file to make sure it exsists
# with open(DATA_FILENAME, mode='w', encoding='utf-8') as f:
#     json.dump([], f)

# for url in listingUrls:
#     # Not all listings fit parser nicley
#     try:
#         data = extract_soup_js(url, waiting_time=[5, 1])
#         print("Parsing listing: " + url)
#         parse_listing(data, DATA_FILENAME)
#     except KeyboardInterrupt:
#         break
#     except:
#         print("FAILED: " + url)
#         pass 


# url = 'https://www.airbnb.com/rooms/plus/22614911?adults=1'
# data = extract_soup_js(url, waiting_time=[5, 1])

# # Parse data
# parse_listing(data, "outputdata.json")

