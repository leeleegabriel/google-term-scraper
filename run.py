#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import argparse
import sqlite3
import time
import logging
# from tqdm import tqdm
from time import sleep

import lib.Helper as Helper
import lib.Scraper as Scraper
import lib.Downloader as Downloader
import lib.Filterer as Filterer

version = 'v0.2.0'
Config_file = './config/config.txt'

logger = logging.getLogger()
handler = logging.StreamHandler()
# loggin.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(logging.Formatter('%(message)s '))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def main():
	logger.info('Starting GTS %s at %s' % (version, time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime())))

	if Scrape:
		config = {'Abspath': os.path.abspath('.'), 'DB_file': DB_file, 'Words': Words_File,
			 'Filetypes': CSearch_dir + '/filetypes.txt', 'Max': Max_Number_of_terms, 'Min': Min_Number_of_terms,
			 'Results': Number_of_results}
		try:
			Scraper.start(config, logger, handler)
		except KeyboardInterrupt:
			logger.debug('Detected KeyboardInterrupt')

	if Download:
		try:
			config = {'Abspath': os.path.abspath('.'), 'DB_file': DB_file, 'Filter_errors': Filter_errors,
			 'App_dir': App_dir, 'Misc_dir': Misc_dir}
			while True:
				Downloader.start(config, logger, handler)
				logger.info(' Sleeping %.2fm' % (Download_timeout / 60.0))
				sleep(Download_timeout)
		except KeyboardInterrupt:
			logger.debug('Detected KeyboardInterrupt')
	if Filter:
		try:
			config = {'Abspath': os.path.abspath('.'), 'DB_file': DB_file, 'Hit_dir': Hit_dir,
			 'Miss_dir': Miss_dir, 'Error_dir': Error_dir, 'App_dir': App_dir, 'Words': Words_File}
			while True:	
				Filterer.start(config, logger, handler)
				logger.info(' Sleeping %.2fm' % (Filter_timeout / 60.0))
				sleep(Filter_timeout)
		except KeyboardInterrupt:
			logger.debug('Detected KeyboardInterrupt')


def SetupDB():
	conn = sqlite3.connect(DB_file)
	c = conn.cursor()
	for x in range(0, DB_timeout):
		try:
			c.execute("""drop table if exists Queries""")
			c.execute("""create table if not exists Used_Queries (query text PRIMARY KEY)""")
			c.execute("""create table if not exists Used_URLs (url text PRIMARY KEY)""")
			c.execute("""create table if not exists Download_Errors(url text PRIMARY KEY, Error text)""")
			c.execute("""create table if not exists URLs (url text)""")
			conn.commit()
		except sqlite3.OperationalError as e:
			logger.info(str(e))
			if "locked" in str(e):
				sleep(1)
			else:
				logger.error(e.message)
				raise
		else:
			break
	conn.close()


if __name__ == '__main__':
	if not os.geteuid() == 0:
		logger.error('\nscript must be run as r00t!\n')
		sys.exit(1)

	try:
		# from googlesearch import search as googlesearch
		import textract
		import tika
	except ImportError as e:
		logger.error('\nError importing, %s\n' % e.message)
		sys.exit(1)

	import configparser
	config = configparser.ConfigParser()
	config.read(Config_file)

	DBase_dir = config.get('Dirs', 'Download_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')

	App_dir = DBase_dir + '/unfiltered/app'
	Misc_dir = DBase_dir + '/unfiltered/misc'
	Hit_dir = DBase_dir + '/filtered/hit'
	Miss_dir = DBase_dir + '/filtered/miss'
	Error_dir = DBase_dir + '/filtered/error'
	CSearch_dir = CBase_dir + '/search'

	dirs = [DBase_dir, CBase_dir, App_dir, Misc_dir, Hit_dir, Miss_dir, Error_dir, CSearch_dir]
	[Helper.makeFolder(dir) for dir in dirs]

	DB_file = CBase_dir + '/' + config.get('Files', 'DB').replace('\'', '')
	Word_file = CSearch_dir + '/' + config.get('Files', 'Word_list').replace('\'', '')

	DB_timeout = int(config.get('Timeouts', 'DB_timeout'))
	Download_timeout = int(config.get('Timeouts', 'Download_timeout'))
	Filter_timeout = int(config.get('Timeouts', 'Filter_timeout'))

	SetupDB()

	parser = argparse.ArgumentParser(description='google-term-scraper', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-s', '--scrape', default=False, dest='scrape', action='store_true', help='search and collect urls, no downloading of file')
	parser.add_argument('-d', '--download', default=False, dest='download', action='store_true', help='download from saved url list, no searching')
	parser.add_argument('-de', '--filter_errors', default=False, action='store_true', help='Don\'t attempt to download previously attempted URLs with errors')
	parser.add_argument('-f', '--filter', default=False, dest='filter', action='store_true', help='download from saved url list, no searching')
	parser.add_argument('-r', '--results', default=10, help='number of top results collected in google search')
	parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Gives Verbose/Debug info in cmd')
	parser.add_argument('-Ma', '--max_terms', default=10, help='max number of secondary search terms per google search')
	parser.add_argument('-Mi', '--min_terms', default=3, help='min number of secondary search terms per google search')
	parser.add_argument('-w', '--word_file', default=Word_file, help='word list name in config/search/ for generating queries')

	args = parser.parse_args()

	Download = args.download
	Scrape = args.scrape
	Filter = args.filter
	Filter_errors = args.filter_errors

	Number_of_results = int(args.results)
	Min_Number_of_terms = int(args.min_terms)
	Max_Number_of_terms = int(args.max_terms)

	Words_File = args.word_file

	if Filter_errors:
		Download = True
	if not Scrape and not Download and not Filter:
		Download, Scrape, Filter = True, True, True
	if Min_Number_of_terms > Max_Number_of_terms:
		logger.info('Error: Max < Min, setting Max terms to 10 and min terms to 3')
		Max_Number_of_terms = 10
		Min_Number_of_terms = 3
	if args.verbose:
		logger.setLevel(logging.DEBUG)

	main()
	logger.write('\nFinished..')
