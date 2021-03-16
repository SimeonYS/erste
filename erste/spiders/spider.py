import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import ErsteItem
from itemloaders.processors import TakeFirst
import requests
import json

pattern = r'(\xa0)?'

url = "https://www.erstegroup.com/bin/erstegroup/gemesgapi/feature/gem_site_en_www-erstegroup-com-en-es7/,"

payload = "{{\"filter\":[{{\"key\":\"path\",\"value\":\"/content/sites/at/eh/www_erstegroup_com/en/news-media/presseaussendungen\"}},{{\"key\":\"tags\",\"value\":\"at:eh/news/Results,at:eh/news/CorporateNews,at:eh/news/CEEInsights,at:eh/news/CorporateBanking,at:eh/news/Innovation,at:eh/news/PeopleProsperity,at:eh/news/Personnel,at:eh/news/Research,at:eh/news/RetailBanking\"}}],\"page\":{},\"query\":\"*\",\"items\":10,\"sort\":\"DATE_RELEVANCE\",\"requiredFields\":[{{\"fields\":[\"teasers.NEWS_DEFAULT\",\"teasers.NEWS_ARCHIVE\",\"teasers.newsArchive\"]}}]}}"
headers = {
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Origin': 'https://www.erstegroup.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://www.erstegroup.com/en/news-media/press-releases',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'TCPID=121241318275207497273; TC_PRIVACY=0@021@1@2@1613647109076@; TC_PRIVACY_CENTER=1; s_fid=2A05616784669697-0E5E6F84BD338769; _cs_c=1; _CT_RS_=Recording; WRUID=3171560824275002; 3cf5c10c8e62ed6f6f7394262fadd5c2=ffb311b6d6c2f7e071b7c1a53fef5c06; f6060f4f56791feac32c0502db744887=a268b48dd6ac23c5ae199d14b474c6f3; s_cc=true; s_sq=%5B%5BB%5D%5D; _cs_cvars=%7B%221%22%3A%5B%22Page%20Name%22%2C%22kohleausstieg%22%5D%2C%222%22%3A%5B%22Page%20Title%22%2C%22Erste%20Group%20to%20phase%20out%20business%20activities%20in%20the%20thermal%20coal%20sector%20by%202030%22%5D%2C%223%22%3A%5B%22Page%20Template%22%2C%22newsContentPage%22%5D%2C%224%22%3A%5B%22Language%22%2C%22en%22%5D%7D; _cs_id=708899a2-a80b-acea-e55a-bd8654377b08.1613647110.3.1615894673.1615894133.1.1647811110209.Lax.0; _cs_s=6.1; __CT_Data=gpv=11&ckp=tld&dm=erstegroup.com&apv_59_www56=11&cpv_59_www56=11&rpv_59_www56=11'
}


class ErsteSpider(scrapy.Spider):
    name = 'erste'
    start_urls = ['https://www.erstegroup.com/en/news-media/press-releases']
    page = 0
    count_of_items = 0
    def parse(self, response):
        data = requests.request("POST", url, headers=headers, data=payload.format(self.page))
        data = json.loads(data.text)
        for index in range(len(data['hits']['hits'])):
            links = data['hits']['hits'][index]['_source']['url']
            yield response.follow(links, self.parse_post)
        if self.count_of_items < data['hits']['total']:
            self.page += 1
            self.count_of_items += 10
            yield response.follow(response.url, self.parse, dont_filter=True)

    def parse_post(self, response):
        try:
            date = response.xpath('(//div[@class="col col-md-10 offset-md-1"]//div[@class="w-auto mw-full rte"]/p)[1]/text()').get().strip()
        except AttributeError:
            date = "-"
        title = response.xpath('//h1/text() | //h2[@class="align-center"]/text() | (//div[@class="w-auto mw-full rte"]/h2)[1]/text()').get().strip()
        content = response.xpath('//div[@class="w-auto mw-full rte"]/ul//text()[not (ancestor::figcaption) and not (ancestor::script)]|//div[@class="textWithImage"][position()>2]//text()[not (ancestor::figcaption) and not (ancestor::script)] | //div[@class="text-image__content col d-f col10-md-7"]//text()[not (ancestor::figcaption) and not (ancestor::script)] | (//div[@class="textWithImage"])[last()]//text()[not (ancestor::figcaption) and not (ancestor::script)]').getall()
        content = [p.strip() for p in content if p.strip()]
        content = re.sub(pattern, "",' '.join(content))

        item = ItemLoader(item=ErsteItem(), response=response)
        item.default_output_processor = TakeFirst()

        item.add_value('title', title)
        item.add_value('link', response.url)
        item.add_value('content', content)
        item.add_value('date', date)

        yield item.load_item()
