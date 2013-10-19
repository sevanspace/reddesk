# Use socket and urllib2 for making url requests
import socket
import urllib2
# Use Queue and threading for multithreading
import Queue
import threading
# use ElementTree for building xml tree from rss feed
from xml.etree import ElementTree as etree




# DEFAULT VALUES

# subreddits
subreddits = ["cityporn", "architectureporn", "infrastructureporn", "villageporn"]

# default timeout
default_timeout = 5

# timeout in secs for downloading images
image_download_timeout = 10

# timeout in secs for parsing subreddits
page_parse_timeout = 5

# getImageLink threads
image_builder_thread_count = 5

# image downloading threads
image_downloader_thread_count = 10

# INITIALIZE

# holds image objects parsed from reddit .rss feeds
image_q = Queue.Queue()



# set urllib2 request timeout
socket.setdefaulttimeout(default_timeout)

# gets response from calling url or prints error output
def urlRequest(url):
	req = urllib2.Request(url)
	try: 
		response = urllib2.urlopen(req)
	except URLError, e:
		if hasattr(e, 'reason'):
			print 'Failed to reach server: ', req
			print 'Reason: ', e.reason
		elif hasattr(e, 'code'):
			print 'The server couldn\'t fulfill the request.'
			print 'Error code: ', e.code
		raise e

	result = response.read()
	response.close()
	return result

def buildXmlTree(url):
	response = urlRequest(url)
	xmltree = etree.fromstring(response)
	return xmltree

# fill image queue with images from subreddit feed
def getImageLinks(subreddit):
	url = "http://www.reddit.com/r/" + subreddit + ".rss"

	xmltree = buildXmlTree(url)

	items = xmltree.findall('channel/item')

	for item in items:
		image = RedditImage(item)
		if (image):
			image_q.put(image)

# RedditImage is instantiated with a Reddit xml 'item'
# and stores parsed details about the item image
class RedditImage:
	def __init__(self, xmlItem):
		self.__xmlItem = xmlItem
		self.url = self.__url()

		# if a valid link url can't be parsed, image is unusable
		if self.url = "":
			return None

		self.title = self.__title()
		self.dimensions = self.__dimensions()

		def __title(self):
			return self.__xmlItem.find('title').text

		def __dimensions(self):
			item_title = self.__xmlItem.find('title').text
			m = re.search('([0-9]{3,5})[^0-9]+([0-9]{3,5})', item_title)
			if m != None and m.lastindex != None and m.lastindex > 1:
				return (int(m.group(1)), int(m.group(2)))
			else:
				return (0,0)

		def __url(self):
			item_description = self.xmlItem.find('description').text
			m = re.search('<a href="([^"]+)">\[link\]', item_description)   
			if m != None and m.lastindex != None and m.lastindex > 0:
				return m.group(1)
			else:
				return ""


# START WORKER THREADING

# runs function on objects in queue_start until empty
def worker(queue_start, function):
	queue_full = True
	while queue_full:
		try:
			obj = queue.get(False)
			function(obj)

		except Queue.empty:
			queue_full - False

# RUNNING ENGINE

def startThreads:
	for i in range(image_builder_thread_count):
		t = threading.Thread(target=worker, args=(image_q,))
		t.start()






# CP'ED CODE ------------


#define a worker function
def worker(queue):
    queue_full = True
    while queue_full:
        try:
            #get your data off the queue, and do some work
            url= queue.get(False)
            data = urllib2.urlopen(url).read()
            print len(data)

        except Queue.Empty:
            queue_full = False

#create as many threads as you want
thread_count = 5
for i in range(thread_count):
    t = threading.Thread(target=worker, args = (q,))
    t.start()



# Setup worker threads to 







# this call to urllib2.urlopen now uses the default timeout
# we have set in the socket module
req = urllib2.Request('http://www.voidspace.org.uk')


try: 
	response = urllib2.urlopen(req)
except URLError, e:
    if hasattr(e, 'reason'):
    	print 'Failed to reach server: ', req
        print 'Reason: ', e.reason
    elif hasattr(e, 'code'):
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
else:
	#everything is fine

