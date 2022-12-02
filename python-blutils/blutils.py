import sys, os
import shutil
import distutils.dir_util
#import json
#import datetime

# Just for getRandomString().
import string
import random



def getRandomString(digits, chars=(string.ascii_lowercase + string.digits)):
	output = ""
	for i in range(digits):
		output += random.choice(chars)
	return output


def printAndQuit(msg):
    print(msg)
    quit()

# Copy file to (over) another file.  If dstPath exists, it must be a file.
def copyFileAs(srcPath, dstPath):
	if not os.path.isfile(srcPath):
		raise Exception("CopyFileAs src is not a file!")
	# dst must not yet exist, or be a file (to overwrite).
	if os.path.exists(dstPath) and not os.path.isfile(dstPath):
		raise Exception("CopyFileAs dst exists, but is not a file!")
	shutil.copy2(srcPath, dstPath)

# Copy file into an existing dir.
def copyFileInto(srcPath, dstPath):
	if not os.path.isfile(srcPath):
		raise Exception("CopyFileInto src is not a file! (" + srcPath + ")")
	if not os.path.isdir(dstPath):
		raise Exception("CopyFileInto dst is not a dir! (" + dstPath + ")")
	shutil.copy2(srcPath, dstPath)

# Copy contents of dir into a new dir.  dstDir must not yet exist.
#def CopyDirOverDir(srcDir, dstDir):
def copyContentsIntoNew(srcDir, dstDir):
	if not os.path.isdir(srcDir):
		raise Exception("CopyContentsIntoNew src is not a dir!")
	# shutil.copytree requires dst not yet exist.  This is redundant.
	if os.path.isdir(dstDir):
		raise Exception("CopyContentsIntoNew dst exists! (" + dstDir + ")")
	shutil.copytree(srcDir, dstDir)
	# There's also: "distutils.dir_util.copy_tree()".  (Why?)

# Copy contents of dir into an existing dir.  dstDir need not be empty.
def copyContentsIntoExisting(srcDir, dstDir):
	if not os.path.isdir(srcDir):
		raise Exception("CopyContentsInto src is not a dir! (" + srcDir + ")")
	if not os.path.isdir(dstDir):
		raise Exception("CopyContentsInto dst is not a dir! (" + dstDir + ")")
	distutils.dir_util.copy_tree(srcDir, dstDir)

# Copy contents of dir into another dir.  dstDir created if DNE.
def copyContentsInto(srcDir, dstDir):
	if not os.path.isdir(srcDir):
		raise Exception("CopyContentsInto src is not a dir!")
	# former (requires dstDir is empty): shutil.copytree(srcDir, dstDir)
	distutils.dir_util.copy_tree(srcDir, dstDir)


# json load/loads(), that strips full-line comments. (First non-whitespace chrs are "//".)
# Incomplete (no midline "//", nor "/* ... */", but better than nothing.  May be extended in the future.)
# (WIP, Broken...)
#def json_stripcomments(jsonStr):
#	newLine = "\r\n" if jsonStr.find("\r\n") > -1 else "\n"
#	lines = jsonStr.split(newLine)
#	for i in range(len(lines)): # Omit full-line comment lines.
#		firstChrIdx = len(lines[i]) - len(lines[i].lstrip())
#		if lines[i][firstChrIdx:firstChrIdx+2] == "//":
#			lines[i] == "" # Delete the line.
#	return newLine.join(lines)
#
#def json_loads(jsonStr):
#	return json.loads(json_stripcomments(jsonStr))
#
#def json_load(file):
#	#with open(fileName) as file:
#	#	return json_loads(file.read())
#	return json_loads(file.read())