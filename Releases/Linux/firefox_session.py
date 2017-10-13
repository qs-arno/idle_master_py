#!/usr/bin/python

import json
import os

###############################################################################

def get_session_info_from_firefox(profile_name, profile_root=None):
    """
    Retrieve session ID and login token from Mozilla Firefox' cookies
    """

    steam_session = dict()

    ## Add the default profile root if we weren't provided one
    if not profile_root:
        profile_root = os.path.expanduser("~") + "/.mozilla/firefox"

    ## Different versions of Firefox store the cookie data on disk in different
    ## files; the different files also have different JSON structure, so even
    ## though there's some code duplication between these if() alternatives,
    ## trust me: it looks way more convoluted if you do it "the right way" with
    ## a for loop. :)
    if os.path.exists(profile_root + "/" + profile_name + "/sessionstore.js"):
        sessionstore_filename = profile_root + "/" + profile_name + "/sessionstore.js"

        with open(sessionstore_filename, "r") as file:
            firefox_sessionstore = json.load(file)

        for window in firefox_sessionstore["windows"]:
            try:
                for cookie in window["cookies"]:
                    if cookie["host"] == "steamcommunity.com" and cookie["name"] == "sessionid":          steam_session["sessionid"]          = cookie["value"]
                    if cookie["host"] == "steamcommunity.com" and cookie["name"] == "steamLogin":         steam_session["steamLogin"]         = cookie["value"]
                    if cookie["host"] == "steamcommunity.com" and cookie["name"] == "steamRememberLogin": steam_session["steamRememberLogin"] = cookie["value"]
                    if cookie["host"] == "steamcommunity.com" and cookie["name"] == "steamparental":      steam_session["steamparental"]      = cookie["value"]
            except:
                continue
    elif os.path.exists(profile_root + "/" + profile_name + "/sessionstore-backups/recovery.js"):
        sessionstore_filename = profile_root + "/" + profile_name + "/sessionstore-backups/recovery.js"

        with open(sessionstore_filename, "r") as file:
            firefox_sessionstore = json.load(file)

        try:
            for cookie in firefox_sessionstore["cookies"]:
                if cookie["host"] == "steamcommunity.com" and cookie["name"] == "sessionid":          steam_session["sessionid"]          = cookie["value"]
                if cookie["host"] == "steamcommunity.com" and cookie["name"] == "steamLogin":         steam_session["steamLogin"]         = cookie["value"]
                if cookie["host"] == "steamcommunity.com" and cookie["name"] == "steamRememberLogin": steam_session["steamRememberLogin"] = cookie["value"]
                if cookie["host"] == "steamcommunity.com" and cookie["name"] == "steamparental":      steam_session["steamparental"]      = cookie["value"]
        except:
            pass

    ## If we didn't get the two values we definitely need, return False so the
    ## caller can detect the failure and act accordingly.
    if steam_session.has_key("sessionid") and steam_session.has_key("steamLogin"):
        return(steam_session)
    else:
        return(False)

###############################################################################

if __name__ == "__main__":
    steam_session = get_session_info_from_firefox()

    import pprint
    pprint.pprint(steam_session)

## EOF
########
