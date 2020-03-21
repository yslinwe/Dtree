#-*- coding:utf-8 -*-
import ffmpeg
import os
import yaml
import threading
import importlib
import time
import subprocess
from bypy import ByPy
import signal
from bilibiliupload import *
import logging
from concurrent.futures import  ThreadPoolExecutor
logging.basicConfig(filename='log.log',
                    filemode='w',##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    #a是追加模式，默认如果不写的话，就是追加模式
                    format='%(message)s',
                    level=logging.DEBUG)
# 字节bytes转化kb\m\g
def formatSize(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        logging.info("传入的字节格式不对")
        return "Error"

    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
           return True
        else:return False
# 字节bytes转化K\M\G
def format_size(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
        return "Error"
    if kb >= 1024:
        M = kb / 1024
        return M
    else:
        M = 0 
        return M
# 获取文件大小
def getDocSize(path):
    try:
        size = os.path.getsize(path)
        return formatSize(size)
    except Exception as err:
        logging.error(err)  
# 获取文件大小
def getDocSizeS(path):
    try:
        size = os.path.getsize(path)
        return format_size(size)
    except Exception as err:
        logging.error(err)  

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
        return file
    except:
        outfile = file[:-4]+"temp"+".flv"
        out,err = (
        
            ffmpeg 
            .input(file) 
            .output(outfile,filter_complex ="aresample=async=1000", acodec = "mp3",vcodec = "copy") 
            .run(quiet = True,overwrite_output = True)
        )
        os.remove(file)
        os.rename(outfile,file)
        return file
    else:
        try:
            outfile = file[:-4]+"temp"+".flv"
            out,err = (
            
                ffmpeg 
                .input(file) 
                .output(outfile,codec = "copy") 
                .run(quiet = True,overwrite_output = True)
            )
            os.remove(file)
            os.rename(outfile,file)
            return file
        except:
            os.remove(file)

def uploadbilibili(USERNAME,PASSWORD,videos,platform,achor_name,rid):
    try:
        b = Bilibili()
        r = b.login(USERNAME, PASSWORD)
        if r:
            logging.info('Bilibili登陆成功')
        else:
            logging.error('Bilibili登陆失败')
        logging.info(videos)
        videolist = []
        flag = True
        for f in videos:
            if flag:
                title = f[:-4]
                flag = False
        num_start = len(platform) + 1
        num_end = num_start + len(achor_name)
        videos = [f for f in os.listdir('./') if f.endswith('flv') and f[num_start:num_end] == achor_name]
        for f in videos:
            videolist.append(VideoPart(f))
        tid = 21
        tag = ['直播回放']
        tag.append(achor_name)
        desc = '关注'+achor_name+str(rid)
        source = 'https://www.'+platform+'.com/'+str(rid)
        b.upload(videolist, title, tid, tag, desc,source)
        logging.info("Bilibili上传完成")
        for f in videos:
            os.remove(f)
    except:logging.error("bilibili上传失败")

def uploadby(filedir,filename,flag):
    try:
        bp = ByPy()
        if flag:
            bp.mkdir(remotepath = filedir)
        # 上传某一文件到百度云网盘对应的远程文件夹
        # ondup中参数代表复制文件，默认值为'overwrite'，指定'newcopy'不会覆盖重复文件
        if os.path.exists(filename):
            bp.upload(localpath= filename, remotepath= filedir, ondup='overwrite')
            os.remove(filename)
    except:logging.info('上传百度云失败')
def baiduupload(videos,achor_name):
    _flag = True
    bypyflag = True
    plist = []
    for f in videos:
        if _flag:
            filedir = achor_name+'/'+f[:-4]
            _flag = False
        pthreads = threading.Thread(target=uploadby,args=(filedir,f,bypyflag))
        pthreads.start()
        plist.append(pthreads)
        bypyflag = False
    for pl in plist:
        pl.join()
    
def oversizeupload(videos,achor_name,rid,platform,upload_platform,USERNAME,PASSWORD):
    # videos = [f for f in os.listdir('./') if f.endswith('flv') and f[num_start:num_end] == achor_name]
    plist = [] 
    if upload_platform=="baiduyun":
        num_start = len(platform) + 1
        num_end = num_start + len(achor_name)
        if len(videos)>0:
            datatime = time.strftime('%Y-%m-%d',time.localtime(time.time()))
            print("##################################")
            print("          "+datatime+achor_name+'直播文件上传baiduyun')
            print("##################################")
            pthreads = threading.Thread(target=baiduupload,args=(videos,achor_name))
            pthreads.start()
            plist.append(pthreads)
        for pl in plist:
            pl.join()
        print("上传完成")
    elif upload_platform=="bilibili":
        num_start = len(platform) + 1
        num_end = num_start + len(achor_name)
        if len(videos)>0:
            datatime = time.strftime('%Y-%m-%d',time.localtime(time.time()))
            print("##################################")
            print(datatime+achor_name+'直播文件上传bilibili')
            print("##################################")
            pthreadsbilibili = threading.Thread(target=uploadbilibili,args=(USERNAME,PASSWORD,videos,platform,achor_name,rid))
            pthreadsbilibili.start()
            pthreadsbilibili.join()
      
def download(achor_name,rid,platform,upload_platform,USERNAME,PASSWORD,lock):
    moudule_platform = importlib.import_module('.'+platform,package='lib')
    
    flag_upload = True
    flag_print = True
    flag_overupload = True
    while True:

        flag = True
        try:
            real_url = moudule_platform.get_real_url(rid)
        except:print("无法录制")
        if len(real_url)>0:
            datatime = time.strftime('%Y-%m-%d %H %M %S',time.localtime(time.time()))
            output_file = platform+"-"+achor_name+"-"+datatime+'.flv'
            #-loglevel quiet
            
            cmd1 = 'ffmpeg -y -i '+'"'+real_url+'"'+' -codec copy -loglevel quiet '+'"'+output_file+'"'
            flag_upload = True
            try:
                return_info = subprocess.Popen(cmd1,shell = False,preexec_fn = os.setpgrp)
                print("111111111111111111")

                while True:
                    print("111111111111111111")
                    if flag_overupload:
                        num_start = len(platform) + 1
                        num_end = num_start + len(achor_name)
                        videos = [f for f in os.listdir('./') if f.endswith('flv') and f[num_start:num_end] == achor_name and f!=output_file]
                        sizeofoutfile = 0
                        for f in videos:
                            if f.endswith('flv') and f[num_start:num_end] == achor_name and f!=output_file:
                                sizeofoutfile = sizeofoutfile + int(getDocSizeS(f))
                        if sizeofoutfile>6000:
                            print("flag_overupload")
                            poversizeupload = threading.Thread(target=oversizeupload,args=(videos,achor_name,rid,platform,upload_platform,USERNAME,PASSWORD))
                            poversizeupload.start()
                            flag_overupload = False
                    else:
                        if not poversizeupload.isAlive():
                            flag_overupload = True  
                            print("aaaaaaaaaaaaaaaaaaaaa")
                    if return_info.poll() !=None: #结束
                        print("线程结束")
                        return_info.send_signal(signal.CTRL_BREAK_EVENT)
                        Ptransformvideo = threading.Thread(target=transformvideo,args=(output_file,))
                        Ptransformvideo.start()
                        flag = False
                        break
                    if getDocSize(output_file):
                        print("超过size")
                        return_info.send_signal(signal.CTRL_BREAK_EVENT)
                        Ptransformvideo = threading.Thread(target=transformvideo,args=(output_file,))
                        Ptransformvideo.start()
                        flag = False
                        break
                    else:
                        lock.acquire()
                        print("##################################")
                        print("          "+achor_name+'已开播,已录制'+str(getDocSizeS(output_file))+'M')
                        print("##################################")
                        lock.release()
                        time.sleep(8)
                    flag_upload =  os.path.exists(output_file)
                        

                returncode = return_info.wait()
                if returncode:
                    raise subprocess.CalledProcessError(returncode, return_info)
            except:
                logging.error('return_info fail')
        elif len(real_url) == 0:
            lock.acquire()
            print("##################################")
            print("          "+achor_name+'未开播')
            print("##################################")

            lock.release()
            if flag_upload:
                pthreadsbilibiliflag = True
                pthreadsflag = True
                if upload_platform=="baiduyun":
                    num_start = len(platform) + 1
                    num_end = num_start + len(achor_name)
                    videos = [f for f in os.listdir('./') if f.endswith('flv') and f[num_start:num_end] == achor_name]
                    if len(videos)>0:
                        datatime = time.strftime('%Y-%m-%d',time.localtime(time.time()))
                        print("##################################")
                        print(datatime+achor_name+'直播文件上传baiduyun')
                        print("##################################")
                       
                        # 百度网盘创建远程文件夹
                        _flag = True
                        bypyflag = True
                        for f in videos:
                            if _flag:
                                filedir = achor_name+'/'+f[:-4]
                                _flag = False
                            pthreads = threading.Thread(target=uploadby,args=(filedir,f,bypyflag))
                            pthreads.start()
                            bypyflag = False
                            time.sleep(1)
                            pthreadsflag=pthreads.is_alive()
                elif upload_platform=="bilibili":
                    num_start = len(platform) + 1
                    num_end = num_start + len(achor_name)
                    videos = [f for f in os.listdir('./') if f.endswith('flv') and f[num_start:num_end] == achor_name]
                   
                    if len(videos)>0:
                        datatime = time.strftime('%Y-%m-%d',time.localtime(time.time()))
                        print("##################################")
                        print(datatime+achor_name+'直播文件上传bilibili')
                        print("##################################")
                        pthreadsbilibili = threading.Thread(target=uploadbilibili,args=(USERNAME,PASSWORD,videos,platform,achor_name,rid))
                        pthreadsbilibili.start()
                        time.sleep(1)
                        pthreadsbilibiliflag=pthreadsbilibili.is_alive()
                else:
                    pass
                if not pthreadsbilibiliflag:
                    flag_upload =True
                elif not pthreadsflag:
                    flag_upload =True
                else:
                    flag_upload = False
        if flag:
            time.sleep(8)
def clearshell():
    while True:
        os.system("clear")
        time.sleep(10)
if __name__ == '__main__':

    lock = threading.Lock() #初始化一把锁
    pool = ThreadPoolExecutor(max_workers=5)
    try:
        with open("./config.yaml", "r",encoding='utf-8') as yaml_file:
            yaml_obj = yaml.load(yaml_file.read())
        
        USERNAME = yaml_obj['USERNAME']
        PASSWORD = yaml_obj['PASSWORD']

        for platform in list(yaml_obj.keys())[2:]:
            for massage in yaml_obj[platform]:
                achor_name = massage
                upload_platform = ''
                if len(yaml_obj[platform][massage])==2:
                    rid = yaml_obj[platform][massage][0]
                    upload_platform = yaml_obj[platform][massage][1]
                else:rid = yaml_obj[platform][massage][0]
                pool.submit(download, achor_name,rid,platform,upload_platform,USERNAME,PASSWORD,lock)
        pool.submit(clearshell)
        pool.close()
        pool.join()
    except Exception as err:
        print(err)
        time.sleep(10)
            
