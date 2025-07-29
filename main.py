import os
import shutil
import time
import threading
import argparse
import sys
import re
from pathlib import Path

import gradio as gr
import fitz

# 设置项目根目录路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ui.gradio_ui import create_reader_ui
from src.api.ds_fetch import chat as api_chat, html_convert, translate
from src.document.content_get import text_extract
from src.document.picture_get import pic_extract, fig_screenshot
from src.document.content_integrate import batch_replace_html_images

# 全局变量跟踪处理状态
processing_status = {}
background_tasks = {}

def setup_environment():
    """设置环境和创建必要目录"""
    temp_dir = project_root / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    
    for subdir in ["html/original", "html/translated", "html/final", "picture", "figures"]:
        (temp_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    return temp_dir

def get_temp_dir():
    return project_root/"temp"

def load_html(temp_dir):
    """获取转化后html"""
    html_dir = temp_dir / "html" / "final"
    if html_dir.exists():
        html_files = sorted(html_dir.glob("*.html"))
        if html_files:
            html_contents = []
            for html_file in html_files:
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        html_contents.append(f.read())
                except Exception:
                    html_contents.append("<p>文件读取失败</p>")
            return html_contents
    
    text_file = temp_dir / "text_ori.txt"
    if text_file.exists():
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
                html_content = f"<div style='white-space: pre-wrap; font-family: Arial, sans-serif; line-height: 1.6;'>{content}</div>"
                return [html_content]
        except Exception:
            pass
    
    return ["<p>未找到可显示的文档内容</p>"]

def process_uploaded_pdf(file):
    """处理PDF"""
    if file is None:
        return "请选择PDF文件", [], "", "<p>请上传PDF文件</p>", 0, "第 **-** 页 / 共 **0** 页", "ready"
    
    try:
        temp_dir = get_temp_dir()
        os.makedirs(temp_dir, exist_ok=True)
        
        # 保存上传的PDF文件
        file_name = "article.pdf"
        pdf_path = os.path.join(temp_dir, file_name)
        shutil.copy2(file.name, pdf_path)

        # 文字提取
        text_pages = text_extract(str(pdf_path))

        # 图片提取
        pic_extract(str(pdf_path))
        fig_screenshot(pdf_path)

        # html转化
        html_pages = html_convert(text_pages)

        # 翻译
        for html_ in html_pages:
            translate(html_)

        # 添加图片
        batch_replace_html_images()
            
    except Exception as e:
        error_msg = f"PDF处理失败: {str(e)}"
        return error_msg, [], "", "<p>PDF处理失败</p>", 0, "error"

def main():
    parser = argparse.ArgumentParser(
        description='论文阅读器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 命令行传入API密钥
  python main.py --api-key sk-your-api-key-here
  
  # 使用环境变量
  export DEEPSEEK_API_KEY=sk-your-api-key-here
  python main.py
        """
    )
    
    parser.add_argument('--api-key', help='DeepSeek API密钥')
    parser.add_argument('--port', type=int, default=7860, help='Web界面端口号 (默认: 7860)')
    parser.add_argument('--share', action='store_true', help='生成公共链接分享')
    parser.add_argument('--host', default="127.0.0.1", help='服务器主机地址 (默认: 127.0.0.1)')
    
    args = parser.parse_args()
    
    if args.api_key:
        os.environ['DEEPSEEK_API_KEY'] = args.api_key
    
    setup_environment()
    
    try:
        demo = create_reader_ui(
            get_temp_dir_func=get_temp_dir,
            load_documents_func=load_html,
            process_pdf_func=process_uploaded_pdf,
            chat_func=api_chat
        )
        
        demo.launch(
            server_port=args.port,
            server_name=args.host,
            share=args.share,
            show_error=True,
            quiet=False,
            inbrowser=True
        )
            
    except ImportError:
        sys.exit(1)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()