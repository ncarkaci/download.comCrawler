#!/usr/bin/env python
#
# Search download.com website and downlaod executables
#
# Firstly calculate paging, after that scrapy all link in pages
# Eliminate other OS and platform applications without windows
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


def run(search_keyword, agentHeader, proxy):
	
	main_url =  "http://download.cnet.com/s/"+search_keyword+"/windows/"	

	content= requests.get(main_url, headers = agentHeader,  proxies=proxy).text

	pattern = re.compile(r'<span\sclass=\"results-total\">\s(.*?)\s</span>')
	match 	= pattern.search(content).group()

	number_of_file 	= 	int(match.split()[3].replace(",",""))
	pageSize 		=	int(number_of_file/10) # Show 10 file in per page
    
	print ("For "+search_keyword+" "+str(number_of_file)+" file found on "+main_url)

	for pageNo in range(1,pageSize):
		page_url = main_url+"?page="+str(pageNo)
		downloadFilesInPage(page_url, agentHeader, proxy)


# Getting redirect links from page
def downloadFilesInPage(url, agentHeader, proxy):

	try:
		print ("Search page : "+url)
				 
		content= requests.get(url, headers = agentHeader,  proxies=proxy).text

		urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)

		urlQueue = queue.Queue()

		for link in urls:
			urlQueue.put(link)
				
		for thread in range(10):
			thread = Thread(target = downloadThread, args = (urlQueue,))
			thread.daemon = True
			thread.start()
			
		urlQueue.join()

	except Exception as err:
		with open('log.txt', "a+") as logfile:				
			print ("Hata : "+ str(err))
			logfile.write("Search result url : "+url+"\n"+"Hata : "+ str(err))

def downloadThread(urlQueue):
	
	while not urlQueue.empty():
		link = urlQueue.get()
		# New user agent for per download link
		user_agent  = UserAgent()
		agentHeader = {'User-Agent': user_agent.random}

		if link.endswith('.html') and (not isDuplicateLink(link.replace("\n", ""))):
			print ("Redirect url link : "+link)
			download_link = getDownloadLink(link,  agentHeader, proxy)
				
			if download_link != '':
				download_link = download_link.replace("\n", "")
				print ("Download url link : "+download_link)	
				downloadFile(download_link,  agentHeader, proxy)
		urlQueue.task_done()
		
# Get download link from redirect link
def getDownloadLink(url,  agentHeader, proxy):
				
	try :
		content= requests.get(url, headers = agentHeader, proxies=proxy).text
		match = re.findall(r'(data-dl-url=(?s)(.*)data-product-id=)', content)

		if match:
			for text in match:

				download_link = str(text[1])
				download_link = download_link.replace(" ", "")
				download_link = download_link.replace("\'", "")
				
				# filter itunes, android market and other download source
				if 'http://files.downloadnow.com' in download_link:
					return download_link
				else :
					print ("Uninted url : "+download_link)
					return ''
		else: 
			print ("Download Link bulunamadı : "+url)

	except Exception as err:
		with open('log.txt', "a+") as logfile:			
			print ("Hata : "+ str(err))
			print (download_link)	
			logfile.write("Download link : "+download_link+"\n"+"Hata : "+ str(err))

# Download files
def downloadFile(url,  agentHeader, proxy):

	local_filename  = url.split('=')[-1]
	if os.path.isfile(local_filename):
		suffix = "_"+str(random.randrange(0, 100000000))
		filename, file_extension = os.path.splitext(local_filename)
		local_filename = filename+suffix+file_extension 
	print ("File name : "+local_filename)

	session 	= requests.session()
	size 		= requests.head(url).headers['Content-Length']
	print ("File size : "+size)	

	length_limit	= 52428800 # 52428800 Byte = 50 Megabyte warn! make this dynamic parameter

	if (int(size) < length_limit):
		response 	= session.get(url, headers=agentHeader, proxies=proxy)	
	
		if response.status_code == 200:
			print ("Downloading file ...")
			with open(local_filename,"wb") as outputfile:
				for chunk in response.iter_content():
					outputfile.write(chunk)
			print ("Downloading completed \n")
		else :
			print ("Url : "+url)
			print ("Response : "+str(response.status_code))
			with open('log.txt',"a+") as logfile:
				logfile.write(str(response.status_code)+" "+url)
	else :
		print ("Can't downloaded because of size big ")
		with open('log.txt',"a+") as logfile:
			logfile.write("\n Can't downloaded because of size big "+"\n"+size+" "+url)
	
def isDuplicateLink(url):

	with open('links.txt') as file:
		for line in file:
			if url in line:	
				print ("Duplicate url : "+url)		
				return True			
	
	with open('links.txt', "a+") as file:
		file.write(url+"\n")
		return False

		
if __name__ == '__main__':
	# Proxy 
	proxy = {
		    'user' : '', # proxy username
		    'pass' : '', # proxy password
		    'host' : "", # proxy host (Kullanılmayacaksa boş bırak)
		    'port' : 8080 # proxy port
		}
	
	# Set variables
	proxy['host'] 	= "5.196.218.190" # Örnek proxy sunuxu adresi
	user_agent  	= UserAgent()
	agentHeader 	= {'User-Agent': user_agent.random}
 
	run(".exe",agentHeader, proxy)

