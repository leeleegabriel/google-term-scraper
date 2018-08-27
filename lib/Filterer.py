#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18
import string
import os
import logging
from nltk.corpus import stopwords

import lib.Helper as Helper

SA_count = 32


def start(config, log, handler):
	os.chdir(config['Abspath'])

	global Hit_dir, Miss_dir, Words_file, logger

	handler.setFormatter(logging.Formatter('[Filter] %(asctime)s : %(message)s '))
	logger = log

	Hit_dir = config['Hit_dir']
	Miss_dir = config['Miss_dir']
	Error_dir = config['Error_dir']
	Unfiltered_dir = config['App_dir']

	Words_file = config['Words']

	Files = Helper.getFiles(Unfiltered_dir + '/*')
	logger.info('Sorting files')
	if Files:
		for file in Files:
			try:
				text = cleanText(getText(file))
				dest = simple_analysis(file, text)
				Helper.moveFile(file, dest)
			except KeyboardInterrupt:
				logger.debug('Detected KeyboardInterrupt')
				raise
			except Helper.ParseError:
				logger.error('Encountered Parse Error with %s', file)
				Helper.moveFile(file, Error_dir + '/' + file.split('/')[:-1])
		logger.info('Finished filtering filtes')
	else:
		logger.info('No files to filter')


def getText(file, lib):
	try:
		import textract
		text = textract.process(file)
	except KeyboardInterrupt:
		logger.debug('Detected KeyboardInterrupt')
		raise
	except Exception:
		try:
			from tika import parser
			text = parser.from_file(file)['content']
		except KeyboardInterrupt:
			logger.debug('Detected KeyboardInterrupt')
			raise
		except Exception:
			raise Helper.ParseError('Whoops')

	return text


def cleanText(text):
	stop = stopwords.words('english')
	filtered = str(text).lower().replace('[^\w\s]', '').replace('\n', ' ')
	filtered = ''.join(x for x in filtered if x in string.printable)
	filtered = ' '.join(word for word in filtered.split() if word not in stop)
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
