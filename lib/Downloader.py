#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/18

import sys
import os
import errno
import configparser
import urllib2
from multiprocessing import Pool
from time import sleep
from tqdm import tqdm
from base64 import b64encode

import Helper
from timeout import timeout

def start(Working_dir, config):
	setupDirs(Working_dir, config)
	Download()

def Download():
	global Dbar 
	Downloads = Helper.filterQueries(Helper.readFile(URL_file), Helper.readFile(URL_blacklist_file))
	tqdm.write('Attempting to Download Files from %s URLs' % len(Downloads))
	Dbar = tqdm(total=len(Downloads))	
	
	pool = Pool(4)
	for url in Downloads:
		pool.apply_async(DownloadWorker, args=(url,), callback=showProg)
		#DownloadWorker(url)
	pool.close()
	pool.join()

def showProg(*a):
	Dbar.update()

def DownloadWorker(url):
	a = 1
	try:
		if not os.path.exists(App_dir + '/' + b64encode(url)) and not os.path.exists(Misc_dir + '/' + b64encode(url)):
			getDownload(url)
	except Exception as e:
		Helper.appendLine(url + " : " + str(e), Errors_file)
	return a

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
	Helper.appendLine(url, URL_blacklist_file)		

def setupDirs(Working_dir, Config_file):
	os.chdir(Working_dir)
	global App_dir, Misc_dir, Errors_file, URL_file, URL_blacklist_file

	config = configparser.ConfigParser()
	config.read(Config_file)

	DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
	CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')
	Unfiltered_dir = DBase_dir + '/unfiltered'
	App_dir = Unfiltered_dir + '/app'
	Misc_dir = Unfiltered_dir + '/Misc'
	CDownload_dir = CBase_dir + '/download'
	CBlackList_dir = CBase_dir + '/blacklists'

	Errors_file = CDownload_dir + '/errors.txt'
	URL_file = CDownload_dir + '/URL.txt'
	URL_blacklist_file = CBlackList_dir + '/URL_blacklist.txt'

	dirs = DBase_dir, CBase_dir, Unfiltered_dir, App_dir, Misc_dir, CDownload_dir, CBlackList_dir
	[Helper.makeFolder(folder) for folder in dirs]

if __name__== "__main__":
	start(os.path.abspath('..'),'./config/config.txt')