#!/usr/bin/env python3

# Telegram bot reporting cancelled departures for a HSL route
#
# Copyright (c) 2022-2023 Antti Honkela
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from time import sleep
from origamibot import OrigamiBot as Bot
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import json
import datetime
import configparser
import os
import sys


def run_query(client, route):
    # Provide a GraphQL query
    query = gql(
    """
{
  cancelledTripTimes(
    routes: ["%s"]
    minDate: "%s"
    maxDate: "%s"
  ) {
    scheduledDeparture
    serviceDay
    trip {
      gtfsId
      tripHeadsign
      routeShortName
      directionId
      pattern {
        code
        name
      }
      route {
        gtfsId
        longName
      }
    }
    realtimeState
    headsign
  }
}""" % (route, str(datetime.date.today()), str(datetime.date.today()))
    )
    return client.execute(query)['cancelledTripTimes']


class MessageCache():
    def __init__(self, bot, chatid):
        self.cache = set()
        self.bot = bot
        self.last_update_date = datetime.date.today()

    def send_message(self, message):
        date = datetime.date.today()
        if self.last_update_date != date:
            self.cache = set()
            self.last_update_date = date
        if (date, message) not in self.cache:
            self.cache.add((date, message))
            self.bot.send_message(chatid, message)
    
    def set_bot(self, bot):
        self.bot = bot
    

def parse_time(time):
    if time % 60 == 0:
        return '%d:%02d' % (time // 3600, (time % 3600) // 60)
    else:
        return '%d:%02d:%02d' % (time // 3600, (time % 3600) // 60, time % 60)


def prettify_result(res):
    cleanname = ' '.join(res['trip']['pattern']['name'].split(' ')[:3])
    return '%s %s' % (parse_time(res['scheduledDeparture']), cleanname)


def create_bot(token, chatid, cache = None):
    bot = Bot(token)   # Create instance of OrigamiBot class
    if cache is None:
        cache = MessageCache(bot, chatid)
    else:
        cache.set_bot(bot)
    return cache, bot



if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(os.path.join(os.environ['HOME'], '.config', 'hsl_telebot', 'hsl_telebot.cfg'))
    token = config['telebot']['token']
    chatid = config['telebot']['chatid']
    route = config['hsl']['route']
    digitransit_api_key = config['hsl']['api_key']
    cache, bot = create_bot(token, chatid)
    # Select your transport with a defined url endpoint
    transport = AIOHTTPTransport(url="https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql",
                    headers={'digitransit-subscription-key': digitransit_api_key})
    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)

    while True:
        try:
            bot.start()   # start bot's threads
            while True:
                res = run_query(client, route)
                for r in res:
                    #print(prettify_result(r))
                    cache.send_message(prettify_result(r))
                sleep(300)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(datetime.datetime.now())
            print(e)
            bot.stop()
            cache, bot = create_bot(token, chatid, cache)
            # Select your transport with a defined url endpoint
            transport = AIOHTTPTransport(url="https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql",
                            headers={'digitransit-subscription-key': digitransit_api_key})
            # Create a GraphQL client using the defined transport
            client = Client(transport=transport, fetch_schema_from_transport=True)
            sleep(60)
