#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-07-17 08:52:38 by lanhin
# Project: Deckstring Crawler
#
# Use this file as a pyspider script
# To crawl deck from http://www.hearthpwn.com/decks
# Refer to http://docs.pyspider.org/en/latest/Quickstart/ for more details

from pyspider.libs.base_handler import *
import re

class Handler(BaseHandler):
    crawl_config = {
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://www.hearthpwn.com/decks', callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            if re.match("http://www.hearthpwn.com/decks/", each.attr.href):
                self.crawl(each.attr.href, callback=self.detail_page)
            if re.match("http://www.hearthpwn.com/decks\?page=", each.attr.href):
                self.crawl(each.attr.href, callback=self.index_page)

    @config(priority=2)
    def detail_page(self, response):
        new_dict = {"url": response.url,
                    "title": response.doc('title').text(),
                    "deckstring": [each.attr("data-clipboard-text") for each in response.doc('[data-ga-click-event-tracking-label="Top"]').items()][0],
                    "date": [each for each in response.doc('[class="deck-details"]')('li').items()][-1].text(),
                    "deck-type": [each for each in response.doc('[class="deck-details"]')('li').items()][0].text(),
                    "archetype": [each for each in response.doc('[class="deck-details"]')('li').items()][1].text(),
                    "rating-sum": response.doc('[class="deck-rating-form"]').text()
                   }
        if response.doc('[class="is-std"]').text():
            new_dict['type'] = 'Standard'
        else:
            new_dict['type'] = 'Wild'

        return new_dict
