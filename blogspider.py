#!/usr/bin/env python3

import sys
import os

from datetime import datetime
from bs4 import BeautifulSoup

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

flagShow = False

listUser = [
'riverzhou2000',
'hshwh212',
'erxianzhongren',
'qingzhuwuyan',
'wsszzh1a',
'ghjiaz0226',
'a4367007',
]

#initialURL     = 'https://ie.icoa.cn'
initialURL      = r'http://{}.blog.163.com/blog/'
prefixCheck     = r'http://{}.blog.163.com/blog/static/'
saveTag         = 'static'

maxRetry        = 20
interVal        = 0
loadDelay       = 1

dictURLHistory  = {}
listURLTodo     = []

logFileName     = r'163spider.{}.log'
dirSave         = os.getcwd()+r'/save.{}/'

def timeNow():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')

class WebEngineView(QWebEngineView):

    def __init__(self,mainwindow):
        super().__init__()
        self.mainwindow = mainwindow
        #self.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)      #支持视频播放
        self.page().windowCloseRequested.connect(self.on_windowCloseRequested)     #页面关闭请求

    def on_windowCloseRequested(self):
        the_index = self.mainwindow.tabWidget.currentIndex()
        self.mainwindow.tabWidget.removeTab(the_index)

    def createWindow(self, QWebEnginePage_WebWindowType):
        new_webview = WebEngineView(self.mainwindow)
        self.mainwindow.create_tab(new_webview)
        return new_webview

class controlWindow(QDialog):

    def __init__(self):
        super().__init__()

        self.initialURL     = ''
        self.prefixCheck    = ''
        self.logFileName    = ''
        self.dirSave        = ''
        self.username       = ''
        self.fLog           = None
        self.listLog        = []

        self.resize(800,600)
        self.setWindowTitle('Control')
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.textBrowser = QTextEdit()
        self.textBrowser.setFocusPolicy(Qt.NoFocus) 
        self.textBrowser.setObjectName('textBrowser')

        self.selectBox = QComboBox()
        self.selectBox.addItems(listUser)

        self.btnInit = QToolButton()
        self.btnInit.setText('初始')
        self.btnInit.setObjectName('btnInit')

        self.btnStart = QToolButton()
        self.btnStart.setText('开始')
        self.btnStart.setObjectName('btnStart')

        self.btnStop = QToolButton()
        self.btnStop.setText('停止')
        self.btnStop.setObjectName('btnStop')

        self.layout.addWidget(self.textBrowser, 0, 0, 1, 9)
        self.layout.addWidget(self.selectBox, 1, 0)
        self.layout.addWidget(self.btnInit, 1, 1)
        self.layout.addWidget(self.btnStart, 1, 2)
        self.layout.addWidget(self.btnStop, 1, 3)

        self.mainwindow = MainWindow(self)

        QMetaObject.connectSlotsByName(self)

    def reject(self):
        self.mainwindow.close()
        super().reject()

    def initUser(self):
        self.initialURL     = initialURL.format(self.username).rstrip('/')
        self.prefixCheck    = prefixCheck.format(self.username)
        self.logFileName    = logFileName.format(self.username)
        self.dirSave        = dirSave.format(self.username)

        dictURLHistory[self.initialURL] = maxRetry

        self.initLog()
        self.checkDir()

    def checkDir(self):
        if not os.path.exists(self.dirSave):
            os.makedirs(self.dirSave)

    def initLog(self):
        self.fLog = open(self.logFileName, 'a', encoding='utf-8')

    def closeLog(self):
        if self.fLog is not None:
            self.fLog.close()

    def logWrite(self, info):
        if self.fLog is not None:
            self.fLog.write(info)
            self.fLog.flush()

    def printf(self,mypstr):
        if len(self.listLog) > 1000:
            self.listLog = self.listLog[100:]
        info = timeNow()+' =>| '+ mypstr+'\n'
        self.logWrite(info)
        self.listLog.append(info)
        self.textBrowser.setPlainText(''.join(self.listLog))
        self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 光标移到最后，这样就会自动显示出来
        QApplication.processEvents()  # 一定加上这个功能，不然有卡顿

    @pyqtSlot()
    def on_btnInit_clicked(self):
        self.printf('Init ...')
        self.username = self.selectBox.currentText()
        self.printf('Current User is {}'.format(self.username))
        self.initUser()
        self.mainwindow.initLoad()

    @pyqtSlot()
    def on_btnStart_clicked(self):
        self.printf('Start ...')
        self.mainwindow.startCrawl()

    @pyqtSlot()
    def on_btnStop_clicked(self):
        self.printf('Stop ...')
        self.mainwindow.stopCrawl()

class MainWindow(QMainWindow):

    def __init__(self, control):
        super().__init__()

        self.control = control

        self.dictWebview = {}
        self.listTab     = []
        self.currentURL  = ''
        self.initialURL  = ''
        self.prefixCheck = ''
        self.dirSave     = ''
        self.flagStart   = False
        self.count       = 0
        self.bgTimer     = QTimer(self)

        if flagShow:
            self.setWindowTitle('QWebEngine')
            self.showMaximized()
            #self.setWindowFlags(Qt.FramelessWindowHint)

        self.tabWidget = QTabWidget()
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setMovable(True)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.close_Tab)
        self.setCentralWidget(self.tabWidget)

        self.webview = WebEngineView(self)
        self.webview.loadFinished.connect(self.loadFinished)
        self.create_tab(self.webview)

    def stopCrawl(self):
        self.flagStart = False

    def startCrawl(self):
        self.flagStart = True
        self.loadFinished()

    def initLoad(self):
        self.initialURL = self.control.initialURL
        self.currentURL = self.control.initialURL
        self.prefixCheck = self.control.prefixCheck
        self.dirSave    = self.control.dirSave
        self.webview.load(QUrl(self.currentURL))

    def create_tab(self,webview):
        tab = QWidget()
        self.tabWidget.addTab(tab, "窗口")
        self.tabWidget.setCurrentWidget(tab)

        self.Layout = QHBoxLayout(tab)
        self.Layout.setContentsMargins(0, 0, 0, 0)
        if flagShow:
            self.Layout.addWidget(webview)

        self.dictWebview[tab] = webview
        self.listTab.append(tab)

    def close_Tab(self,index):
        if self.tabWidget.count()>1:
            self.tabWidget.removeTab(index)
            self.dictWebview.pop(self.listTab[index])
            self.listTab.pop(index)
        else:
            self.close()

    def loadFinished(self):
        #self.control.printf('loadFinished')
        global maxRetry, dictURLHistory, loadDelay
        self.bgTimer.singleShot((maxRetry - dictURLHistory[self.currentURL] + 1 ) * loadDelay * 1000, self.getHTML)

    def getHTML(self):
        #self.control.printf('getHTML')
        self.webview.page().toHtml(self.procHTML)

    def procHTML(self, html):
        global listURLTodo, dictURLHistory, prefixCheck, maxRetry, interVal
        if not self.flagStart:
            self.control.printf('Initial Page Loaded or Stopped.')
            return
        self.save(html)
        self.control.printf('= '+self.currentURL)

        listURLNew = []
        listURLAll = []
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a'):
            url = str(link.get('href'))
            if url is None:
                continue
            url = url.rstrip('/')
            #self.control.printf('* '+url)
            if url.startswith(self.prefixCheck):
                listURLAll.append(url)
                if url not in dictURLHistory:
                    listURLNew.append(url)
                    dictURLHistory[url] = maxRetry
                    self.control.printf('+ '+url)
                else:
                    self.control.printf('- '+url)

        if len(listURLAll) == 0:
            self.control.printf('No URL in Page ! Remain Retry: {}'.format(dictURLHistory[self.currentURL]))
            if dictURLHistory[self.currentURL] > 0:
                dictURLHistory[self.currentURL] -= 1
                listURLTodo.insert(0,self.currentURL)
            self.control.printf('---')
        else:
            dictURLHistory[self.currentURL] = -1
            self.control.printf('--- [{}]'.format(self.count))
            self.count += 1

        if len(listURLNew) > 0:
            listURLTodo += listURLNew

        if len(listURLTodo) == 0:
            self.control.printf('Todo List Empty !!!')
            return

        self.currentURL = listURLTodo[-1]
        listURLTodo.pop()
        self.webview.load(QUrl(self.currentURL))

    def save(self,html):
        global dirSave
        if not self.currentURL.startswith(self.prefixCheck):
            return
        filename = self.currentURL.split(saveTag)[1].strip('/') + '.html'
        with open(self.dirSave+filename, 'w', encoding='utf-8') as f:
            f.write(html)

if __name__ == '__main__':
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    a = QApplication(sys.argv)
    w = controlWindow()
    w.show()
    sys.exit(a.exec_())
