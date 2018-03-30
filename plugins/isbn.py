import re
import requests

from cloudbot import hook
from bs4 import BeautifulSoup
import cloudbot

@hook.on_start()
def load_api(bot):
    global isbndb_key
    global cx

    isbndb_key = bot.config.get("api_keys", {}).get("isbndb_dev_key", None)

def cleanhtml(raw_html):
    cleantext = BeautifulSoup(raw_html, "lxml").text
    return cleantext

def getISBN(book):
    try:
        #url = "http://isbndb.com/api/v2/json/{}/book/".format(isbndb_key)
        headers = {
            'X-API-KEY': 'F0Dwu7BvTU7UZEGZQaFPt5lt3TLAdiaZ2PmYS1lS'
        }

        url = "https://api.isbndb.com/book/{}".format(book)
        print(url)
        resp = requests.get(url=url, headers=headers)
        data = resp.json()
        #print(data)
        return data
    except:
        return("fail")

@hook.command()
def isbn(reply, text):
    """<isbn> -- gets book information"""
    sym = text.strip().lower()

    #print("String: {}".format(sym))
    tmpdata = getISBN(sym)
    if tmpdata == "fail":
        return("Nothing found, try a different ISBN")
    if 'error' in tmpdata:
        return("{}".format(tmpdata['error']))
    data = tmpdata['book']
    print("Data: {}".format(data))
    if 'dewey_decimal' in data:
        print("Found dewey decimal: {}".format(data['dewey_decimal']))
    else:
        data['dewey_decimal'] = ''

    if 'synopsys' in data:
        synopsys = cleanhtml(data['synopsys'])
    else:
        synopsys = ""

    reply("ISBN Lookup | Title: \x02{title}\x02 | Dimentions: \x02{dimensions}\x02 | Edition: \x02{edition}\x02 | Binding: \x02{binding}\x02 | Dewey Decimal: \x02{dewey_decimal}\x02".format(**data))
    reply("Synopsys: {}".format(synopsys))
    for author in data['authors']:
        reply("Author: {}".format(author))
    return()

