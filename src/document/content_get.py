"""
PDF文本提取模块

功能：
- OCR文字识别提取（适用于扫描版PDF）
- 原始文本提取（适用于包含可选择文本的PDF）
- 自动保存提取结果为txt文件
"""
import fitz  
import os
#import easyocr

ARTICLE_TEXT = None
PDF_PATH = "src/document/article.pdf"

#reader = easyocr.Reader(['en'])
'''
def text_ocr(pdf_path=PDF_PATH):
    """
    使用OCR提取PDF文本（适用于扫描版PDF）
    
    Args:
        pdf_path: PDF文件路径
    
    Returns:
        list: 每页文本内容的列表
    
    特点：转换为高分辨率图像后进行OCR识别，自动保存为textOCR.txt
    """
    doc = fitz.open(pdf_path)
    global ARTICLE_TEXT
    ARTICLE_TEXT = []

    try:
        for page in doc:

            pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72)) 
            img_bytes = pix.tobytes("png")

            results = reader.readtext(img_bytes)
            page_text = " ".join([res[1] for res in results])
            ARTICLE_TEXT.append(page_text) 
      
    finally:
        doc.close()

    text_file_path = os.path.join(os.path.dirname(pdf_path), "textOCR.txt")
    with open(text_file_path, 'w', encoding='utf-8') as f:
        f.write(" ".join(ARTICLE_TEXT))

    return ARTICLE_TEXT
'''

def text_extract(pdf_path=PDF_PATH):
    """
    提取PDF中的原始文本（适用于可选择文本的PDF）
    
    Args:
        pdf_path: PDF文件路径
    
    Returns:
        list: 每页文本内容的列表
    
    特点：直接提取嵌入文本，速度快，自动保存为text_ori.txt
    注意：不适用于扫描版PDF，建议使用text_ocr()
    """
    doc = fitz.open(pdf_path)
    text = []
    try:
        for page in doc:
           text.append(page.get_text("text"))
    finally:
        doc.close()

    text_file_path = os.path.join(os.path.dirname(pdf_path), "text_ori.txt")
    with open(text_file_path, 'w', encoding='utf-8') as f:
        f.write(" ".join(text))
    return text
