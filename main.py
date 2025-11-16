#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
from argparse import ArgumentParser

from base.func_report_reminder import ReportReminder
from configuration import Config
from constants import ChatType
from robot import Robot, __version__
from wcferry import Wcf


def weather_report(robot: Robot) -> None:
    """发送天气预报
    """
    try:
        # 获取天气信息
        crawler = WeatherCrawler()
        weather_info = crawler.get_weather()
        
        # 获取接收人
        receivers = robot.config.NEWS  # 使用配置文件中的接收者列表
        if not receivers:
            receivers = ["filehelper"]  # 如果没有配置接收者，默认发送给文件传输助手
        
        # 发送天气信息
        for receiver in receivers:
            robot.sendTextMsg(weather_info, receiver)
            
    except Exception as e:
        robot.LOG.error(f"发送天气预报失败: {str(e)}")
        # 发送错误信息给文件传输助手
        robot.sendTextMsg(f"发送天气预报失败: {str(e)}", "filehelper")

def main(chat_type: int):
    config = Config()
    wcf = Wcf(debug=True)

    def handler(sig, frame):
        wcf.cleanup()  # 退出前清理环境
        exit(0)

    signal.signal(signal.SIGINT, handler)

    robot = Robot(config, wcf, chat_type)
    robot.LOG.info(f"WeChatRobot【{__version__}】成功启动···")

    # 机器人启动发送测试消息
    robot.sendTextMsg("机器人启动成功！", "filehelper")

    # 接收消息
    # robot.enableRecvMsg()     # 可能会丢消息？
    robot.enableReceivingMsg()  # 加队列

    # 每天 7 点发送天气预报
    # robot.onEveryTime("07:00", weather_report, robot=robot)
    robot.onEveryTime("07:00", robot.weatherReport)
        
    # 每天 7:30 发送新闻
    robot.onEveryTime("07:30", robot.newsReport)

    # 每天 16:30 提醒发日报周报月报（这个好像我用不到）
    # robot.onEveryTime("16:30", ReportReminder.remind, robot=robot)

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-c', type=int, default=6, help=f'选择模型参数序号: {ChatType.help_hint()}')
    args = parser.parse_args().c
    main(args)
