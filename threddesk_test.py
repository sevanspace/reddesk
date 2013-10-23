import threddesk

test_image_q = threddesk.startThreads()


print '\nTest Image Queue:\n'

for i in range(test_image_q.qsize()):
	img = test_image_q.get()
	print 'Url: ', img.url
	print '     Title: ', img.title
	print '     Dimensions: ', img.dimensions

