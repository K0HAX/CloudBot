"""
whois.py
Provides a command to allow users to look up information on domain names.
"""

import sys
from contextlib import suppress

from cloudbot import hook

if sys.version_info < (3, 7, 0):
    import pythonwhois
else:
    pythonwhois = None


@hook.command
def whois(text, reply):
    """<domain> - Does a whois query on <domain>."""
    if pythonwhois is None:
        return "The pythonwhois library does not work on this version of Python."

    domain = text.strip().lower()

    try:
        data = pythonwhois.get_whois(domain, normalized=True)
    except pythonwhois.shared.WhoisException:
        reply("Invalid input.")
        raise

    info = []

    # We suppress errors here because different domains provide different data fields
    try:
        info.append(("Registrar", data["registrar"][0]))
    except KeyError:
        info.append(("Registrar", 'Not Found'))
    except TypeError:
        info.append(("Registrar", 'Not Found'))

    try:
        info.append(("Registrant", data["contacts"]["registrant"]["name"]))
    except KeyError:
        info.append(("Registrant", 'Not Found'))
    except TypeError:
        info.append(("Registrant", 'Not Found'))

    try:
        info.append(("Registered", data["creation_date"][0].strftime("%d-%m-%Y")))
    except KeyError:
        info.append(("Registered", 'Not Found'))
    except TypeError:
        info.append(("Registered", 'Not Found'))

    try:
        info.append(("Expires", data["expiration_date"][0].strftime("%d-%m-%Y")))
    except KeyError:
        info.append(("Expires", 'Not Found'))
    except TypeError:
        info.append(("Expires", 'Not Found'))

    if not info:
        return "No information returned."

    info_text = ", ".join("\x02{name}\x02: {info}".format(name=name, info=i) for name, i in info)
    return "{} - {}".format(domain, info_text)
