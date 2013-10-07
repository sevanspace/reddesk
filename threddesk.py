# Use socket and urllib2 for making url requests
import socket
import urllib2
# Use Queue and threading for multithreading
import Queue
import threading





# DEFAULT VALUES

# subreddits
subreddits = ["cityporn", "architectureporn", "infrastructureporn", "villageporn"]

# timeout in secs for downloading images
image_download_timeout = 10

# timeout in secs for parsing subreddits
page_parse_timeout = 5



#INITIALIZE

socket.setdefaulttimeout(timeout)





def getImageLinks(subreddit):
	# get XMLtree from url
	# parse tree to find images
	# put links to images into imageLink queue

	url = "http://www.reddit.com/r/" + subreddit + ".rss"
	xtree = get






worker_data = ['http://google.com', 'http://yahoo.com', 'http://bing.com']


#C/P'ed from stack overflow
#load up a queue with your data, this will handle locking
q = Queue.Queue()
for url in worker_data:
    q.put(url)

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
    	print 'Failed to reach a server.'
        print 'Reason: ', e.reason
    elif hasattr(e, 'code'):
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
else:
	#everything is fine

