"""
HTML内容与图片整合模块

功能：
- html文件处理：process_html_with_images() - 替换html文件中的图片引用
- 智能匹配图片文件（常规图片和图表截图）
- 自动创建处理后的文件到指定目录
"""

import os
import re
import glob

def html_img_replace(html_file_path, output_dir="temp/html/final"):
    """
    处理单个HTML文件，替换其中的图片引用并保存到新位置
    
    Args:
        html_file_path: 待处理的HTML文件路径
        output_dir: 输出目录，默认为"temp/html/final"
    
    Returns:
        str: 替换图片路径后的HTML内容
    
    副作用：
        在output_dir中创建处理后的HTML文件
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML文件不存在: {html_file_path}")
    
    # 从文件名提取页码
    html_filename = os.path.basename(html_file_path)
    page_match = re.search(r'page_?(\d+)', html_filename)
    if not page_match:
        raise ValueError(f"无法从文件名提取页码: {html_filename}")
    
    page_num = int(page_match.group(1))
    
    # 读取HTML内容
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        raise IOError(f"读取HTML文件失败: {e}")
    
    # 定义图片目录路径
    picture_dir = "temp/picture"
    figures_dir = "temp/figures"
    
    # 统计HTML中的所有img标签数量
    img_tag_pattern = r'<img[^>]*src="[^"]*"[^>]*>'
    all_img_tags = re.findall(img_tag_pattern, html_content, re.IGNORECASE)
    total_placeholders = len(all_img_tags)
    
    # 分别搜索两个目录中的图片
    picture_files = []
    figures_files = []
    
    # 搜索picture目录中的图片
    if os.path.exists(picture_dir):
        picture_patterns = [
            f"page_{page_num}_img_*.png",
            f"page_{page_num}_*.png",
            f"page{page_num}_*.png"
        ]
        for pattern in picture_patterns:
            files = glob.glob(os.path.join(picture_dir, pattern))
            picture_files.extend(files)
        picture_files = sorted(list(set(picture_files)))
    
    # 搜索figures目录中的图片
    if os.path.exists(figures_dir):
        figure_patterns = [
            f"page_{page_num}_fig_*.png",
            f"page_{page_num}_figure_*.png",
            f"figure_{page_num}_*.png"
        ]
        for pattern in figure_patterns:
            files = glob.glob(os.path.join(figures_dir, pattern))
            figures_files.extend(files)
        figures_files = sorted(list(set(figures_files)))
    
    # 智能选择图片文件夹
    if total_placeholders > 0:
        picture_match = len(picture_files) == total_placeholders
        figures_match = len(figures_files) == total_placeholders
        
        if picture_match:
            page_images = picture_files
        elif figures_match:
            page_images = figures_files  
        else:
            # 都不匹配，选择数目多的图片
            if len(figures_files) > len(picture_files):
                page_images = figures_files
            else:
                page_images = picture_files
    else:
        # 没有占位符，选择数目多的图片
        if len(figures_files) > len(picture_files):
            page_images = figures_files
        else:
            page_images = picture_files
    
    # 替换HTML中的图片标签
    modified_html = html_content
    img_index = 0
    
    # 替换占位符形式的图片引用
    placeholder_pattern = r'<img[^>]*src="[^"]*"[^>]*>'
    
    def replace_placeholder(match):
        nonlocal img_index
        if img_index < len(page_images):
            img_path = page_images[img_index]
            # 直接使用相对于项目根目录的路径，避免..路径
            relative_path = img_path.replace("\\", "/")
            # 如果路径以../开头，移除../前缀
            if relative_path.startswith("../"):
                relative_path = relative_path[3:]
            # 在路径前添加/前缀
            if not relative_path.startswith("/"):
                relative_path = "/" + relative_path
            
            original_tag = match.group(0)
            # 使用正则表达式替换src属性
            new_img_tag = re.sub(r'src="[^"]*"', f'src="{relative_path}"', original_tag, flags=re.IGNORECASE)
            
            img_index += 1
            return new_img_tag
        else:
            return match.group(0)
    
    modified_html = re.sub(placeholder_pattern, replace_placeholder, modified_html, flags=re.IGNORECASE)
    
    '''
    # 查找figure相关的文本并在其上方插入图片
    if page_images:
        figure_patterns = [
            r'(Figure?\s*\d+[:\.])',
            r'(Fig\.?\s*\d+[:\.])',
            r'(图\s*\d+[:\.])'
        ]
        
        for pattern in figure_patterns:
            matches = list(re.finditer(pattern, modified_html, re.IGNORECASE))
            
            for match in reversed(matches):
                if img_index < len(page_images):
                    img_path = page_images[img_index]
                    relative_path = os.path.relpath(img_path, "src").replace("\\", "/")
                    img_filename = os.path.basename(img_path)
                    
                    figure_with_img = (
                        f'<div class="figure" style="text-align: center; margin: 20px 0;">'
                        f'<img src="{relative_path}" alt="{img_filename}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px;">'
                        f'<figcaption style="font-style: italic; font-size: 0.9em; margin-top: 8px; color: #666;">'
                        f'{match.group(1)}'
                        f'</figcaption>'
                        f'</div>'
                    )
                    
                    modified_html = modified_html[:match.start()] + figure_with_img + modified_html[match.start():]
                    img_index += 1
                    break
    '''
    
    # 创建输出目录并保存处理后的文件
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, html_filename)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modified_html)
    except Exception as e:
        raise IOError(f"保存处理后的HTML文件失败: {e}")
    
    return modified_html
