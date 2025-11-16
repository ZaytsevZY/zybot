# -*- coding: utf-8 -*-

import logging
import re
import time
import xml.etree.ElementTree as ET
from queue import Empty
from threading import Thread
from base.func_zhipu import ZhiPu

from wcferry import Wcf, WxMsg

from base.func_bard import BardAssistant
from base.func_chatglm import ChatGLM
from base.func_chatgpt import ChatGPT
from base.func_chengyu import cy
from base.func_news import News
from base.func_tigerbot import TigerBot
from base.func_xinghuo_web import XinghuoWeb
from configuration import Config
from constants import ChatType
from job_mgmt import Job

__version__ = "39.2.4.0"


class Robot(Job):
    """个性化自己的机器人
    """

    def __init__(self, config: Config, wcf: Wcf, chat_type: int) -> None:
        self.wcf = wcf
        self.config = config
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()

        if ChatType.is_in_chat_types(chat_type):
            if chat_type == ChatType.TIGER_BOT.value and TigerBot.value_check(self.config.TIGERBOT):
                self.chat = TigerBot(self.config.TIGERBOT)
            elif chat_type == ChatType.CHATGPT.value and ChatGPT.value_check(self.config.CHATGPT):
                self.chat = ChatGPT(self.config.CHATGPT)
            elif chat_type == ChatType.XINGHUO_WEB.value and XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
            elif chat_type == ChatType.CHATGLM.value and ChatGLM.value_check(self.config.CHATGLM):
                self.chat = ChatGLM(self.config.CHATGLM)
            elif chat_type == ChatType.BardAssistant.value and BardAssistant.value_check(self.config.BardAssistant):
                self.chat = BardAssistant(self.config.BardAssistant)
            elif chat_type == ChatType.ZhiPu.value and ZhiPu.value_check(self.config.ZhiPu):
                self.chat = ZhiPu(self.config.ZhiPu)
            else:
                self.LOG.warning("未配置模型")
                self.chat = None
        else:
            if TigerBot.value_check(self.config.TIGERBOT):
                self.chat = TigerBot(self.config.TIGERBOT)
            elif ChatGPT.value_check(self.config.CHATGPT):
                self.chat = ChatGPT(self.config.CHATGPT)
            elif XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
            elif ChatGLM.value_check(self.config.CHATGLM):
                self.chat = ChatGLM(self.config.CHATGLM)
            elif BardAssistant.value_check(self.config.BardAssistant):
                self.chat = BardAssistant(self.config.BardAssistant)
            elif ZhiPu.value_check(self.config.ZhiPu):
                self.chat = ZhiPu(self.config.ZhiPu)
            else:
                self.LOG.warning("未配置模型")
                self.chat = None

        self.LOG.info(f"已选择: {self.chat}")
        
        self.commands = {
            '/h': self.show_help,
            '/help': self.show_help,
            '/c': self.clear_chat_history,
            '/clear': self.clear_chat_history,
            '/w': self.get_weather,
            '/weather': self.get_weather,
            '^更新$': self.update_config
        }

    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(value is not None for key, value in args.items() if key != 'proxy')
        return False

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        return self.toChitchat(msg)

    def toChengyu(self, msg: WxMsg) -> bool:
        """
        处理成语查询/接龙消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = False
        texts = re.findall(r"^([#|?|？])(.*)$", msg.content)
        # [('#', '天天向上')]
        if texts:
            flag = texts[0][0]
            text = texts[0][1]
            if flag == "#":  # 接龙
                if cy.isChengyu(text):
                    rsp = cy.getNext(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True
            elif flag in ["?", "？"]:  # 查词
                if cy.isChengyu(text):
                    rsp = cy.getMeaning(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True

        return status

    def handle_command(self, msg: WxMsg) -> bool:
        """统一处理所有命令
        返回True表示已处理命令，False表示不是命令
        """
        content = msg.content.strip().lower()
        command = content.split()[0] if content else ''
        
        if command in self.commands:
            self.commands[command](msg)
            return True
            
        return False
  
    def show_help(self, msg: WxMsg) -> None:
        """显示帮助信息"""
        help_text = (
            "🤖 可用指令：\n"
            "- /h 或 /help：显示帮助信息\n"
            "- /c 或 /clear：清空当前对话历史\n"
            "- /w <city>或 /weather <city>：显示当前天气(default: 北京)"
        )
        if msg.from_group():
            self.sendTextMsg(help_text, msg.roomid, msg.sender)
        else:
            self.sendTextMsg(help_text, msg.sender)  
 
    def clear_chat_history(self, msg: WxMsg) -> None:
        """清空聊天历史"""
        if self.chat:
            chat_id = msg.roomid if msg.from_group() else msg.sender
            if hasattr(self.chat, 'converstion_list'):
                system_prompt = self.chat.system_prompt
                self.chat.converstion_list[chat_id] = [system_prompt] if system_prompt else []
            clear_text = "✨ 已清空对话历史"
            if msg.from_group():
                self.sendTextMsg(clear_text, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(clear_text, msg.sender)
                
    def get_weather(self, msg: WxMsg) -> None:
        """获取天气信息"""
        try:
            from base.func_weather import Weather
            weather = Weather()
            
            parts = msg.content.strip().split()
            city = parts[1] if len(parts) > 1 else "北京"
            
            weather_info = weather.get_weather(city)
            if msg.from_group():
                self.sendTextMsg(weather_info, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(weather_info, msg.sender)
        except Exception as e:
            error_msg = f"获取天气信息失败: {str(e)}"
            self.LOG.error(error_msg)
            if msg.from_group():
                self.sendTextMsg(error_msg, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(error_msg, msg.sender)

    def update_config(self, msg: WxMsg) -> None:
        """更新配置"""
        if msg.from_self():
            self.config.reload()
            self.LOG.info("已更新")
 
    def processMsg(self, msg: WxMsg) -> None:
        """处理消息的主函数"""
        # 群聊消息
        if msg.from_group():
            if msg.roomid not in self.config.GROUPS:
                return

            if msg.is_at(self.wxid):
                self.toAt(msg)
            else:
                self.toChengyu(msg)
            return

        # 非群聊消息处理
        if msg.type == 37:  # 好友请求
            self.autoAcceptFriendRequest(msg)
        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)
        elif msg.type == 0x01:  # 文本消息
            # 先检查是否是命令
            if not self.handle_command(msg):
                # 不是命令则当作普通消息处理
                self.toChitchat(msg) 
    
    def toChitchat(self, msg: WxMsg) -> bool:
        """处理普通对话"""
        if not self.chat:
            rsp = "你@我干嘛？"
        else:
            q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
            rsp = self.chat.get_answer(q, (msg.roomid if msg.from_group() else msg.sender))

        if rsp:
            if msg.from_group():
                self.sendTextMsg(rsp, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(rsp, msg.sender)
            return True
        else:
            self.LOG.error("无法从大模型获得答案")
            return False
        
    def onMsg(self, msg: WxMsg) -> int:
        try:
            self.LOG.info(msg)  # 打印信息
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0

    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    def enableReceivingMsg(self) -> None:
        def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    self.processMsg(msg)
                except Empty:
                    continue  # Empty message
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        self.wcf.enable_receiving_msg()
        Thread(target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True).start()

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats}\n\n{msg}", receiver, at_list)

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)

    def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            scene = int(xml.attrib["scene"])
            self.wcf.accept_new_friend(v3, v4, scene)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def sayHiToNewFriend(self, msg: WxMsg) -> None:
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(
                f"Hi {nickName[0]}，我自动通过了你的好友请求。欢迎使用zybot！\n"
                "\n"
                "🤖 可用指令：\n"
                "- /h 或 /help：显示帮助信息\n" 
                "- /c 或 /clear：清空当前对话历史\n"
                "- /w <city>或 /weather <city>：显示当前天气(default: 北京)\n"
                "\n"
                "支持功能: \n"
                "- 每日07:00发送北京天气预报\n"
                "- 每日07:30发送今日要闻\n",
                msg.sender
            )


    def newsReport(self) -> None:
        receivers = self.config.NEWS
        if not receivers:
            return

        news = News().get_important_news()
        for r in receivers:
            self.sendTextMsg(news, r)

    def weatherReport(self) -> None:
        """每日天气播报"""
        try:
            from base.func_weather import Weather
            weather = Weather()
            weather_info = weather.get_weather()
            
            # 获取接收人
            receivers = self.config.NEWS  # 使用配置文件中的接收者列表
            if not receivers:
                receivers = ["filehelper"]  # 如果没有配置接收者，默认发送给文件传输助手
                
            # 发送天气信息
            for receiver in receivers:
                self.sendTextMsg(weather_info, receiver)
                
        except Exception as e:
            error_msg = f"发送天气预报失败: {str(e)}"
            self.LOG.error(error_msg)
            self.sendTextMsg(error_msg, "filehelper")