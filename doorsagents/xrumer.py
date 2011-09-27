# coding=utf8
import os, shutil, datetime, time, codecs, kwk8, agent, common, win32gui
from xml.sax.saxutils import escape

class XrumerAgent(agent.BaseAgent):
    ''' Параметры (см. методы GetTaskDetails и SetTaskDetails):
    Входные: baseNumber, baseNumberDest, nickName, realName, password, emailAddress, emailPassword, 
    emailLogin, emailPopServer, subject, snippetsFile, spamLinksList, niche.
    Выходные: successCount, halfSuccessCount, failsCount, profilesCount, rBaseLinksCount.
    
    Два режима работы: 1 - создание базы R из сырой базы, 2 - спам по базе R.'''
    
    def _Settings(self):
        '''Настройки'''
        self.appFolder = 'c:\\work\\xrumer707'
        self.appFolderControl1 = 'c:\\work\\control1'
        self.appFolderControl2 = 'c:\\work\\control2'
        self.appCaption = 'XRumer 7.07 Elite, Copyright BotmasterRu.Com, Support ICQ 876975, Administration e-mail botmaster@bk.ru'
        self.appCaptionControl = 'Control of permanent running'
        self.appConfigFile = os.path.join(self.appFolder, 'config.ini')
        self.appSettingsFile = os.path.join(self.appFolder, 'xuser.ini')
        self.appScheduleFile = os.path.join(self.appFolder, 'schedule.xml')
        self.appSettingsControl1File = os.path.join(self.appFolderControl1, 'control.ini')
        self.appSettingsControl2File = os.path.join(self.appFolderControl2, 'control.ini')
        self.doneScript = 'C:\\Work\\doorscenter\\doorsagents\\xrumer-done.bat'
        self.snippetsFolder = 'C:\\Work\\snippets'
        self.snippetsFile = os.path.join(self.snippetsFolder, self.currentTask['snippetsFile'])
        if self.currentTask['type'] == 'XrumerBaseR':  # mode 1
            self.projectName = 'ProjectR%d' % self.currentTask['id']
            self.subjectsFile = os.path.join(self.appFolder, 'Keys', 'Subjects%d.txt' % self.currentTask['baseNumberDest'])
        if self.currentTask['type'] == 'SpamTask':  # mode 2
            self.projectName = 'ProjectS%d' % self.currentTask['id']
            self.subjectsFile = os.path.join(self.appFolder, 'Keys', 'Subjects%d.txt' % self.currentTask['baseNumber'])
        self.projectFile = os.path.join(self.appFolder, 'Projects', self.projectName + '.xml')
        self.logFileTemplate = os.path.join(self.appFolder, 'Logs', self.projectName, '%s id%d.txt' % ('%s', self.currentTask['baseNumber']))
        self.logSuccess = self.logFileTemplate % 'Success'
        self.logHalfSuccess = self.logFileTemplate % 'Halfsuccess'
        self.logFails = self.logFileTemplate % 'Others'
        self.logProfiles = self.logFileTemplate % 'Profiles'
        self.logAnchors = self.logFileTemplate % 'Anchors'
        self.nicheAnchorsFile = os.path.join(self.appFolder, 'Anchors', '%s.txt' % self.currentTask['niche'])
        self.appLinksFolder = os.path.join(self.appFolder, 'Links')
        self.baseR1File = os.path.join(self.appLinksFolder, 'RLinksList id%d.txt' % self.currentTask['baseNumber'])
        self.baseR2File = os.path.join(self.appLinksFolder, 'RLinksList id%d.txt' % self.currentTask['baseNumberDest'])
        
        '''Содержимое файлов настроек'''
        self.appSettingsDictMode1 = {'OnlyRegistering': '0',
            'RegisteringPlusPosting': '0', 
            'FromRegistered': '0', 
            'AggressiveMode': '0', 
            'CheckForActiveLink': '0', 
            'EditProfileAfterLogin': '1', 
            'UploadAvatars': '0', 
            'EnableRefspam': '0', 
            'BBtoHTML': '1', 
            'PostNewMode': '1',
            'SchedulerEnabled': '1',
            'CurrentJob': '0'}
        self.appSettingsDictMode2 = {'OnlyRegistering': '0', 
            'RegisteringPlusPosting': '0', 
            'FromRegistered': '1', 
            'AggressiveMode': '0', 
            'CheckForActiveLink': '0', 
            'EditProfileAfterLogin': '0', 
            'UploadAvatars': '0', 
            'EnableRefspam': '0', 
            'BBtoHTML': '1', 
            'PostNewMode': '3',
            'SchedulerEnabled': '1',
            'CurrentJob': '0'}
        
        '''Файл проекта'''
        self.projectFileContents = '''<?xml version="1.0" encoding="UTF-8"?>
<XRumerProject>
  <PrimarySection>
    <ProjectName>%s</ProjectName>
    <NickName>%s</NickName>
    <RealName>%s</RealName>
    <Password>%s</Password>
    <EmailAddress>%s</EmailAddress>
    <EmailPassword>%s</EmailPassword>
    <EmailLogin>%s</EmailLogin>
    <EmailPOP>%s</EmailPOP>
    <Homepage></Homepage>
    <ICQ></ICQ>
    <City>#file_links[C:\Work\lists\cities-en.txt]</City>
    <Country>#file_links[C:\Work\lists\countries-en.txt]</Country>
    <Occupation></Occupation>
    <Interests></Interests>
    <Signature></Signature>
    <Gender>0</Gender>
    <UnknownFields></UnknownFields>
    <PollTitle></PollTitle>
    <PollOption1></PollOption1>
    <PollOption2></PollOption2>
    <PollOption3></PollOption3>
    <PollOption4></PollOption4>
    <PollOption5></PollOption5>
  </PrimarySection>
  <SecondarySection>
    <Subject1>#file_links[%s,1,N]</Subject1>
    <Subject2></Subject2>
    <PostText>#file_links[%s,7,S] %s #file_links[%s,1,N]</PostText>
    <Prior></Prior>
    <OnlyPriors>false</OnlyPriors>
  </SecondarySection>
</XRumerProject>
''' % (escape(self.projectName), escape(self.currentTask['nickName']), escape(self.currentTask['realName']), escape(self.currentTask['password']), 
       escape(self.currentTask['emailAddress']), escape(self.currentTask['emailPassword']), escape(self.currentTask['emailLogin']), 
       escape(self.currentTask['emailPopServer']), escape(self.subjectsFile), escape(self.snippetsFile), 
       escape(codecs.decode(' '.join(self.currentTask['spamLinksList']), 'cp1251')), escape(self.nicheAnchorsFile))
        
        '''Файл расписания'''
        self.appScheduleFileContents = '''<?xml version="1.0" encoding="UTF-8"?>
<body>
  <Schedule0>
    <PerformedTime></PerformedTime>
    <EventNum>2</EventNum>
    <EventParameter>%s</EventParameter>
    <JobNum>4</JobNum>
    <JobParameter>%s</JobParameter>
  </Schedule0>
  <Schedule1>
    <PerformedTime></PerformedTime>
    <EventNum>6</EventNum>
    <EventParameter></EventParameter>
    <JobNum>12</JobNum>
    <JobParameter></JobParameter>
  </Schedule1>
  <Schedule2>
    <PerformedTime></PerformedTime>
    <EventNum>6</EventNum>
    <EventParameter></EventParameter>
    <JobNum>5</JobNum>
    <JobParameter>%s</JobParameter>
  </Schedule2>
  <Schedule3>
    <PerformedTime></PerformedTime>
    <EventNum>6</EventNum>
    <EventParameter></EventParameter>
    <JobNum>10</JobNum>
    <JobParameter>%s</JobParameter>
  </Schedule3>
  <Schedule4>
    <PerformedTime></PerformedTime>
    <EventNum>6</EventNum>
    <EventParameter></EventParameter>
    <JobNum>1</JobNum>
    <JobParameter></JobParameter>
  </Schedule4>
  <Schedule5>
    <PerformedTime></PerformedTime>
    <EventNum>0</EventNum>
    <EventParameter></EventParameter>
    <JobNum>0</JobNum>
    <JobParameter></JobParameter>
  </Schedule5>
  <Schedule6>
    <PerformedTime></PerformedTime>
    <EventNum>6</EventNum>
    <EventParameter></EventParameter>
    <JobNum>13</JobNum>
    <JobParameter>%s</JobParameter>
  </Schedule6>
</body>
''' % ((datetime.datetime.now() + datetime.timedelta(0, 30)).strftime('%d.%m.%y %H:%M:%S'),  # 30 секунд на авторизацию 
       escape(self.projectName), '%d', self.currentTask['baseNumber'], escape(self.doneScript))
        self.appScheduleFileContentsMode1 = self.appScheduleFileContents % 0
        self.appScheduleFileContentsMode2 = self.appScheduleFileContents % 3
        
        '''Файл настроек control.exe'''
        self.appSettingsControl = '''[Settings]
ApplicationName=%s
Mode=%d
TimeRange=%d
'''
        
    def _CloseApp(self, appCaption):
        '''Закрытие приложения под Windows по заголовку окна'''
        p = win32gui.FindWindow(None, appCaption)
        win32gui.SendMessage(p, 0x10, 0, 0)
    
    def _FilterBaseR(self):
        '''Фильтрация базы R'''
        logTemp = self.logFileTemplate % 'Temporary'
        with open(logTemp, 'w') as fd:
            for line in open(self.logSuccess, 'r'):
                fd.write(line)
            for line in open(self.logHalfSuccess, 'r'):
                fd.write(line)
        kwk8.Kwk8Links(self.baseR1File).SelectByFile(logTemp).Save(self.baseR1File)
        os.unlink(logTemp)
        
    def _ActionOn(self):
        self._Settings()
        '''Установка настроек'''
        if self.currentTask['type'] == 'XrumerBaseR':  # mode 1
            threadsCount = 110
            timeRange = 120
            with open(self.appScheduleFile, 'w') as fd:
                fd.write(self.appScheduleFileContentsMode1)
            common.ModifyIniFile(self.appSettingsFile, self.appSettingsDictMode1)
            with codecs.open(self.subjectsFile, 'w', 'cp1251') as fd:
                fd.write('\n'.join(self.currentTask['subjectsList']))
            if os.path.isfile(self.baseR1File):  # удаляем существующую базу R
                try:
                    os.remove(self.baseR1File)
                except Exception as error:
                    print('Cannot remove old base R: %s' % error)
        if self.currentTask['type'] == 'SpamTask':  # mode 2
            threadsCount = 160
            timeRange = 60
            with open(self.appScheduleFile, 'w') as fd:
                fd.write(self.appScheduleFileContentsMode2)
            common.ModifyIniFile(self.appSettingsFile, self.appSettingsDictMode2)
        with open(self.appConfigFile, 'r') as fd:
            config = fd.readlines()
        config[3] = '%d\n' % threadsCount  # число потоков
        config[8] = 'ON\n'  # автопродолжение
        with open(self.appConfigFile, 'w') as fd:
            fd.writelines(config)
        with codecs.open(self.projectFile, 'w', 'utf8') as fd:
            fd.write(self.projectFileContents)
        with open(self.appSettingsControl1File, 'w') as fd:
            fd.write(self.appSettingsControl % (os.path.join(self.appFolder, 'xpymep.exe'), 0, timeRange))
        with open(self.appSettingsControl2File, 'w') as fd:
            fd.write(self.appSettingsControl % (os.path.join(self.appFolder, 'xpymep.exe'), 1, timeRange))
        '''Если анкоров по нише нет, создаем пустой файл'''
        if not os.path.exists(self.nicheAnchorsFile):
            with open(self.nicheAnchorsFile, 'w') as fd:
                fd.write('')
        '''Запуск приложений'''
        self._RunApp(os.path.join(self.appFolder, 'xpymep.exe'))
        time.sleep(3)
        self._RunApp(os.path.join(self.appFolderControl1, 'control.exe'))
        time.sleep(1)
        self._RunApp(os.path.join(self.appFolderControl2, 'control.exe'))
        return True

    def _ActionOff(self):
        self._Settings()
        '''Значения по умолчанию'''
        self.currentTask['successCount'] = 0
        self.currentTask['halfSuccessCount'] = 0 
        self.currentTask['failsCount'] = 0 
        self.currentTask['profilesCount'] = 0
        self.currentTask['rBaseLinksCount'] = 0
        '''Закрытие приложений'''
        self._CloseApp(self.appCaptionControl)
        time.sleep(1)
        self._CloseApp(self.appCaptionControl)
        time.sleep(3)
        self._CloseApp(self.appCaption)
        '''Копирование базы R'''
        if self.currentTask['type'] == 'XrumerBaseR':  # mode 1
            try:
                shutil.copyfile(self.baseR1File, self.baseR2File)
            except Exception as error:
                print('Cannot copy the new base R: %s' % error)
        '''Копирование анкоров'''
        try:
            shutil.copyfile(self.logAnchors, self.nicheAnchorsFile)
        except Exception as error:
            print('Cannot copy anchors: %s' % error)
        '''Фильтрация базы R по успешным и полууспешным'''
        if self.currentTask['type'] == 'SpamTask':  # mode 2
            try:
                if kwk8.Kwk8Links(self.logFails).Count() > 700:
                    self._FilterBaseR()
            except Exception as error:
                print('Cannot filter new base R: %s' % error)
        '''Выходные параметры'''
        self.currentTask['spamLinksList'] = []
        try:
            self.currentTask['successCount'] = kwk8.Kwk8Links(self.logSuccess).Count()
        except Exception as error:
            print('Cannot count success links: %s' % error)
        try:
            self.currentTask['halfSuccessCount'] = kwk8.Kwk8Links(self.logHalfSuccess).Count()
        except Exception as error:
            print('Cannot count halfsuccess links: %s' % error)
        try:
            self.currentTask['failsCount'] = kwk8.Kwk8Links(self.logFails).Count()
        except Exception as error:
            print('Cannot count fails links: %s' % error)
        try:
            self.currentTask['profilesCount'] = kwk8.Kwk8Links(self.logProfiles).Count()
        except Exception as error:
            print('Cannot count profiles links: %s' % error)
        try:
            self.currentTask['rBaseLinksCount'] = kwk8.Kwk8Links(self.baseR1File).Count()
        except Exception as error:
            print('Cannot count base R links: %s' % error)
        return True

if __name__ == '__main__':
    agent = XrumerAgent('http://searchpro.name/doorscenter/doorsadmin', 3)
