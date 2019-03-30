#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Adapted by Coder-Alpha from Kodi Addon
# https://github.com/coder-alpha
#

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
#########################################################################################################

import re,urllib,urlparse,json,random,time,base64,cookielib,urllib2,sys
import HTMLParser

try:
	from resources.lib.libraries import control
	from resources.lib.libraries import cleantitle
	from resources.lib.libraries import client
	from resources.lib.libraries import testparams
	from resources.lib.libraries import workers
	from resources.lib import resolvers
	from resources.lib import proxies
except:
	pass

USER_AGENT = client.randomagent()

name = 'Einthusan'
loggertxt = []

class source:
	def __init__(self):
		del loggertxt[:]
		self.ver = '0.0.1'
		self.update_date = 'Mar. 28, 2019'
		log(type='INFO', method='init', err=' -- Initializing %s %s %s Start --' % (name, self.ver, self.update_date))
		self.init = False
		self.refreshCookies = False
		self.disabled = False
		self.base_link_alts = ['https://einthusan.tv']
		self.base_link = self.base_link_alts[0]
		self.MainPageValidatingContent = ['Welcome - Einthusan']
		self.type_filter = ['movie']
		self.ssl = False
		self.name = name
		self.headers = {'Origin','https://einthusan.tv','Referer','https://einthusan.tv/movie/browse/?lang=hindi','User-Agent',USER_AGENT}
		self.cookie = None
		self.loggertxt = []
		self.logo = 'https://i.imgur.com/c6OQEfL.png'
		self.speedtest = 0
		if len(proxies.sourceProxies)==0:
			proxies.init()
		self.proxyrequired = False
		self.msg = ''
		self.siteonline = self.testSite()
		self.testparser = 'Unknown'
		self.testparser = self.testParser()
		self.firstRunDisabled = False
		self.init = True
		self.initAndSleepThread()
		log(type='INFO', method='init', err=' -- Initializing %s %s %s End --' % (name, self.ver, self.update_date))
		
	def info(self):
		return {
			'url': self.base_link,
			'name': self.name,
			'msg' : self.msg,
			'speed': round(self.speedtest,3),
			'logo': self.logo,
			'ssl' : self.ssl,
			'frd' : self.firstRunDisabled,
			'online': self.siteonline,
			'online_via_proxy' : self.proxyrequired,
			'parser': self.testparser
		}
			
	def getLog(self):
		self.loggertxt = loggertxt
		return self.loggertxt
		
	def testSite(self):
		for site in self.base_link_alts:
			bool = self.testSiteAlts(site)
			if bool == True:
				return bool
				
		self.base_link = self.base_link_alts[0]
		return False
		
	def testSiteAlts(self, site):
		try:
			self.base_link = site
			if self.disabled:
				log('INFO','testSite', 'Plugin Disabled')
				return False
			x1 = time.time()
			http_res, content = request_einthusan(url=site)
			self.speedtest = time.time() - x1
			for valcon in self.MainPageValidatingContent:
				if content != None and content.find(valcon) >-1:
					log('SUCCESS', 'testSite', 'HTTP Resp : %s for %s' % (http_res,site))
					return True
			log('FAIL', 'testSite', 'Validation content Not Found. HTTP Resp : %s for %s' % (http_res,site))
			return False
		except Exception as e:
			log('ERROR','testSite', '%s' % e)
			return False
			
	def initAndSleepThread(self):
		if self.refreshCookies == False:
			return
		thread_i = workers.Thread(self.InitSleepThread)
		thread_i.start()

	def InitSleepThread(self):
		try:
			while self.init == True:
				tuid = control.id_generator(16)
				control.AddThread('%s-InitSleepThread' % self.name, 'Persists & Monitors Provider Requirements (Every 60 mins.)', time.time(), '4', True, tuid)
				time.sleep(60*60)
				self.siteonline = self.testSite()
				self.testparser = self.testParser()
				self.initAndSleep()
				control.RemoveThread(tuid)
		except Exception as e:
			log('ERROR','InitSleepThread', '%s' % e)
		control.RemoveThread(tuid)
			
	def initAndSleep(self):
		try:
			t_base_link = self.base_link
			self.headers = {'Origin','https://einthusan.tv','Referer','https://einthusan.tv/movie/browse/?lang=hindi','User-Agent',USER_AGENT}

			http_res, content = request_einthusan(url=t_base_link)
			log('SUCCESS', 'initAndSleep', 'Cookies : %s for %s' % (cookie,self.base_link))
		except Exception as e:
			log('ERROR','initAndSleep', '%s' % e)
		
	def testParser(self):
		try:
			if control.setting('Provider-%s' % name) == False:
				log('INFO','testParser', 'Plugin Disabled by User - cannot test parser')
				return False
			if control.setting('use_quick_init') == True:
				log('INFO','testParser', 'Disabled testing - Using Quick Init setting in Prefs.')
				return False
			if self.disabled == True:
				log('INFO','testParser', 'Plugin Disabled - cannot test parser')
				return False
			if self.siteonline == False:
				log('INFO', 'testParser', '%s is offline - cannot test parser' % self.base_link)
				return False
			for movie in testparams.test_movies:
				getmovieurl = self.get_movie(title=movie['title'], year=movie['year'], imdb=movie['imdb'])
				movielinks = self.get_sources(url=getmovieurl, testing=True)
				
				if movielinks != None and len(movielinks) > 0:
					log('SUCCESS', 'testParser', 'Parser is working')
					return True
					
			log('FAIL', 'testParser', 'Parser NOT working')
			return False
		except Exception as e:
			log('ERROR', 'testParser', '%s' % e)
			return False

	def get_movie(self, imdb, title, year, proxy_options=None, key=None):
		try:
			if control.setting('Provider-%s' % name) == False:
				log('INFO','get_movie','Provider Disabled by User')
				return None
			if self.siteonline == False:
				log('INFO','get_movie','Provider is Offline')
				return None
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except Exception as e: 
			log('ERROR', 'get_movie','%s: %s' % (title,e), dolog=self.init)
			return

	def get_show(self, imdb=None, tvdb=None, tvshowtitle=None, year=None, season=None, proxy_options=None, key=None):
		try:
			if control.setting('Provider-%s' % name) == False:
				log('INFO','get_show','Provider Disabled by User')
				return None
			if self.siteonline == False:
				log('INFO','get_show','Provider is Offline')
				return None
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except Exception as e: 
			log('ERROR', 'get_show','%s: %s' % (tvshowtitle,e), dolog=self.init)
			return

	def get_episode(self, url=None, imdb=None, tvdb=None, title=None, year=None, season=None, episode=None, proxy_options=None, key=None):
		try:
			if control.setting('Provider-%s' % name) == False:
				return None
			if url == None: return
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'],  url['season'], url['episode'], url['premiered'] = title, season, episode, year
			url = urllib.urlencode(url)
			return url
		except Exception as e: 
			log('ERROR', 'get_episode','%s: %s' % (title,e), dolog=self.init)
			return

	def get_sources(self, url, hosthdDict=None, hostDict=None, locDict=None, proxy_options=None, key=None, testing=False):
		try:
			sources = []
			if control.setting('Provider-%s' % name) == False:
				log('INFO','get_sources','Provider Disabled by User')
				log('INFO', 'get_sources', 'Completed')
				return sources
			if url == None: 
				log('FAIL','get_sources','url == None. Could not find a matching title: %s' % cleantitle.title_from_key(key), dolog=not testing)
				log('INFO', 'get_sources', 'Completed')
				return sources
			
			year = None
			episode = None
			season = None
			
			log('INFO','get_sources-1', 'data-items: %s' % url, dolog=False)
			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = cleantitle.get(title)
			try:
				year = re.findall('(\d{4})', data['premiered'])[0] if 'tvshowtitle' in data else data['year']
			except:
				try:
					year = data['year']
				except:
					year = None
			
			queries = ['%s+%s' % (title, year), title]
			rs = []
			
			for q in queries:
				page_count = 1
				search_url = self.base_link + '/movie/results/' + '?lang=hindi&page=' + str(page_count) + '&query=%s' % q
				log('INFO','get_sources-2', 'Searching: %s' % search_url)
				r, res = request_einthusan(search_url)

				try:
					movies = client.parseDOM(res, 'section', attrs = {'id': 'UIMovieSummary'})[0]
					movies = client.parseDOM(movies, 'li')

					for block in movies:
						try:
							blocka = client.parseDOM(block, 'div', attrs = {'class': 'block1'})[0]
							loc = self.base_link + client.parseDOM(blocka, 'a', ret='href')[0]
							poster = "http:" + client.parseDOM(blocka, 'img', ret='src')[0]
							titlex = client.parseDOM(block, 'h3')[0]
							yearx = client.parseDOM(block, 'div', attrs = {'class': 'info'})[0]
							yearx = client.parseDOM(yearx, 'p')[0]
							if str(year) in str(yearx):
								rs.append([titlex, yearx, loc, poster])
								log('INFO','get_sources-3', 'match-page-url: %s | %s' % (loc, titlex))
								break
						except:
							pass
					if len(rs) > 0:
						break
				except:
					pass

			if len(rs) > 0:
				links_m = []
				vidtype = 'Movie'
				riptype = 'BRRIP'
				quality = '720p'
				
				for r in rs:
					video_urls = []
					trailers = []
					music_vids = []
					poster = r[3]
					page_url = r[2]
					eindata1,htm = GetEinthusanData(page_url)
					eindata1 = json.loads(eindata1)
					video_urls.append(eindata1['MP4Link'])
					video_urls.append(eindata1['HLSLink'])
					
					if testing == False:
						try:
							matches = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+').findall(htm)
							matches=list(set(matches))
							for match in matches:
								try:
									if 'youtube.com' in match:
										match = match.replace('embed/','watch?v=')
										trailers.append(match)
								except:
									pass
						except Exception as e:
							log('FAIL','get_sources-4','%s' % e)
							
					if testing == False:
						try:
							musicblock = client.parseDOM(htm, 'section', attrs = {'id': 'UICompactMovieClipList'})[0]
							musicblock = client.parseDOM(musicblock, 'li')
							music_vids = []
							for block in musicblock:
								try:
									music_vids_s = []
									locx = self.base_link + client.parseDOM(block, 'a', attrs = {'class': 'title'}, ret='href')[0]
									thumbx = "http:" + client.parseDOM(block, 'img', ret='src')[0]
									titlex = client.parseDOM(block, 'a', attrs = {'class': 'title'})[0]
									titlex = client.parseDOM(titlex, 'h5')[0]
									eindata1,htm1 = GetEinthusanData(locx)
									eindata1 = json.loads(eindata1)
									music_vids_s.append(eindata1['MP4Link'])
									music_vids_s.append(eindata1['HLSLink'])
									music_vids.append([titlex,thumbx,music_vids_s,locx])
								except Exception as e:
									log('FAIL','get_sources-5A','%s : %s' % (e, locx))
						except Exception as e:
							log('FAIL','get_sources-5B','%s' % e)
					
					for vid in trailers:
						try:
							links_m = resolvers.createMeta(vid, self.name, self.logo, '720p', links_m, key, poster=poster, vidtype='Trailer', testing=testing, page_url=page_url)
						except:
							log('FAIL','get_sources-6','Could not add: %s' % vid)
							
					for vid in music_vids:
						try:
							for v in vid[2]:
								links_m = resolvers.createMeta(v, self.name, self.logo, '720p', links_m, key, poster=vid[1], vidtype='Music Video', testing=testing, txt=vid[0], page_url=vid[3])
						except:
							log('FAIL','get_sources-7','Could not add: %s' % v)
					
					for vid in video_urls:
						try:
							links_m = resolvers.createMeta(vid, self.name, self.logo, quality, links_m, key, poster=poster, riptype=riptype, vidtype=vidtype, testing=testing, page_url=page_url)
						except:
							log('FAIL','get_sources-8','Could not add: %s' % vid)
				
				sources += [l for l in links_m]
			
			if len(sources) == 0:
				log('FAIL','get_sources','Could not find a matching title: %s' % cleantitle.title_from_key(key))
			else:
				log('SUCCESS', 'get_sources','%s sources : %s' % (cleantitle.title_from_key(key), len(sources)))
				
			log('INFO', 'get_sources', 'Completed')
			
			return sources
		except Exception as e:
			log('ERROR', 'get_sources', '%s' % e)
			log('INFO', 'get_sources', 'Completed')
			return sources

	def resolve(self, url):
		try:
			return url
		except:
			return
			
def log(type='INFO', method='undefined', err='', dolog=True, logToControl=False, doPrint=True):
	try:
		msg = '%s: %s > %s > %s : %s' % (time.ctime(time.time()), type, name, method, err)
		if dolog == True:
			loggertxt.append(msg)
		if logToControl == True:
			control.log(msg)
		if control.doPrint == True and doPrint == True:
			print msg
	except Exception as e:
		control.log('Error in Logging: %s >>> %s' % (msg,e))


def decodeEInth(lnk):
	t=10
	#var t=10,r=e.slice(0,t)+e.slice(e.length-1)+e.slice(t+2,e.length-1)
	r=lnk[0:t]+lnk[-1]+lnk[t+2:-1]
	return r
	
def encodeEInth(lnk):
	t=10
	#var t=10,r=e.slice(0,t)+e.slice(e.length-1)+e.slice(t+2,e.length-1)
	r=lnk[0:t]+lnk[-1]+lnk[t+2:-1]
	return r
	
def request(url, cookieJar=None, post=None, timeout=20, headers=None, jsonpost=False, https_skip=False, output=None):

	time.sleep(1.0)
	
	cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
	
	if sys.version_info < (2, 7, 9): raise Exception()
	import ssl; ssl_context = ssl.create_default_context()
	ssl_context.check_hostname = False
	ssl_context.verify_mode = ssl.CERT_NONE
	if https_skip == True:
		opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
	else:
		opener = urllib2.build_opener(urllib2.HTTPSHandler(context=ssl_context), cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
	
	header_in_page=None
	if '|' in url:
		url,header_in_page=url.split('|')
	req = urllib2.Request(url)
	req.add_header('User-Agent',USER_AGENT)
	if headers:
		for h,hv in headers:
			req.add_header(h,hv)
	if header_in_page:
		header_in_page=header_in_page.split('&')
		
		for h in header_in_page:
			if len(h.split('='))==2:
				n,v=h.split('=')
			else:
				vals=h.split('=')
				n=vals[0]
				v='='.join(vals[1:])
				#n,v=h.split('=')
			#print n,v
			req.add_header(n,v)
			
	if jsonpost:
		req.add_header('Content-Type', 'application/json')
	response = opener.open(req,post,timeout=timeout)
	
	if output !=None and output=='responsecode':
		resp = str(response.getcode())
		return resp
	
	if response.info().get('Content-Encoding') == 'gzip':
			from StringIO import StringIO
			import gzip
			buf = StringIO( response.read())
			f = gzip.GzipFile(fileobj=buf)
			link = f.read()
	else:
		link=response.read()
	response.close()
	
	return link
	
def parseUrl(url):
	if 'none/' in url:
		id = url.split('none/')[1].split('/')[0]
	else:
		id = url.split('watch/')[1].split('/')[0]
	lang = url.split('lang=')[1]
	
	return id, lang
	
def requestWithHeaders(url, output=None):
	cookieJar = cookielib.LWPCookieJar()	
	headers=[('Origin','https://einthusan.tv'),('Referer','https://einthusan.tv/movie/browse/?lang=hindi'),('User-Agent',USER_AGENT)]
	htm=request(url,headers=headers,cookieJar=cookieJar,output=output)
	return htm
	
def request_einthusan(url):
	try:
		cookieJar = cookielib.LWPCookieJar()	
		headers=[('Origin','https://einthusan.tv'),('Referer','https://einthusan.tv/movie/browse/?lang=hindi'),('User-Agent',USER_AGENT)]
		htm=request(url,headers=headers,cookieJar=cookieJar)
		return 200, htm
	except:
		return 500, None

def GetEinthusanData(url, debug=False):
	
	try:
		htm = None
		id,lang = parseUrl(url)
		cookieJar = cookielib.LWPCookieJar()
		
		headers=[('Origin','https://einthusan.tv'),('Referer','https://einthusan.tv/movie/browse/?lang=hindi'),('User-Agent',USER_AGENT)]
		
		
		if 'none/' in url:
			mainurlajax='https://einthusan.tv/ajax/movie-clip/watch/music-video/none/%s/?lang=%s'%(id,lang)
			mainurl='https://einthusan.tv/movie-clip/watch/music-video/none/%s/?lang=%s'%(id,lang)
		else:
			mainurlajax='https://einthusan.tv/ajax/movie/watch/%s/?lang=%s'%(id,lang)
			mainurl='https://einthusan.tv/movie/watch/%s/?lang=%s'%(id,lang)
		
		htm=request(mainurl,headers=headers,cookieJar=cookieJar)
		
		#print htm

		lnk=re.findall('data-ejpingables=["\'](.*?)["\']',htm)[0]#.replace('&amp;','&')

		jdata='{"EJOutcomes":"%s","NativeHLS":false}'%lnk
		
		gid = re.findall('data-pageid=["\'](.*?)["\']',htm)[0]
		h = HTMLParser.HTMLParser()
		gid = h.unescape(gid).encode("utf-8")
		
		postdata={'xEvent':'UIVideoPlayer.PingOutcome','xJson':jdata,'arcVersion':'3','appVersion':'59','gorilla.csrf.Token':gid}
		postdata = urllib.urlencode(postdata)
		rdata=request(mainurlajax,headers=headers,post=postdata,cookieJar=cookieJar)
		
		r=json.loads(rdata)["Data"]["EJLinks"]
		data=(base64.b64decode(decodeEInth(r)))

		return data,htm
	except Exception as err:
		return "error-fail - code execution error - %s, url - %s" % (str(err), url), htm
 
	
def Test():
	url = 'https://einthusan.tv/movie/watch/9097/?lang=hindi'
	url = 'https://einthusan.tv/movie/watch/6mN3/?lang=hindi'
	url = 'https://einthusan.tv/movie-clip/watch/music-video/none/23WOz1IY5u/?lang=hindi'
	url = 'https://einthusan.tv/movie-clip/watch/music-video/none/23WOz1IY5u/?lang=hindi'
	d,d2 = GetEinthusanData(url=url)
	d = json.loads(d)
	print (d)

def Test2():
	url = 'https://einthusan.tv'
	d = requestWithHeaders(url=url)
	print (d)
	
#Test()