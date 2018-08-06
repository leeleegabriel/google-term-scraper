#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import sqlite3
from googlesearch import search
from itertools import combinations
from time import sleep
from tqdm import tqdm

import Helper

def start(Working_dir, Config_file, DB_file, Max, Min, results):
	global DB, Max_number_of_Terms, Min_Number_of_Terms, Number_of_Results
	DB, Max_number_of_Terms, Min_Number_of_Terms, Number_of_Results = DB_file, Max, Min, results

	getDirs(Working_dir, Config_file)

	tqdm.write('Loading Words from %s' % Word_file)
	Primary_words, Secondary_words = getWords()
	tqdm.write('\t%s Primary Words, %s Secondary words' % (len(Primary_words), len(Secondary_words)))
	tqdm.write('Loading Filetypes from %s' % Filetypes_file)
	FileTypes = Helper.readFile(Filetypes_file)
	tqdm.write('\tLooking for: %s' %  (" ".join(str(x) for x in FileTypes)))
	BaseQuery = str(" ".join(str(x) for x in Primary_words))			
	
	Queries = getQueries(BaseQuery, Secondary_words)
	Scrape(Queries, FileTypes)

def getWords(): 
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

def getQueries(base_query, secondary_words): 
	queries = []
	tqdm.write('Generating Queries')
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

	tqdm.write('Inserting Queries into DB')
	stmt = """INSERT OR IGNORE INTO %s (%s) VALUES (?)""" % ('Queries', 'query')
	[c.execute(stmt,  (row,)) for row in queries]
	conn.commit()

	tqdm.write('Filtering Queries')
	conn.row_factory = lambda cursor, row: row[0]
	c = conn.cursor()
	filtered_queries = c.execute("""SELECT query FROM Queries WHERE query NOT IN (SELECT query FROM Used_Queries)""").fetchall()
	conn.close()

	return filtered_queries

def Scrape(queries, filetypes):
	tqdm.write('Collecting URLs')
	total_urls = len(queries) * ((len(filetypes) + 1) * Number_of_Results)
	with tqdm(total=total_urls, unit='URLs') as pbar:	
		for query in queries:
			search = [] + list(googleSearch(query, 0))
			pbar.update(Number_of_Results)
			for file in filetypes:
				search.extend(googleSearch(file + " " +  query, 0))
				pbar.update(Number_of_Results)
			Helper.insertData(DB, 'URLs', 'url', search)
			Helper.insertData(DB, 'Used_Queries', 'query', query)

def googleSearch(query, count):
	top_results = []
	tqdm.write(query)
	try:
		top_results = [url for url in search(query, stop=Number_of_Results)]
	except Exception as e:
		sleep(2)
		if count < 10:
			top_results = googleSearch(query, count + 1)
		else:
			tqdm.write('Error: %s' % e)
			sys.exit(0)
	return top_results


def getDirs(Working_dir, Config_file):
	os.chdir(Working_dir)
	global Filetypes_file, Word_file

	import configparser
	config = configparser.ConfigParser()
	config.read(Config_file)

	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')
	Search_Dir = CBase_dir + '/search'

	Filetypes_file = Search_Dir + '/filetypes.txt'
	Word_file = Search_Dir + '/words.txt'

if __name__== "__main__":
	start(os.path.abspath('..'),'./config/config.txt', './config/ScrapeDB.db')