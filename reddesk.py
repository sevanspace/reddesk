import time
from appscript import *
import AppKit
import xml.etree.ElementTree as et
import urllib
import re
import os
import glob
import sys
import signal

""" TODO:
issue with timeout on download:
try using urllib2 as noted here:
http://www.voidspace.org.uk/python/articles/urllib2.shtml#sockets-and-layers
"""


screenSizes = [(screen.frame().size.width, screen.frame().size.height)
    for screen in AppKit.NSScreen.screens()]

debug = True

subreddit = "cityporn"
subreddits = ["cityporn", "architectureporn", "infrastructureporn", "villageporn"]

isWindows = False

reddeskRoot = "~/Developer/scripts/reddesk/"

params = urllib.urlencode({'count': 25})

errors = 0
errorLog = []
#error / debugging tools:
def d(debugString):
    if debug:
        print debugString
    return debugString # for simultaneous debug/error-logging

def error(errorString, contextString=None):
    global errors
    errorLog.append({'error': errorString,
                     'timestamp': time.time() })
    if contextString is not None:
        errorLog[len(errorLog) - 1]['context'] = contextString
    errors += 1

print "******REDDESK******"
print "*Desktop retrieval*"
print "*******************"
print ""
d( screenSizes)

imageCycle = 30 #number of images to download at a time and cycle through as backgrounds
imageDelay = 60 * 5 #number of seconds for image to remain as a background
imgSizeToScreen = 1
downloadTimeLimit = 2 #seconds before download times out

imgFiles = [] #global that will be filled with imgFiles

screenDimension = screenSizes[0]

cdFolder = "currentDesktop/"


filetypes = [".jpg", ".png"]
maxFileNameLen = 30

loadTries = 0
maxConnTries = 8

class TimeoutException(Exception):
    pass

def getImgsFromSubreddits(subreddits):
    for subreddit in subreddits:
        url = "http://www.reddit.com/r/" + subreddit + ".rss"
        xtree = getXmlTree(url)
        getImages(xtree) #adds to global imgFiles

def getXmlTree(url):
    global loadTries, maxConnTries
    loadSuccess = False
    xmltree = []
    while not loadSuccess:
        try:
            f = urllib.urlopen(url) #&count?%s" , params)
            xmltext = f.read()
            xmltree = et.fromstring(xmltext)
            loadSuccess = True
        except Exception:
            if loadTries > maxConnTries:
                d("Connection to " + url + " failed.")
                SystemExit("Connection failed")
            if debug:
                print "Connection failed. Retrying..."
            time.sleep(.5)
    return xmltree

def getTitle(item):
    item_title = item.find('title').text
    m = re.search('([^\[\(\]\)]+)', item_title) #[a-zA-Z\s0-9,.\']
    title = ""
    if m != None:
        if m.lastindex != None:
            title = m.group(0).strip()
            #remove any hanging characters at the end of the item_title
            if title.endswith("-"):
                title = title[:-1]
                title = title.strip()
            d("Title: " + title) #get rid of end whitespace
        else:
            error(d("Title found, matching failed in <title>: " + item_title))
    else:
        error(d("Title not found in <title>: " + item_title))

    return title

def getDimensions(item):
    item_title = item.find('title').text
    m = re.search('([0-9]{3,5})[^0-9]+([0-9]{3,5})', item_title)
    dimensions = (0,0)
    if m != None:
        if m.lastindex != None and m.lastindex > 1:
            dimensions = (int(m.group(1)), int(m.group(2)))
            d("Dimensions: " + str(dimensions))
        else:
            error(d("Dimenions found, matching failed in <title>: " + item_title))            
    else:
        error(d( "Dimensions not found in <title>: " + item_title))
 
    return dimensions

def getImgUrl(item):
    item_description = item.find('description').text
    m = re.search('<a href="([^"]+)">\[link\]', item_description)
    imgUrl = ""
    #search for imgur link
    if m != None:
        if m.lastindex != None and m.lastindex > 0:
            imgUrl = m.group(1)
            d("img: " + m.group(1))
        else:
            error(d("img link found, matching failed in <description>: " + item_description))
    else:
        error(d("img not found in <description>: " + item_description))
    return imgUrl

def getImgFiles(images):
    imgFiles = [{'Title': image['Title'],
                 'Dimensions': image['Dimensions'],
                 'ImgUrl': image['ImgUrl'],
                 'Rank': image['Rank']}
                 for image in images
                 if any(ft in image['ImgUrl'] for ft in filetypes) ]
    if debug:
        print imgFiles
        print ""
        print "Total image files: " + str(len(imgFiles))

    return imgFiles

def getSizedImgFiles(images, percentSize, screenDimension, largerThan = True):
    sizedImgFiles = [{'Title': image['Title'],
                      'Dimensions': image['Dimensions'],
                      'ImgUrl': image['ImgUrl'],
                      'Rank': image['Rank']}

    for image in images
    if largerThan and ((image['Dimensions'][0] > screenDimension[0] * percentSize)
                    and (image['Dimensions'][1] > screenDimension[1] * percentSize))
    or (not largerThan) and ((image['Dimensions'][0] < screenDimension[0] * percentSize)
                    and (image['Dimensions'][1] < screenDimension[1] * percentSize))
                     ]
                        
    if debug:
        print sizedImgFiles
        print ""
        print "Total sized image files: " + str(len(sizedImgFiles))

    return sizedImgFiles

def getFileType(imgUrl):
    reversedImgUrl = imgUrl[::-1] #reverses string
    dotIndex = len(imgUrl) - reversedImgUrl.find('.') - 1
    filetype = imgUrl[dotIndex:]
   
    if debug:
        print "Filetype: " + filetype + " for imgUrl: " + imgUrl
    return filetype



def download(url, downloadLocation):
    success = False
    def timeout_handler(signum, frame):
        raise TimeoutException()

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(downloadTimeLimit) # trigger alarm in x seconds

    try:
        urllib.urlretrieve(url, downloadLocation)
        success = True
    except TimeoutException:
        d("Download of " + url + " timed out.")
    finally:
        signal.signal(signal.SIGALRM, old_handler)

    signal.alarm(0)
    
    return success

def downloadImgFiles(images, directory):
    d( "Downloading images...")

    numDownloads = 0

    totalImages = len(images)
    downloadedImgs = []

    d( str(totalImages) + " files to download.")

    for image in images:
        downSuccess = False
        downTries = 0
        maxTries = 1
        while maxTries > downTries:
            try:
                url = image['ImgUrl']
                ft = getFileType(url)
                fileName = image['Title'][0:maxFileNameLen] + ft
                downLocation = directory + fileName
                d( "Attempting download from " + url + " to " + downLocation)
                if download(url, downLocation):
                    image['Location'] = downLocation
                    numDownloads += 1
                    d("  " + str(numDownloads) + " of " + str(totalImages) + " downloaded")
                    downloadedImgs.append(image)
                    downTries += 1
                else:
                    downTries += 1
            except Exception:
                if downTries > maxTries:
                    error(d("Download from " + image['ImgUrl'] + " failed."))
                    break
                d("Download failed. Retrying...")
                downTries += 1
                time.sleep(.5)
    d("Download complete. " + str(numDownloads) + " out of " + str(totalImages) + " downloaded.")
    
    #only return the imgs that successfully downloaded
    return downloadedImgs

def setAsDirectory(folderName):
    if isWindows:
        folderDemarc = "\\"
    else:
        folderDemarc = "/"

    if folderName[-1:] is not folderDemarc:
            folderName += folderDemarc
    
    if debug:
        print "directory set: " + folderName
    return folderName


class Rank:
    def __init__(self):
        self.rank = 0
    
    def next(self):
        self.rank += 1
        return self.rank - 1

def setImgAsDesktop(image):
    
    if debug:
        print "Setting " + image['Location'] + " as desktop..."
    #'/path/to/file.jpg'
    f = image['Location'] #setAsDirectory(reddeskRoot) + image['Location']
    app('Finder').desktop_picture.set(mactypes.File(f))

    """ # this is supposd to work for multiple desktops: (it isn't?)
    se = app('System Events')
    desktops = se.desktops.display_name.get()
    for d in desktops:
        desk = se.desktops[its.display_name == d]
        desk.picture.set(mactypes.File(f))
    """
    if debug:
        print "Success!"


def getTopRanked(images, num):
    if debug:
        print "getting top ranked images..."
    if num > len(images): # catch index out of range
        if debug:
            print "index out of range caught, cleared"
        num = len(images)

    topRankedImgFiles = []
    ranker = Rank()
    while True:
        r = ranker.next()
        for img in images:
            if img['Rank'] is r:
                topRankedImgFiles.append(img)
                if len(topRankedImgFiles) is num:
                    return topRankedImgFiles
#    topRankedImgFiles = images[0:num-1]
    return topRankedImgFiles

def test():
    if debug:
        print ""
        print "getting sized img files..."
        sizedImgFiles = getSizedImgFiles(imgFiles, 1, screenDimension)
        print ""
        print "getting larger img files..."
        LargeSizedImgFiles = getSizedImgFiles(imgFiles, 2, screenDimension)
        print ""
        print "getting smaller img files..."
        smallSizedImgFiles = getSizedImgFiles(imgFiles, 1, screenDimension, False)

def getImages(xmltree):
    global imgFiles
    errorCount = errors
    ranker = Rank()
    images = [{'Title': getTitle(item),
           'Dimensions': getDimensions(item),
           'ImgUrl': getImgUrl(item),
           'Rank': ranker.next()
          } for item in xmltree.iter('item')]

    errorCount = errors - errorCount
    if debug:
        print images
        print ""
        print "Search complete. Errors: " + str(errorCount)

    imgFiles.extend(getImgFiles(images)) #global

def clearContents(path, exceptForFile=None):
    skipFile = ""
    if exceptForFile is not None:
        skipFile = exceptForFile
    files = glob.glob(setAsDirectory(path) + "*") #/PATH/TO/FOLDER/*
    for f in files:
        if f is not skipFile:
            os.remove(f)

def runBackgroundUpdater():
    skipFilePath = None
    while(True):
        if debug:
            print ""
            print "clearing folder contents..."
        clearContents(cdFolder, skipFilePath)

        getImgsFromSubreddits(subreddits)
        #    getXmlTree(url)
        #   getImages() #this fills global imgFiles
        if debug:
            print ""
            print "getting img files..."
        sizedImgFiles = getSizedImgFiles(imgFiles, imgSizeToScreen, screenDimension)
        
        if debug:
            print "downloading top ranked img..."
            
        newDesktopImgs = getTopRanked(sizedImgFiles, imageCycle)
        if len(newDesktopImgs) is 0:
            error(d("ERROR! images are empty!"))
            SystemExit("ERROR in images")
        downloadedImgs = downloadImgFiles(newDesktopImgs, setAsDirectory(cdFolder))

        n = len(downloadedImgs)
        for i in range(n):
            setImgAsDesktop(downloadedImgs[i])
            time.sleep(imageDelay)
            if i is n - 1: #setting the last image should start the next download
                if debug:
                    print "restarting background cycle..."
                skipFilePath = downloadedImgs[i]['Location']
                #clearContents(cdFolder, skipFilePath)
        
            
                
#main!           
runBackgroundUpdater()
