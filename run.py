#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import argparse
import sqlite3
import tqdm
from time import sleep

import lib.Filter as Sorter
import lib.Downloader as Downloader
import lib.Scraper as Scraper
import lib.Helper as Helper

Config_file = './config/config.txt'
DB_file= './config/ScrapeDB.db'

def main():
	if Scrape:
		Scraper.start(os.path.abspath('.'), Config_file, DB_file, Max_Number_of_terms, Min_Number_of_terms, Number_of_results)

	if Download:
		try:
			while True:
				Downloader.start(os.path.abspath('.'), Config_file, DB_file)
				sleep(60)
		except KeyboardInterrupt:
			tqdm.write('\n Stopping..')

	if Filter:
		try:
			while True:		
				Sorter.start(os.path.abspath('.'), Config_file)
				sleep(300)
		except KeyboardInterrupt:
			tqdm.write('\n Stopping..')	
	tqdm.write('\n Finished..')	

def SetupDB_file():
	conn = sqlite3.connect(DB_file)
	c = conn.cursor()
	c.execute("""create table if not exists Queries (query text PRIMARY KEY)""")
	c.execute("""create table if not exists Used_Queries (query text PRIMARY KEY)""")
	c.execute("""create table if not exists Used_URLs (url text PRIMARY KEY)""")
	c.execute("""create table if not exists Download_Errors(url text PRIMARY KEY, Error text)""")
	c.execute("""create table if not exists URLs (url text)""")
	conn.commit()
	conn.close()

def SetupDirs():
	import configparser
	config = configparser.ConfigParser()
	config.read(Config_file)

	DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')
	
	App_dir = DBase_dir + '/unfiltered/app'
	Misc_dir = DBase_dir + '/unfiltered/misc'
	CSearch_dir = CBase_dir + '/search'
	#TODO: actually mk all the dirs needed
	dirs = [DBase_dir, CBase_dir, App_dir, Misc_dir, CSearch_dir,]
	[Helper.makeFolder(directory) for directory in dirs]

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

	SetupDirs()
	SetupDB_file()

	parser = argparse.ArgumentParser(description='google-term-scraper', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-s', '--scrape', default=False, dest='scrape', action='store_true', help='search and collect urls, no downloading of file')
	parser.add_argument('-d', '--download', default=False, dest='download', action='store_true', help='download from saved url list, no searching')
	parser.add_argument('-f', '--filter', default=False, dest='filter', action='store_true', help='download from saved url list, no searching')
	parser.add_argument('-r', '--results', default=10, help='number of top results collected in google search')
	parser.add_argument('-Ma', '--max_terms', default=10, help='max number of secondary search terms per google search')
	parser.add_argument('-Mi', '--min_terms', default=3, help='min number of secondary search terms per google search')
	
	args = parser.parse_args()

	Download, Scrape, Filter = args.download, args.scrape, args.filter
	Number_of_results, Min_Number_of_terms, Max_Number_of_terms = int(args.results), int(args.min_terms), int(args.max_terms)
	if not Scrape and not Download and not Filter:
		Download, Scrape, Filter = True, True, True

	main()