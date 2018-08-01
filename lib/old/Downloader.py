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

class Downloader(object):
	def __init__(self, Websites, Working_dir, config, D_count):
		os.chdir(Working_dir)
		self.DBase_dir, self.CBase_dir, self.Unfiltered_dir, self.App_dir,self.Misc_dir, self.CDownload_dir, self.CBlackList_dir, self.Errors_file, self.URL_file, self.URL_blacklist_file = [''] * 10
		self.Config_file = config
		self.setupDirs()
		self.Downloads = Helper.filterQueries(Websites, Helper.readFile(self.URL_blacklist_file))
		self.Dbar = tqdm(total=len(self.Downloads))	
		self.D_count = D_count

	def start(self):
		self.Download()
		# while run:
		# 	Downloads = Helper.filterQueries(Websites, Helper.readFile(URL_blacklist_file))
		# 	tqdm.write('Attempting to Download Files from %s URLs' % len(Downloads))
		# 	Download(Downloads, D_count)
		# 	checkWebsites = set(Helper.readFile(URL_file))
		# 	if set(Websites) == set(checkWebsites):
		# 		count = 0
		# 		while Websites == checkWebsites and count < 10:
		# 			sleep(60)
		# 			count +=1
		# 		if Websites != checkWebsites:
		# 			Websites = checkWebsites
		# 		else:
		# 			run = False
		# 	else:
		# 		Websites = checkWebsites

	def Download(self):
		tqdm.write('Attempting to Download Files from %s URLs' % len(self.Downloads))
		#pool = Pool(self.D_count)
		for url in tqdm(self.Downloads):
			self.DownloadWorker(url)
			#pool.apply_async(self.DownloadWorker, args=(url,))
		pool.close()
		pool.join()

	def showProg(self, *a):
		self.Dbar.update()

	def DownloadWorker(self, url):
		try:
			if not os.path.exists(self.App_dir + '/' + b64encode(url)) and not os.path.exists(self.Misc_dir + '/' + b64encode(url)):
				self.getDownload(url)
		except Exception as e:
			Helper.appendLine(url + " : " + str(e), self.Errors_file)
		return 1

	@timeout(10, os.strerror(errno.ETIMEDOUT))
	def getDownload(self, url):
		data = urllib2.urlopen(url)
		write = data.read()
		if 'application' in data.info().getheader('Content-Type'):
			folder = self.App_dir + '/'
		else:
			folder = self.Misc_dir + '/'
		with open(folder + b64encode(url), 'wb') as f:
			f.write(write)
		Helper.appendLine(url, self.URL_blacklist_file)		

	def setupDirs(self):
		config = configparser.ConfigParser()
		config.read(self.Config_file)
		self.DBase_dir = config.get('Dirs', 'DBase_dir').replace('\'', '')
		self.CBase_dir = config.get('Dirs', 'Config_dir').replace('\'', '')
		
		self.Unfiltered_dir = self.DBase_dir + '/unfiltered'
		self.App_dir = self.Unfiltered_dir + '/app'
		self.Misc_dir = self.Unfiltered_dir + '/app'
		self.CDownload_dir = self.CBase_dir + '/download'
		self.CBlackList_dir = self.CBase_dir + '/blacklists'

		self.Errors_file = self.CDownload_dir + '/errors.txt'
		self.URL_file = self.CDownload_dir + '/URL.txt'
		self.URL_blacklist_file = self.CBlackList_dir + '/URL_blacklist.txt'

		dirs = self.DBase_dir, self.CBase_dir, self.Unfiltered_dir, self.App_dir, self.Misc_dir, self.CDownload_dir, self.CBlackList_dir
		[Helper.makeFolder(folder) for folder in dirs]