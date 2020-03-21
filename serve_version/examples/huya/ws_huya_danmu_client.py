"""本代码参考了
https://github.com/BacooTang/huya-danmu
https://github.com/IsoaSFlus/danmaku
特此感谢。
"""
from typing import Optional
import re

from aiohttp import ClientSession

from danmu_abc import WsConn, Client
from .utils import WSUserInfo, WebSocketCommand, EWebSocketCommandType, WSPushMessage, MessageNotice
from .tars.core import tarscore
import datetime
import queue

def get_time_now(times):
    HH = times[:-4].split(":")[0]
    MM = times[:-4].split(":")[1]
    SS = times[:-4].split(":")[2].split(".")[0]
    MS = times[:-4].split(":")[2].split(".")[1]
    return int(HH),int(MM),int(SS),int(MS)
import time
def getStr(MM):
    if(MM<10):
       return '0'+str(MM)
    else: return str(MM)
def save(filename, contents):
      fh = open(filename, 'a+', encoding='utf-8')
      fh.write(contents)
      fh.close()
      

q = queue.Queue()


emots = {
    "/{wg":"[无辜]",
    "/{kiss":"[亲亲]",
    "/{ns"  :"[难受]",
    "/{hj"  : "[滑稽]",
    "/{dhl" : "[打呼噜]",
    "/{cfds" : "[单身狗]",
    "/{​cfds" : "[单身狗]",
    "/{cfdl" : "[超粉大佬]",
    "/{zj" : "[震惊]",
    "/{dx" : "[大笑]",
    "/{sh" : "[送花]",
    "/{tx" : "[偷笑]",
    "/{dk" : "[大哭]",
    "/{hh" : "[嘿哈]",
    "/{66" : "[666]",
    "/{gd" : "[感动]",
    "/{yw" : "[疑问]",
    "/{xh" : "[喜欢]",
    "/{jx" : "[奸笑]",
    "/{zan" : "[赞]",
    "/{ka" : "[可爱]",
    "/{am" : "[傲慢]",
    "/{kx" : "[开心]",
    "/{88" : "[拜拜]",
    "/{hx"  : "[害羞]",
    "/{zs"  : "[衰]",
    "/{pu"  : "[吐血]",
    "/{zc"  : "[嘴馋]",
    "/{sq"  : "[生气]",
    "/{fe"  : "[扶额]",
    "/{bz"  : "[闭嘴]",
    "/{kw"  : "[枯萎]",
    "/{xu"  : "[嘘]",
    "/{xk"  : "[笑哭]",
    "/{lh"  : "[流汗]",
    "/{bk"  : "[不看]",
    "/{hq"  : "[哈欠]",
    "/{tp"  : "[调皮]",
    "/{gl"  : "[鬼脸]",
    "/{cl"  : "[戳脸]",
    "/{dg"  : "[大哥]",
    "/{kun" : "[困]",
    "/{yb"  : "[拥抱]",
    "/{zt"  : "[猪头]",
    "/{kl"  : "[骷髅]",
    "/{cc"  : "[臭臭]",
    "/{xd"  : "[心动]",
    "/{dao" : "[刀]"
}

class WsDanmuClient(Client):
    def __init__(
            self, room: str, area_id: int,filename: str,
            session: Optional[ClientSession] = None, loop=None):
        heartbeat = 60.0
        conn = WsConn(
            url='wss://cdnws.api.huya.com',
            receive_timeout=heartbeat+10,
            session=session)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self.t1 = datetime.datetime.now()
        self._room = room
        self._filename = filename
        self._ayyuid = None
        self._topsid = None
        self._subsid = None
        self.flag = True
        self.flag2 = True
        self.last_msc = 0
        self._pack_heartbeat = b'\x00\x03\x1d\x00\x00\x69\x00\x00\x00\x69\x10\x03\x2c\x3c\x4c\x56\x08\x6f\x6e\x6c\x69\x6e\x65\x75\x69\x66\x0f\x4f\x6e\x55\x73\x65\x72\x48\x65\x61\x72\x74\x42\x65\x61\x74\x7d\x00\x00\x3c\x08\x00\x01\x06\x04\x74\x52\x65\x71\x1d\x00\x00\x2f\x0a\x0a\x0c\x16\x00\x26\x00\x36\x07\x61\x64\x72\x5f\x77\x61\x70\x46\x00\x0b\x12\x03\xae\xf0\x0f\x22\x03\xae\xf0\x0f\x3c\x42\x6d\x52\x02\x60\x5c\x60\x01\x7c\x82\x00\x0b\xb0\x1f\x9c\xac\x0b\x8c\x98\x0c\xa8\x0c'
    def checkemot(self,str):
        if(('/{') in str == False ): return str
        for key in emots: 
            str = str.replace(key, emots[key])
        return str

    async def _prepare_client(self) -> bool:
        url = f'https://m.huya.com/{self._room}'
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.88 Mobile Safari/537.36'
        }
        async with ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                room_page = await resp.text()
                self._ayyuid = int(re.search(r"ayyuid: +'([0-9]+)'", room_page, re.MULTILINE).group(1))
                self._topsid = int(re.search(r"TOPSID += +'([0-9]+)'", room_page, re.MULTILINE).group(1))
                self._subsid = int(re.search(r"SUBSID += +'([0-9]+)'", room_page, re.MULTILINE).group(1))
        return True

    async def _one_hello(self) -> bool:
        ws_user_info = WSUserInfo()
        ws_user_info.lUid = self._ayyuid
        ws_user_info.lTid = self._topsid
        ws_user_info.lSid = self._subsid

        output_stream = tarscore.TarsOutputStream()
        ws_user_info.writeTo(output_stream)

        ws_command = WebSocketCommand()
        ws_command.iCmdType = EWebSocketCommandType.EWSCmd_RegisterReq
        ws_command.vData = output_stream.getBuffer()
        output_stream = tarscore.TarsOutputStream()
        ws_command.writeTo(output_stream)

        return await self._conn.send_bytes(output_stream.getBuffer())

    async def _one_heartbeat(self) -> bool:
        return await self._conn.send_bytes(self._pack_heartbeat)
        
    async def _one_read(self) -> bool:
        pack = await self._conn.read_bytes()

        if pack is None:
            return False

        return self.handle_danmu(pack)
    
    def handle_danmu(self, pack):
        # print(f'{self._area_id} 号数据连接:', pack)

        stream = tarscore.TarsInputStream(pack)
        command = WebSocketCommand()
        command.readFrom(stream)
        
        if command.iCmdType == EWebSocketCommandType.EWSCmdS2C_MsgPushReq:
            stream = tarscore.TarsInputStream(command.vData)
            msg = WSPushMessage()
            msg.readFrom(stream)
            # 仅实现了说话的弹幕
            if msg.iUri == 1400:
                stream = tarscore.TarsInputStream(msg.sMsg)
                msg = MessageNotice()
                msg.readFrom(stream)
                #print(f' [{msg.tUserInfo.sNickName.decode("utf-8")}]: {self.checkemot(msg.sContent.decode("utf-8"))}')
                
                t2 = datetime.datetime.now()
                interval = (t2 - self.t1)
                if(self.flag):
                    interval = str(interval) 
                    self.flag = False
                HH,MM,SS,MS = get_time_now(str(interval))
                MM = MM + HH*60
                if((((MM*60+SS)*100+MS)-self.last_msc)>=50):
                    
                    self.last_msc = (MM*60+SS)*100+MS
                    MS = getStr(MS)
                    SS = getStr(SS)
                    MM = getStr(MM)
                    if(q.qsize()>0):
                        msg = '\n'f'[{MM}:{SS}.{MS}]'f'[{msg.tUserInfo.sNickName.decode("utf-8")[0:5]}...]: 'f'{self.checkemot(msg.sContent.decode("utf-8"))}{q.get()}'
                    else:
                        msg = '\n'f'[{MM}:{SS}.{MS}]'f'[{msg.tUserInfo.sNickName.decode("utf-8")[0:5]}...]: 'f'{self.checkemot(msg.sContent.decode("utf-8"))}'
                        self.flag2 = True
                    save(self._filename, msg)
                
                else:
                
                    if(self.flag2):
                        MS = getStr(MS)
                        SS = getStr(SS)
                        MM = getStr(MM)
                        msg = '\\n'f'[{msg.tUserInfo.sNickName.decode("utf-8")[0:5]}...]: 'f'{self.checkemot(msg.sContent.decode("utf-8"))}'
                        save(self._filename, msg)
                        self.flag2 = False
                    else:
                        msg = '\\n'f'[{msg.tUserInfo.sNickName.decode("utf-8")[0:5]}...]: 'f'{self.checkemot(msg.sContent.decode("utf-8"))}'
                        q.put(msg)
        return True

    async def reset_roomid(self, room):
        async with self._opening_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            await self._conn.close()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room = room
            print(f'{self._area_id} 号数据连接已经切换房间（{room}）')
