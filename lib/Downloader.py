#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import os
import os.path
import errno
import sqlite3
import logging
from time import sleep
from urllib.request import urlopen
# from tqdm import tqdm
from base64 import b64encode

from lib.timeout import timeout

DB_timeout = 600

# TODO: split start into multiple methods


def start(config, log, handler):
	os.chdir(config['Abspath'])

	global App_dir, Misc_dir, logger

	handler.setFormatter(logging.Formatter('[Download] %(message)s '))
	logger = log

	DB = config['DB_file']
	Filter_errors = config['Filter_errors']
	App_dir = config['App_dir']
	Misc_dir = config['Misc_dir']

	conn = sqlite3.connect(DB)
	c = conn.cursor()

	logger.info(' Getting URLs from DB')
	for x in range(0, DB_timeout):
		try:
			if Filter_errors:
				c.execute("""SELECT url FROM URLs WHERE url NOT IN(SELECT url FROM Used_URLs) AND url NOT IN(SELECT url FROM Download_Errors)""")
			else:
				c.execute("""SELECT url FROM URLs WHERE url NOT IN(SELECT url FROM Used_URLs)""")
			Downloads = [line[0] for line in c.fetchall()]
		except sqlite3.OperationalError as e:
			if "locked" in str(e):
				sleep(1)
			else:
				raise
		else:
			break
	conn.close()

	if Downloads:
		logger.info(' Attempting to Download Files from %s URLs' % len(Downloads))
		for url in Downloads:
			try:
				if not os.path.isfile(App_dir + '/' + b64encode(url)) and not os.path.isfile(Misc_dir + '/' + b64encode(url)):
					logger.debug('Downloading %s', url)
					getDownload(DB, url)
				else:
					logger.debug('Already downloaded %s', url)
			except KeyboardInterrupt:
				logger.debug('Detected KeyboardInterrupt')
				raise
			except Exception as error:
				logger.debug('Logging download error: %s', url)
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
							logger.error(str(e))
							raise
					else:
						break
				conn.close()
		logger.info(' Finished downloading files')
	else:
		logger.info(' No new URLs found')


@timeout(10, os.strerror(errno.ETIMEDOUT))
def getDownload(DB, url):
	data = urlopen(url)
	write = data.read()
	if 'application' in data.info().getheader('Content-Type'):
		folder = App_dir + '/'
	else:
		folder = Misc_dir + '/'
	logger.debug('Saving %s to %s', url, folder)
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
				logger.error(e.message)
				raise
		else:
			break
	conn.close()


if __name__ == "__main__":
	start(os.path.abspath('..'), './config/config.txt', './config/ScrapeDB.db')
