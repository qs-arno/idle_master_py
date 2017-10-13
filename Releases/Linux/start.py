import requests
import cookielib
import bs4
import time
import re
import subprocess
import sys
import os
import json
import logging
import datetime
import ctypes
from colorama import init, Fore, Back, Style
import firefox_session
init()

os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))

logging.basicConfig(filename="idlemaster.log",filemode="w",format="[ %(asctime)s ] [%(name)s] [%(levelname)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p",level=logging.DEBUG)
logging.addLevelName( logging.CRITICAL, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))
logging.addLevelName( logging.ERROR,    "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
logging.addLevelName( logging.WARNING,  "\033[1;35m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName( logging.DEBUG,    "\033[1;30m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("[ %(asctime)s ] [%(name)s] [%(levelname)s] %(message)s", "%m/%d/%Y %I:%M:%S %p"))
logging.getLogger('').addHandler(console)

## Don't care about urllib3's logspam, set its threshold to WARNING
my_logger = logging.getLogger('requests.packages.urllib3.connectionpool')
my_logger.setLevel(logging.WARNING)

if sys.platform.startswith('win32'):
	ctypes.windll.kernel32.SetConsoleTitleA("Idle Master")

logging.info("WELCOME TO IDLE MASTER")

try:
	authData={}
	authData["sessionid"]=None
	authData["steamLogin"]=None
	authData["sort"]=None
	authData["steamparental"]=None
	authData["wantExitPrompt"]=True
	authData["hasPlayTime"]="false"
	authData["firefoxProfile"]=None
	execfile("./settings.txt",authData)
except Exception, e:
	logging.critical("Error loading config file: " + e.message)
	if authData["wantExitPrompt"]:
		raw_input("Press Enter to continue...")
	sys.exit()
	
## Read steamcommunity.com cookies from Firefox session store if we have one
if authData["firefoxProfile"]:
    logging.debug("Reading cookie data from Firefox session store")
    firefox_session_info=firefox_session.get_session_info_from_firefox(authData["firefoxProfile"])
    if firefox_session_info:
        authData['sessionid']=firefox_session_info['sessionid']
        authData['steamLogin']=firefox_session_info['steamLogin']

## Derive profile URI
myProfileURL = "http://steamcommunity.com/profiles/"+authData["steamLogin"][:17]
logging.debug("Profile: " + myProfileURL)

## Bail if we don't have a sessionid cookie
if authData["sessionid"]:
    logging.debug("Session ID cookie : " + authData['sessionid'])
else:
	logging.critical("No sessionid set")
	if authData["wantExitPrompt"]:
	    raw_input("Press Enter to continue...")
	sys.exit()
	
## Bail if we don't have a steamLogin cookie
if authData["steamLogin"]:
    logging.debug("Login cookie      : " + authData['steamLogin'])
else:
	logging.critical("No steamLogin set")
	if authData["wantExitPrompt"]:
		raw_input("Press Enter to continue...")
	sys.exit()

def generateCookies():
	global authData
	try:
		cookies = dict(sessionid=authData["sessionid"], steamLogin=authData["steamLogin"], steamparental=authData["steamparental"])
	except:
		logging.critical("Error setting cookies")
		if authData["wantExitPrompt"]:
		    raw_input("Press Enter to continue...")
		sys.exit()

	return cookies

def dropDelay(numDrops):
	if numDrops>1:
		baseDelay = (15*60)
	else:
		baseDelay = (5*60)
	return baseDelay
	
def idleOpen(appID):
	try:
		logging.info("Starting game " + getAppName(appID) + " to idle cards")
		global process_idle
		global idle_time

		idle_time = time.time()

		if sys.platform.startswith('win32'):
			process_idle = subprocess.Popen("steam-idle.exe "+str(appID))
		elif sys.platform.startswith('darwin'):
			process_idle = subprocess.Popen(["./steam-idle", str(appID)])
		elif sys.platform.startswith('linux'):
			process_idle = subprocess.Popen(["python2", "steam-idle.py", str(appID)])
	except:
		logging.critical("Error launching steam-idle with game ID " + str(appID))
		if authData["wantExitPrompt"]:
		    raw_input("Press Enter to continue...")
		sys.exit()

def idleClose(appID):
	try:
		logging.info("Closing game " + getAppName(appID))
		process_idle.terminate()
		total_time = int(time.time() - idle_time)
		logging.info(getAppName(appID) + " took " + Fore.GREEN + str(datetime.timedelta(seconds=total_time)) + Fore.RESET + " to idle.")
	except:
		logging.critical("Error closing game. Exiting.")
		if authData["wantExitPrompt"]:
		    raw_input("Press Enter to continue...")
		sys.exit()

def chillOut(appID):
	logging.warning("Suspending operation for "+getAppName(appID))
	idleClose(appID)
	stillDown = True
	while stillDown:
		logging.info("Sleeping for 5 minutes.")
		time.sleep(5*60)
		try:
			rBadge = requests.get(myProfileURL+"/gamecards/" + str(appID) + "/",cookies=cookies)
			indBadgeData = bs4.BeautifulSoup(rBadge.text)
			badgeLeftString = indBadgeData.find_all("span",{"class": "progress_info_bold"})[0].contents[0]
			if "card drops" in badgeLeftString:
				stillDown = False
		except:
			logging.info("Still unable to find drop info.")
	# Resume operations.
	idleOpen(appID)
	
def getAppName(appID):
	try:
		api = requests.get("http://store.steampowered.com/api/appdetails/?appids=" + str(appID) + "&filters=basic")
		api_data = json.loads(api.text)
		return Fore.CYAN + api_data[str(appID)]["data"]["name"].encode('ascii', 'ignore') + Fore.RESET
	except:
		return Fore.CYAN + "App "+str(appID) + Fore.RESET

def getPlainAppName(appid):
	try:
		api = requests.get("http://store.steampowered.com/api/appdetails/?appids=" + str(appID) + "&filters=basic")
		api_data = json.loads(api.text)
		return api_data[str(appID)]["data"]["name"].encode('ascii', 'ignore')
	except:
		return "App "+str(appID)

def get_blacklist():
	try:
		with open('blacklist.txt', 'r') as f:
			lines = f.readlines()
		blacklist = [int(n.strip()) for n in lines]
	except:
		blacklist = [];

	if not blacklist:
		logging.debug("No games have been blacklisted")

	return blacklist

logging.info("Finding games that have card drops remaining")

try:
	cookies = generateCookies()
	r = requests.get(myProfileURL+"/badges/",cookies=cookies)
except:
	logging.critical("Error reading badge page")
	if authData["wantExitPrompt"]:
		raw_input("Press Enter to continue...")
	sys.exit()

try:
	badgesLeft = []
	badgePageData = bs4.BeautifulSoup(r.text, "lxml")
	badgeSet = badgePageData.find_all("div",{"class": "badge_title_stats"})
except:
	logging.critical("Error finding drop info")
	if authData["wantExitPrompt"]:
		raw_input("Press Enter to continue...")
	sys.exit()

# For profiles with multiple pages
try:
	badgePages = int(badgePageData.find_all("a",{"class": "pagelink"})[-1].text)
	if badgePages:
		logging.info(str(badgePages) + " badge pages found.  Gathering additional data")
		currentpage = 2
		while currentpage <= badgePages:
			r = requests.get(myProfileURL+"/badges/?p="+str(currentpage),cookies=cookies)
			badgePageData = bs4.BeautifulSoup(r.text, "lxml")
			badgeSet = badgeSet + badgePageData.find_all("div",{"class": "badge_title_stats"})
			currentpage = currentpage + 1
except Exception, e:
	logging.warning("Error reading badge page: " + e.message)

userinfo = badgePageData.find("a",{"class": "user_avatar"})
if not userinfo:
	logging.critical("Invalid cookie data, cannot log in to Steam")
	if authData["wantExitPrompt"]:
		raw_input("Press Enter to continue...")
	sys.exit()

blacklist = get_blacklist()

if authData["sort"]=="mostvalue" or authData["sort"]=="leastvalue":
	logging.debug("Getting card values")

for badge in badgeSet:

	try:
		badge_text = badge.get_text()
		dropCount = badge.find_all("span",{"class": "progress_info_bold"})[0].contents[0]
		has_playtime = re.search("[0-9\.] hrs on record", badge_text) != None
        
		if "No card drops" in dropCount or (has_playtime == False and authData["hasPlayTime"].lower() == "true") :
			continue
		else:
			# Remaining drops
			dropCountInt, junk = dropCount.split(" ",1)
			dropCountInt = int(dropCountInt)
			linkGuess = badge.find_parent().find_parent().find_parent().find_all("a")[0]["href"]
			junk, badgeId = linkGuess.split("/gamecards/",1)
			badgeId = int(badgeId.replace("/",""))
			if badgeId in blacklist:
				logging.warning(getAppName(badgeId) + " on blacklist, skipping game")
				continue
			else:
				logging.info("Need to idle: [" + str(badgeId) + "] " + Fore.GREEN + getAppName(badgeId) + Fore.RESET)
				if authData["sort"]=="mostvalue" or authData["sort"]=="leastvalue":
					gameValue = requests.get("http://api.enhancedsteam.com/market_data/average_card_price/?appid=" + str(badgeId) + "&cur=usd")
					push = [badgeId, dropCountInt, float(str(gameValue.text))]
					badgesLeft.append(push)
				else:
					push = [badgeId, dropCountInt, 0]
					badgesLeft.append(push)
	except:
		continue

logging.info("Idle Master needs to idle " + Fore.GREEN + str(len(badgesLeft)) + Fore.RESET + " games")

def getKey(item):
	if authData["sort"]=="mostcards" or authData["sort"]=="leastcards":
		return item[1]
	elif authData["sort"]=="mostvalue" or authData["sort"]=="leastvalue":
		return item[2]
	else:
		return item[0]

sortValues = ["", "mostcards", "leastcards", "mostvalue", "leastvalue"]
if authData["sort"] in sortValues:
	if authData["sort"]=="":
		games = badgesLeft
	if authData["sort"]=="mostcards" or authData["sort"]=="mostvalue":
		games = sorted(badgesLeft, key=getKey, reverse=True)
	if authData["sort"]=="leastcards" or authData["sort"]=="leastvalue":
		games = sorted(badgesLeft, key=getKey, reverse=False)
else:
	logging.critical("Invalid sort value")
	if authData["wantExitPrompt"]:
		raw_input("Press Enter to continue...")
	sys.exit()

for appID, drops, value in games:
	delay = dropDelay(int(drops))
	stillHaveDrops=1
	numCycles=50
	maxFail=2
	
	idleOpen(appID)

	logging.info(getAppName(appID) + " has " + str(drops) + " card drops remaining")

	if sys.platform.startswith('win32'):
		ctypes.windll.kernel32.SetConsoleTitleA("Idle Master - Idling " + getPlainAppName(appID) + " [" + str(drops) + " remaining]")

	while stillHaveDrops==1:
		try:
			logging.info("Sleeping for " + str(delay / 60) + " minutes")
			time.sleep(delay)
			numCycles-=1
			if numCycles<1: # Sanity check against infinite loop
				stillHaveDrops=0

			logging.info("Checking to see if " + getAppName(appID) + " has remaining card drops")
			rBadge = requests.get(myProfileURL + "/gamecards/" + str(appID) + "/",cookies=cookies)
			indBadgeData = bs4.BeautifulSoup(rBadge.text, "lxml")
			badgeLeftString = indBadgeData.find_all("span",{"class": "progress_info_bold"})[0].contents[0]
			if "No card drops" in badgeLeftString:
				logging.info("No card drops remaining")
				stillHaveDrops=0
			else:
				dropCountInt, junk = badgeLeftString.split(" ",1)
				dropCountInt = int(dropCountInt)
				delay = dropDelay(dropCountInt)
				logging.warning(getAppName(appID) + " has " + str(dropCountInt) + " card drops remaining")
				if sys.platform.startswith('win32'):
					ctypes.windll.kernel32.SetConsoleTitleA("Idle Master - Idling " + getPlainAppName(appID) + " [" + str(dropCountInt) + " remaining]")
		except:
			if maxFail>0:
				logging.warning("Error checking if drops are done, number of tries remaining: " + str(maxFail))
				maxFail-=1
			else:
				# Suspend operations until Steam can be reached.
				chillOut(appID)
				maxFail+=1
				break

	idleClose(appID)
	logging.info("Successfully completed idling cards for " + getAppName(appID))

logging.debug("Successfully completed idling process")
if authData["wantExitPrompt"]:
	raw_input("Press Enter to continue...")
