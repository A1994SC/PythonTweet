try:
	import json
except ImportError:
	import simplejson as json
import sqlite3
import time
from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
from datetime import datetime

config = {}
filename = "config.py"
exec(compile(open(filename, "rb").read(), filename, 'exec'), config)
str_table = "create table if not exists alerts (timestamp INT primary key, read_time TEXT not null ,loc TEXT not null, time INT not null, credits INT not null, reward TEXT, note TEXT not null)"

def database(bodyMeth, dbName="warframe.db"):
	conn = sqlite3.connect(dbName)
	cur  = conn.cursor()
	cur.execute(str_table)
	bodyMeth(cur, 3200)
	conn.commit()
	conn.close()
	
def databaseChecker(bodyMeth, dbName="warframe.db"):
	conn = sqlite3.connect(dbName)
	cur  = conn.cursor()
	cur.execute(str_table)
	while True:
		try:
			bodyMeth(cur, 50)
			conn.commit()
			time.sleep(360)
		except KeyboardInterrupt:
			conn.commit()
			conn.close()
			break

def twitterAuth():
	oauth = OAuth(config["access_token"], config["access_secret"], 
		config["consumer_key"], config["consumer_secret"])
	return Twitter(auth = oauth)
	
def twitterGetTweets(twitter, acc_name, twe_con):
	ary = []
	int_size = config["int_maxTweetCount"]
	tweets = twitter.statuses.user_timeline(count=twe_con, screen_name=acc_name)
	for tweet in tweets:
		ary.append([tweet['created_at'], tweet['text'], tweet['id']])
	if ((twe_con / int_size) > 1.0):
		while len(ary) < twe_con:
			tweets = twitter.statuses.user_timeline(count=int_size, 
				screen_name=acc_name, max_id=str(ary[len(ary)-1][2]))
			print("Sleeping. Ary len(" + str(len(ary)) + ")")
			if len(tweets) < int_size:
				for tweet in tweets:
					print([tweet['created_at'], tweet['text'], tweet['id']])
			time.sleep(5)
			for tweet in tweets:
				ary.append([tweet['created_at'], tweet['text'], tweet['id']])
	return ary

str_time ="%a %b %d %H:%M:%S +0000 %Y";
	
def dateToUnix(str_date):
	return int(datetime.strptime(str_date, str_time).timestamp())
	
def parseTextBody(str_body):
	ary = []
	ary_temp = str_body.split(":")
	ary.append(ary_temp[0])	#(0)
	str_temp = ""
	for i in ary_temp:
		if i is ary[0]:
			continue
		else:
			str_temp += i
	ary_temp = str_temp.split("-")
	
	ary.append(ary_temp[0]) #(1) notes
	ary.append(ary_temp[1]) #(2) time
	ary.append(ary_temp[2]) #(3) credits
	if len(ary_temp) == 4:
		ary.append(ary_temp[3]) #(4)
	return ary

ary_insert = []
int_invas = 0
parse = ""
ts = ""
ht = ""
lc = ""
tm = ""
cd = ""
rd = ""
ns = ""
	
def datebaseBody(cur, int_count):
	twitter = twitterAuth();
	ary = twitterGetTweets(twitter, "warframealerts", int_count);
	ary_insert = [];
	int_invas = 0;
	for i in ary:
		if "Invasion" in i[1]:
			int_invas += 1;
			continue
		else:
			parse = parseTextBody(i[1])
			ts	= dateToUnix(i[0])
			ht	= i[0]
			lc 	= parse[0].strip()
			tm	= parse[2].strip()[:-1]
			cd	= parse[3].strip()[:-2]
			rd	= ""
			if len(parse) == 5:
				rd 	= parse[4].strip()
			ns	= parse[1].strip()
			ary_insert.append((ts, ht, lc, tm, cd, rd, ns))
	
	print("alerts: " + str(len(ary_insert)) + " | Invasion: " + str(int_invas))
	print([lc, tm, cd, rd, ns])
	print(datetime.now())
	cur.executemany("insert or ignore into alerts values (?,?,?,?,?,?,?)", ary_insert)
		
def main():
	bool = False
	if bool:
		database(datebaseBody)
	else:
		databaseChecker(datebaseBody)

main()