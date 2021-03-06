# coding=utf8
import os, urllib2, pycurl, cStringIO, random, datetime, time, threading, Queue

#proxyListRawUrls = ['http://alexborisov.net/proxyc/list-all.txt', 'http://searchpro.name/tools/proxy-all.txt']
proxyListRawUrls = ['http://searchpro.name/tools/proxy.txt']
proxyCacheFile = 'proxies.txt'

googleQueryUrl = 'http://www.google.com/search?q=site:.%s&hl=en&safe=off&tbs=qdr:d'
googleSuccessStr = 'search tools</a>'
googleFailStr = 'unusual traffic from your computer'

class GoogleProxy(object):
    '''Прокси. Умеет получать данные с заданного адреса. Заточен под работу с гуглом.'''
    
    def __init__(self, type, address, timeout = 10):
        '''Инициализация'''
        self.type = type
        self.address = address
        self.timeout = timeout
        self.googleFails = 0
        self.googleAccess = True
        self.lastError = ''
    
    def __str__(self):
        '''Строковое представление'''
        return self.address
    
    def _Read(self, url):
        '''Читаем урл и возвращаем текст'''
        attemptsCount = 2
        for _ in range(attemptsCount):
            try:
                buf = cStringIO.StringIO()
                curl = pycurl.Curl()
                curl.setopt(pycurl.HTTPHEADER, ["Accept:"])
                curl.setopt(pycurl.FOLLOWLOCATION, 1)
                curl.setopt(pycurl.MAXREDIRS, 5)
                curl.setopt(pycurl.CONNECTTIMEOUT, self.timeout)
                curl.setopt(pycurl.TIMEOUT, self.timeout)
                if self.type == 'http':
                    curl.setopt(pycurl.PROXY, self.address)
                curl.setopt(pycurl.URL, url)
                curl.setopt(pycurl.WRITEFUNCTION, buf.write)
                curl.setopt(pycurl.USERAGENT, 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)')
                curl.perform()
                return buf.getvalue()
            except Exception as error:
                self.lastError = str(error)
        return ''
    
    def Request(self, query, maxFails = 5):
        '''Делаем запрос в гугл'''
        html = self._Read(googleQueryUrl % query)
        if (html != '') and (html.find(googleSuccessStr) < 0):
            self.googleFails += 1
        if (self.googleFails > maxFails) or (html.find(googleFailStr) >= 0):
            self.googleAccess = False
            '''if html.find(googleFailStr) < 0:
                print('Failed html: %s' % html)'''
        return html
        
class GoogleProxiesList(object):
    '''Список прокси под гугл'''
    
    def __init__(self):
        '''Инициализация'''
        self.proxyList = []
        self.LoadFromCache()
    
    def GetRandom(self):
        '''Возвращаем случайную прокси из списка'''
        return random.choice(self.proxyList)
        
    def LoadFromCache(self):
        '''Загружаем из кэша'''
        print('Loading proxies ...')
        self.proxyList = []
        if os.path.exists(proxyCacheFile):
            for line in open(proxyCacheFile):
                if line.strip() != '':
                    self.proxyList.append(GoogleProxy('http', line.strip()))
        print('Proxies: %d.' % len(self.proxyList))
        
    def SaveToCache(self):
        '''Пишем в кэш'''
        with open(proxyCacheFile, 'w') as fd:
            for proxy in self.proxyList:
                fd.write(proxy.address + '\n')

    def Update(self):
        '''Проверка прокси'''
        print('Updating proxies ...')
        dateTimeStart = datetime.datetime.now()
    
        '''Получаем сырые списки'''
        proxyListRawList = []
        for url in proxyListRawUrls:
            proxyListRawList.extend(urllib2.urlopen(url).read().splitlines())
        proxyListRawList = list(set(proxyListRawList))
        print('Proxies raw: %d.' % len(proxyListRawList))
    
        '''Проверка'''
        threadsCount = 100
        queueProxyRaw = Queue.Queue()
        queueProxyChecked = Queue.Queue()
        for line in proxyListRawList:
            if line.strip() != '':
                queueProxyRaw.put(GoogleProxy('http', line.strip()))
        GoogleProxiesCheckerMonitor(queueProxyRaw, queueProxyChecked).start()
        for _ in range(threadsCount):
            GoogleProxiesChecker(queueProxyRaw, queueProxyChecked).start()
        queueProxyRaw.join()
        
        '''Обработка результатов'''
        proxyListNew = []
        while not queueProxyChecked.empty():
            proxy = queueProxyChecked.get()
            proxyListNew.append(proxy)
            queueProxyChecked.task_done()
        self.proxyList = proxyListNew[:]
        self.SaveToCache()
    
        '''Статистика'''
        timeDelta = (datetime.datetime.now() - dateTimeStart).seconds
        print('Parsed %d of %d proxies in %d sec. (%.2f sec./proxy)' % (len(self.proxyList), len(proxyListRawList), timeDelta, timeDelta * 1.0 / len(proxyListRawList)))

class GoogleProxiesChecker(threading.Thread):
    '''Поточный чекер прокси'''

    def __init__(self, queueRaw, queueChecked):
        '''Инициализация'''
        threading.Thread.__init__(self)
        self.daemon = True
        self.queueRaw = queueRaw
        self.queueChecked = queueChecked

    def run(self):
        '''Обработка очередей'''
        while not self.queueRaw.empty():
            proxy = self.queueRaw.get()
            proxy.Request('"xxx"', 0)
            if proxy.googleAccess:
                self.queueChecked.put(proxy)
            self.queueRaw.task_done()

class GoogleProxiesCheckerMonitor(threading.Thread):
    '''Монитор чекера прокси'''
    
    def __init__(self, queue1, queue2):
        '''Инициализация'''
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue1 = queue1
        self.queue2 = queue2
        self.queue1InitialSize = self.queue1.qsize()
        
    def run(self):
        print('Monitoring started.')
        lastActionTime = time.time()
        while not self.queue1.empty():
            '''Каждые N секунд выводим текущую информацию'''
            if time.time() - lastActionTime > 5:
                print('... %d/%d (%.2f%%) => %d.' % ((self.queue1InitialSize - self.queue1.qsize()), self.queue1InitialSize, (self.queue1InitialSize - self.queue1.qsize()) * 100.0 / self.queue1InitialSize, self.queue2.qsize()))
                lastActionTime = time.time()
            time.sleep(1)
        print('Monitoring finished.')

if __name__ == '__main__':
    proxyList = GoogleProxiesList()
    proxyList.Update()
