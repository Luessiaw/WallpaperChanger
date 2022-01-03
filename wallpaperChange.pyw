from easygui import diropenbox,integerbox,boolbox # 简单对话框
from random import randint # 随机数
from os import listdir # 读取文件名
from os.path import join # 合并路径
from PIL.Image import open as openImage # 读取图片
from pystray import MenuItem,Icon # 托盘图标
from ctypes import windll # 设置壁纸的api
from apscheduler.schedulers.background import BackgroundScheduler # 定时任务
from datetime import datetime # 提供now()函数以即时触发任务
from configparser import ConfigParser # 读取参数

class WallpaperChanger:
    def __init__(self):
        self.initConfig() # 初始化参数
        self.setScheduler() # 设置调度器
        self.setIcon() # 设置托盘

    def initConfig(self):
        self.index = 0
        try:
            self.readConfig()
        except:
            self.config = None
            self.path = ''
            self.timeSep = 360
            self.random = False
            self.setConfig(setRandom=False) 
            # 为了方便，默认不开启随机

    def readConfig(self):
        # 读取参数
        print('读取参数...')

        self.config = ConfigParser()
        self.config.read('config.ini')

        self.path = self.config['DEFAULT']['path']
        print('图片路径: %s' % self.path)

        self.timeSep = self.config['DEFAULT'].getint('timeSep')
        print('时间间隔: %s' % self.displayMinute(self.timeSep))

        self.random = self.config['DEFAULT'].getboolean('random')
        print('随机: %s' % self.random)

    def setConfig(self,setPath=True,setTimeSep=True,setRandom=True):
        # 更改参数
        if setPath:
            path = ''
            while not path:
                path = diropenbox(msg='选择壁纸所在的文件夹',\
                    default=self.path)
            self.path = self.config['DEFAULT']['path'] = path
            print('图片路径设置为: %s' % path)

        if setTimeSep:
            timeSep = integerbox(msg='切换壁纸的时间间隔（分钟）',\
                title='输入时间间隔',default=self.timeSep,lowerbound=1,upperbound=43200)
                # 默认6个小时换一次。设置下限和上限。
            if timeSep:
                self.timeSep = timeSep
                self.config['DEFAULT']['timeSep'] = str(self.timeSep)
                print('时间间隔设置为: %s' % self.displayMinute(self.timeSep))

        if setRandom:
            self.random = not self.random
            # 通过勾选菜单来更改随机选择，只需要每次更改时取反即可
            self.config['DEFAULT']['random'] = str(self.random)
            print('随机设置为: %s' % self.random)
        
        with open('config.ini','w') as file:
            self.config.write(file)

    def setWallpaper(self):
        # 更改墙纸
        imgs = list(map(lambda img:join(self.path,img),listdir(self.path)))
        if self.random:
            self.index = randint(0,len(imgs)-1)
        else:
            self.index = (self.index+1) % len(imgs)
            # 取模运算实现数列循环
        img = imgs[self.index]
        windll.user32.SystemParametersInfoW(20,0,img,0)
        # 我没搞清这几个参数的作用
        print('壁纸已更改为：%s' % img)
    
    def displayMinute(self,minutes):
        # 由minutes选择合适的时间单位
        days=minutes//1440
        minutes=minutes%1440
        hours=minutes//60
        minutes=minutes%60

        output=''
        if days:
            output += '%d天' % days
        if hours:
            output += '%d小时' % hours
        if minutes:
            output += '%d分钟' % minutes

        return output

    def setScheduler(self):
        # 设置调度器
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        self.job = self.scheduler.add_job(func=self.setWallpaper,trigger='interval',minutes=self.timeSep)

    def setIcon(self):
        # 设置托盘
        def next():
            self.job.modify(next_run_time=datetime.now())

        def random():
            self.setConfig(False,False,True)

        def timeSep():
            self.setConfig(False,True,False)
            self.timeSepMenu = MenuItem('时间间隔: %s' % self.displayMinute(self.timeSep),timeSep)
            self.icon.menu = (self.nextMenu,self.randomMenu,self.timeSepMenu,self.pathMenu,self.exitMenu)
            # 更新菜单文本
            self.job.reschedule(trigger='interval',minutes=self.timeSep)
            # 更新任务

        def path():
            self.setConfig(True,False,False)
        
        def exit():
            if boolbox('确定退出吗？',choices=('是','否'),default_choice='否',cancel_choice='否'):
                self.stop()

        self.nextMenu = MenuItem('下一张',next)
        self.randomMenu = MenuItem('随机',random,checked=lambda item:self.random)
        self.timeSepMenu = MenuItem('时间间隔: %s' % self.displayMinute(self.timeSep),timeSep)
        self.pathMenu = MenuItem('文件路径',path)
        self.exitMenu = MenuItem('退出',exit)

        menu = (self.nextMenu,self.randomMenu,self.timeSepMenu,self.pathMenu,self.exitMenu)

        self.icon = Icon('',openImage('icon.ico'),'wallpaper changer',menu)

    def run(self):
        self.scheduler.start()
        self.icon.run()
    
    def stop(self):
        self.scheduler.shutdown()
        self.icon.stop()

if __name__ == '__main__':
    wallpaperChanger = WallpaperChanger()
    wallpaperChanger.run()
