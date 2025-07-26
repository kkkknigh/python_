from openai import OpenAI

DEEPSEEK_API_KEY = ''

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

import api.ds_prompt as ds_prompt
from document.content_get import ARTICLE_TEXT

#存储聊天上下文
CHAT_MESSAGE = []

def chat_fetch(query, target="", text=ARTICLE_TEXT):
    '''
    与 AI 聊天并获取回复。

    Args:
        query (str): 用户提出的问题或指令。
        target (str, optional): 目标对象或主题。默认为 ""。
        text (str, optional): 上下文文本，默认为 ARTICLE_TEXT。

    Returns:
        str: AI 的回复。
    '''
    # 获取提示词
    prompt = prompt.chat_promopt(query, target, text)
    CHAT_MESSAGE.append({"role": "user", "content": prompt})
    # 获取回答
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=CHAT_MESSAGE,
            temperature=0.7,
            max_tokens=500
        )
    except Exception as e:
        raise e
    
    # 更新聊天历史
    CHAT_MESSAGE.append(response.choices[0].message)
    # 返回回答
    return response.choices[0].message['content'].strip()

def chat_reset():
    '''
    重置聊天历史
    '''
    CHAT_MESSAGE.clear()
    return CHAT_MESSAGE


# 预置聊天提示词获取函数
PROMPT_DEMAND = {"translate": ds_prompt.translate_prompt(), 
          "recommend": ds_prompt.recommend_prompt(), 
          "analyze": ds_prompt.analyze_prompt(), }


def pdf_fetch(demand = "translate", text=ARTICLE_TEXT):
    '''
    根据需求从 AI 获取回复。

    Args:
        demand (str, optional): 需求的类型，例如 "translate"、"recommend" 或 "analyze"。默认为 "translate"。
        text (str, optional): 上下文文本，默认为 ARTICLE_TEXT。

    Returns:
        str: AI 的回复。
    '''
    # 获取提示词
    prompt = PROMPT_DEMAND[demand](text)
    # 获取回答
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=prompt,
            temperature=0.7,
            max_tokens=500
        )
    except Exception as e:
        raise e
    
    # 返回回答
    return response.choices[0].message['content'].strip()