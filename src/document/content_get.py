'''
获取 PDF 中文字(OCR/元文本)和图片内容(元数据)
'''

import fitz  
import os
import easyocr
from PIL import Image
from io import BytesIO

ARTICLE_TEXT = None
PDF_PATH = "src/document/article.pdf"

reader = easyocr.Reader(['en'])

def text_ocr(pdf_path=PDF_PATH):
    '''
    使用 OCR 提取 PDF 每页的文本
    
    该函数将 PDF 的每一页转换为图像，然后使用 EasyOCR 进行文字识别，
    提取出文本内容并保存到文件中。
    
    Args:
        pdf_path (str, optional): PDF 文件路径。默认为 PDF_PATH 常量值。
    
    Returns:
        list: 包含每页文本内容的列表，每个元素代表一页的文本
    
    Side Effects:
        - 修改全局变量 ARTICLE_TEXT
        - 在 PDF 同目录下创建 textOCR.txt 文件
    
    Raises:
        FileNotFoundError: 当 PDF 文件不存在时
        Exception: OCR 处理过程中的其他异常
    '''
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

def text_extract(pdf_path=PDF_PATH):
    '''
    提取 PDF 中的原始文字并保存为 txt 文件
    
    该函数直接从 PDF 文档中提取嵌入的文本内容（非 OCR），
    适用于包含可选择文本的 PDF 文件。
    
    Args:
        pdf_path (str, optional): PDF 文件路径。默认为 PDF_PATH 常量值。
    
    Returns:
        list: 包含每页文本内容的列表，每个元素代表一页的原始文本
    
    Side Effects:
        - 在 PDF 同目录下创建 text_ori.txt 文件
    
    Note:
        - 只能提取 PDF 中嵌入的文本，无法识别图片中的文字
        - 对于扫描版 PDF 或图片型 PDF，建议使用 text_ocr() 函数
        - 提取速度比 OCR 方式快，但依赖于 PDF 的文本结构
    
    Raises:
        FileNotFoundError: 当 PDF 文件不存在时
        IOError: 文件读写过程中的 IO 异常
    '''
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