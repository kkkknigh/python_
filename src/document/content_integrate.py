'''
整合原文+翻译+图片，获得可显示在阅读器上的文本
'''
import re

def extract_html_content(text):
    """
    从文本中提取HTML内容
    
    Args:
        text (str): 包含HTML内容的文本
        
    Returns:
        str: 提取的HTML内容，如果没有找到则返回None
    """
    # 匹配完整的HTML文档（包含DOCTYPE声明）
    doctype_pattern = r'<!DOCTYPE\s+html[^>]*>.*?</html>'
    doctype_match = re.search(doctype_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if doctype_match:
        return doctype_match.group(0)
    
    # 如果没有DOCTYPE，匹配html标签包围的内容
    html_pattern = r'<html[^>]*>.*?</html>'
    html_match = re.search(html_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if html_match:
        return html_match.group(0)
    
    # 如果没有完整的html标签，查找可能的HTML片段
    html_fragment_pattern = r'<[^>]+>.*?</[^>]+>'
    fragments = re.findall(html_fragment_pattern, text, re.DOTALL)
    
    if fragments:
        return '\n'.join(fragments)
    
    return None

def clean_html_response(response_text):
    """
    清理AI响应，只保留HTML内容
    
    Args:
        response_text (str): AI的完整响应
        
    Returns:
        str: 清理后的HTML内容
    """
    html_content = extract_html_content(response_text)
    if html_content:
        return html_content
    else:
        # 如果没有找到HTML标签，返回原文本
        return response_text
