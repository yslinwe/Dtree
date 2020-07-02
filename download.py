# -*- coding: utf-8 -*-
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
from queue import Queue
from bypy import ByPy
import signal
from upload import upload_test
import datetime
b = Bilibili()
videolist = []
new_videos = []
title = ''
flag_upload = False
description_names = ""
flag_have_start = True
flag_haved_vd = True
flag_haved_d = True 
flag_haved_upload = True 
numberOftime = 0
#获取文件的大小,结果保留两位小数，单位为MB'''
def get_FileSize(filePath):
    fsize = os.path.getsize(filePath)
    fsize = fsize/float(1024*1024)
    return round(fsize,2)

def writeFile(fileName,starttime):
    # 打开文件
    fd = os.open(fileName,os.O_RDWR|os.O_CREAT)
    # 写入字符串
    global numberOftime
    numberOftime = os.write(fd,starttime.encode())
    os.close(fd)

def readFile(fileName):
    # 打开文件
    fd = os.open(fileName,os.O_RDWR)
        
    # 读取文本
    ret = os.read(fd,numberOftime)
    # 关闭文件
    os.close(fd)
    return ret.decode('utf-8')
def popen(cmd,roomid,achorname,targeturl,platform):
    time = 1
    flag_getdanmu = True
    flag_startdanmu = False #防止未开播录制弹幕
    
    p = subprocess.Popen(cmd, shell =True,stdout=subprocess.PIPE, bufsize=1)
    for line in iter(p.stdout.readline, b''):
        outstr = str(line,'utf-8')
        
        #match2 = re.findall(r"当前没有在直播",outstr)
        #print(match)
        #if len(match)>0:
        print(achorname,outstr)
        match1 = re.findall(r"下载停止",outstr)
        match2 = re.findall(r"liveStatus\s- (.+)\s",outstr)
        match3 = re.findall(r"文件大小或录制时长超过阈值(.+)\s",outstr)
        if len(match2)>0:
            global flag_upload
            global flag_haved_vd
            global flag_haved_d
            global flag_haved_upload
            if match2[0].strip() == "1":
                flag_upload = False
                flag_have_start = True
                flag_haved_vd = True
                flag_haved_d = True
                flag_haved_upload = True
                startTime = datetime.datetime.now().strftime('%Y-%m-%d-%H') + '时'
                writeFile("startime.txt",startTime)
                if flag_getdanmu:
                    cmd1 = 'node ./huyadanmudouyu/huya.js '+roomid+' ./danmu '+achorname+"_"+"P"+str(time)
                    time = time + 1
                    p1 = subprocess.Popen(cmd1, shell =True,stdout=subprocess.PIPE, preexec_fn = os.setpgrp ,bufsize=1)
                    print(achorname,' danmu录制')
                    p1.stdout.close()
                    flag_getdanmu = False
                    flag_startdanmu = True
            else: 
                time = 0
                flag_upload = True
        if flag_getdanmu and flag_startdanmu:
            cmd1 = 'node ./huyadanmudouyu/huya.js '+roomid+' ./danmu '+achorname+"_"+"P"+str(time)
            time = time + 1
            p1 = subprocess.Popen(cmd1, shell =True,stdout=subprocess.PIPE, preexec_fn = os.setpgrp ,bufsize=1)
            flag_startdanmu = False
            flag_getdanmu = False
        if len(match3)>0:
            if match3[0].strip() == '，重新尝试录制' and not flag_getdanmu:
                print(achorname,' 停止danmu录制')
                os.killpg(p1.pid,9)
                os.killpg(p.pid,9)
                flag_getdanmu = True
                flag_startdanmu = True
        if len(match1)>0:
            if match1[0].strip() == "下载停止" and not flag_getdanmu or match1[0].strip()=="SignalHandler is running":
                time = 0
                print(achorname,' 停止danmu录制')
                os.killpg(p1.pid,9)
                os.killpg(p.pid,9)
                flag_getdanmu = False
                flag_startdanmu = False

        if len(match1)>0:
            if match1[0].strip() == "下载停止" or match1[0].strip()=="SignalHandler is running":
                global description_names
                if platform=='huya':
                    description_names=huya_des(targeturl)
                elif platform == 'douyu':
                    description_names=douyu_des(targeturl)
                writeFile(achorname+"endTitle.txt",description_names)
                os.killpg(p.pid,9)
        
    p.stdout.close()
    p.wait()   
def uploadby(filedir,filename,flag):
    try:
        bp = ByPy()
        if flag:
            bp.mkdir(remotepath = filedir)
        filename = os.path.join('./danmu',filename)
        if os.path.exists(filename):
            bp.upload(localpath= filename, remotepath= filedir, ondup='overwrite')
            os.remove(filename)
    except:print('baidu up fail')
def baiduupload(flielist,achor_name):
    print(flielist)
    _flag = True
    bypyflag = True
    plist = []
    for f in flielist:
        if _flag:
            filedir = achor_name+'/'+f.split("_")[0]+'/'
            _flag = False
        pthreads = threading.Thread(target=uploadby,args=(filedir,f,bypyflag))
        pthreads.start()
        plist.append(pthreads)
        bypyflag = False
    for pl in plist:
        pl.join()
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

def cutvideo(achorname):
    path = os.getcwd()
    file_list = []
    
    for f in get_file_list(os.listdir('./download'),"download"):
        if f.endswith('flv') and f[0:len(achorname)] == achorname:
            file_list.append(f)
            fileofname=os.path.join('download',f)
            output_file = f
            newFilePath=os.path.join(path,output_file)
            shutil.move(fileofname, newFilePath)  # 移动
    return file_list
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
def get_file_list(dir_list,file_path):
    if not dir_list:
        return dir_list
    else:
        # 注意，这里使用lambda表达式，将文件按照最后修改时间顺序升序排列
        # os.path.getmtime() 函数是获取文件最后修改时间
        # os.path.getctime() 函数是获取文件最后创建时间
        dir_list = sorted(dir_list,  key=lambda x: os.path.getmtime(os.path.join(file_path, x)))
        # print(dir_list)
        return dir_list
def new_get_file_list(dir_list,file_path):
    if not dir_list:
        return dir_list
    else:
        dir_list = sorted(dir_list,  key=lambda x: float(x[:-4].split("-")[-2]))
        return dir_list
def transformvideo(file):
    #cmd1 = 'ffmpeg -y -i '+'"'+real_url+'"'+' -filter_complex "[0:1]asetpts,aresample=async=1000" -acodec mp3 -vcodec copy -loglevel quiet '+'"'+output_file+'"'
    try:
        outfile = file[:-4]+"temp"+".flv"
        out,err = (
        
            ffmpeg 
            .input(file) 
            .output(outfile,filter_complex ="[0:1]asetpts,aresample=async=1000", acodec = "mp3",vcodec = "copy") 
            .run(quiet = True,overwrite_output = True)
        )
        os.remove(file)
        os.rename(outfile,file)
    except:
        try:
            outfile = file[:-4]+"temp"+".flv"
            out,err = (
            
                ffmpeg 
                .input(file) 
                .output(outfile,filter_complex ="[1:0]asetpts,aresample=async=1000", acodec = "mp3",vcodec = "copy") 
                .run(quiet = True,overwrite_output = True)
            )
            os.remove(file)
            os.rename(outfile,file)
        except:
            pass
def uploadbilibili(USERNAME,PASSWORD,videos,platform,achor_name,rid):
    try:
        b = Bilibili()
        while True:
            try:
                r = b.login(USERNAME, PASSWORD)
                if r:
                    print('Bilibili登陆成功')
                    break
            except Exception as err:
                print('Bilibili登陆失败',err)
                time.sleep(60)
        print(videos)
        videolist = []
        for f in videos:
            transformvideo(f)
            videolist.append(VideoPart(f))
        tid = 71	#https://github.com/uupers/BiliSpider/wiki/视频分区对应表
        tag = ['直播回放']
        tag.append(achor_name)
        desc = '关注'+platform+achor_name+str(rid)+'\n如有问题，请联系删除。'
        source = 'https://www.'+platform+'.com/'+str(rid)
        b.upload(videolist, title, tid, tag, desc,source)
        print("Bilibili上传完成")
        for f in videos:
            os.remove(f)
    except Exception as err:
        print(err)

def job(targeturl,achorname,roomid,platform,description_names,timefilelist,USERNAME,PASSWORD):
    #timefilelist
    description_names = readFile(achorname+"endTitle.txt")
    if(description_names==""):
        description_names = huya_des(targeturl)
    global title
    title = achorname+'-'+readFile("startime.txt")+'-'+description_names
    #uploadbilibili(USERNAME,PASSWORD,timefilelist,platform,achorname,roomid)
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
def delete_danmu(achorname):
    for file in os.listdir('./danmu'):
        if file.endswith('LRC') and file.split("_")[2]==achorname:
            file_t=os.path.join('danmu',file) 
            s=os.path.getsize(file_t)
            if (s/1024)<=1: #单位为k
                os.remove(file_t)
def delete_video(achorname):
    for file in os.listdir('./download'):
        if file.endswith('flv') and file[0:len(achorname)] == achorname:
            file_t=os.path.join('download',file) 
            s=os.path.getsize(file_t)
            if (s/1024/1024)<1:
                os.remove(file_t)
def processs_task(targeturl,USERNAME,PASSWORD):
    vlq = Queue()
    danmu = Queue()
    
    allfilelist = []
    allfilelist_two = []
    timefilelist = []
    global flag_have_start
    global flag_haved_vd
    global flag_haved_d
    global flag_haved_upload
    platform = targeturl.split('.')[1]
    if platform == 'huya':
        print(targeturl)
        achorname,roomid = huya_message(targeturl)
    elif platform == 'douyu':
        print(targeturl)
        achorname,roomid = douyu_message(targeturl)
    p1 = threading.Thread()
    p2 = threading.Thread()
    while True:
        cmd = 'java -Dfile.encoding=utf-8 -jar BiliLiveRecorder.jar '+'"'+'fileSize=512&fileName={startTime}-{endTime}&timeFormat=HH:mm&liver='+platform+'&qn=-1&id='+roomid+'"'
        try:
            popen(cmd,roomid,achorname,targeturl,platform)
        except Exception as err: 
            print("下载出错:",err)
        
        #flag_upload作用是等待下載完全結束
        if flag_upload:
            if flag_haved_d:
                delete_danmu(achorname)
                lcrfile = [f for f in os.listdir('./danmu') if f.endswith('LRC') and f.split("_")[2]==achorname]
                if len(lcrfile)>0:
                    lcrfile=get_file_list(lcrfile,'./danmu')
                    baiduupload(lcrfile,achorname)
                else:flag_haved_d = False
            if flag_haved_vd:
                delete_video(achorname)
                file_list = cutvideo(achorname)#從download 文件夾移動文件到本目錄
                if len(file_list)>0:
                    timefilelist = get_file_list(file_list,'./')#按時間排序文件
                    #加入隊列
                    if len(timefilelist)>0 and flag_upload:
                        vlq.put(timefilelist)
                else:flag_haved_vd = False
        if p1.is_alive():
            print(achorname+'p1上传文件')
        if p2.is_alive():
            print(achorname+'p2上传文件')
        if flag_upload and not p1.is_alive() and vlq.qsize()>0 and not p2.is_alive():                                  
            p1 = threading.Thread(target=job,args=(targeturl,achorname,roomid,platform,description_names,vlq.get(),USERNAME,PASSWORD))
            p1.start()
            flag_have_start = False
        elif not p2.is_alive() and flag_haved_upload and not p1.is_alive():
            print("检查")
            videofile = [f for f in os.listdir('./') if f.endswith('flv') and f[0:len(achorname)] == achorname]
            flag_haved_upload = False
            if len(videofile)>0:
                videofile = new_get_file_list(videofile,'./')
                p2 = threading.Thread(target=job,args=(targeturl,achorname,roomid,platform,description_names,videofile,USERNAME,PASSWORD))
                p2.start()
                
        time.sleep(10)
        print(vlq.qsize())
def mkdir(path):
    # 引入模块
    import os
 
    # 去除首位空格
    #path=path.strip()
    # 去除尾部 \ 符号
    #path=path.rstrip("\\")
 
    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists=os.path.exists(path)
 
    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path) 
 
        print(path+' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        print(path+' 目录已存在')
        return False
if __name__ == '__main__':

    with open("config.yaml", "r") as yaml_file:
        yaml_obj = yaml.load(yaml_file.read(),Loader=yaml.FullLoader)
    global USERNAME
    global PASSWORD
    USERNAME = yaml_obj['USERNAME']
    PASSWORD = yaml_obj['PASSWORD']
    targeturl = yaml_obj['link']
    mkdir('./danmu')
    mkdir('./download')
    for target in targeturl:
        task = mp.Process(target=processs_task,args=(target,USERNAME,PASSWORD))
        task.start()
