from openai import OpenAI
import os

DEEPSEEK_API_KEY = ''

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# 存储聊天上下文
CHAT_MESSAGE = []

def chat(query, text, target=""):
    '''
    与 AI 聊天并获取回复。

    Args:
        query (str): 用户提出的问题或指令。
        text (str): 上下文文本。
        target (str, optional): 目标对象或主题。默认为 ""。

    Returns:
        str: AI 的回复。
    '''

    #提示词
    prompt = f"""你是一个善解人意的助教，正在帮助同学理解论文内容。
    文章内容：{text}
    {f'同学特别关注这部分：{target}' if target else ''}
    同学的疑问：{query}
    请你详细地解答他的疑问，并引用文章中的相关内容进行说明。"""
    #更新聊天历史
    CHAT_MESSAGE.append({"role": "user", "content": prompt})
    
    # 获取回答
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=CHAT_MESSAGE,
            temperature=0.7,
            max_tokens=1000  # 增加最大token数以获得更详细的回答
        )
    except Exception as e:
        raise e
    
    # 更新聊天历史
    CHAT_MESSAGE.append(response.choices[0].message)
    
    # 返回回答
    return response.choices[0].message.content.strip()

def chat_reset():
    '''
    重置聊天历史
    '''
    CHAT_MESSAGE.clear()
    return CHAT_MESSAGE

def html_convert(text):
    '''
    将论文文本内容转换为 HTML 格式并分页保存到 html 文件夹
    
    Args:
        text (list or str): 要转换的文本内容，可以是字符串或字符串列表
    
    Returns:
        list: 包含每页 HTML 内容的列表
    
    Raises:
        Exception: API 调用失败时抛出异常
    '''
    prompt_template = """请将以下一篇论文的第一页/下一页内容转换为规范的HTML格式：

转换要求：
1. 符合学术论文的HTML格式规范
2. 自动识别和组织文章结构：标题、摘要、正文段落、引用等
3. 根据聊天历史考虑上下文关系，确保连续性
5. 输出完整的HTML文档，包含<!DOCTYPE html>声明
6. 添加基本且美观的CSS样式以提高可读性
7. 确保输出内容可以直接保存为.html文件

请不要添加任何HTML代码之外的解释文字。

待转换的下一页论文内容：
{}"""
    
    responses = []
    html_history = []
    # 确保 text 是可迭代的
    if isinstance(text, str):
        text = [text]
    
    # 创建html文件夹
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_dir = os.path.join(current_dir, "html")
    os.makedirs(html_dir, exist_ok=True)
    
    # 分页处理文件
    for i, page_text in enumerate(text, 1):
        try:
            full_prompt = prompt_template.format(page_text)
            html_history.append({"role": "user", "content": full_prompt})
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=html_history,
                temperature=0.3,  
                max_tokens=8192
            )
            html_history.append(response.choices[0].message)
            html_content = response.choices[0].message.content.strip()
            responses.append(html_content)
            
            # 保存HTML文件
            html_filename = f"page_{i}.html"
            html_filepath = os.path.join(html_dir, html_filename)
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
        except Exception as e:
            error_msg = f"第{i}页转换失败: {str(e)}"
            print(error_msg)
    
    return responses


def translate(text_part):
    '''
    将 PDF 文本内容翻译成中文
    
    Args:
        text_part (str): 要翻译的文本内容
    
    Returns:
        str: 翻译后的 HTML 格式中文内容
    
    Raises:
        Exception: API 调用失败时抛出异常
    '''
    
    prompt = f"""请将以下英文论文内容翻译成中文：

{text_part}

翻译要求：
1. 保持学术论文的专业性和准确性
2. 保留专业术语的原文（可在括号中标注）
3. 输出为完整的HTML格式文档
4. 包含<!DOCTYPE html>声明和完整的<html></html>标签
5. 在HTML body中采用原文-翻译对照格式
6. 格式：<p class='original'>原文段落</p><p class='translation'>翻译段落</p>
7. 添加基本的CSS样式以提高可读性
8. 不要添加任何HTML代码之外的解释文字

请确保输出的内容可以直接保存为.html文件。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=8192
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise e


def recommend(text):
    '''
    基于 PDF 内容生成推荐建议
    
    Args:
        text (str): 要分析的文本内容
    
    Returns:
        str: 基于内容的推荐建议
    
    Raises:
        Exception: API 调用失败时抛出异常
    '''

    prompt = f"""基于以下论文内容，为读者推荐相关论文：

{text}

推荐要求：
1. 你是该研究领域的资深学者
2. 推荐与该论文主题相关的重要论文
3. 输出格式：<论文标题> [DOI/链接]（如果知道的话）
4. 每条推荐简要说明推荐理由
5. 推荐5-10篇论文
6. 以纯文本形式分条列出

请不要包含其他解释内容。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=8192
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise e


def analyze(text):
    '''
    对 PDF 文本内容进行深度分析
    
    Args:
        text (str): 要分析的文本内容
    
    Returns:
        str: 文本内容的详细分析结果
    
    Raises:
        Exception: API 调用失败时抛出异常
    '''

    prompt = f"""请对以下论文进行深度分析：

{text}

分析要求：
1. 研究背景与动机
2. 主要贡献和创新点
3. 关键技术和方法
4. 实验设计与结果
5. 优势与局限性
6. 未来研究方向
7. 学术价值和应用前景

输出格式：
- 使用标题分段组织内容
- 每个要点用简洁的语言概括
- 分条列出主要内容

请提供结构化的专业分析。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=8192
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise e





def split_text(text, max_length=3000):
    '''
    将长文本分割成较小的段落，用于分批处理

    Args:
        text (str): 要分割的文本
        max_length (int): 每段的最大长度

    Returns:
        list: 分割后的文本段落列表
    '''
    chunks = []
    sentences = text.split('. ')
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence + '. ') <= max_length:
            current_chunk += sentence + '. '
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def pdf_fetch_long(text, demand="translate", chunk_size=3000):
    '''
    处理长篇内容的翻译或分析，通过分段处理来避免token限制

    Args:
        demand (str): 需求类型，支持 "translate"、"recommend"、"analyze"
        text (str): 输入文本
        chunk_size (int): 每段的最大字符数

    Returns:
        str: 完整的处理结果
    '''
    # 根据需求类型选择对应的函数
    demand_functions = {
        "translate": translate,
        "recommend": recommend,
        "analyze": analyze
    }
    
    if demand not in demand_functions:
        raise ValueError(f"不支持的需求类型: {demand}")
    
    pdf_func = demand_functions[demand]
    
    # 如果文本较短，直接处理
    if len(text) <= chunk_size:
        return pdf_func(text)
    
    # 分割文本
    chunks = split_text(text, chunk_size)
    results = []
    
    print(f"文本过长，将分为 {len(chunks)} 段进行处理...")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"正在处理第 {i}/{len(chunks)} 段...")
        try:
            result = pdf_func(chunk)
            results.append(result)
        except Exception as e:
            print(f"处理第 {i} 段时出错: {e}")
            results.append(f"[处理第 {i} 段时出错: {e}]")
    
    # 合并结果
    final_result = "\n\n".join(results)
    return final_result