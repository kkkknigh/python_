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
    
    特点：支持CMYK转RGB，智能过滤装饰图，按页码命名，避免重复提取
    """
    doc = fitz.open(pdf_path)
    saved_files = []
    picture_dir = os.path.join(os.path.dirname(pdf_path), "picture")
    os.makedirs(picture_dir, exist_ok=True)
    
    # 记录已处理的图片，避免重复
    processed_images = set()

    try:
        for page_num, page in enumerate(doc):
            page_img_count = 0  # 每页单独计数
            
            for img in page.get_images(full=True):
                # 使用图片的MD5哈希作为唯一标识符
                img_index = img[0]  # 图片在文档中的索引
                
                # 避免重复处理同一张图片
                if img_index in processed_images:
                    continue
                
                # 获取图片位置信息
                img_rects = page.get_image_rects(img_index)
                if not img_rects:
                    continue
                
                # 合并同一图片的多个位置区域，取最大边界
                combined_rect = img_rects[0]
                for rect in img_rects[1:]:
                    combined_rect = fitz.Rect(
                        min(combined_rect.x0, rect.x0),
                        min(combined_rect.y0, rect.y0), 
                        max(combined_rect.x1, rect.x1),
                        max(combined_rect.y1, rect.y1)
                    )
                
                # 使用筛选函数判断是否为学术相关图片
                if not _is_academic_relevant_image(page, combined_rect):
                    continue  # 跳过无关图片
                
                try:
                    base_image = doc.extract_image(img_index)
                    image = Image.open(BytesIO(base_image["image"]))
                    
                    # 检查图片尺寸，过滤过小的图片
                    if image.width < 50 or image.height < 50:
                        continue
                    
                    # 简单的图片内容检查：检查是否为单色或几乎单色的图片
                    # 这类图片可能是背景、分隔线等装饰元素
                    if image.mode in ['RGB', 'RGBA']:
                        # 转换为灰度来简化分析
                        gray_image = image.convert('L')
                        # 计算像素值的标准差，标准差很小说明颜色变化很小
                        import numpy as np
                        pixels = np.array(gray_image)
                        pixel_std = np.std(pixels)
                        
                        # 如果标准差很小，可能是单色背景
                        if pixel_std < 10:  # 标准差阈值
                            continue

                    # CMYK转RGB
                    if image.mode == 'CMYK':
                        image = image.convert('RGB')
                    elif image.mode not in ['RGB', 'L']:
                        image = image.convert('RGB')
        
                    filepath = os.path.join(picture_dir, f"page_{page_num + 1}_img_{page_img_count + 1}.png")
                    image.save(filepath, "png")
                    saved_files.append(filepath)
                    
                    # 标记为已处理并更新计数
                    processed_images.add(img_index)
                    page_img_count += 1
                    
                except Exception as e:
                    continue
                    
    finally:
        doc.close()

    return saved_files

def _is_academic_relevant_image(page, img_rect, min_size=40):
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
    
    # 4. 检查是否为纯文本区域（避免提取标题等文本内容）
    blocks = page.get_text("dict")["blocks"]
    
    # 计算图片区域内的文字密度
    text_in_image_area = 0
    for block in blocks:
        if "lines" in block:
            block_rect = fitz.Rect(block["bbox"])
            if _rects_overlap(block_rect, img_rect):
                overlap_rect = _get_overlap_rect(block_rect, img_rect)
                if overlap_rect:
                    text_in_image_area += overlap_rect.width * overlap_rect.height
    
    # 如果图片区域内文字密度过高，可能是纯文本，跳过
    image_area = img_rect.width * img_rect.height
    if image_area > 0 and text_in_image_area / image_area > 0.8:
        return False
    
    # 5. 检查周围文本内容：寻找学术相关的关键词
    academic_keywords = [
        'fig', 'figure', 'table', 'chart', 'graph', 'diagram', 'scheme',
        'image', 'photo', 'illustration', 'plot', 'data', 'result', 'analysis',
        'equation', 'formula', 'model', 'experiment', 'method', 'procedure',
        'section', 'chapter', 'paper', 'study', 'research', 'conclusion',
        'abstract', 'introduction', 'discussion', 'algorithm', 'function',
        'structure', 'system', 'process', 'comparison', 'evaluation'
    ]
    
    # 扩展搜索区域查找相关文本
    search_area = fitz.Rect(
        max(0, img_rect.x0 - 100),
        max(0, img_rect.y0 - 100), 
        min(page_width, img_rect.x1 + 100),
        min(page_height, img_rect.y1 + 100)
    )
    
    # 获取搜索区域内的文本
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
    
    # 6. 综合判断
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
    
    特点：支持多种标题格式，智能定位，8倍高精度截图，避免重复处理
    """
    doc = fitz.open(pdf_path)
    figures = []
    figures_dir = os.path.join(os.path.dirname(pdf_path), "figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    # 记录已处理的figure，避免重复
    processed_figures = set()
    
    try:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            figure_matches = re.finditer(r'(?:Fig\.?|Figure)\s*(\d+):?\s*(.*?)(?=\n\n|\n[A-Z]|\Z)', 
                                       text, re.DOTALL | re.IGNORECASE)
            
            for match in figure_matches:
                fig_num = match.group(1)
                fig_caption = match.group(2).strip()
                
                # 创建唯一标识符（页码+图表编号）
                figure_id = f"{page_num + 1}_{fig_num}"
                
                # 避免重复处理同一个figure
                if figure_id in processed_figures:
                    continue
                
                caption_rect = _find_caption_position(page, fig_num)
                
                if caption_rect and _has_image_above(page, caption_rect):
                    try:
                        figure_rect = _estimate_figure_area(page, caption_rect)
                        
                        # 验证figure区域的有效性
                        if figure_rect.width < 50 or figure_rect.height < 50:
                            continue
                            
                        screenshot_path = _screenshot_figure(page, figure_rect, page_num + 1, fig_num, figures_dir)
                        
                        figures.append({
                            'page': page_num + 1,
                            'figure_number': fig_num,
                            'caption': f"Fig. {fig_num}: {fig_caption}",
                            'screenshot_path': screenshot_path,
                            'figure_rect': figure_rect
                        })
                        
                        # 标记为已处理
                        processed_figures.add(figure_id)
                        
                    except Exception as e:
                        continue
                    
    finally:
        doc.close()
    
    return figures

def _find_caption_position(page, fig_num):
    """查找figure/table/scheme标题位置，支持各种格式"""
    blocks = page.get_text("dict")["blocks"]
    # 支持所有大小写组合和不同类型  
    patterns = [
        # Figure patterns
        f"fig. {fig_num}", f"fig.{fig_num}", f"fig {fig_num}",
        f"Fig. {fig_num}", f"Fig.{fig_num}", f"Fig {fig_num}",
        f"FIG. {fig_num}", f"FIG.{fig_num}", f"FIG {fig_num}",
        f"figure {fig_num}", f"Figure {fig_num}", f"FIGURE {fig_num}",
        # Table patterns
        f"tab. {fig_num}", f"tab.{fig_num}", f"tab {fig_num}",
        f"Tab. {fig_num}", f"Tab.{fig_num}", f"Tab {fig_num}",
        f"TAB. {fig_num}", f"TAB.{fig_num}", f"TAB {fig_num}",
        f"table {fig_num}", f"Table {fig_num}", f"TABLE {fig_num}",
        # Scheme patterns
        f"sch. {fig_num}", f"sch.{fig_num}", f"sch {fig_num}",
        f"Sch. {fig_num}", f"Sch.{fig_num}", f"Sch {fig_num}",
        f"SCH. {fig_num}", f"SCH.{fig_num}", f"SCH {fig_num}",
        f"scheme {fig_num}", f"Scheme {fig_num}", f"SCHEME {fig_num}"
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

def _has_image_above(page, caption_rect, tolerance=15):
    """检查标题上方是否有图片，通过图片对象和文字密度验证"""
    blocks = page.get_text("dict")["blocks"]
    text_blocks = [fitz.Rect(block["bbox"]) for block in blocks if "lines" in block]
    text_blocks.sort(key=lambda rect: rect.y0)
    
    # 找到标题上方相邻区域
    direct_above_bottom = max([0] + [rect.y1 for rect in text_blocks 
                                     if (rect.y1 < caption_rect.y0
                                     and rect.width >= caption_rect.width * 0.5)])
    
    # 定义搜索区域（增大搜素范围）
    search_rect = fitz.Rect(
        caption_rect.x0, direct_above_bottom - tolerance,
        caption_rect.x1, caption_rect.y0 + tolerance
    )
    
    # 检查是否有实际图片对象
    has_actual_image = False
    for img in page.get_images(full=True):
        for img_rect in page.get_image_rects(img[0]):
            if _rects_overlap(img_rect, search_rect):
                has_actual_image = True
                break
        if has_actual_image:
            break
    
    # 如果有实际图片对象，直接返回True
    if has_actual_image:
        return True
    
    # 统计文本块并找最近大段落（一次遍历完成Rect构造和is_sec判断）
    blocks = page.get_text("dict")["blocks"]
    caption_width = caption_rect.width
    text_blocks = []
    for block in blocks:
        if "lines" in block:
            rect = fitz.Rect(block["bbox"])
            is_sec = (rect.width >= caption_width * 0.9) and \
                ((abs(rect.x0-caption_rect.x0) <= 50) or (abs(rect.x1-caption_rect.x1) <= 50))
            text_blocks.append({'rect': rect, 'is_sec': is_sec, 'block': block})
    text_blocks.sort(key=lambda b: b['rect'].y0)

    # 找到search_rect上方最近的大段落文字块
    sec_y1 = 0
    for b in reversed(text_blocks):
        if b['is_sec'] and b['rect'].y1 < search_rect.y0:
            sec_y1 = b['rect'].y1
            break

    # 只统计sec_y1和search_rect.y0之间的所有文字块面积（避免重复Rect构造）
    text_area = 0
    for b in text_blocks:
        rect = b['rect']
        if rect.y1 > sec_y1 and rect.y0 < search_rect.y0:
            # 先做包围盒快速判断
            if rect.x1 <= search_rect.x0 or rect.x0 >= search_rect.x1 or rect.y1 <= search_rect.y0 or rect.y0 >= search_rect.y1:
                continue
            # 只在有重叠时才计算面积
            overlap_x0 = max(rect.x0, search_rect.x0)
            overlap_y0 = max(rect.y0, search_rect.y0)
            overlap_x1 = min(rect.x1, search_rect.x1)
            overlap_y1 = min(rect.y1, search_rect.y1)
            if overlap_x1 > overlap_x0 and overlap_y1 > overlap_y0:
                text_area += (overlap_x1 - overlap_x0) * (overlap_y1 - overlap_y0)
    
    total_area = search_rect.width * search_rect.height
    
    # 如果没有实际图片，进行更严格的文字密度检查
    if total_area > 0:
        text_density = text_area / total_area
        # 如果文字密度较低，可能有图片存在
        if text_density < 0.4:  
            return True
    
    # 如果搜索区域很大但没有文字，也可能有图片
    if total_area > 10000 and text_area < 1000:  # 大区域但文字很少
        return True
    
    return False

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
    
    # 扩大搜索区域，确保能找到所有相关图片
   
    blocks = page.get_text("dict")["blocks"]
    text_blocks = [fitz.Rect(block["bbox"]) for block in blocks if "lines" in block]
    text_blocks.sort(key=lambda rect: rect.y0)

    # 筛选搜索区域：宽度小于caption_rect的块不包括在内
    caption_width = caption_rect.width
    filtered_text_blocks = [rect for rect in text_blocks 
                           if rect.width >= caption_width * 0.9
                           and (abs(rect.x0-caption_rect.x0) <= 40
                            or abs(rect.x1-caption_rect.x1) <= 40)]  # 至少是标题宽度的50%

    # 然后计算搜索区域
    direct_above_bottom = max([5] + [rect.y1 for rect in filtered_text_blocks 
                                 if rect.y1 < caption_rect.y0])
    
    search_area = fitz.Rect(
        max(0, caption_rect.x0), 
        max(0, direct_above_bottom),
        min(page_rect.width, caption_rect.x1), 
        caption_rect.y0
    )
    
    related_rects = []
    for img in page.get_images(full=True):
        for img_rect in page.get_image_rects(img[0]):
            if _rects_overlap(img_rect, search_area):
                related_rects.append(img_rect)
    
    # 确定边界
    if related_rects:
        # 获取所有相关图片的边界
        all_x0 = [r.x0 for r in related_rects]
        all_x1 = [r.x1 for r in related_rects]
        all_y0 = [r.y0 for r in related_rects]
        
        # 计算图片的实际边界，给予适当的边距
        img_left = min(all_x0 + [caption_rect.x0])
        img_right = max(all_x1 + [caption_rect.x1])
        img_top = min(all_y0)
        
        # 设置更合理的边界，确保不切割图片
        # 左边界：取图片左边界和页面5%边距中的较小值，但不能小于0
        left_boundary = max(0, img_left)
        
        # 右边界：取图片右边界和页面95%边距中的较大值，但不能超过页面宽度
        right_boundary = min(page_rect.width, img_right)
        
        # 顶边界：图片顶部留少量空间
        top_boundary = max(20, img_top-10)
            
    else:
        # 分析文本块
        blocks = page.get_text("dict")["blocks"]
        text_blocks = []
        for block in blocks:
            if "lines" in block:
                rect = fitz.Rect(block["bbox"])
                # 判断是否为新的段落文字
                block_height = rect.y1 - rect.y0
                # 统计词数
                word_count = 0
                for line in block["lines"]:
                    for span in line["spans"]:
                        word_count += len(span["text"].split())
                is_sec = (
                    (rect.width >= caption_width * 0.6)
                    and ((abs(rect.x0-caption_rect.x0) <= 50) or (abs(rect.x1-caption_rect.x1) <= 50))
                    and (block_height > 15)
                    and (word_count > 1)
                )
            
            
                text_blocks.append({'rect': rect, 'is_sec': is_sec})
        text_blocks.sort(key=lambda b: b['rect'].y0)
        # 选择所有正文text_blocks的最低点作为截图上边界
        candidate_y1 = [0] + [block['rect'].y1 for block in text_blocks if block['is_sec'] and block['rect'].y1 < caption_rect.y0]
        if candidate_y1:
            top_boundary = max(candidate_y1) + 5
        else:
            return
        left_boundary = caption_rect.x0
        right_boundary = caption_rect.x1
    
    return fitz.Rect(left_boundary, top_boundary, right_boundary, caption_rect.y0)

def _screenshot_figure(page, figure_rect, page_num, fig_num, output_dir):
    """高精度截图保存figure区域（8倍缩放）"""
    # 验证区域有效性
    page_rect = page.rect
    
    # 确保figure_rect在页面范围内
    figure_rect = figure_rect & page_rect
    
    # 如果裁剪后区域无效，使用默认区域
    if figure_rect.width <= 10 or figure_rect.height <= 10:
        figure_rect = fitz.Rect(page_rect.width * 0.1, page_rect.height * 0.1,
                               page_rect.width * 0.9, page_rect.height * 0.9)
    
    # 再次确保在页面边界内
    figure_rect = figure_rect & page_rect
    
    try:
        # 8x缩放高精度截图
        matrix = fitz.Matrix(8.0, 8.0)
        pixmap = page.get_pixmap(matrix=matrix, clip=figure_rect, alpha=False)
        
        # 保存
        filepath = os.path.join(output_dir, f"page_{page_num}_fig_{fig_num}.png")
        pixmap.save(filepath)
        pixmap = None  # 释放内存
        
        return filepath
    except Exception as e:
        # 尝试使用更保守的区域重新截图
        safe_rect = fitz.Rect(page_rect.width * 0.1, page_rect.height * 0.1,
                             page_rect.width * 0.9, page_rect.height * 0.9)
        matrix = fitz.Matrix(4.0, 4.0)  # 降低缩放倍数
        pixmap = page.get_pixmap(matrix=matrix, clip=safe_rect, alpha=False)
        
        filepath = os.path.join(output_dir, f"page_{page_num}_fig_{fig_num}_safe.png")
        pixmap.save(filepath)
        pixmap = None
        
        return filepath