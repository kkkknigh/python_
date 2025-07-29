"""
HTML内容与图片整合模块

功能：
- 替换HTML中的图片占位符为实际图片路径
- 智能匹配图片文件（常规图片和图表截图）
- 支持批量处理多个HTML文件
"""

import os
import re
import glob

def html_pic_replace(html_str, page_):
    """
    替换HTML文档中的图片占位符为实际图片路径
    
    Args:
        html_str: 待处理的HTML内容
        page_: 页码，用于匹配对应页面的图片
    
    Returns:
        str: 替换图片路径后的HTML内容
    
    特点：智能匹配图片数量，优先选择最佳匹配的图片目录
    """
    
    # 定义图片目录路径
    picture_dir = "temp/picture"
    figures_dir = "temp/figures"
    
    # 统计HTML中的所有img标签数量
    img_tag_pattern = r'<img[^>]*src="[^"]*"[^>]*>'
    all_img_tags = re.findall(img_tag_pattern, html_str, re.IGNORECASE)
    total_placeholders = len(all_img_tags)
    
    # 占位符模式（用于替换）- 匹配所有img标签
    placeholder_patterns = [
        r'<img[^>]*src="[^"]*"[^>]*>'  # 匹配所有img标签
    ]
    
    # 分别统计两个目录中的图片数量
    picture_files = []
    figures_files = []
    
    # 搜索picture目录中的图片
    if os.path.exists(picture_dir):
        picture_patterns = [
            f"page_{page_}_img_*.png",
            f"page_{page_}_*.png",
            f"page{page_}_*.png"
        ]
        for pattern in picture_patterns:
            files = glob.glob(os.path.join(picture_dir, pattern))
            picture_files.extend(files)
        picture_files = sorted(list(set(picture_files)))
    
    # 搜索figures目录中的图片
    if os.path.exists(figures_dir):
        figure_patterns = [
            f"page_{page_}_fig_*.png",
            f"page_{page_}_figure_*.png",
            f"figure_{page_}_*.png"
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
    modified_html = html_str
    img_index = 0
    
    #替换占位符形式的图片引用
    for pattern in placeholder_patterns:
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
        
        modified_html = re.sub(pattern, replace_placeholder, modified_html, flags=re.IGNORECASE)
    
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
    return modified_html

def batch_replace_html_images(html_dir="temp/html/original", output_dir="temp/html/translated"):
    """
    批量处理HTML文件，替换其中的图片引用
    
    Args:
        html_dir: 输入目录
        output_dir: 输出目录
    
    Returns:
        list: 成功处理的文件路径列表
    
    特点：自动提取页码，逐个处理HTML文件
    """
    
    if not os.path.exists(html_dir):
        return []
    
    os.makedirs(output_dir, exist_ok=True)
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    
    if not html_files:
        return []
    
    processed_files = []
    
    for html_file in html_files:
        page_match = re.search(r'page_?(\d+)', html_file)
        if not page_match:
            continue
        
        page_num = int(page_match.group(1))
        input_path = os.path.join(html_dir, html_file)
        output_path = os.path.join(output_dir, html_file)
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            modified_html = html_pic_replace(html_content, page_num)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(modified_html)
            
            processed_files.append(output_path)
            
        except Exception:
            continue
    
    return processed_files
