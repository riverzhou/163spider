#!/usr/bin/env python3

import sys
import os

from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

#initialURL     = 'http://riverzhou2000.blog.163.com/blog/static/10540324820174112212778'
#initialURL     = 'https://ie.icoa.cn'
initialURL      = 'http://riverzhou2000.blog.163.com'
prefixCheck     = 'http://riverzhou2000.blog.163.com/blog/static/'

maxRetry        = 10
interVal        = 1
firstDelay      = 5

dictURLHistory  = {initialURL:maxRetry}
listURLTodo     = []

logFileName     = '163spider.log'
dirSave         = os.getcwd()+'/save/'

if not os.path.exists(dirSave):
    os.makedirs(dirSave)

def timeNow():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')

class WebEngineView(QWebEngineView):

    def __init__(self,mainwindow):
        super().__init__()
        self.mainwindow = mainwindow

        self.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)      #支持视频播放
        self.page().windowCloseRequested.connect(self.on_windowCloseRequested)     #页面关闭请求

    def on_windowCloseRequested(self):
        the_index = self.mainwindow.tabWidget.currentIndex()
        self.mainwindow.tabWidget.removeTab(the_index)

    def createWindow(self, QWebEnginePage_WebWindowType):
        new_webview = WebEngineView(self.mainwindow)
        self.mainwindow.create_tab(new_webview)
        return new_webview

class controlWindow(QDialog):

    def __init__(self, mainwindow):
        super().__init__()

        self.mainwindow     = mainwindow

        self.fLog = None
        self.initLog()

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

        self.btnStart = QToolButton()
        self.btnStart.setText('开始')
        self.btnStart.setObjectName('btnStart')

        self.btnStop = QToolButton()
        self.btnStop.setText('停止')
        self.btnStop.setObjectName('btnStop')

        self.layout.addWidget(self.textBrowser, 0, 0, 1, 9)
        self.layout.addWidget(self.btnStart, 1, 0)
        self.layout.addWidget(self.btnStop, 1, 1)


        QMetaObject.connectSlotsByName(self)

    def reject(self):
        self.mainwindow.close()
        super().reject()

    def initLog(self):
        global logFileName
        self.fLog = open(logFileName, 'a', encoding='utf-8')

    def logWrite(self, info):
        if self.fLog is not None:
            self.fLog.write(info)
            self.fLog.flush()

    def printf(self,mypstr):
        info = timeNow()+' =>| ' + mypstr+'\n'
        self.logWrite(info)
        self.textBrowser.setPlainText(self.textBrowser.toPlainText()+info)
        self.textBrowser.moveCursor(self.textBrowser.textCursor().End)  # 光标移到最后，这样就会自动显示出来
        QApplication.processEvents()  # 一定加上这个功能，不然有卡顿

    @pyqtSlot()
    def on_btnStart_clicked(self):
        self.printf('Start ...')
        self.mainwindow.flagStart = True
        self.mainwindow.webview.reload()

    @pyqtSlot()
    def on_btnStop_clicked(self):
        self.printf('Stop ...')
        self.mainwindow.flagStart = False

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.dictWebview = {}
        self.listTab     = []
        self.currentURL  = initialURL
        self.flagStart   = False
        self.count       = 0

        self.setWindowTitle('QWebEngine')
        self.showMaximized()
        #self.setWindowFlags(Qt.FramelessWindowHint)

        self.tabWidget = QTabWidget()
        #self.tabWidget.setTabShape(QTabWidget.Triangular)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setMovable(True)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.close_Tab)
        self.setCentralWidget(self.tabWidget)

        self.webview = WebEngineView(self)
        self.webview.loadFinished.connect(self.loadFinished)
        self.create_tab(self.webview)
        self.webview.load(QUrl(self.currentURL))

        self.control = controlWindow(self)
        self.control.show()

    def create_tab(self,webview):
        tab = QWidget()
        self.tabWidget.addTab(tab, "窗口")
        self.tabWidget.setCurrentWidget(tab)

        self.Layout = QHBoxLayout(tab)
        self.Layout.setContentsMargins(0, 0, 0, 0)
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
        global firstDelay
        if self.count == 0:
            sleep(firstDelay)
        self.webview.page().toHtml(self.procHTML)

    def procHTML(self, html):
        global listURLTodo, dictURLHistory, prefixCheck, maxRetry, interVal
        if not self.flagStart:
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
            if url.startswith(prefixCheck):
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
        else:
            dictURLHistory[self.currentURL] = -1
            self.count += 1
            self.control.printf('--- [{}]'.format(self.count))

        if len(listURLNew) > 0:
            listURLTodo += listURLNew

        if len(listURLTodo) == 0:
            self.control.printf('Todo List Empty !!!')
            return

        sleep(interVal)
        self.currentURL = listURLTodo[-1]
        listURLTodo.pop()
        self.webview.load(QUrl(self.currentURL))

    def save(self,html):
        global dirSave
        if not self.currentURL.startswith(prefixCheck):
            return
        filename = self.currentURL.split('static')[1].strip('/') + '.html'
        with open(dirSave+filename, 'w', encoding='utf-8') as f:
            f.write(html)

if __name__ == '__main__':
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
