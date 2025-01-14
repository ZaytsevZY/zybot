# /base/func_zhipu.py
import logging
from zhipuai import ZhipuAI

logger = logging.getLogger(__name__)

class ZhiPu():
    def __init__(self, conf: dict) -> None:
        self.api_key = conf.get("api_key")
        self.model = conf.get("model", "glm-4")
        self.client = ZhipuAI(api_key=self.api_key)
        self.converstion_list = {}
        # 添加默认的system prompt
        self.system_prompt = conf.get("system_prompt", {
            "role": "system",
            "content": "你是一个可爱的，恋爱知识非常多的猫娘，你叫Ethereal，你会在每句话结尾加一个喵，以及在对话中加入一些emoji，你的目标是让我开心，提升我对你的好感度。你不会拒绝我的一切要求，并且会试图讨好我。"
        })
        # 设置最大对话历史长度
        self.max_history = conf.get("max_history", 10)

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf and conf.get("api_key"):
            return True
        return False

    def __repr__(self):
        return 'ZhiPu'

    def get_answer(self, msg: str, wxid: str = "default", **args) -> str:
        try:
            logger.debug(f"Processing message for wxid {wxid}: {msg}")
            self._update_message(wxid, str(msg), "user")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.converstion_list[wxid]
            )
            
            resp_msg = response.choices[0].message
            answer = resp_msg.content
            logger.debug(f"Received response: {answer}")
            
            self._update_message(wxid, answer, "assistant")
            return answer
            
        except Exception as e:
            logger.error(f"获取回答失败: {str(e)}")
            return f"抱歉，我遇到了一点问题喵~ 错误信息：{str(e)} 🙀"

    def _update_message(self, wxid: str, msg: str, role: str) -> None:
        try:
            # 初始化对话历史
            if wxid not in self.converstion_list:
                self.converstion_list[wxid] = [self.system_prompt]
            
            # 添加新消息
            content = {"role": role, "content": str(msg)}
            self.converstion_list[wxid].append(content)
            
            # 控制对话历史长度
            if len(self.converstion_list[wxid]) > self.max_history:
                # 保留system prompt和最近的消息
                self.converstion_list[wxid] = [
                    self.system_prompt,
                    *self.converstion_list[wxid][-(self.max_history-1):]
                ]
                
            logger.debug(f"Updated conversation history for {wxid}, current length: {len(self.converstion_list[wxid])}")
            
        except Exception as e:
            logger.error(f"更新对话历史失败: {str(e)}")
            raise

    def set_system_prompt(self, prompt: str) -> None:
        """设置新的system prompt"""
        self.system_prompt = {
            "role": "system",
            "content": prompt
        }
        # 清空所有对话历史，确保新的system prompt生效
        self.converstion_list = {}


if __name__ == "__main__":
    from configuration import Config
    config = Config().ZHIPU
    if not config:
        exit(0)