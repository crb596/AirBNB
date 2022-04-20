import scrapy
from scrapy_playwright.page import PageCoroutine, PageMethod




class ToScrapeCSSSpider(scrapy.Spider):
    name = "playwritehouse"

    def start_requests(self):

        start_url = 'https://www.airbnb.com/rooms/plus/22614911?adults=1'
        yield scrapy.Request(
            url=start_url,
            meta= dict(
                playwright = True,
                playwright_include_page = True,
            )
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        title = await page.title()
        await page.context.close()  # close the context
        await page.close()
        yield {'text' : response.text}