import random
import unittest
import os
import shutil
from bilibiliupload import *
import ffmpeg
import subprocess
import re
import multiprocessing as mp
import time
from bs4 import BeautifulSoup
import requests
import yaml
import signal
import sys
import threading
from upload import upload_test
b = Bilibili()
videolist = []
new_videos = []
title = ''
flag_upload = False
flag_haved_start =True
#获取文件的大小,结果保留两位小数，单位为MB'''
def get_FileSize(filePath):
    fsize = os.path.getsize(filePath)
    fsize = fsize/float(1024*1024)
    return round(fsize,2)
def popen(cmd,roomid,achorname,targeturl,platform):
    flag_getdanmu = True
    file_part =''
    p = subprocess.Popen(cmd, shell =True,stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        outstr = str(line,'utf-8')
        
        #match2 = re.findall(r"当前没有在直播",outstr)
        #print(match)
        #if len(match)>0:
        print(achorname,outstr)
        match1 = re.findall(r"下载停止",outstr)
        match2 = re.findall(r"liveStatus\s- (.+)\s",outstr)
        if len(match2)>0:
            global flag_upload
            global flag_haved_start
            if match2[0].strip() == "1":
                flag_upload = False
                flag_haved_start = True
            else: 
                flag_upload = True
                if platform=='huya':
                    description_names=huya_des(targeturl)
                elif platform == 'douyu':
                    description_names=douyu_des(targeturl)
                p.stdout.close()
                p.wait()   
                return description_names

        '''     
                if flag_getdanmu:
                    cmd1 = 'node ./huyaDanmu-master/huya.js '+roomid+' ./danmu wanzi'
                    p1 = subprocess.Popen(cmd1)
                    flag_getdanmu = False
        if len(match1)>0:
            if match1[0].strip() == "下载停止" and not flag_getdanmu:
                p1.kill()
        '''

def huya_des(target):
    req = requests.get(url = target)
    html = req.text
    bf = BeautifulSoup(html,'lxml')
    texts = bf.find_all('div',class_="host-title")
    return texts[0].text

def douyu_des(target):
    req = requests.get(url = target)
    html = req.text
    bf = BeautifulSoup(html,'lxml')
    texts = bf.find_all('div',class_="Title-headline")
    return texts[0].text

def cutvideo(achorname,roomid,platform,description_names):
    numID = 0
    path = os.getcwd()
    for f in os.listdir('./download'):
        if f.endswith('flv') and f[0:len(achorname)] == achorname:
            fileofname=os.path.join('download',f)
            output_file = f
            newFilePath=os.path.join(path,output_file)
            shutil.move(fileofname, newFilePath)  # 移动

def PFI(num):
    if num<10:
        return '0'+str(num)
    else: 
        return str(num)
def cutlcr():
    numoftime = 1
    for file in os.listdir('./danmu'):
        if file.endswith('LRC'):
            file_t=os.path.join('danmu',file) 
            s=os.path.getsize(file_t)
            if (s/1024)<=1: #单位为k
                os.remove(file_t)

    lcrfile = [f for f in os.listdir('./danmu') if f.endswith('LRC')]
    path = './danmu/'+title
    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path)

    for f in lcrfile:
        newFilePath=os.path.join(path,f)
        filepath = os.path.abspath('./danmu/' + f)
        shutil.move(filepath, newFilePath)  # 移动
    
def job(targeturl,achorname,roomid,platform,description_names,USERNAME,PASSWORD):
    cutvideo(achorname,roomid,platform,description_names)
    for f in os.listdir('./'):
        if f.endswith('flv') and f[0:len(achorname)] == achorname:
	        name = os.path.basename(f)
	        MatchName = re.search(r"(\D.+)-(.+)\s(.+)\s(.+)\s(.+)-(.+)",name)
	        global title
	        title = achorname+'-'+MatchName.group(4).replace('-','.')+'.'+ MatchName.group(5).split('-')[0]+'-'+description_names
	        break
    print(title)
    upload_test(achorname,targeturl,title,USERNAME,PASSWORD)

def huya_message(targeturl):
    req = requests.get(url = targeturl)
    html = req.text
    bf = BeautifulSoup(html,'lxml')
    achorname = bf.find_all('h3', class_ = 'host-name')[0].text
    roomid = bf.find_all('span', class_ = 'host-rid')[0].text 
    return achorname,roomid
def douyu_message(targeturl):
    req = requests.get(url = targeturl)
    html = req.text
    bf = BeautifulSoup(html,'lxml')
    achorname = bf.find_all('a', class_ = 'Title-anchorName')[0].text
    roomid = targeturl.split('/')[len(targeturl.split('/'))-1] 
    return achorname,roomid
def processs_task(targeturl,USERNAME,PASSWORD):
    allfilelist = []
    allfilelist_two = []

    platform = targeturl.split('.')[1]
    if platform == 'huya':
        print(targeturl)
        achorname,roomid = huya_message(targeturl)
    elif platform == 'douyu':
        print(targeturl)
        achorname,roomid = douyu_message(targeturl)

    while True:
        cmd = 'java -Dfile.encoding=utf-8 -jar BiliLiveRecorder.jar '+'"'+'debug=false&check=true&fileSize=1024&liver='+platform+'&qn=0&retry=0&id='+roomid+'"'
        description_names=popen(cmd,roomid,achorname,targeturl,platform)
        print(description_names)
        global flag_haved_start
        for file in os.listdir('./download'):
            if file.endswith('flv') and file[0:len(achorname)] == achorname:
                file_t=os.path.join('download',file) 
                s=os.path.getsize(file_t)
                if (s/1024/1024)<1:
                    os.remove(file_t)
        if flag_upload and flag_haved_start: 
            print(achorname+'上传文件')
            p1 = threading.Thread(target=job,args=(targeturl,achorname,roomid,platform,description_names,USERNAME,PASSWORD))
            p1.start()
            flag_haved_start = False
        time.sleep(10)

if __name__ == '__main__':

    with open("config.yaml", "r") as yaml_file:
        yaml_obj = yaml.load(yaml_file.read(),Loader=yaml.FullLoader)
    global USERNAME
    global PASSWORD
    USERNAME = yaml_obj['USERNAME']
    PASSWORD = yaml_obj['PASSWORD']
    targeturl = yaml_obj['link']
    
    for target in targeturl:
        task = mp.Process(target=processs_task,args=(target,USERNAME,PASSWORD))
        task.start()
