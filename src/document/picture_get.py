'''
和图片内容(元数据)
'''

from PIL import Image
from io import BytesIO
import re
import fitz  
import os

PDF_PATH = "src/document/article.pdf"

def pic_extract(pdf_path=PDF_PATH):
    '''
    提取 PDF 中的所有图片并保存为 PNG 文件
    
    该函数遍历 PDF 的每一页，提取其中的所有图片，进行格式转换后
    保存为 PNG 格式的文件。支持 CMYK 到 RGB 的颜色空间转换。
    
    Args:
        pdf_path (str, optional): PDF 文件路径。默认为 PDF_PATH 常量值。
    
    Returns:
        list: 包含所有保存图片文件路径的列表
    
    Side Effects:
        - 在 PDF 同目录下创建 picture 文件夹
        - 保存提取的图片文件到 picture 文件夹中
    
    Note:
        - 图片文件命名格式：page_{页码}_img_{图片序号}.png
        - 自动处理 CMYK 颜色模式转换为 RGB
        - 不支持的颜色模式会统一转换为 RGB
    
    Raises:
        FileNotFoundError: 当 PDF 文件不存在时
        IOError: 图片保存过程中的 IO 异常
    '''
    doc = fitz.open(pdf_path)
    saved_files = []
    
    # 确保图片目录存在
    picture_dir = os.path.join(os.path.dirname(pdf_path), "picture")
    os.makedirs(picture_dir, exist_ok=True)

    try:
        img_count = 0
        for page_num, page in enumerate(doc):
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(BytesIO(image_bytes))

                   #CMYK到RGB转换
                if image.mode == 'CMYK':
                    image = image.convert('RGB')
                elif image.mode not in ['RGB', 'L']:
                    image = image.convert('RGB')
    
                filename = f"page_{page_num + 1}_img_{img_count + 1}.png"
                filepath = os.path.join(picture_dir, filename)
                image.save(filepath, "png")
                saved_files.append(filepath)
                img_count += 1
    finally:
        doc.close()

    return saved_files


def fig_screenshot(pdf_path=PDF_PATH):
    '''
    以截图形式提取 PDF 中的 Figure
    
    该函数通过分析 PDF 文本中的 "Fig." 引用，定位并截图保存完整的 figure 区域。
    
    Args:
        pdf_path (str, optional): PDF 文件路径。默认为 PDF_PATH 常量值。
    
    Returns:
        list: 包含所有 figure 信息的列表，每个元素包含：
            - page: 页码
            - figure_number: figure 编号
            - caption: figure 标题
            - screenshot_path: 截图保存路径
            - figure_rect: figure 在页面中的位置
    
    Side Effects:
        - 在 PDF 同目录下创建 figures 文件夹
        - 保存 figure 截图文件到 figures 文件夹中
    
    Note:
        - 截图文件命名格式：page_{页码}_fig_{编号}.png
        - 使用 2x 缩放以获得高清截图
        - 自动估算 figure 位置（通常在标题上方）
    
    Raises:
        FileNotFoundError: 当 PDF 文件不存在时
        IOError: 截图保存过程中的 IO 异常
    '''
    doc = fitz.open(pdf_path)
    figures = []
    
    # 确保 figures 目录存在
    figures_dir = os.path.join(os.path.dirname(pdf_path), "figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    try:
        for page_num, page in enumerate(doc):
            # 获取页面文本
            text = page.get_text()
            
            # 查找所有 figure 引用，支持 Fig. 和 Figure 两种格式
            figure_matches = re.finditer(r'(?:Fig\.|Figure)\s*(\d+):?\s*(.*?)(?=\n\n|\n[A-Z]|\Z)', text, re.DOTALL | re.IGNORECASE)
            
            for match in figure_matches:
                fig_num = match.group(1)
                fig_caption = match.group(2).strip()
                
                # 查找 figure 标题在页面中的精确位置，支持多种格式
                caption_rect = _find_caption_position(page, fig_num)
                
                if caption_rect:
                    # 检查上方是否有图片，筛选掉正文中的fig引用
                    if _has_image_above(page, caption_rect):
                        # 估算 figure 的位置（通常在标题上方）
                        figure_rect = _estimate_figure_area(page, caption_rect)
                        
                        # 截图保存 figure
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
    '''
    查找 figure 标题在页面中的位置，支持多种格式
    
    Args:
        page: PyMuPDF 页面对象
        fig_num (str): figure 编号，如 "4"
    
    Returns:
        fitz.Rect: 标题位置矩形，如果未找到返回 None
    '''
    # 获取页面的文本块信息
    blocks = page.get_text("dict")["blocks"]
    
    # 构建多种可能的 figure 引用格式
    figure_patterns = [
        f"fig. {fig_num}",      # fig. 4
        f"fig.{fig_num}",       # fig.4
        f"figure {fig_num}",    # figure 4
        f"figure{fig_num}",     # figure4
    ]
    
    for block in blocks:
        if "lines" not in block:
            continue
            
        # 提取块中的所有文本
        block_text = ""
        for line in block["lines"]:
            line_text = " ".join([span["text"] for span in line["spans"]])
            block_text += line_text + " "
        
        # 检查是否包含任一 figure 引用格式
        block_text_lower = block_text.lower()
        for pattern in figure_patterns:
            if pattern in block_text_lower:
                return fitz.Rect(block["bbox"])
    
    return None

def _has_image_above(page, caption_rect, tolerance=10):
    '''
    检查figure标题上方直接接触的区域是否有图片，用于筛选真正的图片标题
    
    Args:
        page: PyMuPDF 页面对象
        caption_rect: 标题位置矩形
        tolerance (int): 允许的间距容差（点数）
    
    Returns:
        bool: 如果上方直接接触区域有图片返回True，否则返回False
    '''
    # 获取页面所有文本块，找到紧邻标题上方的区域
    blocks = page.get_text("dict")["blocks"]
    text_blocks = []
    
    for block in blocks:
        if "lines" in block:  # 只处理文本块
            block_rect = fitz.Rect(block["bbox"])
            text_blocks.append(block_rect)
    
    # 按y坐标排序（从上到下）
    text_blocks.sort(key=lambda rect: rect.y0)
    
    # 找到标题上方直接相邻的区域
    caption_top = caption_rect.y0
    direct_above_bottom = 50  # 默认从页面顶部开始
    
    # 查找标题上方最近的文本块
    for block_rect in text_blocks:
        if block_rect.y1 <= caption_top + tolerance:  # 在标题上方或接触
            direct_above_bottom = max(direct_above_bottom, block_rect.y1)
    
    # 定义直接接触的搜索区域
    direct_search_rect = fitz.Rect(
        caption_rect.x0 - 20,  # 左边界稍微扩展
        direct_above_bottom - tolerance,  # 从上方文本块底部开始
        caption_rect.x1 + 20,  # 右边界稍微扩展
        caption_rect.y0 + tolerance  # 到标题顶部
    )
    
    # 检查直接接触区域是否有实际图片
    images = page.get_images(full=True)
    for img in images:
        img_rects = page.get_image_rects(img[0])
        for img_rect in img_rects:
            if _rects_overlap(img_rect, direct_search_rect):
                return True
    
    # 如果没有实际图片，检查该区域是否主要是非文字内容
    # 计算直接接触区域的文字密度
    text_area_in_region = 0
    total_search_area = direct_search_rect.width * direct_search_rect.height
    
    if total_search_area <= 0:
        return False
    
    for block in blocks:
        if "lines" in block:
            block_rect = fitz.Rect(block["bbox"])
            if _rects_overlap(block_rect, direct_search_rect):
                overlap_rect = _get_overlap_rect(block_rect, direct_search_rect)
                if overlap_rect:
                    text_area_in_region += overlap_rect.width * overlap_rect.height
    
    # 如果文字密度低于30%，认为可能有图片内容
    text_density = text_area_in_region / total_search_area
    return text_density < 0.3

def _rects_overlap(rect1, rect2):
    '''
    检查两个矩形是否重叠
    
    Args:
        rect1, rect2: fitz.Rect 对象
    
    Returns:
        bool: 如果重叠返回True
    '''
    return not (rect1.x1 <= rect2.x0 or rect2.x1 <= rect1.x0 or 
                rect1.y1 <= rect2.y0 or rect2.y1 <= rect1.y0)

def _get_overlap_rect(rect1, rect2):
    '''
    获取两个矩形的重叠区域
    
    Args:
        rect1, rect2: fitz.Rect 对象
    
    Returns:
        fitz.Rect: 重叠区域矩形，如果不重叠返回None
    '''
    if not _rects_overlap(rect1, rect2):
        return None
    
    x0 = max(rect1.x0, rect2.x0)
    y0 = max(rect1.y0, rect2.y0)
    x1 = min(rect1.x1, rect2.x1)
    y1 = min(rect1.y1, rect2.y1)
    
    return fitz.Rect(x0, y0, x1, y1)

def _estimate_figure_area(page, caption_rect):
    '''
    基于标题位置估算 figure 的显示区域
    通过向上搜索直到遇到其他文字块来确定 figure 的上边界，确保不切掉图片
    
    Args:
        page: PyMuPDF 页面对象
        caption_rect: 标题位置矩形
    
    Returns:
        fitz.Rect: 估算的 figure 位置矩形
    '''
    page_rect = page.rect
    margin_ratio = 0.05  # 页面边距比例
    
    # 首先找到与该figure相关的所有图片
    images = page.get_images(full=True)
    related_image_rects = []
    
    search_area = fitz.Rect(
        caption_rect.x0 - 100,
        max(0, caption_rect.y0 - 400),  # 向上搜索400点
        caption_rect.x1 + 100,
        caption_rect.y0
    )
    
    # 收集标题上方的所有图片位置
    for img in images:
        img_rects = page.get_image_rects(img[0])
        for img_rect in img_rects:
            if _rects_overlap(img_rect, search_area):
                related_image_rects.append(img_rect)
    
    # 获取页面所有文本块
    blocks = page.get_text("dict")["blocks"]
    text_blocks = []
    page_width = page_rect.width
    
    # 过滤出文本块，区分正文和图片说明文字
    for block in blocks:
        if "lines" in block:  # 只处理文本块
            block_rect = fitz.Rect(block["bbox"])
            block_width = block_rect.width
            
            # 提取块中的文本内容用于分析
            block_text = ""
            for line in block["lines"]:
                line_text = " ".join([span["text"] for span in line["spans"]])
                block_text += line_text + " "
            
            # 判断是否为图片说明文字的标准：
            # 1. 宽度小于页面宽度的70%（说明文字通常较窄）
            # 2. 或者包含常见的图片说明关键词
            is_caption_text = (
                block_width < page_width * 0.7 or  # 宽度较窄
                any(keyword in block_text.lower() for keyword in [
                    'fig.', 'figure', 'table', 'scheme', 'chart', 
                    'diagram', 'image', 'photo', 'illustration'
                ]) or
                len(block_text.strip()) < 200  # 文字较少（可能是说明文字）
            )
            
            text_blocks.append({
                'rect': block_rect,
                'text': block_text,
                'width': block_width,
                'is_caption': is_caption_text
            })
    
    # 按y坐标（从上到下）排序
    text_blocks.sort(key=lambda block: block['rect'].y0)
    
    # 找到当前标题块的位置
    caption_y = caption_rect.y0
    
    # 确定上边界：优先考虑图片位置，然后考虑文本块
    if related_image_rects:
        # 如果有相关图片，以最上方图片的顶部为准
        top_boundary = min(img_rect.y0 for img_rect in related_image_rects) - 5
        # 确保不超出页面顶部
        top_boundary = max(20, top_boundary)
    else:
        # 如果没有图片，向上搜索最近的正文文字块
        top_boundary = 50  # 默认上边界（页面顶部留白）
        
        for block in text_blocks:
            block_rect = block['rect']
            # 只考虑正文文字块作为截断边界
            if not block['is_caption'] and block_rect.y1 < caption_y - 20:  # 留间距
                # 更新上边界为这个正文块的底部
                top_boundary = max(top_boundary, block_rect.y1 + 10)
    
    # 确定左右边界：如果有图片，以图片的边界为准
    if related_image_rects:
        left_boundary = min(img_rect.x0 for img_rect in related_image_rects) - 10
        right_boundary = max(img_rect.x1 for img_rect in related_image_rects) + 10
        
        # 确保不超出页面边界，但保持适当的边距
        left_boundary = max(page_rect.width * margin_ratio, left_boundary)
        right_boundary = min(page_rect.width * (1 - margin_ratio), right_boundary)
    else:
        # 如果没有图片，使用默认边距
        left_boundary = page_rect.width * margin_ratio
        right_boundary = page_rect.width * (1 - margin_ratio)
    
    # 下边界：标题上方留10点间距
    bottom_boundary = caption_rect.y0 - 10
    
    figure_rect = fitz.Rect(
        left_boundary,
        top_boundary,
        right_boundary,
        bottom_boundary
    )
    
    return figure_rect

def _screenshot_figure(page, figure_rect, page_num, fig_num, output_dir):
    '''
    高精度截图保存 figure 区域
    
    Args:
        page: PyMuPDF 页面对象
        figure_rect: figure 位置矩形
        page_num (int): 页码
        fig_num (str): figure 编号
        output_dir (str): 输出目录
    
    Returns:
        str: 保存的截图文件路径
    '''
    # 使用更高的缩放因子以获得超高清截图
    zoom_factor = 8.0  # 提升到4x缩放以获得更高精度
    matrix = fitz.Matrix(zoom_factor, zoom_factor)
    
    # 验证截图区域的有效性
    page_rect = page.rect
    if figure_rect.width <= 0 or figure_rect.height <= 0:
        # 如果计算出的区域无效，使用页面中央区域作为备选
        figure_rect = fitz.Rect(
            page_rect.width * 0.1,
            page_rect.height * 0.1,
            page_rect.width * 0.9,
            page_rect.height * 0.9
        )
    
    # 确保截图区域在页面范围内
    figure_rect = figure_rect & page_rect  # 取交集，确保不超出页面边界
    
    # 获取指定区域的高分辨率像素图
    pixmap = page.get_pixmap(matrix=matrix, clip=figure_rect, alpha=False)
    
    # 生成文件名和路径
    filename = f"page_{page_num}_fig_{fig_num}.png"
    filepath = os.path.join(output_dir, filename)
    
    # 保存高质量截图
    pixmap.save(filepath)
    pixmap = None  # 释放内存
    
    return filepath