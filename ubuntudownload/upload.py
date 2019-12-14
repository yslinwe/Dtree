import json
import os,shutil
from selenium import webdriver
import selenium.common
import time
from slider import slider_cracker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# 10800 18000 4110
chromedrive_path = './chromedriver'
user_name = ''
pass_word = ''

class Upload(object):
    def __init__(self, title):
        self.title = title
        # self.date = date
        # self.url = url

    @property
    def file_list(self):
        file_list = []
        for file_name in os.listdir('.'):
            if self.title in file_name:
                file_list.append(file_name)
        file_list = sorted(file_list)
        return file_list

    @staticmethod
    def remove_filelist(file_list):
        #if not os.path.exists("直播录像"):
            #os.makedirs("直播录像")                #创建路径
        for r in file_list:
            os.remove(r)
            #shutil.move(r,"直播录像")          #移动文件
            #print('移动到直播录像-' + r)

    def filter_file(self):
        file_list = self.file_list
        if len(file_list) == 0:
            return False
        for r in file_list:
            file_size = os.path.getsize(r) / 1024 / 1024 / 1024
            if file_size <= 0.001:
                os.remove(r)
                print('过滤删除-' + r)
        file_list = self.file_list
        if len(file_list) == 0:
            print('视频过滤后无文件可传')
            return False
        for f in file_list:
            if f.endswith('.part'):
                os.rename(f, os.path.splitext(f)[0])
                print('%s存在已更名' % f)
        return True

    @staticmethod
    def assemble_videopath(file_list):
        root = os.getcwd()
        videopath = ''
        for i in range(len(file_list)):
            file = file_list[i]
            videopath += root + '/' + file + '\n'
        videopath = videopath.rstrip()
        return videopath

    @staticmethod
    def is_element_exist(driver, xpath):
        s = driver.find_elements_by_xpath(xpath=xpath)
        if len(s) == 0:
            print("元素未找到:%s" % xpath)
            return False
        elif len(s) == 1:
            return True
        else:
            print("找到%s个元素：%s" % (len(s), xpath))
            return False

    def upload(self, title_, file_list, link):
        while True:
            filename = 'bilibili.cookie'
            # title_ = self.r_title
            videopath = self.assemble_videopath(file_list)

            # service_log_path = "{}/chromedriver.log".format('/home')
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument("user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36'")
            driver = webdriver.Chrome(executable_path=chromedrive_path, chrome_options=chrome_options)
            # service_log_path=service_log_path)
            try:

                driver.get("https://www.bilibili.com")
                # driver.delete_all_cookies()
                if os.path.isfile(filename):
                    with open(filename) as f:
                        new_cookie = json.load(f)

                    for cookie in new_cookie:
                        # print(cookie)
                        driver.add_cookie(cookie)

                driver.get("https://member.bilibili.com/video/upload.html")

                # print(driver.title)
                self.add_videos(driver, title_, videopath)

                # js = "var q=document.getElementsByClassName('content-header-right')[0].scrollIntoView();"
                # driver.execute_script(js)

                cookie = driver.get_cookies()
                with open(filename, "w") as f:
                    json.dump(cookie, f)

                self.add_information(driver, link, title_)

                driver.find_element_by_xpath('//*[@class="upload-v2-container"]/div[2]/div[3]/div[5]/span[1]').click()
                # screen_shot = driver.save_screenshot('bin/1.png')
                # print('截图')
                time.sleep(3)
                upload_success = driver.find_element_by_xpath(r'//*[@id="app"]/div/div[3]/h3').text
                if upload_success == '':
                    driver.save_screenshot('err.png')
                    print('稿件提交失败，截图记录')
                    
                else:
                    print(upload_success)
                    self.remove_filelist(file_list)
                    break
                # print('稿件提交完成！')
                # print('%s提交完成！' % title_)
                
            except selenium.common.exceptions.NoSuchElementException:
                print('发生错误')
            # except selenium.common.exceptions.TimeoutException:
            #     logger.exception('超时')
            except selenium.common.exceptions.TimeoutException:
                print('准备更新cookie')
                # screen_shot = driver.save_screenshot('bin/1.png')
                WebDriverWait(driver, 10).until(
                    ec.presence_of_element_located((By.XPATH, r'//*[@id="login-username"]')))

                username = driver.find_element_by_xpath(r'//*[@id="login-username"]')
                username.send_keys(user_name)

                password = driver.find_element_by_xpath('//*[@id="login-passwd"]')
                password.send_keys(pass_word)
                
                driver.find_element_by_class_name("btn-login").click()
                # print('第四步')
                # try:
                cracker = slider_cracker(driver)
                cracker.crack()
                # except:
                #     logger.exception('出错')
                time.sleep(5)
                if driver.title == '投稿 - 哔哩哔哩弹幕视频网 - ( ゜- ゜)つロ 乾杯~ - bilibili':
                    cookie = driver.get_cookies()
                    print(cookie)
                    with open(filename, "w") as f:
                        json.dump(cookie, f)
                    print('更新cookie成功')
                else:
                    print('更新cookie失败')
                    time.sleep(10)
            finally:
                driver.quit()
                print('浏览器驱动退出')

    def add_videos(self, driver, title_, videopath):
        WebDriverWait(driver, 20).until(
            ec.presence_of_element_located((By.NAME, 'buploader')))
        upload = driver.find_element_by_name('buploader')
        # print(driver.title)
        # print(driver.title)
        upload.send_keys(videopath)  # send_keys
        print('开始上传' + title_)
        time.sleep(2)
        button = r'//*[@class="new-feature-guide-v2-container"]/div/div/div/div/div[1]'
        if self.is_element_exist(driver, button):
            sb = driver.find_element_by_xpath(button)
            sb.click()
            sb.click()
            sb.click()
            print('点击')
        while True:
            # info = driver.find_elements_by_xpath(
            #     '//*[@id="app"]/div[3]/div[2]/div[2]/div[2]/div/div/div[2]/div[2]')
            # print(info)
            info = driver.find_elements_by_class_name(r'item-upload-info')
            for t in info:
                # print(t)
                try:
                    if t.text != '':
                        print(t.text)
                except selenium.common.exceptions.StaleElementReferenceException:
                    print("selenium.common.exceptions.StaleElementReferenceException")

                # else:
                #     print('出问题啦')
            time.sleep(10)
            # text = driver.find_elements_by_xpath(
            #     '//*[@id="app"]/div[3]/div[2]/div[2]/div[2]/div/div/div[2]/div[2]/span')
            text = driver.find_elements_by_xpath(r'//*[@class="item-upload-info"]/span')
            aggregate = set()
            for s in text:
                if s.text != '':
                    aggregate.add(s.text)
                    print(s.text)
            # if text == 'Upload complete' or text == '上传完成':
            #     break

            if len(aggregate) == 1 and ('Upload complete' in aggregate or '上传完成' in aggregate):
                break
        print('上传%s个数%s' % (title_, len(info)))

    @staticmethod
    def add_information(driver, link, title_):
        # 点击模板
        driver.find_element_by_xpath(r'//*[@class="normal-title-wrp"]/div/p').click()
        driver.find_element_by_class_name(r'template-list-small-item').click()
        # driver.find_element_by_xpath(
        #     r'//*[@id="app"]/div[3]/div[2]/div[3]/div[1]/div[1]/div/div[2]/div[1]').click()
        # 输入转载来源
        input_o = driver.find_element_by_xpath(
            '//*[@class="upload-v2-container"]/div[2]/div[3]/div[1]/div[4]/div[3]/div/div/input')
        input_o.send_keys(link)
        # 选择分区
        # driver.find_element_by_xpath(r'//*[@id="item"]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/div[3]/div').click()
        # driver.find_element_by_xpath(r'//*[@id="item"]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[2]/div[2]/div[1]/div[3]/div[2]/div[6]').click()
        # 稿件标题
        title = driver.find_element_by_xpath(
            '//*[@class="upload-v2-container"]/div[2]/div[3]/div[1]/div[8]/div[2]/div/div/input')
        title.send_keys(Keys.CONTROL + 'a')
        title.send_keys(Keys.BACKSPACE)
        title.send_keys(title_)
        # js = "var q=document.getElementsByClassName('content-tag-list')[0].scrollIntoView();"
        # driver.execute_script(js)
        # time.sleep(3)
        # 输入相关游戏
        # driver.save_screenshot('bin/err.png')
        # print('截图')
        # text_1 = driver.find_element_by_xpath(
        #     '//*[@id="item"]/div/div[2]/div[3]/div[2]/div[2]/div[1]/div[5]/div/div/div[1]/div[2]/div/div/input')
        # text_1.send_keys('星际争霸2')
        # 简介
        text_2 = driver.find_element_by_xpath(
            '//*[@class="upload-v2-container"]/div[2]/div[3]/div[1]/div[12]/div[2]/div/textarea')
        text_2.send_keys('如有问题，请联系删除')

    def start(self, url,title):
        print("start")
        if self.filter_file():
            print('准备上传' + title)
            try:
                self.upload(title, self.file_list, link=url)
            except selenium.common.exceptions.WebDriverException:
                print('WebDriverException')
            # except :
            #     logger.exception('?')
def upload_test(achorname,url,title,USERNAME,PASSWORD):
    global user_name
    global pass_word
    user_name = USERNAME
    pass_word = PASSWORD
    print(user_name,pass_word)
    Upload(achorname).start(url,title)
