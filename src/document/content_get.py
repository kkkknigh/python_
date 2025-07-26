'''
获取 PDF 中文字和图片内容（支持 OCR）
'''

import fitz  # PyMuPDF
import base64
import os
import tempfile
import pytesseract
from PIL import Image
from io import BytesIO

ARTICLE_TEXT = ""
PDF_PATH = 'src/document/article.pdf'

def text_ocr(pdf_path=PDF_PATH):
    '''
    使用 OCR 提取 PDF 每页的文本
    '''
    doc = fitz.open(pdf_path)
    global ARTICLE_TEXT
    ARTICLE_TEXT = ""

    for page in doc:
        pix = page.get_pixmap(dpi=300)
        image = Image.open(BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        ARTICLE_TEXT += text + "\n\n"

    return ARTICLE_TEXT.strip()

def pic_extract(pdf_path=PDF_PATH):
    '''
    提取 PDF 中的所有图片，返回 base64 字符串列表
    '''
    doc = fitz.open(pdf_path)
    images = []

    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            images.append(f"data:image/{image_ext};base64,{image_base64}")

    return images
