#!/usr/bin/env python3

import os
import re
from bs4 import BeautifulSoup
from html2text import html2text, HTML2Text

listUser = [
    'river',
]

def procHTML(htmlDir,mdDir,htmlFileName):

    blogHTMLHead = '<html>'
    blogHTMLBody = '<html><hr/>'
    blogHTMLComment = '<html><hr/>'

    with open(htmlDir+htmlFileName, 'r', encoding='utf-8') as rf:
        html = rf.read()
        soup = BeautifulSoup(html, 'html.parser')

        for title in soup.find_all('h3', class_='title'):
            blogHTMLHead += str(title) + '\n'
        for category in soup.find_all('span', class_='pleft'):
            for child in category.find_all(class_='blogsep'):
                blogHTMLHead += str(child)
            for child in category.find_all('a'):
                blogHTMLHead += str(child)
        for count in soup.find_all('div', class_='editopbar'):
            for child in count.find_all('span', class_='fc07'):
                blogHTMLHead += '<br/>' + str(child) + '\n'
        blogHTMLHead = blogHTMLHead.replace('|', '<br/>')

        for content in soup.find_all('div', class_='nbw-blog'):
            blogHTMLBody += str(content) + '\n'

        for comment in soup.find_all('div', class_='comment'):
            for child in comment.find_all('span', class_='fc07'):
                blogHTMLComment += '<br/>' + str(child) + '\n'
            for child in comment.find_all('div', class_='cnt'):
                blogHTMLComment += str(child) + '\n'

    blogHTMLHead += '</html>'
    blogHTMLBody += '</html>'
    blogHTMLComment += '</html>'

    # print(blogHTMLHead)
    # print(blogHTMLBody)
    # print(blogHTMLComment)

    blogMD = ''
    h = HTML2Text()
    h.ignore_links = True
    blogMD += h.handle(blogHTMLHead)
    h.ignore_links = False
    blogMD += h.handle(blogHTMLBody)
    h.ignore_links = True
    blogMD += h.handle(blogHTMLComment)

    #print(blogMD)

    newMD = []
    flagLastEmpty = True
    for line in blogMD.split('\n'):
        if line.strip() == '':
            if flagLastEmpty:
                continue
            else:
                newMD.append(line)
                flagLastEmpty = True
        else:
            newMD.append(line)
            flagLastEmpty = False

    title = newMD[0].lstrip('#').strip()
    date = newMD[2].split()[0].strip()
    mdFileName = date+'_'+title+'.md'
    mdFileName = re.sub('[\/:*?"<>|]','-',mdFileName)
    with open(mdDir+mdFileName, 'w', encoding='utf-8') as wf:
        wf.write('\n'.join(newMD))

def checkDir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def main():
    htmldir = r'/save.{}/'
    mddir = r'/save.{}.md/'
    for username in listUser:
        hdir = os.getcwd() + htmldir.format(username)
        mdir = os.getcwd() + mddir.format(username)
        if not os.path.exists(hdir) :
            print('Dir Error!!')
            return
        checkDir(mdir)
        for htmlfilename in os.listdir(hdir):
            print(hdir+htmlfilename)
            procHTML(hdir,mdir,htmlfilename)


if __name__ == "__main__":
    main()
