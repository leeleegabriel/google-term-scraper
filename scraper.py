#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import urllib2	
import argparse
import errno
from itertools import combinations
from itertools import imap
from subprocess import call
from time import sleep
from tqdm import tqdm
from base64 import b64encode

import lib.Filter as Sorter
import lib.FileIO as FileIO
from lib.timeout import timeout

Config_file = './config/config.txt'

def main():
	if Search:
		tqdm.write('Loading Words from %s' % Word_file)

		Primary_words, Secondary_words = getWords()

		tqdm.write('\t%s Primary Words, %s Secondary words' % (len(Primary_words), len(Secondary_words)))
		tqdm.write('Loading Filetypes from %s' % Filetypes_file)

		FileTypes = FileIO.readFile(Filetypes_file)
		tqdm.write('\tLooking for: %s' %  (" ".join(str(x) for x in FileTypes)))

		BaseQuery = str(" ".join(str(x) for x in Primary_words))			
		Queries = filterQueries(getQueries(BaseQuery, Secondary_words), FileIO.readFile(Query_Blacklist_file))
		Websites = getWebsites(Queries, FileTypes)
	elif(Download):
		Websites = FileIO.readFile(URL_file)
	if Download:
		run = True
		while run:
			Downloads = filterQueries(Websites, FileIO.readFile(URL_blacklist_file))
			tqdm.write('Attempting to Download Files from %s URLs' % len(Downloads))
			getDownloads(Downloads)
			newWebsites = set(FileIO.readFile(URL_file))
			if set(Websites) == set(newWebsites):
				run = False
			else:
				Websites = newWebsites
	if Filter:
		Sorter.start(os.path.abspath('.'), Config_file)
	tqdm.write('\n Finished..')

def getWords(): 
	Primary_words = []
	Secondary_words = []
	File_types = []
	with open(Word_file) as f:
		lines = f.readlines()
		lines = [x.strip() for x in lines]
		for line in lines:
			if '*' in line:
				Primary_words.append(line.replace('*', ''))
			else:
				Secondary_words.append(line)
	return Primary_words, Secondary_words

def getQueries(base_query, secondary_words): 
	queries = []
	tqdm.write('Generating Queries')
	if len(secondary_words) < Max_Number_of_terms:
		r_count = len(secondary_words)
	else: 
		r_count = Max_Number_of_terms
	if len(secondary_words) < Min_Number_of_terms:
		l_count = 1
	else:
		l_count = Min_Number_of_terms
	for x in tqdm(range(l_count, r_count + 1)):
		queries.extend([base_query + " " + s for s in[" ".join(term) for term in combinations(secondary_words, x)]])
	return queries

def getWebsites(queries, filetypes):
	websites = FileIO.readFile(URL_file)
	tqdm.write('Collecting URLs')
	total_urls = len(queries) * ((len(filetypes) + 1) * Number_of_results)
	with tqdm(total=total_urls, unit='URLs') as pbar:	
		for query in queries:
			search = [] + list(googleSearch(query, 0))
			pbar.update(Number_of_results)
			for file in filetypes:
				search.extend(googleSearch(file + " " +  query, 0))
				pbar.update(Number_of_results)
			search = set(search)
			filterWebsites(search, filetypes)
			FileIO.appendFile(search, URL_file) # this is weird, maybe just append with a array contained in loop
			FileIO.appendLine(query, Query_Blacklist_file)
			websites.extend(search)
	return set(websites)

def googleSearch(query, count):
	top_results = []
	try:
		for url in googlesearch(query, tld="co.in", num=Number_of_results, stop=1, pause=2):
			top_results.append(url)
	except Exception as e:
		sleep(.5)
		if count < 10:
			top_results = googlesearch(query, count + 1)
		else:
			tqdm.write('Error: %s' % e)
			sys.exit(0)
	return top_results

def filterWebsites(urls, filetypes):
	downloads = [url for url in urls if ext in url]
	return	downloads

def getDownloads(downloads):
	tqdm.write('Downloading Files')
	e_count = 0
	for url in tqdm(downloads, unit="Files"):
		if not os.path.exists(App_dir + '/' + b64encode(url)) and not os.path.exists(Misc_dir + '/' + b64encode(url)):
			try:
				getDownload(url)
			except Exception as e:
				FileIO.appendLine(url + " : " + str(e), Errors_file)
				e_count += 1
	tqdm.write('\tFailed Downloading From %s URLs' % e_count)

@timeout(10, os.strerror(errno.ETIMEDOUT))
def getDownload(url):
	data = urllib2.urlopen(url)
	write = data.read()
	if 'application' in data.info().getheader('Content-Type'):
		folder = App_dir + '/'
	else:
		folder = Misc_dir + '/'
	with open(folder + b64encode(url), 'wb') as f:
		f.write(write)
	FileIO.appendLine(url, URL_blacklist_file)		

def filterQueries(queries, blacklist):
	tqdm.write('Filtering using Blacklist')
	return [x for x in tqdm(queries) if x not in blacklist]

if __name__ == '__main__':
	if not os.geteuid() == 0:
		tqdm.write('\nscript must be run as root!\n')
		sys.exit(1)
	
	try:
		from googlesearch import search as googlesearch
	except ImportError:
		tqdm.write('\nError importing google\n')
		sys.exit(1)

	import configparser
	config = configparser.ConfigParser()
	config.read(Config_file)
	DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')
	App_dir = DBase_dir + '/unfiltered/app'
	Misc_dir = DBase_dir + '/unfiltered/misc'
	CDownloads_dir = CBase_dir + '/download'
	CSearch_dir = CBase_dir + '/search'
	CBlacklists_dir = CBase_dir + '/blacklists'
	dirs = [DBase_dir, CBase_dir, App_dir, Misc_dir, CDownloads_dir, CSearch_dir, CBlacklists_dir]

	Errors_file = CDownloads_dir + '/errors.txt'
	URL_file = CDownloads_dir+ '/URL.txt'
	Word_file = CSearch_dir + '/words.txt'
	Filetypes_file = CSearch_dir + '/filetypes.txt'
	Query_Blacklist_file = CBlacklists_dir + '/Query_blacklist.txt'
	URL_blacklist_file = CBlacklists_dir + '/URL_blacklist.txt'

	parser = argparse.ArgumentParser(description='google-term-scraper', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-S', '--search_only', default=False, dest='search_only', action='store_true', help='only search and collect urls, no downloading of file')
	parser.add_argument('-D', '--download_only', default=False, dest='download_only', action='store_true', help='only download from saved url list, no searching')
	parser.add_argument('-F', '--filter_only', default=False, dest='filter_only', action='store_true', help='only download from saved url list, no searching')
	parser.add_argument('-R', '--results', default=10, help='number of top results collected in google search')
	parser.add_argument('-Ma', '--max_terms', default=10, help='max number of secondary search terms per google search')
	parser.add_argument('-Mi', '--min_terms', default=2, help='min number of secondary search terms per google search')
	
	args = parser.parse_args()

	if((args.download_only and args.search_only and args.filter_only) or (args.download_only and args.search_only) or (args.download_only and args.filter_only) or (args.search_only and args.filter_only)):
		tqdm.write('Invalid Flags')
		sys.exit(1)

	Download, Search, Filter = [True, True, True]
	if(args.download_only):
		Search, Filter = [False, False]
	elif(args.search_only):
		Download, Filter = [False, False]
	elif(args.filter_only):
		Download, Search = [False, False]
	Number_of_results = int(args.results)
	Min_Number_of_terms = int(args.min_terms)
	Max_Number_of_terms = int(args.max_terms)

	[FileIO.makeFolder(directory) for directory in dirs]
	main()