import os

from langchain_community.chat_models.zhipuai import ChatZhipuAI
from langchain_core.messages import AIMessage, HumanMessage

# to get your api key for free, visit and signup: https://open.bigmodel.cn/usercenter/apikeys
zhipu_api_key = os.environ.get("ZHIPU_API_KEY")

chat = ChatZhipuAI(api_key=zhipu_api_key, model="glm-4")

response = chat.invoke(
    [
        HumanMessage(content="你好"),
        AIMessage(content="你好！有什么可以帮助你的吗？"),
        HumanMessage(content="对比分析一下平安 E 生保和众安普惠保产品的优劣势"),
    ]
)

print(response.content)
