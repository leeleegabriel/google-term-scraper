#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import os
import sqlite3
import urllib.request as request
# import html5lib
import random
import logging
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from googlesearch import search
from itertools import combinations
from time import sleep
# from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus

import lib.Helper as Helper
import lib.ProxyServer as Proxy

Proxy_count = 25
DB_timeout = 600


def start(config, log, handler):
	os.chdir(config['Abspath'])

	global DB, Number_of_Results, logger

	handler.setFormatter(logging.Formatter('[Scrape] %(asctime)s : %(message)s '))
	logger = log

	DB = config['DB_file']
	Max_number_of_Terms = config['Max']
	Min_Number_of_Terms = config['Min']
	Number_of_Results = config['Results']

	Filetypes_file = config['Filetypes']
	Word_file = config['Words']

	Primary_words, Secondary_words = getWords(Word_file)
	logger.info('Loaded Words from %s' % Word_file)
	logger.info('\t%s Primary Words, %s Secondary words' % (len(Primary_words), len(Secondary_words)))

	FileTypes = Helper.readFile(Filetypes_file)
	logger.info('Loaded Filetypes from %s' % Filetypes_file)
	logger.info('\tLooking for: %s' % (" ".join(str(x) for x in FileTypes)))

	BaseQuery = str(" ".join(str(x) for x in Primary_words))
	Queries = filterQueries(generateQueries(BaseQuery, Secondary_words, Max_number_of_Terms, Min_Number_of_Terms))

	Scrape(Queries, FileTypes)


def getWords(Word_file):
	Primary_words = []
	Secondary_words = []
	with open(Word_file) as f:
		lines = f.readlines()
		lines = [x.strip() for x in lines]
		for line in lines:
			if '*' in line:
				Primary_words.append(line.replace('*', ''))
			else:
				Secondary_words.append(line)
	return Primary_words, Secondary_words


def generateQueries(base_query, secondary_words, Max, Min):
	queries = []
	logger.info('Generating Queries')
	if len(secondary_words) < Max:
		r_count = len(secondary_words)
	else: 
		r_count = Max
	if len(secondary_words) < Min:
		l_count = 1
	else:
		l_count = Min

	for x in range(l_count, r_count + 1):
		queries.extend(["intext:" + base_query + " " + s for s in[" ".join(term) for term in combinations(secondary_words, x)]])

	return queries


def filterQueries(queries):
	logger.info('Inserting Queries into DB')
	filtered_queries = []
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	for x in range(0, DB_timeout):
		try:
			c.execute("""create table Queries (query text PRIMARY KEY)""")
			stmt = """INSERT INTO %s (%s) VALUES (?)""" % ('Queries', 'query')
			[c.execute(stmt, (row,)) for row in queries]
			stmt = """SELECT query FROM Queries WHERE query NOT IN (SELECT query FROM Used_Queries)"""
			conn.row_factory = lambda cursor, row: row[0]
			filtered_queries = c.execute(stmt).fetchall()
			break
		except sqlite3.OperationalError as e:
			if "locked" in str(e):
				sleep(1)
			else:
				logger.error(str(e))
				raise
		else:
			break
	conn.close()
	return filtered_queries


def Scrape(queries, filetypes):
	# total_urls = len(queries) * ((len(filetypes) + 1) * Number_of_Results)
	i = 0

	logger.info('Collecting URLs')
	if queries:
		for query in queries:
			# if i % 10 == 0 and i != 0:
			# 	Proxies = Proxy.getProxies(Proxy_count)
			urls = [] + list(googleSearch(query))
			[urls.append(googleSearch('filtetype:' + file + ' ' + query)) for file in filetypes]
			if urls:
				insertURL(urls)
				insertQuery(query)
			else:
				logger.debug('Found no urls with %s', query)
			# insertQuery(query)
			i += 1
		logger.info('Finished searching for urls')
	else:
		logger.info('No new queries found')


def insertURL(urls):
	conn = sqlite3.connect(DB)
	c = conn.cursor()

	stmt = """INSERT OR IGNORE INTO %s (%s) VALUES (?)""" % ('URLs', 'url')
	for x in range(0, DB_timeout):
		try:
			[c.execute(stmt, (row,)) for row in urls]
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


def insertQuery(query):	
	conn = sqlite3.connect(DB)
	c = conn.cursor()

	stmt = """INSERT OR IGNORE INTO %s (%s) VALUES (?)""" % ('Used_Queries', 'query')
	for x in range(0, DB_timeout):
		try:
			c.execute(stmt, (query,))
			conn.commit()
		except sqlite3.OperationalError as e:
			if "locked" in str(e):
				sleep(1)
			else:
				logger.error(str(message))
				raise
		else:
			break
	conn.close()


def googleSearch(query):
	url = 'https://www.google.com/search?' + urlencode({'q': query, 'num': Number_of_Results}, quote_via=quote_plus)
	req = request.Request(url, headers={'User-Agent': getRandomHeader()})
	proxies = Proxy.getProxies(Proxy_count)
	for i in range(0, Proxy_count):
		try:
			req.set_proxy(random.choice(proxies), 'http')
			response = urlopen(req)
			soup = BeautifulSoup(response.read(), "html5lib")
			links = soup.findAll("a")
			url_list = []
			for link in links:
				link_href = link.get('href')
				if "url?q=" in link_href and not "webcache" in link_href:
				    url_list.append(link.get('href').split("?q=")[1].split("&sa=U")[0])
			return url_list
		except HTTPError as e:
			logger.debug(str(e))
		except URLError as e:
			logger.debug(str(e))
		except Exception as e:
			logger.error(str(e))
			raise
	raise Helper.ProxyError('Failed Scraping attempts')


def getRandomHeader():
	user_agent_list = [
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
		'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
		'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
		'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
		'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
		'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
		'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
		'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
		'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
		'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
		'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
		'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
		'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
		'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
		'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
		'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
		'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
		'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
		'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
		'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)', 
		'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
	]
	return random.choice(user_agent_list)
