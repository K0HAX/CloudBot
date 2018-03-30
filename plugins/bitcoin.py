import re
import json
import requests
from cloudbot import hook

def getBTCQuotes():
	rsp = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
	if rsp.status_code in (200,):
		fin_data = json.loads(rsp.content.decode('unicode_escape'))
		return fin_data

@hook.command()
def btc():
	return bitcoin()

@hook.command()
def bitcoin():
    #"""Gets bitcoin information"""

    try:
	    data = getBTCQuotes()
    except:
	    return "Error getting quote."

    print("Data: {}".format(data))

    # return "Demo mode active"

    if not data['chartName']:
        return "No results."

    symbol = "Bitcoin"
    price = float(data['bpi']['USD']['rate'].replace(',', ''))

    # this is for dead companies, if this isn't here Percentc will fail with DBZ
    if price == 0:
        return "\x02Bitcoin\x02 - {}".format(price)

    return "\x02\x037Bitcoin\x03\x02: ${0:.2f}/btc".format(price)

