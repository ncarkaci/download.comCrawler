#!/usr/bin/env python
#
# Search download.com website and downlaod executables as given searchkeyword
#
# Firstly calculate paging, after that scrapy all link in pages
# Eliminate other OS and platform applications without windows
# Make download proces with multithread approach
#
# Author: Necmettin Çarkacı
# E-mail: necmettin [ . ] carkaci [ @ ] gmail [ . ] com
#
# Usage : download_com_spider


import requests, re, os, random

from threading import Thread
import queue as queue

try:
	from fake_useragent import UserAgent
except:
	print ("Missing libary. Try below command installing library. \n pip install fake-useragent")


def run(searchKeywordList, agentHeader, proxy):

	for search_keyword in searchKeywordList :
	
		main_url =  "http://download.cnet.com/s/"+search_keyword+"/windows/"	

		content= requests.get(main_url, headers = agentHeader,  proxies=proxy).text

		pattern = re.compile(r'<span\sclass=\"results-total\">\s(.*?)\s</span>')
		match 	= pattern.search(content).group()

		number_of_file 	= 	int(match.split()[3].replace(",",""))
		pageSize 		=	int(number_of_file/10) # Show 10 file in per page
	    
		print ("For "+search_keyword+" "+str(number_of_file)+" file found on "+main_url)

		for pageNo in range(1,pageSize):
			page_url = main_url+"?page="+str(pageNo)
		
			if not os.path.exists(search_keyword):
				os.makedirs(search_keyword)
			downloadFilesInPage(page_url, search_keyword, agentHeader, proxy)


# Getting redirect links from page
def downloadFilesInPage(url, category, agentHeader, proxy):

	try:
		print ("Search page : "+url)
				 
		content= requests.get(url, headers = agentHeader,  proxies=proxy).text

		urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)

		urlQueue = queue.Queue()

		for link in urls:
			urlQueue.put(link)
				
		for thread in range(10):
			thread = Thread(target = downloadThread, args = (urlQueue,category,))
			thread.daemon = True
			thread.start()
			
		urlQueue.join()

	except Exception as err:
		writeError(url,"Error, while collecting redirect links :"+str(err))

def downloadThread(urlQueue, category):
	
	try:
		while not urlQueue.empty():
			link = urlQueue.get()
			# New user agent for per download link
			user_agent  = UserAgent()
			agentHeader = {'User-Agent': user_agent.random}

			if link.endswith('.html') and (not isDuplicateLink(link.replace("\n", ""))):
				#print ("Redirect url link : "+link)
				download_link = getDownloadLink(link,  agentHeader, proxy)
				
				if download_link != '':
					download_link = download_link.replace("\n", "")
					#print ("Download url link : "+download_link)	
					downloadFile(download_link, category, agentHeader, proxy)
			urlQueue.task_done()

	except Exception as err:
		writeError(link,"Error while thread downloading :"+str(err))			
		
# Get download link from redirect link
def getDownloadLink(url,  agentHeader, proxy):
				
	try :
		content= requests.get(url, headers = agentHeader, proxies=proxy).text
		match = re.findall(r'(data-dl-url=(?s)(.*)data-product-id=)', content)

		if match:
			download_link = ''
			for text in match:

				download_link = str(text[1])
				download_link = download_link.replace(" ", "")
				download_link = download_link.replace("\'", "")
				
				# filter itunes, android market and other download source
				if 'http://files.downloadnow.com' in download_link:
					return download_link
				else :
					writeError(download_link,"Uninted url :")		

					print ("Uninted url : "+download_link)
					return ''
		else: 
			writeError(url,"No download link :")
			print ("Download Link bulunamadı : "+url)
			return ''

	except Exception as err:
		writeError(download_link,"Error, while getting donwnload link :"+str(err))		

# Download files
def downloadFile(url, category, agentHeader, proxy):

	try :

		local_filename  = url.split('=')[-1]
		if not os.path.isfile(category+os.sep+local_filename):
			#print ("File name : "+local_filename)

			session 	= requests.session()
			size 		= requests.head(url).headers['Content-Length']
			#print ("File size : "+size)	

			if (int(size) < length_limit):
				response 	= session.get(url, headers=agentHeader, proxies=proxy)	
	
				if response.status_code == 200:
					print ("Downloading file : "+local_filename)
					with open(category+os.sep+local_filename,"wb") as outputfile:
						for chunk in response.iter_content():
							outputfile.write(chunk)
					print ("Downloading completed : "+local_filename+"\n")
				else :
					writeError(url,"Response : "+str(response.status_code))
			else :
				writeError(url,"Can't downloaded because of big size.")
		else :
			# Rename and download closed
			'''
			suffix = "_"+str(random.randrange(0, 100000000))
			filename, file_extension = os.path.splitext(local_filename)
			local_filename = filename+suffix+file_extension 
			'''
			writeError(url,"There is file with same name.")

	except Exception as err:
		writeError(url,"Can't downloaded because of big size."+str(err))		
	
def isDuplicateLink(url):

	with open('links.txt') as file:
		for line in file:
			if url in line:	
				print ("Duplicate url : "+url)		
				return True			
	
	with open('links.txt', "a+") as file:
		file.write(url+"\n")
		return False


def writeError(url, error):
	with open('log.txt', "a+") as logfile:				
		print (error)
		logfile.write(url+"\n"+error)
	
if __name__ == '__main__':
	# Proxy 
	proxy = {
		    'user' : '', # proxy username
		    'pass' : '', # proxy password
		    'host' : "", # proxy host (Kullanılmayacaksa boş bırak)
		    'port' : 8080 # proxy port
		}
	
	# Set variables
	proxy['host'] 	= "5.196.218.190" # Sample proxy sunuxu address
	user_agent  	= UserAgent()
	agentHeader 	= {'User-Agent': user_agent.random}

	searchKeywordList = ["security", "browsers", "biz-soft", "chat-voip-email", "desktop-enhancements", "developers", 				"digitalphoto", "drivers", "education", "entertainment", "games", "design", "home", "internet", "ios", 				"audio", "networking", "productivity", "customization", "travel", "video", "utilities"] 

	length_limit	= 10485760 # 10485760 Byte = 10 Megabyte upper limit for download. Don't download big file from 10 Mb.

	run(searchKeywordList, agentHeader, proxy)



