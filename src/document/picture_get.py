"""
PDF图片提取模块

功能：
- 提取PDF中的嵌入图片并转换为PNG格式  
- 智能过滤无关图片（logo、装饰图等）
- 基于Figure标题的高精度截图提取
- 支持多种标题格式（Fig./Figure，大小写不敏感）
"""

from PIL import Image
from io import BytesIO
import re
import fitz  
import os

PDF_PATH = "src/document/article.pdf"

def pic_extract(pdf_path=PDF_PATH):
    """
    提取PDF中的学术相关图片并保存为PNG文件
    
    Args:
        pdf_path: PDF文件路径
    
    Returns:
        list: 保存的图片文件路径列表
    
    特点：支持CMYK转RGB，智能过滤装饰图，按页码命名
    """
    doc = fitz.open(pdf_path)
    saved_files = []
    picture_dir = os.path.join(os.path.dirname(pdf_path), "picture")
    os.makedirs(picture_dir, exist_ok=True)

    try:
        img_count = 0
        for page_num, page in enumerate(doc):
            for img in page.get_images(full=True):
                # 获取图片位置信息
                img_rects = page.get_image_rects(img[0])
                if not img_rects:
                    continue
                
                img_rect = img_rects[0]  # 取第一个位置
                
                # 使用筛选函数判断是否为学术相关图片
                if not _is_academic_relevant_image(page, img_rect):
                    continue  # 跳过无关图片
                
                base_image = doc.extract_image(img[0])
                image = Image.open(BytesIO(base_image["image"]))

                # CMYK转RGB
                if image.mode == 'CMYK':
                    image = image.convert('RGB')
                elif image.mode not in ['RGB', 'L']:
                    image = image.convert('RGB')
    
                filepath = os.path.join(picture_dir, f"page_{page_num + 1}_img_{img_count + 1}.png")
                image.save(filepath, "png")
                saved_files.append(filepath)
                img_count += 1
    finally:
        doc.close()

    return saved_files

def _is_academic_relevant_image(page, img_rect, min_size=50):
    """
    判断图片是否为学术相关内容
    
    筛选策略：尺寸、位置、宽高比、周围文本关键词
    """
    page_rect = page.rect
    
    # 1. 尺寸筛选：过小的图片通常是装饰性的
    if img_rect.width < min_size or img_rect.height < min_size:
        return False
    
    # 2. 位置筛选：页眉页脚的小图片通常是logo或装饰
    page_height = page_rect.height
    page_width = page_rect.width
    
    # 位于页面顶部5%或底部5%的小图片可能是logo
    if ((img_rect.y0 < page_height * 0.05 or img_rect.y1 > page_height * 0.95) and 
        img_rect.width < page_width * 0.3 and img_rect.height < page_height * 0.1):
        return False
    
    # 3. 宽高比筛选：极端宽高比通常是装饰性元素
    aspect_ratio = img_rect.width / img_rect.height if img_rect.height > 0 else 0
    if aspect_ratio > 10 or aspect_ratio < 0.1:  # 过于细长或过于扁平
        return False
    
    # 4. 检查周围文本内容：寻找学术相关的关键词
    academic_keywords = [
        'fig', 'figure', 'table', 'chart', 'graph', 'diagram', 'scheme',
        'image', 'photo', 'illustration', 'plot', 'data', 'result', 'analysis',
        'equation', 'formula', 'model', 'experiment', 'method', 'procedure'
    ]
    
    # 扩展搜索区域查找相关文本
    search_area = fitz.Rect(
        max(0, img_rect.x0 - 100),
        max(0, img_rect.y0 - 100), 
        min(page_width, img_rect.x1 + 100),
        min(page_height, img_rect.y1 + 100)
    )
    
    # 获取搜索区域内的文本
    blocks = page.get_text("dict")["blocks"]
    nearby_text = ""
    for block in blocks:
        if "lines" in block:
            block_rect = fitz.Rect(block["bbox"])
            if _rects_overlap(block_rect, search_area):
                for line in block["lines"]:
                    line_text = " ".join(span["text"] for span in line["spans"])
                    nearby_text += line_text + " "
    
    # 检查是否包含学术关键词
    nearby_text_lower = nearby_text.lower()
    has_academic_keywords = any(keyword in nearby_text_lower for keyword in academic_keywords)
    
    # 5. 综合判断
    # 大尺寸图片更可能是学术内容
    is_large = img_rect.width > page_width * 0.4 or img_rect.height > page_height * 0.2
    
    # 如果图片较大，即使没有关键词也可能是学术图片
    if is_large:
        return True
    
    # 中等尺寸图片需要有学术关键词支持
    return has_academic_keywords



def fig_screenshot(pdf_path=PDF_PATH):
    """
    提取PDF中的Figure图表（高精度截图）
    
    Args:
        pdf_path: PDF文件路径
    
    Returns:
        list: figure信息字典列表，包含页码、编号、标题、截图路径等
    
    特点：支持多种标题格式，智能定位，8倍高精度截图
    """
    doc = fitz.open(pdf_path)
    figures = []
    figures_dir = os.path.join(os.path.dirname(pdf_path), "figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    try:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            figure_matches = re.finditer(r'(?:Fig\.?|Figure)\s*(\d+):?\s*(.*?)(?=\n\n|\n[A-Z]|\Z)', 
                                       text, re.DOTALL | re.IGNORECASE)
            
            for match in figure_matches:
                fig_num = match.group(1)
                fig_caption = match.group(2).strip()
                caption_rect = _find_caption_position(page, fig_num)
                
                if caption_rect and _has_image_above(page, caption_rect):
                    figure_rect = _estimate_figure_area(page, caption_rect)
                    screenshot_path = _screenshot_figure(page, figure_rect, page_num + 1, fig_num, figures_dir)
                    
                    figures.append({
                        'page': page_num + 1,
                        'figure_number': fig_num,
                        'caption': f"Fig. {fig_num}: {fig_caption}",
                        'screenshot_path': screenshot_path,
                        'figure_rect': figure_rect
                    })
    finally:
        doc.close()
    
    return figures

def _find_caption_position(page, fig_num):
    """查找figure标题位置，支持fig./Fig./Figure等格式"""
    blocks = page.get_text("dict")["blocks"]
    # 支持所有大小写组合  
    patterns = [
        f"fig. {fig_num}", f"fig.{fig_num}", f"fig {fig_num}",
        f"Fig. {fig_num}", f"Fig.{fig_num}", f"Fig {fig_num}",
        f"FIG. {fig_num}", f"FIG.{fig_num}", f"FIG {fig_num}",
        f"figure {fig_num}", f"Figure {fig_num}", f"FIGURE {fig_num}"
    ]
    
    for block in blocks:
        if "lines" not in block:
            continue
        
        # 提取文本
        block_text = " ".join(" ".join(span["text"] for span in line["spans"]) 
                             for line in block["lines"])
        
        # 不区分大小写匹配
        if any(pattern.lower() in block_text.lower() for pattern in patterns):
            return fitz.Rect(block["bbox"])
    
    return None

def _has_image_above(page, caption_rect, tolerance=10):
    """检查标题上方是否有图片，通过图片对象和文字密度验证"""
    blocks = page.get_text("dict")["blocks"]
    text_blocks = [fitz.Rect(block["bbox"]) for block in blocks if "lines" in block]
    text_blocks.sort(key=lambda rect: rect.y0)
    
    # 找到标题上方相邻区域
    direct_above_bottom = max([50] + [rect.y1 for rect in text_blocks 
                                     if rect.y1 <= caption_rect.y0 + tolerance])
    
    # 定义搜索区域
    search_rect = fitz.Rect(
        caption_rect.x0 - 20, direct_above_bottom - tolerance,
        caption_rect.x1 + 20, caption_rect.y0 + tolerance
    )
    
    # 检查是否有实际图片
    for img in page.get_images(full=True):
        for img_rect in page.get_image_rects(img[0]):
            if _rects_overlap(img_rect, search_rect):
                return True
    
    # 计算文字密度
    text_area = sum((_get_overlap_rect(fitz.Rect(block["bbox"]), search_rect) or 
                    fitz.Rect(0,0,0,0)).width * 
                   (_get_overlap_rect(fitz.Rect(block["bbox"]), search_rect) or 
                    fitz.Rect(0,0,0,0)).height
                   for block in blocks if "lines" in block and 
                   _rects_overlap(fitz.Rect(block["bbox"]), search_rect))
    
    total_area = search_rect.width * search_rect.height
    return total_area > 0 and text_area / total_area < 0.3

def _rects_overlap(rect1, rect2):
    """检查两个矩形是否重叠"""
    return not (rect1.x1 <= rect2.x0 or rect2.x1 <= rect1.x0 or 
                rect1.y1 <= rect2.y0 or rect2.y1 <= rect1.y0)

def _get_overlap_rect(rect1, rect2):
    """获取两个矩形的重叠区域"""
    if not _rects_overlap(rect1, rect2):
        return None
    return fitz.Rect(max(rect1.x0, rect2.x0), max(rect1.y0, rect2.y0),
                     min(rect1.x1, rect2.x1), min(rect1.y1, rect2.y1))

def _estimate_figure_area(page, caption_rect):
    """估算figure显示区域，基于相关图片和文本块分析"""
    page_rect = page.rect
    
    # 找到相关图片
    search_area = fitz.Rect(caption_rect.x0 - 100, max(0, caption_rect.y0 - 400),
                           caption_rect.x1 + 100, caption_rect.y0)
    
    related_rects = []
    for img in page.get_images(full=True):
        for img_rect in page.get_image_rects(img[0]):
            if _rects_overlap(img_rect, search_area):
                related_rects.append(img_rect)
    
    # 分析文本块
    blocks = page.get_text("dict")["blocks"]
    text_blocks = []
    for block in blocks:
        if "lines" in block:
            rect = fitz.Rect(block["bbox"])
            text = " ".join(" ".join(span["text"] for span in line["spans"]) 
                           for line in block["lines"])
            
            # 判断是否为说明文字
            is_caption = (rect.width < page_rect.width * 0.7 or 
                         any(k in text.lower() for k in ['fig.', 'fig ', 'figure', 'table', 'scheme']) or
                         len(text.strip()) < 200)
            
            text_blocks.append({'rect': rect, 'is_caption': is_caption})
    
    text_blocks.sort(key=lambda b: b['rect'].y0)
    
    # 确定边界
    if related_rects:
        top_boundary = max(20, min(r.y0 for r in related_rects) - 5)
        left_boundary = max(page_rect.width * 0.05, min(r.x0 for r in related_rects) - 10)
        right_boundary = min(page_rect.width * 0.95, max(r.x1 for r in related_rects) + 10)
    else:
        # 搜索最近的正文文字块
        top_boundary = 50
        for block in text_blocks:
            if (not block['is_caption'] and 
                block['rect'].y1 < caption_rect.y0 - 20):
                top_boundary = max(top_boundary, block['rect'].y1 + 10)
        
        left_boundary = page_rect.width * 0.05
        right_boundary = page_rect.width * 0.95
    
    return fitz.Rect(left_boundary, top_boundary, right_boundary, caption_rect.y0 - 10)

def _screenshot_figure(page, figure_rect, page_num, fig_num, output_dir):
    """高精度截图保存figure区域（8倍缩放）"""
    # 验证区域有效性
    page_rect = page.rect
    if figure_rect.width <= 0 or figure_rect.height <= 0:
        figure_rect = fitz.Rect(page_rect.width * 0.1, page_rect.height * 0.1,
                               page_rect.width * 0.9, page_rect.height * 0.9)
    
    # 8x缩放高精度截图
    figure_rect &= page_rect
    matrix = fitz.Matrix(8.0, 8.0)
    pixmap = page.get_pixmap(matrix=matrix, clip=figure_rect, alpha=False)
    
    # 保存
    filepath = os.path.join(output_dir, f"page_{page_num}_fig_{fig_num}.png")
    pixmap.save(filepath)
    pixmap = None  # 释放内存
    
    return filepath