#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import argparse
import sqlite3
import time
from tqdm import tqdm
from time import sleep

import lib.Helper as Helper
import lib.Scraper as Scraper
import lib.Downloader as Downloader
import lib.Filterer as Filterer
import lib.ProxyServer as Proxy

version = 'v0.1.1'
Config_file = './config/config.txt'
DB_file= './config/ScrapeDB.db'

def main():
	tqdm.write('Starting GTS %s at %s' % (version, time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime())))
	if Scrape:
		try:
			Proxy.start(Proxy_IP, Proxy_Port)
			config = {'Abspath': os.path.abspath('.'), 'Config_file': Config_file, 'DB_file': DB_file, 'Words': Words_File, 'Max': Max_Number_of_terms, 'Min': Min_Number_of_terms, 'Results': Number_of_results}
			Scraper.start(config)
		except KeyboardInterrupt:
			pass

	if Download:
		try:
			while True:
				Downloader.start(os.path.abspath('.'), Config_file, DB_file, Filter_errors)
				sleep(60)
		except KeyboardInterrupt:
			pass
	if Filter:
		try:
			while True:		
				Filterer.start(os.path.abspath('.'), Config_file)
				sleep(300)
		except KeyboardInterrupt:
			pass

def SetupDB():
	conn = sqlite3.connect(DB_file)
	c = conn.cursor()
	c.execute("""create table if not exists Queries (query text PRIMARY KEY)""")
	c.execute("""create table if not exists Used_Queries (query text PRIMARY KEY)""")
	c.execute("""create table if not exists Used_URLs (url text PRIMARY KEY)""")
	c.execute("""create table if not exists Download_Errors(url text PRIMARY KEY, Error text)""")
	c.execute("""create table if not exists URLs (url text)""")
	conn.commit()
	conn.close()

if __name__ == '__main__':
	if not os.geteuid() == 0:
		tqdm.write('\nscript must be run as root!\n')
		sys.exit(1)
	
	try:
		from googlesearch import search as googlesearch
	except ImportError:
		tqdm.write('\nError importing google\n')
		sys.exit(1)

	try:
		import textract
	except ImportError:
		tqdm.write('\nError importing textract\n')
		sys.exit(1)

	try:
		import tika 
	except ImportError:
		tqdm.write('\nError importing tika\n')
		sys.exit(1)

	import configparser
	config = configparser.ConfigParser()
	config.read(Config_file)

	DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')
	
	App_dir = DBase_dir + '/unfiltered/app'
	Misc_dir = DBase_dir + '/unfiltered/misc'
	Hit_dir = DBase_dir + '/filtered/hit'
	Miss_dir = DBase_dir + '/filtered/miss'
	Error_dir = DBase_dir + '/filtered/error'
	CSearch_dir = CBase_dir + '/search'

	dirs = [DBase_dir, CBase_dir, App_dir, Misc_dir, Hit_dir, Miss_dir, Error_dir, CSearch_dir,]
	[Helper.makeFolder(directory) for directory in dirs]

	Proxy_IP = config.get('Proxy_Handler', 'IP').replace('\'', '')
	Proxy_Port = int(config.get('Proxy_Handler', 'Port'))

	SetupDB()

	parser = argparse.ArgumentParser(description='google-term-scraper', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-s', '--scrape', default=False, dest='scrape', action='store_true', help='search and collect urls, no downloading of file')
	parser.add_argument('-d', '--download', default=False, dest='download', action='store_true', help='download from saved url list, no searching')
	parser.add_argument('-f', '--filter', default=False, dest='filter', action='store_true', help='download from saved url list, no searching')
	parser.add_argument('-r', '--results', default=10, help='number of top results collected in google search')
	parser.add_argument('-e', '--filter_errors', default=False, action='store_true', help='filter URLs with errors')
	parser.add_argument('-Ma', '--max_terms', default=10, help='max number of secondary search terms per google search')
	parser.add_argument('-Mi', '--min_terms', default=3, help='min number of secondary search terms per google search')
	parser.add_argument('-w', '--word_file', default='words.txt', help='word list name in config/search/ for generating queries')

	args = parser.parse_args()

	Download, Scrape, Filter = args.download, args.scrape, args.filter
	Number_of_results, Min_Number_of_terms, Max_Number_of_terms = int(args.results), int(args.min_terms), int(args.max_terms)
	Filter_errors = args.filter_errors
	Words_File = args.word_file
	if not Scrape and not Download and not Filter:
		Download, Scrape, Filter = True, True, True

	main()
	tqdm.write('\nFinished..')	