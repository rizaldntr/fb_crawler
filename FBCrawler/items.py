# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import TakeFirst, Join, MapCompose

def comments_strip(string,loader_context):
    try:
        string = string[0].rstrip(' Komentar')
        string = string.replace(".", "")
        return string
    except Exception as e:
        return e

def reactions_strip(string,loader_context):
    try:
        if string[0].rfind('rb') >= 0:
            string = string[0].rstrip("rb")
            string = string.strip()
            string = string.replace(",", ".")
            string = float(string)
            string = string * 1000
        elif len(string[0]) == 0:
            string = 0
    except Exception as e:
        return e
    return string

def url_strip(url):
    fullurl = url[0]
    i = fullurl.find('&id=')
    if i != -1:
        return fullurl[:i+4] + fullurl[i+4:].split('&')[0]
    else:  #catch photos   
        i = fullurl.find('/photos/')
        if i != -1:
            return fullurl[:i+8] + fullurl[i+8:].split('/?')[0]
        else: #catch albums
            i = fullurl.find('/albums/')
            if i != -1:
                return fullurl[:i+8] + fullurl[i+8:].split('/?')[0]
            else:
                return fullurl


class FbcrawlItem(scrapy.Item):
    source = scrapy.Field()   
    date = scrapy.Field(      # when was the post published
        input_processor=TakeFirst()
    )       
    text = scrapy.Field(
        output_processor=Join(separator=u'')
    )                       # full text of the post
    comments_count = scrapy.Field(
        output_processor=comments_strip
    )
    comments = scrapy.Field()                                       
    reactions = scrapy.Field(
        output_processor=reactions_strip
    )                  # num of reactions
    likes = scrapy.Field(
        output_processor=reactions_strip
    )                      
    ahah = scrapy.Field(
        output_processor=reactions_strip
    )                      
    love = scrapy.Field(
        output_processor=reactions_strip
    )                      
    wow = scrapy.Field(
        output_processor=reactions_strip
    )                      
    sigh = scrapy.Field(
        output_processor=reactions_strip
    )                      
    grrr = scrapy.Field(
        output_processor=reactions_strip
    )                      
    share = scrapy.Field()                      # num of shares
    url = scrapy.Field(
        output_processor=url_strip
    )
    shared_from = scrapy.Field()

class CommentsItem(scrapy.Item):
    source = scrapy.Field()   
    reply_to=scrapy.Field()
    date = scrapy.Field()       
    text = scrapy.Field(
        output_processor=Join(separator=u'')
    )                       # full text of the post
    reactions = scrapy.Field(
        output_processor=reactions_strip
    )                  # num of reactions
    likes = scrapy.Field(
        output_processor=reactions_strip
    )                      
    ahah = scrapy.Field()                      
    love = scrapy.Field()                      
    wow = scrapy.Field()                      
    sigh = scrapy.Field()                      
    grrr = scrapy.Field()                      
    share = scrapy.Field()                      # num of shares
    url = scrapy.Field()
    shared_from = scrapy.Field()