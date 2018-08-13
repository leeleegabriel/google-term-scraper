#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import os
import os.path
import errno
import configparser
import sqlite3
from time import sleep
from urllib.request import urlopen
from tqdm import tqdm
from base64 import b64encode

from lib.timeout import timeout

DB_timeout = 600


def start(config):
	os.chdir(config['Abspath'])

	global App_dir, Misc_dir

	DB = config['DB_file']
	Filter_errors = config['Filter_errors']
	App_dir = config['App_dir']
	Misc_dir = config['Misc_dir']

	conn = sqlite3.connect(DB)
	c = conn.cursor()
	tqdm.write(' Getting URLs from DB')
	for x in range(0, DB_timeout):
		try:
			if Filter_errors:
				c.execute("""SELECT url FROM URLs WHERE url NOT IN(SELECT url FROM Used_URLs) AND url NOT IN(SELECT url FROM Download_Errors)""")
			else:
				c.execute("""SELECT url FROM URLs WHERE url NOT IN(SELECT url FROM Used_URLs)""")
			Downloads = [line[0] for line in  c.fetchall()]
		except sqlite3.OperationalError as e:
			if "locked" in str(e):
				sleep(1)
			else:
				raise
		else:
			break
	conn.close()

	if Downloads:
		tqdm.write(' Attempting to Download Files from %s URLs' % len(Downloads))
		for url in tqdm(Downloads):
			try:
				if not os.path.isfile(App_dir + '/' + b64encode(url)) and not os.path.isfile(Misc_dir + '/' + b64encode(url)):
					getDownload(DB, url)
			except KeyboardInterrupt:
				raise
			except Exception as error:
				conn = sqlite3.connect(DB)
				c = conn.cursor()
				for x in range(0, DB_timeout):
					try:
						c.execute("""INSERT OR REPLACE INTO Download_Errors (url, Error) VALUES (?, ?)""", (url, str(error)))
						conn.commit()
					except sqlite3.OperationalError as e:
						if "locked" in str(e):
							sleep(1)
						else:
							raise
					else:
						break
				conn.close()
	else:
		tqdm.write(' No URLs Found')


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
	for x in range(0, DB_timeout):
		try:
			c.execute("""INSERT OR REPLACE INTO Used_URLs(url) VALUES (?)""", (url,))
			conn.commit()
		except sqlite3.OperationalError as e:
			if "locked" in str(e):
				sleep(1)
			else:
				raise
		else:
			break
	conn.close()


if __name__ == "__main__":
	start(os.path.abspath('..'), './config/config.txt', './config/ScrapeDB.db')
