#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import os
import sqlite3
# import html5lib
import random
import logging
import urllib.request as request
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlencode, quote_plus
from itertools import combinations
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

import lib.Helper as Helper


os.chdir('../')


class Scraper():
	def __init__(self, logger, DB, ChromeDriver_file, Max_number_of_Terms, Min_Number_of_Terms, Number_of_Results, Filetypes_file, Word_file):
		self.logger = logger
		self.DB = DB
		self.ChromeDriver_file = ChromeDriver_file
		self.Max_number_of_Terms = Max_number_of_Terms
		self.Min_Number_of_Terms = Max_number_of_Terms
		self.Number_of_Results = Number_of_Results
		self.Filetypes_file = Filetypes_file
		self.Word_file = Word_file
		self.Proxy_count = 25
		self.DB_timeout = 600
		self.Browser_delay = 0.5

	def start(self):
		Primary_words, Secondary_words = self.getWords(self.Word_file)
		self.logger.info('Loaded Words from %s' % self.Word_file)
		self.logger.info('\t%s Primary Words, %s Secondary words' % (len(Primary_words), len(Secondary_words)))
		FileTypes = Helper.readFile(self.Filetypes_file)
		self.logger.info('Loaded Filetypes from %s' % self.Filetypes_file)
		self.logger.info('\tLooking for: %s' % (" ".join(str(x) for x in FileTypes)))
		BaseQuery = str(" ".join(str(x) for x in Primary_words))
		Queries = self.filterQueries(self.generateQueries(BaseQuery, Secondary_words))
		self.Scrape(Queries, FileTypes)

	def getWords(self):
		Primary_words = []
		Secondary_words = []
		with open(self.Word_file) as f:
			lines = f.readlines()
			lines = [x.strip() for x in lines]
			for line in lines:
				if '*' in line:
					Primary_words.append(line.replace('*', ''))
				else:
					Secondary_words.append(line)
		return Primary_words, Secondary_words

	def generateQueries(self, base_query, secondary_words):
		queries = []
		if len(secondary_words) < self.Max_number_of_Terms:
			r_count = len(secondary_words)
		else:
			r_count = self.Max_number_of_Terms
		if len(secondary_words) < self.Min_Number_of_Terms:
			l_count = 1
		else:
			l_count = self.Min_Number_of_Terms
		self.logger.info('Generating Queries')
		for x in range(l_count, r_count + 1):
			queries.extend(["intext:" + base_query + " " + s for s in[" ".join(term) for term in combinations(secondary_words, x)]])
		return queries

	def filterQueries(self, queries):
		filtered_queries = []
		conn = sqlite3.connect(self.DB)
		c = conn.cursor()
		self.logger.info('Inserting Queries into DB')
		for x in range(0, self.DB_timeout):
			try:
				c.execute("""create table Queries (query text PRIMARY KEY)""")
				c.executemany("""INSERT INTO Queries (query) VALUES (?)""", queries)
				conn.row_factory = lambda cursor, row: row[0]
				filtered_queries = c.execute("""SELECT query FROM Queries WHERE query NOT IN (SELECT query FROM Used_Queries)""").fetchall()
				break
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
		return filtered_queries

	def Scrape(self, queries, filetypes):
		self.logger.info('Collecting URLs')
		if queries:
			chrome_options = Options()
			chrome_options.add_argument('--headless')
			chrome_options.add_argument('--window-size=1920x1080')
			driver = webdriver.Chrome(executable_path=os.path.absolute(self.ChromeDriver_file), chrome_options=chrome_options)
			driver.implicitly_wait(30)
			for query in queries:
				urls = [] + list(self.googleSearch(driver, query))
				[urls.append(self.googleSearch(driver,'filtetype:' + f + ' ' + query)) for f in filetypes]
				if urls:
					self.insertURLs(urls)
					self.insertUsedQuery(query)
				else:
					self.logger.debug('Found no urls with %s', query)
			driver.close()
			self.logger.info('Finished searching for urls')
		else:
			self.logger.info('No new queries found')

	def googleSearch(self, driver, query):
		url = 'https://www.google.com/search?' + urlencode({'q': query, 'num': self.Number_of_Results}, quote_via=quote_plus)
		driver.get(url)
		soup = BeautifulSoup(driver.page_source, "html5lib")
		links = soup.findAll("a")
		url_list = []
		for link in links:
			link_href = link.get('href')
			if "url?q=" in link_href and not "webcache" in link_href:
				url_list.append(link.get('href').split("?q=")[1].split("&sa=U")[0])
		sleep(self.Browser_delay)
		return url_list

	def insertURLs(self, queries):
		conn = sqlite3.connect(self.DB)
		c = conn.cursor()
		for x in range(0, self.DB_timeout):
			try:
				c.executemany("""INSERT OR IGNORE INTO URLs (url) VALUES (?)""", queries)
				conn.commit()
			except sqlite3.OperationalError as e:
				if "locked" in str(e):
					sleep(1)
				else:
					self.logger.error(str(e.message))
					conn.close()
					raise
			else:
				break
		conn.close()

	def insertUsedQuery(self, query):
		conn = sqlite3.connect(self.DB)
		c = conn.cursor()
		for x in range(0, self.DB_timeout):
			try:
				c.execute("""INSERT OR IGNORE INTO Used_Queries (query) VALUES (?)""", query)
				conn.commit()
			except sqlite3.OperationalError as e:
				if "locked" in str(e):
					sleep(1)
				else:
					self.logger.error(str(e.message))
					conn.close()
					raise
			else:
				break
		conn.close()
