#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import os
import os.path
import errno
import configparser
import sqlite3
from urllib.request import urlopen
from tqdm import tqdm
from base64 import b64encode

#import Helper
from lib.timeout import timeout

#TODO: Clean up globals, and start()
def start(Working_dir, Config_file, DB, Filter_errors):
	os.chdir(Working_dir)
	
	global App_dir, Misc_dir

	config = configparser.ConfigParser()
	config.read(Config_file)

	DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
	Unfiltered_dir = DBase_dir + '/unfiltered'
	App_dir = Unfiltered_dir + '/app'
	Misc_dir = Unfiltered_dir + '/misc'

	tqdm.write(' Getting URLs from DB')
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	if Filter_errors:
		c.execute("""SELECT url FROM URLs WHERE url NOT IN(SELECT url FROM Used_URLs) AND url NOT IN(SELECT url FROM Download_Errors)""")
	else:
		c.execute("""SELECT url FROM URLs WHERE url NOT IN(SELECT url FROM Used_URLs)""")
	Downloads = [line[0] for line in  c.fetchall()]
	conn.close()

	tqdm.write(' Attempting to Download Files from %s URLs' % len(Downloads))
	for url in tqdm(Downloads):
		try:
			if not os.path.isfile(App_dir + '/' + b64encode(url)) and not os.path.isfile(Misc_dir + '/' + b64encode(url)):
				getDownload(DB, url)
		except KeyboardInterrupt:
			raise
		except Exception as e:
			#tqdm.write(url + ' ' + str(e))
			conn = sqlite3.connect(DB)
			c = conn.cursor()
			c.execute("""INSERT OR REPLACE INTO Download_Errors (url, Error) VALUES (?, ?)""", (url, str(e)))
			conn.commit()
			conn.close()

@timeout(10, os.strerror(errno.ETIMEDOUT))
def getDownload(DB, url):
	data = urlopen(url)
	write = data.read()
	if 'application' in data.info().getheader('Content-Type'):
		folder = App_dir + '/'
	else:
		folder = Misc_dir + '/'
	with open(folder + b64encode(url), 'wb') as f:
		f.write(write)

	conn = sqlite3.connect(DB)	
	c = conn.cursor()
	c.execute("""INSERT OR REPLACE INTO Used_URLs(url) VALUES (?)""", (url,))
	conn.commit()
	conn.close()

if __name__== "__main__":
	start(os.path.abspath('..'),'./config/config.txt', './config/ScrapeDB.db')