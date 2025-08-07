import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            #url="https://www.nbcnews.com/business",
            url="https://finance.yahoo.com/quote/AAPL/profile/",
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())