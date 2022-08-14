'''
https://github.com/Sugobet/EVE_Get_MaNei

Sugobet
QQ: 321355478
qq群: 924372864
'''

import os
import time
import datetime
from PIL import Image
import cv2
from cnocr import CnOcr
import threading


path = 'C:/Users/sugob/Desktop/EVE_Get_MaNei'
devices = {'kuanggong1': '127.0.0.1:62001'}      # cmd输入adb devices查看模拟器地址
M = {
    '第一槽位': [920, 438],
    '第二槽位': [868, 438],
    '第三槽位': [814, 438],
    '第四槽位': [924, 495],
    '第五槽位': [868, 495],
    '第六槽位': [813, 495],
    '第七槽位': [762, 495],
}
high_cao = {'kuanggong1': [M['第一槽位']]}
low_cao = {'kuanggong1': [M['第二槽位'], M['第三槽位'], M['第四槽位'], M['第五槽位'], M['第六槽位'], M['第七槽位']]}


def IF_Img_I(src, mp):
    # w, h = mp.shape[::2]
    res = None
    try:
        res = cv2.matchTemplate(src,mp,cv2.TM_CCOEFF_NORMED)
    except Exception:
        return False, 0.999
    _, mac_v, _, _ = cv2.minMaxLoc(res)
    if mac_v < 0.99:
        return True, mac_v
    return False, mac_v


class Listening:
    def __init__(self, device_name: str, device_address: str, cnocr: CnOcr):
        self.device_name = device_name
        self.device_address = device_address

        self.ocr = cnocr

    
    def screenc(self):
        os.system(f'adb -s {self.device_address} exec-out screencap -p > {self.device_name}.png')


    def crop(self, x1, y1, x2, y2, img: Image.Image) -> Image.Image:
        try:
            newimg = img.crop((x1, y1, x2, y2))
        except Exception:
            return
        return newimg


    def IsInSpace(self, img: Image.Image):
        '''
        : 判断是否在太空
        '''
        status = self.crop(453, 511, 508, 526, img)
        if not status:
            return False

        res = self.ocr.ocr(status)
        for keys in res:
            if '米' in keys['text'] or '秒' in keys['text']:
                return True
        return False


    def IsAtSation(self, img: Image.Image):
        '''
        : 判断是否在空间站
        '''
        status = self.crop(877, 163, 941, 194, img)
        if not status:
            return False

        res = self.ocr.ocr(status)
        for keys in res:
            key: str = keys['text']
            key = key.replace(" ", "")
            if '离站' in key:
                return True
        return False

    
    def IsHaveKArea(self, img: Image.Image):
        '''
        : 判断矿区存在
        '''

        status = self.crop(260, 70, 704, 166, img)
        if not status:
            return True

        res = self.ocr.ocr(status)
        if res == []:
            return True
        for key in res:
            if '内没有可' in key['text']:
                return False
        return True


    def GetShipState(self, img: Image.Image):
        '''
        : 判断舰船状态
        : state -> 1 -> 准备跃迁
        : state -> 2 -> 跃迁至
        : state -> 3 -> 即将到达
        : state -> 4 -> 舰船正在停止
        '''
        if self.IsAtSation(img):
            return False, -1, ''

        status = self.crop(374, 394, 594, 414, img)
        if not status:
            return False, -1, ''

        res = self.ocr.ocr(status)
        if res == []:
            return False, -1, ''
        text = res[0]['text']
        if '准备' in text:
            return True, 1, '准备跃迁'
        if '跃迁至' in text:
            return True, 2, '跃迁至'
        if '即将到达' in text:
            return True, 3, '即将到达'
        if '停止' in text:
            return True, 4, '舰船正在停止'
        return False, -1, ''
    

    def FindBlueFuckShip(self, img: Image.Image):
        '''
        : 蓝加拦截 舰船监测
        '''
        status = self.crop(792, 51, 911, 316, img)
        if not status:
            return False

        res = self.ocr.ocr(status)
        if res == []:
            return False
        for key in res:
            if '拦截' in key['text']:
                tim = str(datetime.datetime.now()).replace(' ', '---')
                print(self.device_name, f'疑似蓝加拦截----------------{tim}')
                print(self.device_name, f'疑似蓝加拦截----------------{tim}')
                print(self.device_name, f'疑似蓝加拦截----------------{tim}')
                img.save(f'{path}/{self.device_name}_FUCK_BLUE_SHIP_{tim}.png')
                return True
        return False

    
    def IsMax(self, img: Image.Image):
        '''
        : 监测满仓
        '''
        status = self.crop(229, 89, 711, 171, img)
        if not status:
            return False

        res = self.ocr.ocr(status)
        if res == []:
            return False
        for key in res:
            if '满了' in key['text']:
                return True

        return False
    

    def LocalHaveEnemy(self, img: Image.Image):
        '''
        : 监测本地红白
        '''
        i1 = self.crop(82, 419, 116, 438, img)
        res = self.ocr.ocr(i1)
        if res == []:
            return False
        num = (res[0]['text']).replace('o', '0').replace('O', '0').replace('D', '0').replace('U', '0')
        if len(num) >= 2:
            return True
        if len(num) == 1 and num != '0':
            return True
        
        i1 = self.crop(144, 418, 177, 438, img)
        res = self.ocr.ocr(i1)
        if res == []:
            return False
        num = (res[0]['text']).replace('o', '0').replace('O', '0').replace('D', '0').replace('U', '0')
        if len(num) >= 2:
            return True
        if len(num) == 1 and num != '0':
            return True
        
        return False
        

class Command:
    def __init__(self, device_name, device_address, cnocr: CnOcr):
        self.device_name = device_name
        self.device_address = device_address
        self.ocr = cnocr

        self.adb = f'adb -s {self.device_address} '
    

    def screenc(self):
        os.system(f'adb -s {self.device_address} exec-out screencap -p > {self.device_name}.png')

    
    def crop(self, x1, y1, x2, y2, img) -> Image.Image:
        try:
            newimg = img.crop((x1, y1, x2, y2))
        except Exception:
            return
        return newimg


    def GetShipType(self):
        os.system(self.adb + 'shell input tap 46 21')
        time.sleep(0.5)
        os.system(self.adb + 'shell input tap 141 164')
        time.sleep(4)

        self.screenc()
        img = Image.open(f'{path}/{self.device_name}.png')

        state = self.crop(4, 164, 186, 198, img)
        if not state:
            return False, -1, ''
        os.system(self.adb + 'shell input tap 924 31')

        res = self.ocr.ocr(state)
        if res == []:
            return False, -1, ''
        text = res[0]['text']
        if '回旋' in text:
            return True, 1, '回旋者级'
        if '猎获' in text:
            return True, 2, '猎获级'
        if '妄想' in text:
            return True, 3, '妄想级'
        if '妄想级二' in text:
            return True, 4, '妄想级二型'
        if '逆' in text:
            return True, 5, '逆戟鲸级'
        
        return False, -1, ''
    

    def OutHome(self):
        os.system(self.adb + 'shell input tap 896 176')


    def PutK(self):
        os.system(self.adb + 'shell input tap 20 89')
        time.sleep(4)
        os.system(self.adb + 'shell input tap 86 77')

        self.screenc()
        img = Image.open(f'{path}/{self.device_name}.png')

        res = self.ocr.ocr(img)
        if res == []:
            return False
        for key in res:
            if '矿石舱' in key['text']:
                x = int(key['position'][0][0])
                y = int(key['position'][0][1])
                os.system(self.adb + f'shell input tap {str(x)} {str(y)}')
                break

        time.sleep(0.3)
        os.system(self.adb + 'shell input tap 734 487')
        time.sleep(0.3)
        os.system(self.adb + 'shell input tap 105 112')
        time.sleep(0.3)
        os.system(self.adb + 'shell input tap 427 120')
        time.sleep(3)
        os.system(self.adb + 'shell input tap 924 31')
        return True


    def SetHomePoint(self):
        os.system(self.adb + 'shell input tap 927 302')
        time.sleep(0.1)
        os.system(self.adb + 'shell input tap 21 146')
        time.sleep(0.3)
        os.system(self.adb + 'shell input tap 186 504')
        time.sleep(0.3)
        os.system(self.adb + 'shell input tap 302 258')
        time.sleep(0.3)
        os.system(self.adb + 'shell input tap 79 228')
        time.sleep(0.3)
        os.system(self.adb + 'shell input tap 301 199')
        time.sleep(0.3)
        os.system(self.adb + 'shell input tap 188 189')


    def GoToKAreaUp(self, img: Image.Image):
        res = self.ocr.ocr(img)
        if res == []:
            return False, -1, ''

        css = []
        sts = []
        std = []
        for key in res:
            if '集群' in key['text']:
                x = int(key['position'][0][0])
                y = int(key['position'][0][1])
                css.append([x, y])
                continue
            if '星群' in key['text']:
                x = int(key['position'][0][0])
                y = int(key['position'][0][1])
                sts.append([x, y])
                continue
            if '星带' in key['text']:
                x = int(key['position'][0][0])
                y = int(key['position'][0][1])
                std.append([x, y])
                continue
        
        if css != []:
            os.system(self.adb + f'shell input tap {str(css[0][0])} {str(css[0][1])}')
            return True, 1, '小行星集群'
        if sts != []:
            os.system(self.adb + f'shell input tap {str(sts[0][0])} {str(sts[0][1])}')
            return True, 2, '小行星群'
        if std != []:
            os.system(self.adb + f'shell input tap {str(std[0][0])} {str(std[0][1])}')
            return True, 3, '小行星带'
        
        return False, -1, ''
    

    def GoToKAreaDown(self, img: Image.Image):
        res = self.ocr.ocr(img)
        if res == []:
            return False

        for key in res:
            if '跃迁' in key['text']:
                x = int(key['position'][0][0])
                y = int(key['position'][0][1])
                os.system(self.adb + f'shell input tap {str(x)} {str(y)}')
                return True
        return False
    

    def RunK(self):
        '''
        : 接近矿石
        '''
        os.system(self.adb + 'shell input tap 799 20')
        time.sleep(0.5)
        os.system(self.adb + 'shell input tap 808 472')

        time.sleep(0.5)
        os.system(self.adb + 'shell input tap 824 65')
        time.sleep(0.5)
        os.system(self.adb + 'shell input tap 630 133')


    def ActHighCao(self, type: str):
        '''
        : 激活高槽
        '''
        os.system(self.adb + f'shell input tap 477 531')
        time.sleep(1)
        for lis in high_cao[self.device_name]:
            os.system(self.adb + f'shell input tap {lis[0]} {lis[1]}')
            time.sleep(0.5)
        if type == '逆戟鲸级':
            time.sleep(2)
            for lis in high_cao[self.device_name]:
                os.system(self.adb + f'shell input tap {lis[0]} {lis[1]}')
                time.sleep(0.5)


    def ToShipShow(self):
        '''
        : 总览切换至 舰船 标签
        '''
        os.system(self.adb + 'shell input tap 799 20')
        time.sleep(0.5)
        os.system(self.adb + 'shell input tap 808 146')


    def ToKShow(self):
        '''
        : 总览切换至 挖矿 标签
        '''
        os.system(self.adb + 'shell input tap 799 20')
        time.sleep(0.2)
        os.system(self.adb + 'shell input tap 817 414')
        time.sleep(0.2)
        os.system(self.adb + 'shell input tap 939 62')


    def GoHome(self):
        os.system(self.adb + 'shell input tap 21 147')


    def ActLowCao(self):
        '''
        : 激活低槽
        '''
        for lis in low_cao[self.device_name]:
            os.system(self.adb + f'shell input tap {lis[0]} {lis[1]}')
            time.sleep(0.01)


def Start(device_name, device_address, cnocr):
    des = ''
    is_waK = False
    listening = Listening(device_name, device_address, cnocr)
    command = Command(device_name, device_address, cnocr)
    # 检测本地红白、跑路
    # 在空间站内：检测舰船类型、离站、设置自动导航
    # 检测仓库满仓: 回家、放置矿石
    # 在矿区：检测蓝加拦截、接近矿石、激活高槽、总览切换至 舰船 列表
    # 在太空: 切换总览至 挖矿 、寻找矿区进入矿区、检测舰船状态、跃迁细节
    while True:
        listening.screenc()
        img = Image.open(f'{path}/{device_name}.png')
        dtm = datetime.datetime.now()
        state = listening.LocalHaveEnemy(img)
        # 检测本地红白
        if state:
            if listening.IsAtSation(img):
                print(device_name, '检测到本地有人---------------', dtm)
                continue
            command.GoHome()
            command.ActLowCao()
            print(device_name, '检测到本地有人---------------', dtm)
            while True:
                # 检测舰船状态
                listening.screenc()
                img = Image.open(f'{path}/{device_name}.png')
                _, _, des22 = listening.GetShipState(img)
                if des22 == '即将到达':
                    print(device_name, des22 + '空间站', dtm)
                    break
                time.sleep(1)
            continue

        # 在空间站内
        if listening.IsAtSation(img):
            listening.screenc()
            img = Image.open(f'{path}/{device_name}.png')
            s, _, des1 = command.GetShipType()
            print(des1)
            des = des1
            if not s:
                print(device_name, f'{des}  该船型暂不支持, {device_name} 暂停运行', dtm)
                return
            
            command.OutHome()
            while True:
                # 检测是否已出站
                listening.screenc()
                img = Image.open(f'{path}/{device_name}.png')
                if listening.IsInSpace(img):
                    break
                time.sleep(1)
            # 已出站
            print(device_name, '已出站')
            # 设置自动导航
            time.sleep(3)

            command.SetHomePoint()
            continue

        # 仓库满仓
        if listening.IsMax(img):
            print(device_name, '仓库满仓')
            command.GoHome()
            command.ActLowCao()

            while True:
                # 检测是否已进站
                listening.screenc()
                img = Image.open(f'{path}/{device_name}.png')
                if listening.IsAtSation(img):
                    time.sleep(3)
                    # 放置矿石
                    print(device_name, '放置矿石')
                    command.PutK()
                    break
                time.sleep(1)
            continue

        # 检测蓝加拦截舰船
        if listening.FindBlueFuckShip(img):
            command.GoHome()
            command.ActLowCao()

            while True:
                # 检测是否已进站
                listening.screenc()
                img = Image.open(f'{path}/{device_name}.png')
                if listening.IsAtSation(img):
                    print(device_name, '安全逃离----------', dtm)
                    print(device_name, '等待三分钟-----------', dtm)
                    time.sleep(90)
                    break
                time.sleep(1)
            continue

        # 在太空 & 挖矿  整合
        if listening.IsInSpace(img):
            # 整合     判断矿区消失
            if is_waK and listening.IsHaveKArea(img):
                continue
            print(device_name, '矿区消失')
            is_waK = False
            # 切换总览-挖矿
            command.ToKShow()
            # 寻找、进入矿区
            print(device_name, '寻找、进入矿区')
            listening.screenc()
            img = Image.open(f'{path}/{device_name}.png')
            _, _, des33 = command.GoToKAreaUp(img)
            print(des33)

            time.sleep(1)
            listening.screenc()
            img = Image.open(f'{path}/{device_name}.png')
            st = command.GoToKAreaDown(img)
            if not st:
                continue
            while True:
                # 检测舰船状态
                listening.screenc()
                _, index, des2 = listening.GetShipState(Image.open(f'{path}/{device_name}.png'))
                print(device_name, '检测舰船状态', des2)
                if index == 4:
                    print(device_name, '已进入矿区')
                    break
                time.sleep(1)
            if not is_waK:
                # 接近矿石
                print(device_name, '接近矿石')
                command.RunK()
                # 激活高槽
                print(device_name, '激活高槽')
                command.ActHighCao(des)
                # 切换总览-舰船
                print(device_name, '切换总览-舰船')
                command.ToShipShow()
                is_waK = True
            continue


if __name__ == '__main__':
    for key, val in devices.items():
        cnocr = CnOcr(rec_model_name='densenet_lite_136-gru')
        t = threading.Thread(target=Start, args=(key, val, cnocr))
        t.start()