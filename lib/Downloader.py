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

os.chdir('../')


class Downloader():
	def __init__(self, logger, DB_file, Filter_errors, App_dir, Misc_dir):
		self.logger = logger
		self.DB = DB_file
		self.Filter_errors = Filter_errors
		self.App_dir = App_dir
		self.Misc_dir =Misc_dir	
		self.DB_timeout = 600

	def start(self):
		Downloads = self.filterDownloads(self.self.DB, self.Filter_errors)
		if Downloads:
			self.getFiles(Downloads, self.DB)
		else:
			self.logger.info('No new URLs found')

	def filterDownloads(self):
		self.logger.info('Getting URLs from self.DB')
		conn = sqlite3.connect(self.DB)
		c = conn.cursor()

		Downloads = []
		for x in range(0, self.DB_timeout):
			try:
				if self.Filter_errors:
					c.execute("""SELECT url FROM URLs WHERE url NOT IN(SELECT url FROM Used_URLs) AND url NOT IN(SELECT url FROM Download_Errors)""")
				else:
					c.execute("""SELECT url FROM URLs WHERE url NOT IN(SELECT url FROM Used_URLs)""")
				Downloads = [line[0] for line in c.fetchall()]
			except sqlite3.OperationalError as e:
				if "locked" in str(e):
					sleep(1)
				else:
					self.logger.error(str(e))
					conn.close()
					raise
			else:
				break
		conn.close()
		return Downloads

	def getFiles(self, Downloads):
		self.logger.info('Attempting to Download Files from %s URLs' % len(Downloads))
		for url in Downloads:
			try:
				if not os.path.isfile(self.App_dir + b64encode(url)) and not os.path.isfile(self.Misc_dir  + b64encode(url)):
					self.logger.debug('Downloading %s', url)
					self.downloadFile(self.DB, url)
				else:
					self.logger.debug('Already downloaded %s', url)
			except KeyboardInterrupt:
				self.logger.debug('Detected KeyboardInterrupt')
				raise
			except Exception as error:
				self.logger.debug('Logging download error: %s', url)
				conn = sqlite3.connect(self.DB)
				c = conn.cursor()
				for x in range(0, self.DB_timeout):
					try:
						c.execute("""INSERT OR REPLACE INTO Download_Errors (url, Error) VALUES (?, ?)""", (url, str(error)))
						conn.commit()
					except sqlite3.OperationalError as e:
						if "locked" in str(e):
							sleep(1)
						else:
							self.logger.error(str(e))
							conn.close()
							raise
					else:
						break
				conn.close()
		self.logger.info('Finished downloading files')

	@timeout(10, os.strerror(errno.ETIMEDOUT))
	def downloadFile(self, url):
		data = urlopen(url)
		write = data.read()
		if 'application' in data.info().getheader('Content-Type'):
			folder = self.App_dir
		else:
			folder = self.Misc_dir

		self.logger.debug('Saving %s to %s', url, folder)
		with open(folder + b64encode(url), 'wb') as f:
			f.write(write)

		conn = sqlite3.connect(self.DB)
		c = conn.cursor()
		for x in range(0, self.DB_timeout):
			try:
				c.execute("""INSERT OR REPLACE INTO Used_URLs(url) VALUES (?)""", (url,))
				conn.commit()
			except sqlite3.OperationalError as e:
				if "locked" in str(e):
					sleep(1)
				else:
					self.logger.error(str(e))
					conn.close()
					raise
			else:
				break
		conn.close()
