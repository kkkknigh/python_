'''
获取 PDF 中文字(OCR/元文本)和图片内容(元数据)
'''

import fitz  # PyMuPDF
import os
import easyocr
from PIL import Image, ImageCms
from io import BytesIO

ARTICLE_TEXT = ""
PDF_PATH = "python_/src/document/article.pdf"

reader = easyocr.Reader(['en'])

def text_ocr(pdf_path=PDF_PATH):
    '''
    使用 OCR 提取 PDF 每页的文本
    '''
    doc = fitz.open(pdf_path)
    global ARTICLE_TEXT
    ARTICLE_TEXT = ""

    try:
        for page in doc:

            pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))  # 设置DPI
            img_bytes = pix.tobytes("png")

            results = reader.readtext(img_bytes)
            page_text = " ".join([res[1] for res in results])
            ARTICLE_TEXT += page_text 
      
    finally:
        doc.close()

    text_file_path = os.path.join(os.path.dirname(pdf_path), "textOCR.txt")
    with open(text_file_path, 'w', encoding='utf-8') as f:
        f.write(ARTICLE_TEXT.strip())

    return ARTICLE_TEXT.strip()

def pic_extract(pdf_path=PDF_PATH):
    '''
    提取 PDF 中的所有图片并保存为 PNG 文件
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

                   # 简单但有效的CMYK到RGB转换
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

def text_extract(pdf_path=PDF_PATH):
    '''
    提取 PDF 中的文字并保存为md
    '''
    doc = fitz.open(pdf_path)
    text = ""
    try:
        for page in doc:
           text += page.get_text("text")
    finally:
        doc.close()

    text_file_path = os.path.join(os.path.dirname(pdf_path), "text_ori.txt")
    with open(text_file_path, 'w', encoding='utf-8') as f:
        f.write(text.strip())
    return text
