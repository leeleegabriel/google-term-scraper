#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

Word_file = './config/words.txt'
Filetypes_file = './config/filetypes.txt'
Query_Blacklist_file = './config/Query_blacklist.txt'
URL_blacklist_file = './config/URL_blacklist.txt'
URL_file = './config/url.txt'
Errors_file = './config/errors.txt'
Downloads_folder = './downloads'


def main():
	if search:
		tqdm.write('Loading Words from %s' % Word_file)

		Primary_words, Secondary_words = getWords()

		tqdm.write('\t%s Primary Words, %s Secondary words' % (len(Primary_words), len(Secondary_words)))
		tqdm.write('Loading Filetypes from %s' % Filetypes_file)

		FileTypes = readFile(Filetypes_file)

		tqdm.write('\tLooking for: %s' %  (" ".join(str(x) for x in FileTypes)))

		BaseQuery = str(" ".join(str(x) for x in Primary_words))
		if use_Query_blacklist:
			tqdm.write('Filtering out Queries using Query Blacklist')
			Queries = filterQueries(getQueries(BaseQuery, Secondary_words), readFile(Query_Blacklist_file))
		else:
			Queries = getQueries(BaseQuery, Secondary_words) 
		Websites = set(getWebsites(Queries, FileTypes))
	else:
		Websites = set(readFile(URL_file))

	if download:	
		tqdm.write('test')
		Downloads = sortWebsites(Websites, FileTypes)
		tqdm.write('\t Attempting to Download Files from %s URLs' % len(Downloads))
		getDownloads(Downloads)
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
	websites = []
	tqdm.write('Collecting URLs')
	total_urls = queries * ((len(filetypes) + 1) * Number_of_results)
	with tqdm(total=total_urls)	as pbar:
		for query in tqdm(queries):
			search = []
			search.extend(googleSearch(query))
			pbar.update(Number_of_results)
			if use_filefilter:
				for file in filetypes:
					search.extend(googleSearch(file + " " +  query))
					pbar.update(Number_of_results)
			search = set(search)
			appendFile(search, URL_file) # this is weird, maybe just append with a array contained in loop
			if use_Query_blacklist:
				appendFile(query, Query_Blacklist_file)
			websites.extend(search)
	websites = set(websites)
	writeFile(websites, URL_file)
	return websites

def googleSearch(query):
	top_results = []
	from googlesearch import search # why this fixed an error idk but idgaf
	for url in googlesearch(query, tld="co.in", num=Number_of_results, stop=1, pause=2):
		top_results.append(url)
	return top_results

def sortWebsites(urls, filetypes):
	downloads = []
	screens = []
	for url in urls:
		if any(ext in url for ext in filetypes):
			downloads.append(url)
	return downloads

def getDownloads(downloads):
	tqdm.write('Filtering out URLs using URL Blacklist')
	downloads = filterQueries(downloads, readFile(URL_blacklist_file))
	for url in tqdm(downloads):
		file_name = base64.base64encode(url)
		file = Downloads_folder + file_name
		if not os.path.exists(file):
			try:
				data = urllib2.urlopen(url)
				write = data.read()
				with open(file, 'wb') as f:
					f.write(write)
			except Exception as e:
				appendFile(url, Errors_file)
	tqdm.write('\n\tFailed Downloading From %s URLs' % len(errors))

def filterQueries(queries, blacklist):
	return [x for x in tqdm(queries) if x not in blacklist]

def readFile(file_path):
	if not os.path.exists(file_path):
		open(file_path, 'w')
	with open(file_path, 'r+') as f:
		file = f.readlines()
		file = [x.strip() for x in file]
	return file

def appendFile(data, file_path):
	if not os.path.exists(file_path):
		open(file_path, 'w')
	with open(file_path, 'a') as f:
		[f.write(line + '\n') for line in data]

def writeFile(data, file_path):
	with open(file_path, 'w') as f:
		[f.write(line + '\n') for line in data]

if __name__ == '__main__':
	import sys
	import os
	from subprocess import call

	if not os.geteuid() == 0:
		tqdm.write('\nscript must be run as root!\n')
		sys.exit(1)
	try:
		from itertools import combinations
		from itertools import imap
	except ImportError:
		tqdm.write('\nError importing intertools\n')
		sys.exit(1)
	try:
		from googlesearch import search as googlesearch
	except ImportError:
		tqdm.write('\nError importing google\n')
		sys.exit(1)
	try: 
		import urllib2
	except ImportError:
		tqdm.write('\nError importing urllib2\n')
		sys.exit(1)
	try:
		import argparse
	except ImportError:
		tqdm.write('\n Error importing argparse')
	try:
		from tqdm import tqdm
	except ImportError:
		tqdm.write('\n Error importing tqdm')
	from time import sleep

	parser = argparse.ArgumentParser(description='google-term-scraper', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-S', '--search_only', default=False, dest='no_download', action='store_true', help='only search and collect urls, no downloads or screens')
	parser.add_argument('-D', '--download_only', default=False, dest='no_search', action='store_true', help='only download from saved url list, no searching')
	parser.add_argument('-nB', '--no_Query_blacklist', default=False, dest='no_Query_blacklist', action='store_true', help='will not use a blacklist to filter already used searches')
	parser.add_argument('-nF', '--no_filter_filetypes', default=False, dest='no_filter_files', action='store_true', help='will not use filefilter: search engine option')
	parser.add_argument('-R', '--results', default=10, help='number of top results collected in google search')
	parser.add_argument('-Ma', '--max_terms', default=10, help='max number of secondary search terms per google search')
	parser.add_argument('-Mi', '--min_terms', default=2, help='min number of secondary search terms per google search')
	
	args = parser.parse_args()
	download = not args.no_download
	search = not args.no_search
	Number_of_results = int(args.results)
	Min_Number_of_terms = int(args.min_terms)
	Max_Number_of_terms = int(args.max_terms)
	use_Query_blacklist = not args.no_Query_blacklist
	use_filefilter = not args.no_filter_files

	if not os.path.exists(Downloads_folder):	
		os.makedirs(Downloads_folder)
	if not download and not search:
		tqdm.write('k.')
		sys.exit(1)
	else:
		main()