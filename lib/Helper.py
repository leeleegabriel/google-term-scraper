#!/usr/bin/python
# -*- coding: UTF-8 -*
# Lee Vanrell 7/1/1

import os
import glob
# from tqdm import tqdm


def readFile(file_path):
	# if not os.path.exists(file_path):
	# 	open(file_path, 'w')
	with open(file_path, 'r+') as f:
		file = [x.strip() for x in f.readlines()]
	return file


def moveFile(src, dest):
	os.rename(src, dest)


def checkFile(file):
	if os.path.isfile(file):
		return True
	return False


def getFiles(directory):
	return glob.glob(directory)


def makeFolder(folder_path):
	if not os.path.exists(folder_path):
		os.makedirs(folder_path)


class ProxyError(Exception):
    def __init__(self, message):
        super().__init__(message)


class ParseError(Exception):
    def __init__(self, message):
        super().__init__(message)


# def insertData(db, table, column, data):
# 	conn = sqlite3.connect(db)
# 	c = conn.cursor()
# 	stmt = """INSERT OR IGNORE INTO %s (%s) VALUES (?)""" % (table, column)
# 	[c.execute(stmt,  (row,)) for row in data]
# 	conn.commit()
# 	conn.close()
