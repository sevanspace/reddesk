# Use socket and urllib2 for making url requests
import socket
import urllib2
# Use Queue and threading for multithreading
import Queue
import threading
# use ElementTree for building xml tree from rss feed
from xml.etree import ElementTree as etree
# use re for regex matching when parsing rss feed
import re

# DEFAULT VALUES:

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

# getImageLink thread list to keep track of running threads
image_builder_threads = []

# image downloading thread list to keep track of running threads
image_downloader_threads = []

# INITIALIZATION:

# holds subreddits waiting to be parsed by worker threads
subreddit_q = Queue.Queue()

# fill queue with given subreddit list
for sub in subreddits:
	subreddit_q.put(sub)

# holds image objects parsed from reddit .rss feeds
image_q = Queue.Queue()

# set urllib2 request timeout
socket.setdefaulttimeout(default_timeout)


# HOW THREDDESK WORKS:

# Worker threads "build" RedditImages by parsing subreddit .rss feeds.
# RedditImages are classes defined by:
#   - a url (to download image)
#   - a title (for the file)
#   - dimensions (for setting to the appropriate screen size)

# Worker threads deposit "built" RedditImages into the image queue.
# New worker threads pick up these RedditImages and begin downloading the actual files.




# SUBREDDIT PARSING METHODS:

# gets response from calling url or prints error output
def urlRequest(url):
	req = urllib2.Request(url)
	try: 
		response = urllib2.urlopen(req)
	except urllib2.URLError, e:
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


# REDDITIMAGE CLASS:

# RedditImage is instantiated with a Reddit xml 'item'
# and stores parsed details about the item image
class RedditImage:
	def __init__(self, xmlItem):
		self.__xmlItem = xmlItem
		self.url = self.__url()

		# if a valid link url can't be parsed, image is unusable
		if self.url == "":
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
		item_description = self.__xmlItem.find('description').text
		m = re.search('<a href="([^"]+)">\[link\]', item_description)   
		if m != None and m.lastindex != None and m.lastindex > 0:
			return m.group(1)
		else:
			return ""


# WORKER THREADING METHODS:

# runs function on objects in queue until empty
def worker(queue, function):
	queue_full = True
	while queue_full:
		try:
			#queue.get() blocks until an item is available unless passed False
			obj = queue.get(False)
			function(obj)

		except Queue.Empty:
			queue_full = False


# RUNNING ENGINE:

# initiate and start threads to find images in subreddits
def startThreads():
	# start threads to find images in subreddits and fill image_q
	for i in range(image_builder_thread_count):
		t = threading.Thread(target=worker, args=(subreddit_q, getImageLinks))
		t.start()
		image_builder_threads.append(t)

	# FOR TESTING ONLY:
	# wait for each image_builder thread to finish
	while image_builder_threads:
		t = image_builder_threads.pop()
		t.join()

	# return the image_q for debugging
	return image_q





	# start threads to download images from image_q
#	for i in range(image_downloader_thread_count):
#		t = threading.Thread(target=worker, args=(image_q,))
#		t.start()




