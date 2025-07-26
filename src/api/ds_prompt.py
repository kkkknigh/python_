from document.content_get import ARTICLE_TEXT

def translate_prompt(text = ARTICLE_TEXT):
    prompt = f"这是一篇论文：{text}。" + \
    "请你将这篇论文翻译为中文，\
    形式要求：以html形式输出，\
    原文与翻译文本间隔分段输出，\
    格式为原文-翻译文本-原文-翻译文本，\
    保持原有排版不变。"

    return prompt


def analyze_prompt(text = ARTICLE_TEXT):
    
    prompt = f"这是一篇论文：{text}。" + \
    "请你分析一下这篇论文中的关键概念、关键创新点、\
    关键技术等。\
    输出格式要求：分条列出"

    return prompt

                
def recommend_prompt(text = ARTICLE_TEXT):
    
    prompt = f"这是一篇论文：{text}。" + \
    "你是一位这个研究方向的专业学者，\
    请你根据这篇文章对读者给出一些相关论文阅读建议\
    输出格式要求：以纯文本形式输出，格式如下：<文章名>[链接]，\
    <>为必选项，[]为可选项"
    return prompt


def chat_prompt(query, target = "", text = ARTICLE_TEXT):
    prompt = "你是一个善解人意的助教，正在帮助同学理解论文内容。"
    prompt += f"\n\n文章内容：{text}"
    
    if target:  
        prompt += f"\n\n同学特别关注这部分：{target}"
    
    prompt += f"\n\n同学的疑问：{query}"
    prompt += "\n\n请你详细地解答他的疑问，并引用文章中的相关内容进行说明。"
    
    return prompt


