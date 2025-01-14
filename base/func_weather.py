
# base/func_weather.py
import requests
import logging
from datetime import datetime

class Weather:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.city_codes = {
            "北京": "101010100",
            "天津": "101030100",
            "上海": "101020100",
            "深圳": "101280601"
        }

    def get_weather(self, city_name="北京"):
        """获取指定城市的天气信息（当前天气和今日预报）"""
        try:
            if city_name not in self.city_codes:
                return f"暂不支持 {city_name} 的天气查询，支持的城市有：{', '.join(self.city_codes.keys())}"

            city_code = self.city_codes[city_name]
            url = f"http://t.weather.itboy.net/api/weather/city/{city_code}"
            
            response = requests.get(url, headers=self.headers)
            data = response.json()
            
            if data['status'] != 200:
                return "获取天气信息失败，请稍后重试"
                
            weather = data['data']
            forecast = weather['forecast'][0]
            
            # 合并当前天气和今日预报
            weather_info = (
                f"📍 {city_name}天气信息\n"
                f"🕒 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"\n== 实时天气 ==\n"
                f"🌡️ 当前温度：{weather['wendu']}°C\n"
                f"💧 相对湿度：{weather['shidu']}\n"
                f"🌍 空气质量：{weather['quality']}\n"
                f"☔ 降水量：{weather.get('rain', '0')}mm\n"
                f"\n== 今日预报 ==\n"
                f"🌤️ 天气状况：{forecast['type']}\n"
                f"🌡️ 温度区间：{forecast['low']} ~ {forecast['high']}\n"
                f"🌪️ 风向风力：{forecast['fx']} {forecast['fl']}\n"
                f"🌅 日出时间：{forecast['sunrise']}\n"
                f"🌇 日落时间：{forecast['sunset']}\n"
                f"📝 温馨提示：{forecast['notice']}"
            )
            
            return weather_info
            
        except Exception as e:
            self.logger.error(f"获取天气信息失败: {str(e)}")
            return "获取天气信息失败，请稍后再试"