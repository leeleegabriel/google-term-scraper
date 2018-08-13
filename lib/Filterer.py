#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18
import string
import configparser
import os
from tqdm import tqdm
from os import listdir
from nltk.corpus import stopwords

import lib.Helper as Helper

SA_count = 32


def start(Working_dir, Config_file):
	os.chdir(Working_dir)

	global Hit_dir, Miss_dir, Words_file

	config = configparser.ConfigParser()
	config.read(Config_file)
	DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')

	Hit_dir = config['Hit_dir']
	Miss_dir = config['Miss_dir']
	Error_dir = config['Error_dir']
	Unfiltered_dir = config['App_dir']

	Words_file = config['Words']

	Files = Helper.getFiles(Unfiltered_dir + '/*')
	tqdm.write(' Sorting files')
	for file in tqdm(Files, unit='Files'):
		try:
			text = cleanText(getText(file))
			dest = simple_analysis(file, text)
			Helper.moveFile(file, dest)
		except KeyboardInterrupt:
			raise
		except ParseError:
			Helper.moveFile(file, Error_dir + '/' + file.split('/')[:-1])


def getText(file, lib):
	try:
		import textract
		text = textract.process(file)
	except KeyboardInterrupt:
		raise
	except Exception:
		try:
			from tika import parser
			text = parser.from_file(file)['content']
		except KeyboardInterrupt:
			raise
		except Exception:
			raise Helper.ParseError('Whoops')

	return text


def cleanText(text):
	stop = stopwords.words('english')
	filtered = str(text).lower().replace('[^\w\s]', '').replace('\n', ' ')
	filtered = ''.join(x for x in filtered if x in string.printable)
	filtered = ' '.join(word for word in filtered.split() if not in stop)
	# count = Counter(filtered).most_common(10)
	return filtered


def simple_analysis(file, text):
	terms = [t.replace('*', '').lower() for t in Helper.readFile(Words_file)]
	if sum(text.count(term) for term in terms) > SA_count:
		dest = Hit_dir + '/' + file.split('/')[-1] 
	else:
		dest = Miss_dir + '/' + file.split('/')[-1] 
	return dest


def readTerms():
	with open(Words_file, 'r') as f:
		terms = [x.strip() for x in f.readlines()]
	return terms


if __name__ == "__main__":
	start(os.path.abspath('..'), './config/config.txt')
