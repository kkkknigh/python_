from openai import OpenAI
import os, re
import sys
import argparse

DEEPSEEK_API_KEY = 'sk-1b7afa90a6764df78928048a0da5f824'


def get_api_key():
    """
    获取API密钥
    
    Returns:
        str: API密钥
    """
    # 1. 优先使用全局变量中的API密钥
    global DEEPSEEK_API_KEY
    if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-'):
        return DEEPSEEK_API_KEY
    
    # 2. 尝试从环境变量获取
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if api_key:
        return api_key
    
    # 如果都没有，抛出异常
    raise ValueError("未找到API密钥。请通过以下方式之一提供：\n"
                   "1. 修改代码中的全局变量 DEEPSEEK_API_KEY\n"
                   "2. 环境变量: export DEEPSEEK_API_KEY=YOUR_KEY\n"
                   "3. 命令行参数: --api-key YOUR_KEY\n"
                   "4. 交互式输入")
# 初始化客户端
try:
    DEEPSEEK_API_KEY = get_api_key()
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
except ValueError as e:
    print(f"API密钥配置错误: {e}")
    client = None

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

    if client is None:
        raise RuntimeError("API客户端未初始化，请检查API密钥配置")
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


def clean_html_content(text):
    """
    清洗AI输出内容，提取可渲染的HTML文档
    
    Args:
        text (str): 包含HTML内容的纯文本
        
    Returns:
        str: 清洗后的HTML内容
    """
    if not text:
        return ""
    
    text = text.strip()
    
    # 首先检查是否存在代码块中的HTML内容
    code_block_match = re.search(r'```(?:html)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        # 提取代码块中的内容
        code_content = code_block_match.group(1).strip()
        
        # 检查代码块中是否包含HTML
        if '<!DOCTYPE' in code_content or '<html' in code_content:
            text = code_content
    
    # 匹配完整的HTML文档（包含DOCTYPE声明）
    doctype_match = re.search(r'(<!DOCTYPE\s+html[^>]*>.*?</html>)', text, re.DOTALL | re.IGNORECASE)
    if doctype_match:
        return doctype_match.group(1)
    
    # 匹配html标签包围的内容
    html_match = re.search(r'(<html[^>]*>.*?</html>)', text, re.DOTALL | re.IGNORECASE)
    if html_match:
        return html_match.group(1)
    
    # 如果都没找到，返回原文本
    return text

html_history = []  # html转换历史，保持风格一致

def html_convert(page_text, page_num):
    '''
    将论文文本内容转换为 HTML 格式并保存为.html文件
    
    Args:
        text (str): 要转换的文本内容，字符串，为原论文某页的文本
    
    Returns:
        str: 该页 HTML 内容
    
    Raises:
        Exception: API 调用失败时抛出异常
    '''

    if client is None:
        raise RuntimeError("API客户端未初始化，请检查API密钥配置")
    
    prompt = f"""请将以下学术论文内容转换为规范的HTML格式：

【转换要求】
1. 输出格式：生成完整HTML文档，包含<!DOCTYPE html>声明、<head>和<body>标签
2. 文档结构：识别并组织为标题、摘要、章节、段落、引用、图表说明等学术元素
3. 页面连贯性：与之前页面保持一致的格式和样式，确保内容的连续性
4. 排版美观：
   - 使用响应式设计，正文宽度限制在800px以内
   - 标题使用<h1>至<h4>标签，保持层次清晰
   - 段落使用<p>标签，设置合适的行高(1.5-1.8)和段间距
   - 字体大小16-18px，提高可读性
5. 特殊元素处理：
   - 公式：识别公式，使用<span class="math">$LaTeX公式$</span>标记，并用latex语法还原编辑公式
   - 图片引用：识别"Figure/Fig.X"的文本，在其上方添加<div class="figure"><img src="图片路径占位" alt="图描述"><figcaption>图片说明</figcaption></div>
   - 引用：使用<blockquote>或<cite>标签标记引用内容
   - 参考文献：使用<ol class="references">和<li>标签列出
6. 内嵌基本且美观的css样式，可以适当创意发挥以提高可读性

请不要添加任何HTML代码之外的解释，直接输出可保存的完整HTML。

【待转换的论文内容】
{page_text} """
    
    # 获取html文件夹
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    current_dir = os.path.abspath(project_root)
    html_dir = os.path.join(current_dir, "temp", "html", "original")

    # 处理文件
    try:
        html_history.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=html_history,
            temperature=0.3,  
            max_tokens=8192
            )
        html_history.append(response.choices[0].message)
        html_content = response.choices[0].message.content.strip()
        # 清洗输出，获得纯html
        html_content = clean_html_content(html_content)
        # 保存HTML文件
        html_filename = f"page_{page_num}.html"
        html_filepath = os.path.join(html_dir, html_filename)
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
                error_msg = f"第{page_num}页转换失败: {str(e)}"
                print(error_msg)
    
    return html_content


def translate(page_text, page_num):
    '''
    将 PDF 文本内容翻译成中文，并且保存为html文件
    
    Args:
        text_part (str): 要翻译的文本内容(html)
    
    Returns:
        str: 翻译后的 HTML 格式中文内容
    
    Raises:
        Exception: API 调用失败时抛出异常
    '''

     # 获取html文件夹
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    current_dir = os.path.abspath(project_root)
    html_dir = os.path.join(current_dir, "temp", "html", "translated")

    if client is None:
        raise RuntimeError("API客户端未初始化，请检查API密钥配置")
    
    prompt = f"""请将以下英文论文内容翻译成中文：

{page_text}

翻译要求：
1. 保持学术论文的专业性和准确性
2. 保留专业术语的原文（可在括号中标注）
3. 输出为完整的HTML格式文档
4. 开头为<!DOCTYPE html>声明或完整的<html></html>标签
5. 在HTML body中采用原文-翻译-原文-翻译对照格式，分段落翻译
6. 格式：<p class='original'>原文段落</p><p class='translation'>翻译段落</p>
7. 除译文外保持原文的CSS样式不变
8. 除添加翻译段落外不要改变原html
9. 不要添加任何HTML代码之外的解释文字

请确保输出的内容可以直接保存为.html文件。"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=8192
        )
        html_content = response.choices[0].message.content.strip()
        # 清洗输出，获得纯html
        html_content = clean_html_content(html_content)
        # 保存HTML文件
        html_filename = f"page_{page_num}.html"
        html_filepath = os.path.join(html_dir, html_filename)
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return html_content
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

    if client is None:
        raise RuntimeError("API客户端未初始化，请检查API密钥配置")
    
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

    if client is None:
        raise RuntimeError("API客户端未初始化，请检查API密钥配置")
    
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