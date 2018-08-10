#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import sqlite3
import urllib.request as request
import html5lib
import random
from googlesearch import search
from itertools import combinations
from time import sleep
from tqdm import tqdm 
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus

import lib.Helper as Helper
import lib.ProxyServer as Proxy

def start(config):
	os.chdir(config['abspath'])
	
	global Number_of_Results

	DB = config['DB']
	Max_number_of_Terms = config['Max']
	Min_Number_of_Terms = config['Min']
	Number_of_Results = config['Results']

	# this whole importing the config thing is garbage wtf am i doing
	# TODO: More elegant solution
	import configparser
	cparser = configparser.ConfigParser()
	cparserg.read(config['Config_file'])

	CBase_dir = cparser.get('Dirs', 'Config_dir').replace('\'', '')

	Filetypes_file = CBase_dir + '/search/filetypes.txt'
	Word_file = CBase_dir + '/search' + config['Words']

	Primary_words, Secondary_words = getWords(Word_file)
	tqdm.write(' Loaded Words from %s' % Word_file)
	tqdm.write('\t%s Primary Words, %s Secondary words' % (len(Primary_words), len(Secondary_words)))
	
	Filetypes_file = CBase_dir + '/search/filetypes.txt'
	FileTypes = Helper.readFile(Filetypes_file)
	tqdm.write(' Loaded Filetypes from %s' % Filetypes_file)
	tqdm.write('\tLooking for: %s' %  (" ".join(str(x) for x in FileTypes)))

	BaseQuery = str(" ".join(str(x) for x in Primary_words))			
	Queries = getQueries(DB, BaseQuery, Secondary_words, Max_number_of_Terms, Min_Number_of_Terms)

	Scrape(DB, Queries, FileTypes)

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

def getQueries(DB, base_query, secondary_words, Max, Min): 
	queries = []
	tqdm.write(' Generating Queries')
	if len(secondary_words) < Max_number_of_Terms:
		r_count = len(secondary_words)
	else: 
		r_count = Max_number_of_Terms
	if len(secondary_words) < Min_Number_of_Terms:
		l_count = 1
	else:
		l_count = Min_Number_of_Terms
	
	for x in tqdm(range(l_count, r_count + 1)):
		queries.extend(["intext:" + base_query + " " + s for s in[" ".join(term) for term in combinations(secondary_words, x)]])
	
	conn = sqlite3.connect(DB)
	c = conn.cursor()

	tqdm.write(' Inserting Queries into DB')
	stmt = """INSERT OR IGNORE INTO %s (%s) VALUES (?)""" % ('Queries', 'query')
	[c.execute(stmt,  (row,)) for row in queries]
	conn.commit()

	tqdm.write(' Filtering Queries')
	conn.row_factory = lambda cursor, row: row[0]
	c = conn.cursor()
	filtered_queries = c.execute("""SELECT query FROM Queries WHERE query NOT IN (SELECT query FROM Used_Queries)""").fetchall()
	conn.close()

	return filtered_queries

def Scrape(DB, queries, filetypes):
	tqdm.write(' Collecting URLs')
	Proxies = Proxy.getProxies(25)
	total_urls = len(queries) * ((len(filetypes) + 1) * Number_of_Results)
	with tqdm(total=total_urls, unit='URLs') as pbar:	
		for query in queries:
			e_count = 0
			urls = []
			result = list(googleSearch(Proxies, query))
			if search[0] not 'error':
				urls = urls + result
			else:
				e_count += 1
			pbar.update(Number_of_Results)
			for file in filetypes:
				result = googleSearch(Proxies, 'filtetype:' + file + ' ' +  query)
				pbar.update(Number_of_Results)
				if search[0] not 'error':
					urls = urls + result
				else:
					e_count += 1

			conn = sqlite3.connect(DB)
			c = conn.cursor()

			if urls:
				stmt = """INSERT OR IGNORE INTO %s (%s) VALUES (?)""" % ('URLs', 'url')
				[c.execute(stmt,  (row,)) for row in search]
				conn.commit()

			if e_count == 0:
				stmt = """INSERT OR IGNORE INTO %s (%s) VALUES (?)""" % ('Used_Queries', 'query')
				c.execute(stmt,  (query,))
				conn.commit()

			conn.close()

def googleSearch(query):
	url = 'https://www.google.com/search?' + urlencode({'q' : query, 'num' : Number_of_results}, quote_via=quote_plus)
	req = request.Request(url, headers={'User-Agent' : getRandomHeader()})
	for i in range(0, 25):
		try:
			req.set_proxy(Proxies[i], 'http')
			response = request.urlopen(req)
			soup = BeautifulSoup(response.read(), "html5lib")
			links = soup.findAll("a")
			url_list = []
			for link in links:
				link_href = link.get('href')
				if "url?q=" in link_href and not "webcache" in link_href:
				    url_list.append(link.get('href').split("?q=")[1].split("&sa=U")[0])
			return url_list
		except urllib.HTTPError as e:
			pass
		except:
			raise
	raise ProxyError('Ran out of Functional Proxies')

#	try:
#		return  getURL(req)
#	except urllib.HTTPError as e:
#		if e.code == 503 or e.code == 404:
#			for i in range(0, 10):
#				try:
#					req.set_proxy(getRandomProxy(), 'http')
#					return getURL(req)
#				except urllib.HTTPError as e:
#					raise
#		raise

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

class ProxyError(Exception):
    def __init__(self, message):
        super().__init__(message)

if __name__== "__main__":
	start(os.path.abspath('..'),'./config/config.txt', './config/ScrapeDB.db')