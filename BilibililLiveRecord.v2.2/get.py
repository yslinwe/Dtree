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

b = Bilibili()
videolist = []
new_videos = []
title = ''
flag_upload = False
#获取文件的大小,结果保留两位小数，单位为MB'''
def get_FileSize(filePath):
    fsize = os.path.getsize(filePath)
    fsize = fsize/float(1024*1024)
    return round(fsize,2)
def popen(cmd,roomid,achorname,targeturl,platform):
    flag_getdanmu = True
    file_part =''
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1)
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
            if match2[0].strip() == "1":
                flag_upload = False
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

    for f in os.listdir('./download'):
        if f.endswith('flv') and f[0:len(achorname)] == achorname:
            name = os.path.basename(f)
            MatchName = re.search(r"(\D.+)-(.+)\s(.+)\s(.+)\s(.+)-(.+)",name)
            global title
            title = achorname+'-'+MatchName.group(4).replace('-','.')+'.'+ MatchName.group(5).split('-')[0]+'-'+description_names
            break
    numID = 0
    for f in os.listdir('./download'):
        if f.endswith('flv') and f[0:len(achorname)] == achorname:
            print(achorname,f,'转码')
            file=os.path.join('download',f)
            outfile = f[:-4]+'-checked'+str(numID)+'.flv'
            numID=numID+1
            outfile=os.path.join('download',outfile)
            #cmd3 = 'ffmpeg -y -i '+'"'+file+'"'+' -filter_complex "[0:1]asetpts,aresample=async=1000" -acodec mp3 -vcodec copy '+'"'+outfile+'"'
            cmd2='java -Dfile.encoding=utf-8 -cp BiliLiveRecorder.jar nicelee.bilibili.live.FlvChecker '+'"'+file+'"' + ' true'
            '''
            try:
                return_info = subprocess.Popen(cmd3,stdout=subprocess.PIPE, bufsize=1)
                return_info.stdout.close()
                returncode = return_info.wait()
                if returncode:
                    raise subprocess.CalledProcessError(returncode, return_info)
            except:
            '''
            p2 = subprocess.Popen(cmd2,stdout=subprocess.PIPE, bufsize=1)
            p2.stdout.close()
            p2.wait()
            os.remove(file)
    numID = 0
    for f in os.listdir('./download'):
        if f.endswith('flv') and f[0:len(achorname)] == achorname:
            path = './download/'+achorname+'/'
            isExists=os.path.exists(path)
            if not isExists:
                os.makedirs(path)
 
            output_file = str(numID)+'.flv'
            numID = numID + 1 
            fileofname=os.path.join('download',f)
            newoutput_file=os.path.join('download',output_file) 
            os.rename(fileofname,newoutput_file)
            newFilePath=os.path.join(path,output_file)
            shutil.move(newoutput_file, newFilePath)  # 移动

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

def test_login(USERNAME,PASSWORD):
    r = b.login(USERNAME, PASSWORD)
    if not r:
        print("登陆失败")
    else:print('登陆成功')
    
def test_upload(achorname,roomid,targeturl):
    flag = True
    flag_start = True
    allfilelist = []

    videos = [f for f in os.listdir('download/'+achorname) if f.endswith('flv')]
    path = './download/'+achorname+'/'+title
    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        print(path,'创建成功')
    else:print(path,'已经存在')
    for f in videos:
        newFilePath=os.path.join(path,f)
        filepath = os.path.abspath('./download/'+achorname+'/' + f)
        shutil.move(filepath, newFilePath)  # 移动

    new_videos = [f for f in os.listdir(path) if f.endswith('flv')]
    def reverse_word(word):
        return int(word[:-4])
    new_videos_sorted =sorted(new_videos,key=reverse_word)
    print('上传文件',new_videos_sorted)
    for new_file in new_videos_sorted:
        new_files=os.path.join(path,new_file)
        videolist.append(VideoPart(new_files))
    tid = 21
    tag = ['直播回放']
    tag.append(achorname)
    desc = '关注'+achorname+roomid
    source = targeturl
    #cutlcr()
    b.upload(videolist, title, tid, tag, desc,source)
    for new_file in new_videos_sorted:
        new_files=os.path.join(path,new_file)
        os.remove(new_files)
    print('上传完成')
def job(targeturl,achorname,roomid,platform,description_names,USERNAME,PASSWORD):
    cutvideo(achorname,roomid,platform,description_names)
    test_login(USERNAME,PASSWORD)
    test_upload(achorname,roomid,targeturl)

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
    flag_haved_start = False

    platform = targeturl.split('.')[1]
    if platform == 'huya':
        print(targeturl)
        achorname,roomid = huya_message(targeturl)
    elif platform == 'douyu':
        print(targeturl)
        achorname,roomid = douyu_message(targeturl)
    path = './download/'+achorname
    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path)

    while True:
        cmd = 'java -Dfile.encoding=utf-8 -jar BiliLiveRecorder.jar '+'"'+'debug=false&check=true&fileSize=1024&liver='+platform+'&qn=0&retry=0&id='+roomid+'"'
        description_names=popen(cmd,roomid,achorname,targeturl,platform)
 
        flag_start = True

        for file in os.listdir('./download'):
            if file.endswith('flv') and file[0:len(achorname)] == achorname:
                file_t=os.path.join('download',file) 
                s=os.path.getsize(file_t)
                if (s/1024/1024)<1:
                    os.remove(file_t)
                else:allfilelist.append(file)
            if file.endswith('part') and file[0:len(achorname)] == achorname:
                flag_start = False
        if len(allfilelist)==0:
            flag_start = False
            flag_haved_start = False
            flag_with_file = False
        else:
            flag_with_file = True

        allfilelist.clear()
            
        for file in os.listdir('./download/'+achorname):
            if file.endswith('flv') and file[0:len(achorname)] == achorname:
                allfilelist_two.append(file)
        if len(allfilelist_two)>0 and flag_with_file:
            flag_start = False
        allfilelist_two.clear()

        if flag_with_file and flag_haved_start:
            flag_start = False

        if flag_upload and flag_start:
            p1 = mp.Process(target=job,args=(targeturl,achorname,roomid,platform,description_names,USERNAME,PASSWORD))
            p1.start()
            flag_haved_start = True
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
