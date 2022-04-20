import scrapy
import chompjs
import urllib
import re

class ToScrapeCSSSpider(scrapy.Spider):
    name = "scrapehouses"
    # download_delay = 10


    def start_requests(self):

        # 42 listings
        # start_urls = [
        #     'https://www.airbnb.com/s/Broomfield--CO--United-States/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&date_picker_type=flexible_dates&query=Broomfield%2C%20CO%2C%20United%20States&place_id=ChIJO_iIW8yKa4cRsEK8kOiXBQc&adults=1&source=structured_search_input_header&search_type=user_map_move&ne_lat=39.9675166357289&ne_lng=-105.0067410973196&sw_lat=39.893933488186256&sw_lng=-105.14063697134304&zoom=13&search_by_map=true&flexible_trip_lengths%5B%5D=weekend_trip'
        # ]
        # # Slightly over 300
        # start_urls = [
        #     'https://www.airbnb.com/s/Broomfield--CO--United-States/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&date_picker_type=flexible_dates&query=Broomfield%2C%20CO%2C%20United%20States&place_id=ChIJO_iIW8yKa4cRsEK8kOiXBQc&adults=1&source=structured_search_input_header&search_type=user_map_move&ne_lat=40.01708793363594&ne_lng=-104.93018012319851&sw_lat=39.8472844159739&sw_lng=-105.20277838980007&zoom=12&search_by_map=true&flexible_trip_lengths%5B%5D=weekend_trip'
        # ]
        #1 listing
        start_urls = [
            'https://www.airbnb.com/s/Broomfield--CO--United-States/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&date_picker_type=flexible_dates&query=Broomfield%2C%20CO%2C%20United%20States&place_id=ChIJO_iIW8yKa4cRsEK8kOiXBQc&adults=1&source=structured_search_input_header&search_type=user_map_move&ne_lat=39.876843701579354&ne_lng=-105.08908385688119&sw_lat=39.87153284340391&sw_lng=-105.09760255271249&zoom=17&search_by_map=true&flexible_trip_lengths%5B%5D=weekend_trip'
        ]


        # headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
        for url in start_urls:
            # yield scrapy.Request(url, meta={'listingsViewed':0})
            yield scrapy.Request(url, meta={"proxy": "https://kudezyyi-rotate:r3onw2cuy65h@p.webshare.io:80/"})
            # yield scrapy.Request(url, callback=self.parse, headers=headers)




    listingsViewed = 0

    def parse(self, response):
        for scripts in response.css('script#data-deferred-state::text'):
            data = chompjs.parse_js_object(scripts.get())
            # TO DO: If less than 300, go through each of the pages, if more than 300, subdivide query into 4 smaller ones
            # Go through listings for the page
            sections = data['niobeMinimalClientData'][0][1]['data']['presentation']['explore']['sections']['sections']

            resultCount = 0

            listingsViewed = 0
            try:
                listingsViewed = response.meta['listingsViewed']
            except KeyError:
                print("No meta set")


            # Check to see how many listings were returned by the query
            if("EXPLORE_STRUCTURED_PAGE_TITLE" in sections[0]['sectionId']):
                resultCount = int(''.join(filter(str.isdigit, sections[0]['section']['structuredTitle'])))
            # print(resultCount)
            if(resultCount < 300):
                for SectionContainers in sections:
                    if("PAGINATED_HOMES" in SectionContainers['sectionId']):
                        # Check to make sure has homes
                        i = 0
                        if "section" in SectionContainers and "child" in SectionContainers["section"] and "section" in SectionContainers["section"]["child"] and "items" in SectionContainers["section"]["child"]["section"]:
                            for listing in SectionContainers["section"]["child"]["section"]["items"]:
                                
                                # Got a listing ID
                                # print(listing["listing"]["id"])
                                # yield {
                                #     'listingId': listing["listing"]["id"],
                                # }

                                # Use the listing parser
                                request = scrapy.Request("https://www.airbnb.com/rooms/"+listing["listing"]["id"],callback=self.parseListing)
                                yield request

                                listingsViewed += 1
                # If there are more pages
                if listingsViewed < resultCount:
                    url = str(response).lstrip("<123456 7890").rstrip(">")
                    # Check to see if "&pagination_search=true&items_offset=20&section_offset=3" is already in the url
                    pos = url.find("&pagination_search=true&items_offset=")
                    if pos == -1:
                        newUrl = url + "&pagination_search=true&items_offset=" + str(listingsViewed) + "&section_offset=3"
                    else:
                        newUrl = url[0 : pos : ] + "&pagination_search=true&items_offset=" + str(listingsViewed) + "&section_offset=3"
                    
                    # Get next page
                    yield scrapy.Request(newUrl, callback=self.parse, meta={'listingsViewed':listingsViewed})

            # There are more than 300 listings
            else:
                print("More than 300 listings, splitting into 4 maps")
                url = str(response).lstrip("<123456 7890").rstrip(">")
                # Get 4 borders

                urlObj = urllib.parse
                parsedUrl = urlObj.parse_qs(urllib.parse.urlparse(url).query)

                north = float(parsedUrl['ne_lat'][0])
                south = float(parsedUrl['sw_lat'][0])
                east = float(parsedUrl['ne_lng'][0])
                west = float(parsedUrl['sw_lng'][0])

                centerLat = (north + south) / 2
                centerLong = (east + west) / 2 


                print(url)
                # Create 4 new urls
                urlSouth = url.replace(str(north), str(centerLat))
                urlNorth = url.replace(str(south), str(centerLat))
                urlSouthWest = urlSouth.replace(str(east), str(centerLong))
                urlSouthEast = urlSouth.replace(str(west), str(centerLong))
                urlNorthWest = urlNorth.replace(str(east), str(centerLong))
                urlNorthEast = urlNorth.replace(str(west), str(centerLong))

                print(urlSouthWest)
                print(urlNorthWest)
                
                urls = [urlSouthWest, urlSouthEast, urlNorthWest, urlNorthEast]

                # yield response.follow_all(urls, self.parse)
                yield response.follow(urlSouthWest, self.parse)
                yield response.follow(urlNorthWest, self.parse)
                yield response.follow(urlSouthEast, self.parse)
                yield response.follow(urlNorthEast, self.parse)

                
    def parseListing(self, response):
         
        
        # yield{"data": response}
        print(response.text)

        # for scripts in response.css('script#data-deferred-state::text'):
        #     data = chompjs.parse_js_object(scripts.get())
        #     sections = data['niobeMinimalClientData'][0][1]['data']['presentation']['stayProductDetailPage']['sections']['sections']
        #     metadata = data['niobeMinimalClientData'][0][1]['data']['presentation']['stayProductDetailPage']['sections']['metadata']
            
            
        #     # Variables to return
        #     guests = ''
        #     rooms = ''
        #     baths = ''
        #     beds = ''
        #     title = ''
        #     url = str(response).lstrip("<123456 7890").rstrip(">")
        #     listing_id = re.findall(r'\d+', url)[0]
        #     average_review = ''
        #     total_reviews = ''
        #     lat = metadata['loggingContext']['eventDataLogging']['listingLat']
        #     lng = metadata['loggingContext']['eventDataLogging']['listingLng']
        #     superhost = metadata['loggingContext']['eventDataLogging']['isSuperhost']
        #     listing_id = metadata['loggingContext']['eventDataLogging']['listingId']
        #     roomType = metadata['loggingContext']['eventDataLogging']['roomType']
        #     pictureCount = metadata['loggingContext']['eventDataLogging']['pictureCount']
        #     amenities = metadata['loggingContext']['eventDataLogging']['amenities']
        #     accuracyRating = metadata['loggingContext']['eventDataLogging']['accuracyRating']
        #     checkinRating = metadata['loggingContext']['eventDataLogging']['checkinRating']
        #     cleanlinessRating = metadata['loggingContext']['eventDataLogging']['cleanlinessRating']
        #     communicationRating = metadata['loggingContext']['eventDataLogging']['communicationRating']
        #     locationRating = metadata['loggingContext']['eventDataLogging']['locationRating']
        #     valueRating = metadata['loggingContext']['eventDataLogging']['valueRating']
        #     guestSatisfactionOverall = metadata['loggingContext']['eventDataLogging']['guestSatisfactionOverall']
        #     reviewCount = metadata['loggingContext']['eventDataLogging']['visibleReviewCount']


        #     for SectionContainers in sections:
        #         if("OVERVIEW_DEFAULT" in SectionContainers['sectionId']):
        #             if "section" in SectionContainers and "detailItems" in SectionContainers["section"]:
        #                 for info in SectionContainers['section']["detailItems"]:
        #                     if "guest" in info['title']:
        #                         guests = re.findall("\d+\.\d+|\d+", info['title'])[0]
        #                     if "room" in info['title']:
        #                         rooms = re.findall("\d+\.\d+|\d+", info['title'])[0]
        #                     if "bath" in info['title']:
        #                         baths = re.findall("\d+\.\d+|\d+", info['title'])[0]
        #                     if "bed" in info['title']:
        #                         beds = re.findall("\d+\.\d+|\d+", info['title'])[0]
            

            # yield{
            #     'listingId': listing_id,
            #     'guests': guests,
            #     'rooms': rooms,
            #     'baths': baths,
            #     'beds': beds,
            #     'lat': lat,
            #     'lng': lng,
            #     'superhost': superhost,
            #     'roomType': roomType,
            #     'pictureCount': pictureCount,
            #     'accuracyRating': accuracyRating,
            #     'checkinRating': checkinRating,
            #     'cleanlinessRating': cleanlinessRating,
            #     'communicationRating': communicationRating,
            #     'locationRating': locationRating,
            #     'valueRating': valueRating,
            #     'guestSatisfactionOverall': guestSatisfactionOverall,
            #     'reviewCount': reviewCount,
            # }
            # print(sections)
        # print(response)