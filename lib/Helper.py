#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/1

import os
import glob
from tqdm import tqdm

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

def appendLine(data, file_path):
	if not os.path.exists(file_path):
		open(file_path, 'w')
	with open(file_path, 'a') as f:
		f.write(data + '\n')

def writeFile(data, file_path):
	with open(file_path, 'w') as f:
		[f.write(line + '\n') for line in data]

def moveFile(src, dest):
	tqdm.moving(src)
	os.rename(src, dest)

def getFiles(directory):
	return glob.glob(directory)

def makeFolder(folder_path):
	if not os.path.exists(folder_path):	
		os.makedirs(folder_path)

def filterQueries(queries, blacklist):
	tqdm.write('Filtering using Blacklist')
	return [x for x in tqdm(queries) if x not in blacklist]