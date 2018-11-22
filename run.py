#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import argparse
import sqlite3
import time
import logging
import configparser
from time import sleep

import lib.Helper as Helper
from lib.Scraper import Scraper
from lib.Downloader import Downloader
from lib.Filterer import Filterer

version = 'v0.3.5'
Config_file = 'config.txt'

logger = logging.getLogger()
handler = logging.StreamHandler()
# loggin.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(logging.Formatter('%(asctime)s : %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

DB_timeout = 60
Download_timeout = 60
Filter_timeout = 600


# Maybe make directories static/generated from CBase_dir/DBase_dir

def main():
	logger.info('Starting GTS %s at %s' % (version, time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.localtime())))
	Sample_dir, Unfiltered_dir, App_dir, Misc_dir, Hit_dir, Miss_dir, Error_dir, CSearch_dir, DB_file, Words_file, Filetypes_file, ChromeDriver_file = setupDirs()
	Scrape, Download, Filter, Filter_errors, Number_of_results, Min_Number_of_terms, Max_Number_of_terms, Words_file = getArgs(Words_file)
	setupDB(DB_file)

	if Scrape:
		scraper = Scraper(logger, DB_file, ChromeDriver_file, Max_Number_of_terms, Min_Number_of_terms, Number_of_results, Filetypes_file, Words_file)
		try:
			scraper.start()
		except KeyboardInterrupt:
			logger.debug('Detected KeyboardInterrupt')

	if Download:
		downloader =Downloader(logger, DB_file, Filter_errors, App_dir, Misc_dir)
		try:
			while True:
				downloader.start()
				logger.info(' Sleeping %.2fm' % (Download_timeout / 60.0))
				sleep(Download_timeout)
		except KeyboardInterrupt:
			logger.debug('Detected KeyboardInterrupt')

	if Filter:
		filterer = Filterer(logger, Sample_dir, Hit_dir, Miss_dir, Error_dir, Unfiltered_dir, Words_file)
		try:
			while True:
				filterer.start()
				logger.info(' Sleeping %.2fm' % (Filter_timeout / 60.0))
				sleep(Filter_timeout)
		except KeyboardInterrupt:
			logger.debug('Detected KeyboardInterrupt')


def setupDirs():
	print(Config_file)
	config = configparser.ConfigParser()
	config.read(Config_file)
	print(config.sections())

	DBase_dir = config.get('Dirs', 'Download_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')

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

	DB_file = CBase_dir + config.get('Files', 'DB').replace('\'', '')
	Words_file = CBase_dir + config.get('Files', 'Word_list').replace('\'', '')
	Filetypes_file = CSearch_dir + 'filetypes.txt'
	ChromeDriver_file = CBase_dir + config.get('Files', 'ChromeDriver').replace('\'', '')

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
	parser.add_argument('-r', '--results', default=10, help='number of top results collected in google search')
	parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Gives Verbose/Debug info in cmd')
	parser.add_argument('-Ma', '--max_terms', default=10, help='max number of secondary search terms per google search')
	parser.add_argument('-Mi', '--min_terms', default=3, help='min number of secondary search terms per google search')
	parser.add_argument('-w', '--word_file', default=Words_file, help='word list name in config/search/ for generating queries')

	args = parser.parse_args()

	Scrape = args.scrape
	Download = args.download
	Filter = args.filter
	Filter_errors = args.filter_errors

	Number_of_results = int(args.results)
	Min_Number_of_terms = int(args.min_terms)
	Max_Number_of_terms = int(args.max_terms)

	Words_File = args.word_file

	# if Filter_errors:
	# 	Download = True
	if not Scrape and not Download and not Filter:
		Download, Scrape, Filter = True, True, True

	if Min_Number_of_terms > Max_Number_of_terms:
		logger.info('Error: Max < Min, setting Max terms to 10 and min terms to 3')
		Max_Number_of_terms = 10
		Min_Number_of_terms = 3

	if args.verbose:
		logger.setLevel(logging.DEBUG)

	return Scrape, Download, Filter, Filter_errors, Number_of_results, Min_Number_of_terms, Max_Number_of_terms, Words_file


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
	#nltk.download()
	main()
	logger.write('\nFinished..')
