import os
import shutil
import time
import threading
import argparse
import sys
import re
import uuid
from pathlib import Path

import gradio as gr
import fitz

# 设置项目根目录路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ui.gradio_ui import create_reader_ui
from src.api.ds_fetch import chat as api_chat, html_convert, translate, clinet_initialize
from src.document.content_get import text_extract
from src.document.picture_get import pic_extract, fig_screenshot
from src.document.content_integrate import html_img_replace

processing_status = {"status": "idle", "message": "请上传PDF并点击处理", "completed_pages": [], "progress": 0}

def setup_environment():
    """设置环境和创建必要目录"""
    
    clinet_initialize()
    
    temp_dir = project_root / "temp"
    
    # 清除已存在的目录
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    
    # 重新创建目录
    temp_dir.mkdir(exist_ok=True)
    
    for subdir in ["html/original", "html/translated", "html/final", "picture", "figures"]:
        (temp_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    return temp_dir

def get_temp_dir():
    return project_root/"temp"

def load_html(temp_dir):
    """
    获取可供显示的的html
    优先级：/final > /original > text_ori.txt
    """
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
    
    html_dir_ori = temp_dir / "html" / "original"
    if html_dir_ori.exists():
        html_files = sorted(html_dir_ori.glob("*.html"))
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

def process_pdf_background(pdf_path):
    """后台异步处理PDF"""
    
    global processing_status
    completed_pages = []
    try:
    
        # 1. 图片提取
        processing_status.update({
            "status": "processing", 
            "message": "图片提取中", 
            "completed_pages": completed_pages, 
            "progress": 5
        })
        pic_paths = pic_extract(pdf_path)
        fig_paths = fig_screenshot(pdf_path)
        if (not pic_paths) and (fig_paths):
            processing_status.update({
                "status": "error", 
                "message": "图片提取失败", 
                "completed_pages": completed_pages, 
                "progress": 5
            })
            return
          
        # 2. 文字提取
        processing_status.update({
            "status": "processing", 
            "message": "文本提取中", 
            "completed_pages": completed_pages, 
            "progress": 10
        })
        text_pages = text_extract(str(pdf_path))
        if not text_pages:
            processing_status.update({
                "status": "error", 
                "message": "文本提取失败", 
                "completed_pages": completed_pages,  
                "progress": 10
            })
            return
        
        total_pages = len(text_pages)
        
        # 3. 依次处理所有页面
        temp_dir = get_temp_dir()
        
        for i, text_page in enumerate(text_pages):
            page_num = i+1
            processing_status.update({
                "status": "processing", 
                "message": f"处理第 {page_num}页html转换中", 
                "completed_pages": completed_pages,
                "progress": 90*i/total_pages + 10
            })
            
            # 1.HTML转换 
            html_page = html_convert(text_page, page_num)
            if not html_page:
                processing_status.update({
                    "status": "error", 
                    "message": f"处理第 {page_num}页html转换失败", 
                    "completed_pages": completed_pages,
                    "progress": 90*i/total_pages + 10
                })
                return
            
            # 2.翻译HTML
            processing_status.update({
                "status": "processing", 
                "message": f"翻译第 {page_num}页中", 
                "completed_pages": completed_pages,
                "progress": 90*i/total_pages + 10 + 45/total_pages
            })

            translated_html = translate(html_page, page_num)
            if not translated_html:
                processing_status.update({
                    "status": "error", 
                    "message": f"翻译第 {page_num}页失败", 
                    "completed_pages": completed_pages,
                    "progress": 90*i/total_pages + 10 + 45/total_pages
                })
                return
            
            translated_file_path = temp_dir / "html" / "translated"/ f"page_{page_num}.html"
            
            # 3. 图片嵌入
            processing_status.update({
                "status": "processing", 
                "message": f"整合第 {page_num}页图片中", 
                "completed_pages": completed_pages,
                "progress": 90*i/total_pages + 10 + 45/total_pages
            })
            final_html = html_img_replace(str(translated_file_path), output_dir=str(temp_dir / "html" / "final"))
            if not final_html:
                processing_status.update({
                    "status": "error", 
                    "message": f"整合第 {page_num}页图片失败", 
                    "completed_pages": completed_pages,
                    "progress": 90*i/total_pages + 10 + 45/total_pages
                })
                return
            
            # 页面完成，添加到完成列表
            completed_pages.append(page_num)
            processing_status.update({
                "status": "page_completed", 
                "message": f"第 {page_num} 页处理完成！({page_num}/{total_pages})", 
                "completed_pages": completed_pages,
                "progress": 90*i/total_pages + 10 + 45/total_pages
            })

        processing_status.update({
            "status": "processing", 
            "message": "所有页面处理完成，正在最终整理中", 
            "completed_pages": completed_pages,
            "progress": 99
        })
    
        processing_status.update({
            "status": "completed", 
            "message": f"处理完成！共处理 {total_pages} 页", 
            "completed_pages": completed_pages,
            "progress": 100
        })
        
    except Exception as e:
        processing_status.update({
            "status": "error", 
            "message": f"PDF处理失败: {str(e)}",
            "completed_pages": completed_pages,
            "progress": 0
        })
    
def start_pdf_processing(file):
    """启动PDF处理任务"""
    global processing_status
    
    if file is None:
        return "错误：未选择任何文件", None
    
    try:
        # 重置处理状态
        processing_status.update({
            "status": "processing", 
            "message": "开始处理", 
            "completed_pages": [], 
            "progress": 0
        })
        
        temp_dir = get_temp_dir()
        
        # 清理旧文件
        for cleanup_dir in ["html", "picture", "figures"]:
            cleanup_path = temp_dir / cleanup_dir
            if cleanup_path.exists():
                shutil.rmtree(cleanup_path)
        
        # 重新创建目录
        for subdir in ["html/original", "html/translated", "html/final", "picture", "figures"]:
            (temp_dir / subdir).mkdir(parents=True, exist_ok=True)

        # 保存PDF文件
        pdf_path = temp_dir / "article.pdf"
        shutil.copy2(file.name, str(pdf_path))
    
        # 启动后台处理线程
        thread = threading.Thread(target=process_pdf_background, args=(str(pdf_path),))
        thread.daemon = True
        thread.start()
        
        return "处理已开始，请等待..."
        
    except Exception as e:
        return f"启动处理失败: {str(e)}"
    
def check_processing_status():
    """检查处理状态"""
    status = processing_status
    
    if status["status"] == "idle":
        return status["message"], False, 0, []
    elif status["status"] == "processing":
        return status["message"], False, status.get("progress", 0), status.get("completed_pages", [])
    elif status["status"] == "page_completed":
        return status["message"], False, status.get("progress", 0), status.get("completed_pages", [])
    elif status["status"] == "completed":
        return status["message"], True, 100, status.get("completed_pages", [])
    elif status["status"] == "error":
        return status["message"], True, 0, status.get("completed_pages", [])
    else:
        return "未知状态", False, 0, []

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
            get_temp_dir,
            load_html,
            start_pdf_processing,
            check_processing_status,
            api_chat
        )
        
        demo.launch(
            server_port=args.port,
            server_name=args.host,
            share=True,
            show_error=True,
            quiet=False,
            inbrowser=True,
            allowed_paths=[str(project_root)]  # 允许访问项目根目录下的文件
        )
            
    except ImportError:
        sys.exit(1)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()