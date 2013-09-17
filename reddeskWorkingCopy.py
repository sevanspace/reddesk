import time
from appscript import *
import AppKit
import xml.etree.ElementTree as et
import urllib
import re

screenSizes = [(screen.frame().size.width, screen.frame().size.height)
    for screen in AppKit.NSScreen.screens()]

subreddit = "cityporn"

isWindows = False

reddeskRoot = "~/Developer/scripts/reddesk/"

params = urllib.urlencode({'count': 25})

print "******REDDESK******"
print "*Desktop retrieval*"
print "*******************"
print ""
print screenSizes



errors = 0
filetypes = [".jpg", ".png"]
maxFileTitleLength = 30
debug = True


url = "http://www.reddit.com/r/" + subreddit + ".rss"
loadSuccess = False
loadTries = 0
maxTries = 8
while not loadSuccess:
    try:
        f = urllib.urlopen(url) #&count?%s" , params)
        xmltext = f.read()
        xmltree = et.fromstring(xmltext)
        loadSuccess = True
    except Exception:
        if loadTries > maxTries:
            if debug:
                print "Connection to " + url + " failed."
            SystemExit("Connection failed")
        if debug:
            print "Connection failed. Retrying..."
        time.sleep(.5)



def getTitle(item):
    global errors
    global debug
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
            if debug:
                print "Title: " + title #get rid of end whitespace
        else:
            if debug:
                print "Title found, matching failed in <title>: " + item_title
            errors += 1
    else:
        if debug:
            print "Title not found in <title>: " + item_title
        errors += 1

    return title

def getDimensions(item):
    global errors
    global debug
    item_title = item.find('title').text
    m = re.search('([0-9]{3,5})[^0-9]+([0-9]{3,5})', item_title)
    dimensions = ()
    if m != None:
        if m.lastindex != None and m.lastindex > 1:
            dimensions = (int(m.group(1)), int(m.group(2)))
            if debug:
                print "Dimensions: " + str(dimensions)
        else:
            if debug:
                print "Dimenions found, matching failed in <title>: " + item_title
            errors += 1
    else:
        if debug:
            print "Dimensions not found in <title>: " + item_title
        errors += 1

    return dimensions

def getImgUrl(item):
    global errors
    global debug
    item_description = item.find('description').text
    m = re.search('<a href="([^"]+)">\[link\]', item_description)
    imgUrl = ""
    #search for imgur link
    if m != None:
        if m.lastindex != None and m.lastindex > 0:
            imgUrl = m.group(1)
            if debug:
                print "img: " + m.group(1)
        else:
            if debug:                  
                print "img link found, matching failed in <description>: " + item_description
            errors += 1
    else:
        if debug:
            print "img not found in <description>: " + item_description
        errors += 1

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
    if debug:
        print "getting file type for " + imgUrl
    reversedImgUrl = imgUrl[::-1] #reverses string
    if debug:
        print "reversedImgUrl = " + reversedImgUrl
    dotIndex = len(imgUrl) - reversedImgUrl.find('.') - 1
    if debug:
        print "dotIndex: " + str(dotIndex)
    filetype = imgUrl[dotIndex:]
   
    if debug:
        print "Filetype: " + filetype + " for imgUrl: " + imgUrl
    return filetype

def downloadImgFiles(images, directory):
    if debug:
        print "Downloading images..."
    numDownloads = 0
    totalImages = len(images)
    for image in images:
        downSuccess = False
        downTries = 0
        maxTries = 1
        while not downSuccess:
            try:
                url = image['ImgUrl']
                ft = getFileType(url)
                if debug:
                    print "url: " + url
                    print "filetype: " + ft
                
                downLocation = directory + image['Title'][0:maxFileTitleLength] + getFileType(url)
                if debug:
                    print "Attempting download from " + url + " to " + downLocation
                urllib.urlretrieve(url, downLocation)
                downSuccess = True
                image['Location'] = downLocation
                numDownloads += 1
                if debug:
                    print "  " + str(numDownloads) + " of " + str(totalImages) + " downloaded"
            except Exception:
                if downTries > maxTries:
                    if debug:
                        print "Download from " + image['ImgUrl'] + " failed."
                    break
                if debug:
                    print "Download failed. Retrying..."
                downTries += 1
                time.sleep(.5)
    if debug:
        print "Download complete. " + str(numDownloads) + " out of " + str(totalImages) + " downloaded."

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

ranker = Rank()
images = [{'Title': getTitle(item),
           'Dimensions': getDimensions(item),
           'ImgUrl': getImgUrl(item),
           'Rank': ranker.next()
          } for item in xmltree.iter('item')]

if debug:
    print images
    print ""
    print "Search complete. Errors: " + str(errors)

imgFiles = getImgFiles(images)

def getTopRanked(images, num):
    topRankedImgFiles = [images[i] for i in range(num)]
    return topRankedImgFiles

screenDimension = screenSizes[0]
print ""
print "getting sized img files..."
sizedImgFiles = getSizedImgFiles(imgFiles, 1, screenDimension)
print ""
print "getting larger img files..."
LargeSizedImgFiles = getSizedImgFiles(imgFiles, 2, screenDimension)
print ""
print "getting smaller img files..."
smallSizedImgFiles = getSizedImgFiles(imgFiles, 1, screenDimension, False)

cdFolder = "currentDesktop/"

print ""
print "getting slightly largr img files..."
LSizedImgFiles = getSizedImgFiles(imgFiles, 1.2, screenDimension)

print "downloading top ranked img..."
newDesktopImgs = getTopRanked(LSizedImgFiles, 1)
downloadImgFiles(newDesktopImgs, setAsDirectory(cdFolder))

setImgAsDesktop(newDesktopImgs[0])
