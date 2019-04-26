# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy.http import FormRequest
from scrapy.loader import ItemLoader
from FBCrawler.items import FbcrawlItem, CommentsItem

PUBLIC_POST_URL = 'https://mbasic.facebook.com/graphsearch/str/{}/stories-keyword/stories-public?source=pivot'
FRIEND_POST_URL = 'https://mbasic.facebook.com/graphsearch/str/{}/stories-keyword/stories-feed?&source=pivot'

# Reference: https://github.com/rugantio/fbcrawl
class FacebookSpider(scrapy.Spider):
    name = 'facebook'
    allowed_domains = ['mbasic.facebook.com']
    start_urls = ['https://mbasic.facebook.com']
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['source','shared_from','date','text', \
                               'reactions','likes','ahah','love','wow', \
                               'sigh','grrr','comments_count','url']
    }

    def __init__(self, *args, **kwargs):
        logger = logging.getLogger('scrapy.middleware')
        logger.setLevel(logging.WARNING)
        super().__init__(*args,**kwargs)

        if 'email' not in kwargs or 'password' not in kwargs:
            raise AttributeError('You need to provide valid email and password:\n'
                                 'scrapy facebook -a email="EMAIL" -a password="PASSWORD"')
        else:
            self.logger.info('Email and password provided, using these as credentials')

        if 'query' not in kwargs:
            raise AttributeError('You need to provide a valid query to crawl!'
                                 'scrapy facebook -a query="SEARCH_QUERY"')

        self.count = 0
        self.lang = 'id'
    
    def parse(self, response):

        yield FormRequest.from_response(
                response,
                formxpath='//form[contains(@action, "login")]',
                formdata={'email': self.email,'pass': self.password},
                callback=self.parse_home
        )

    def parse_home(self, response):
        '''
        This method has multiple purposes:
        1) Handle failed logins due to facebook 'save-device' redirection
        2) Set language interface, if not already provided
        3) Navigate to given page 
        '''
        #handle 'save-device' redirection
        if response.xpath("//div/a[contains(@href,'save-device')]"):
            self.logger.info('Got stuck in "save-device" checkpoint')
            self.logger.info('I will now try to redirect to the correct page')
            yield FormRequest.from_response(
                response,
                formdata={'name_action_selected': 'dont_save'},
                callback=self.parse_home
                )

        query_url_public = PUBLIC_POST_URL.format(self.query.replace(" ", "+"))
        query_url_friends = FRIEND_POST_URL.format(self.query.replace(" ", "+"))
        self.logger.info('Scraping facebook with query: {}'.format(self.query))
        yield scrapy.Request(url=query_url_public,callback=self.parse_query)
        yield scrapy.Request(url=query_url_friends,callback=self.parse_query)

    def parse_query(self, response):
        '''
        new.context['lang'] = self.lang           
        Parse the given page selecting the posts.
        new.context['lang'] = self.lang           
        Then ask recursively for another page.
        '''

        for post in response.xpath("//div[contains(@role,'article')]"):
            new = ItemLoader(item=FbcrawlItem(),selector=post)
            self.logger.info('Parsing post n = {}'.format(abs(self.count)))
            new.add_xpath('comments_count', "./div[2]/div[2]/a[1]/text()")        
            new.add_xpath('url', ".//a[contains(@href,'footer')]/@href")
            post = post.xpath(".//a[contains(@href,'footer')]/@href").extract() 
            try:
                temp_post = response.urljoin(post[0])
                self.count -= 1
                yield scrapy.Request(temp_post, self.parse_post, priority = self.count, meta={'item':new})
            except Exception as e:
                self.logger.error(e)
            
        next_page = response.xpath('//div[@id="see_more_pager"]/a/@href').extract_first()
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse_query)
    
    def parse_post(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response,parent=response.meta['item'])
        new.add_xpath('source', "//td/div/h3/strong/a/text() | //span/strong/a/text() | //div/div/div/a[contains(@href,'post_id')]/strong/text()")
        new.add_xpath('shared_from','//div[contains(@data-ft,"top_level_post_id") and contains(@data-ft,\'"isShare":1\')]/div/div[3]//strong/a/text()')
        new.add_xpath('date','//div/div/abbr/text()')
        new.add_xpath('text','//div[@data-ft]//p//text() | //div[@data-ft]/div[@class]/div[@class]/text()')
        new.add_xpath('reactions',"//a[contains(@href,'reaction/profile')]/div/div/text()")  
        
        reactions = response.xpath("//div[contains(@id,'sentence')]/a[contains(@href,'reaction/profile')]/@href")
        reactions = response.urljoin(reactions[0].extract())
        yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':new})
        
    def parse_reactions(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response, parent=response.meta['item'])
        new.context['lang'] = self.lang           
        new.add_xpath('likes',"//a[contains(@href,'reaction_type=1')]/span/text()")
        new.add_xpath('ahah',"//a[contains(@href,'reaction_type=4')]/span/text()")
        new.add_xpath('love',"//a[contains(@href,'reaction_type=2')]/span/text()")
        new.add_xpath('wow',"//a[contains(@href,'reaction_type=3')]/span/text()")
        new.add_xpath('sigh',"//a[contains(@href,'reaction_type=7')]/span/text()")
        new.add_xpath('grrr',"//a[contains(@href,'reaction_type=8')]/span/text()")        
        return new.load_item()
