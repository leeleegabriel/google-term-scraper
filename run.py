#!/usr/bin/python3
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import argparse
import sqlite3
import time
import logging
import configparser
import asyncio
import datetime
from time import sleep

import lib.Helper as Helper
from lib.Scraper import Scraper
from lib.Downloader import Downloader
from lib.Filterer import Filterer

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s - %(threadName)-11s -  %(levelname)s - %(message)s')


fh1 = logging.FileHandler('./data/logs/%s.data_debug.log' % (datetime.datetime.now().strftime('%Y-%m-%d')))
fh1.setLevel(logging.DEBUG)
fh1.setFormatter(fmt)
logger.addHandler(fh1)


fh2 = logging.FileHandler('./data/logs/data.log')
fh2.setLevel(logging.INFO)
fh2.setFormatter(fmt)
logger.addHandler(fh2)


DB_timeout = 60
Download_timeout = 60
Filter_timeout = 600
Number_of_results = 100
Min_Number_of_terms = 10
Max_Number_of_terms = 10
version = 'v0.3.5'
Download_dir = './downloads/'
Config_dir = './config/'
DB = 'ScrapeDB.db'
Word_list = 'words.txt'
Filetypes = 'filetypes.txt'
ChromeDriver = 'chromedriver'


def main():
	logger.info('Starting GTS %s at %s' % (version, time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime())))
	Sample_dir, Unfiltered_dir, App_dir, Misc_dir, Hit_dir, Miss_dir, Error_dir, CSearch_dir, DB_file, Words_file, Filetypes_file, ChromeDriver_file = setupDirs()
	Scrape, Download, Filter, Filter_errors, Words_file = getArgs(Words_file)
	setupDB(DB_file)

	loop = asyncio.get_event_loop()

	if Scrape:
		scraper = Scraper(logger, DB_file, ChromeDriver_file, Max_Number_of_terms, Min_Number_of_terms, Number_of_results, Filetypes_file, Words_file)
		future_S = loop.run_in_executor(None, scraper.run, loop)

	if Download:
		downloader =Downloader(logger, DB_file, Filter_errors, App_dir, Misc_dir)
		future_d = loop.run_in_executor(None, downloader.run, loop)

	if Filter:
		filterer = Filterer(logger, Sample_dir, Hit_dir, Miss_dir, Error_dir, Unfiltered_dir, Words_file)
		future_f = loop.run_in_executor(None, filterer.run, loop)

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		if Scrape:
			scraper.running = False
		if Dowload:
			downloader.running = False
		if Filter:
			filterer.running = False
	while not scraper.fin and not downloader.fin and filterer.fin:
		pass
	loop.close()
	logger.info('Fin.')	

def setupDirs():
	DBase_dir = Download_dir
	CBase_dir = Config_dir

	Sample_dir = DBase_dir + 'samples/'
	Unfiltered_dir = DBase_dir + '/Unfiltered_dir/'
	App_dir = DBase_dir + 'unfiltered/app/'
	Misc_dir = DBase_dir + 'unfiltered/misc/'
	Hit_dir = DBase_dir + 'filtered/hit/'
	Miss_dir = DBase_dir + 'filtered/miss/'
	Error_dir = DBase_dir + 'filtered/error/'
	CSearch_dir = CBase_dir + 'search/'

	dirs = [DBase_dir, CBase_dir, Sample_dir, Unfiltered_dir, App_dir, Misc_dir, Hit_dir, Miss_dir, Error_dir, CSearch_dir]
	for dire in dirs:
		Helper.makeFolder(dire)

	DB_file = CBase_dir + DB
	Words_file = CBase_dir + Word_list
	Filetypes_file = CSearch_dir + Filetypes
	ChromeDriver_file = CBase_dir + ChromeDriver

	files = [Words_file, Filetypes_file, ChromeDriver_file]
	missing_files = [f for f in files if not Helper.checkFile(f)]
	if missing_files:
		logger.error('missing files: %s' % missing_files)
		sys.exit(0)

	return Sample_dir, Unfiltered_dir, App_dir, Misc_dir, Hit_dir, Miss_dir, Error_dir, CSearch_dir, DB_file, Words_file, Filetypes_file, ChromeDriver_file


def getArgs(Words_file):
	parser = argparse.ArgumentParser(description='google-term-scraper', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-s', '--scrape', default=False, dest='scrape', action='store_true', help='search and collect urls, no downloading of file')
	parser.add_argument('-d', '--download', default=False, dest='download', action='store_true', help='download from saved url list, no searching')
	parser.add_argument('-de', '--filter_errors', default=False, action='store_true', help='Don\'t attempt to download previously attempted URLs with errors')
	parser.add_argument('-f', '--filter', default=False, dest='filter', action='store_true', help='download from saved url list, no searching')
	parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Gives Verbose/Debug info in cmd')
	parser.add_argument('-w', '--word_file', default=Words_file, help='word list name in config/search/ for generating queries')

	args = parser.parse_args()

	Scrape = args.scrape
	Download = args.download
	Filter = args.filter
	Filter_errors = args.filter_errors

	Words_file = args.word_file

	if not Scrape and not Download and not Filter:
		Download, Scrape, Filter = True, True, True
	if args.verbose:
		logger.setLevel(logging.DEBUG)

	return Scrape, Download, Filter, Filter_errors, Words_file


def setupDB(DB_file):
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
		import textract
		import tika
		import nltk
		import sklearn
	except ImportError as e:
		logger.error('\nError importing, %s\n' % e.message)
		sys.exit(1)
	main()
	logger.write('\nFinished..')
