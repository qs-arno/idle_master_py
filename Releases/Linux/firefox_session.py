#!/usr/bin/python

import json

###############################################################################

def get_session_info_from_firefox(profile_name, profile_root=None):
    """
    Retrieve session ID and login token from Firefox' cookies, if possible.
    """

    ## Add the default profile root if we weren't provided one
    if not profile_root:
        import os
        profile_root = os.path.expanduser("~") + '/.mozilla/firefox'

    sessionstore_filename = profile_root + '/' + profile_name + '/sessionstore.js'

    with open(sessionstore_filename, 'r') as file:
        firefox_sessionstore = json.load(file)

    steam_session = dict()
    for window in firefox_sessionstore['windows']:
        try:
            for cookie in window['cookies']:
                if cookie['host'] == 'steamcommunity.com' and cookie['path'] == '/' and cookie['name'] == 'sessionid':          steam_session['sessionid']          = cookie['value']
                if cookie['host'] == 'steamcommunity.com' and cookie['path'] == '/' and cookie['name'] == 'steamLogin':         steam_session['steamLogin']         = cookie['value']
                if cookie['host'] == 'steamcommunity.com' and cookie['path'] == '/' and cookie['name'] == 'steamRememberLogin': steam_session['steamRememberLogin'] = cookie['value']
                if cookie['host'] == 'steamcommunity.com' and cookie['path'] == '/' and cookie['name'] == 'steamparental':      steam_session['steamparental']      = cookie['value']
        except:
            continue

    return(steam_session)

###############################################################################

if __name__ == "__main__":
    steam_session = get_session_info_from_firefox()

    import pprint
    pprint.pprint(steam_session)

## EOF
########
