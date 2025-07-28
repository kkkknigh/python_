#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF智能分析系统 - 简化版

核心功能：
- PDF文件上传
- 文字提取（OCR + 原生文本）
- 图片提取
- HTML转换
"""

import os
import sys
import gradio as gr
import shutil

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 导入自定义模块
try:
    from document.content_get import text_ocr, pic_extract, text_extract
    from api.ds_fetch import html_convert
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def process_pdf_upload(file):
    """
    处理PDF文件上传并执行核心后端逻辑
    
    Args:
        file: Gradio文件对象
    
    Returns:
        str: 处理结果详情
    """
    if file is None:
        return "❌ 请选择PDF文件"
    
    try:
        # 1. 保存上传文件
        temp_dir = os.path.join(current_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        file_name = os.path.basename(file.name)
        pdf_path = os.path.join(temp_dir, file_name)
        shutil.copy2(file.name, pdf_path)
        
        results = [f"📁 文件上传成功: {file_name}"]
        
        # 2. 文字提取 - 原生文本
        try:
            original_pages = text_extract(pdf_path)
            original_text = " ".join(original_pages)
            results.append(f"✅ 原生文本提取: {len(original_text)} 字符")
        except Exception as e:
            original_text = ""
            results.append(f"❌ 原生文本提取失败: {str(e)}")

        
        # 4. 选择最佳文本
        best_pages = original_pages 
        text_source = "原生文本" 
        if best_pages:
            results.append(f"📝 采用{text_source}作为主要内容")
        
        # 5. 图片提取
        try:
            extracted_images = pic_extract(pdf_path)
            results.append(f"✅ 图片提取成功: {len(extracted_images)} 张")
            if extracted_images:
                picture_dir = os.path.dirname(extracted_images[0])
                results.append(f"📁 图片保存目录: {picture_dir}")
        except Exception as e:
            results.append(f"❌ 图片提取失败: {str(e)}")
        
        # 6. HTML转换
        if best_pages:
            try:
                # 截取前3000字符进行转换
                html_results = html_convert(best_pages)
            except Exception as e:
                results.append(f"❌ HTML转换失败: {str(e)}")
        else:
            results.append("⚠️ 无文本内容，跳过HTML转换")
        
        # 处理完成总结
        results.append("\n" + "="*40)
        results.append("🎉 核心处理流程完成")
        results.append(f"📂 文件存储位置: {temp_dir}")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ 处理过程出错: {str(e)}"

def create_interface():
    """创建简化的Gradio界面"""
    
    with gr.Blocks(title="PDF处理系统", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # 📄 PDF智能处理系统
        
        **核心功能：**
        - 📤 PDF文件上传
        - 📝 文字提取（原生文本 + OCR识别）
        - 🖼️ 图片批量提取
        - 🌐 HTML格式转换
        
        上传PDF文件后系统将自动执行所有处理步骤
        """)
        
        # 文件上传区域
        with gr.Row():
            pdf_file = gr.File(
                label="选择PDF文件",
                file_types=[".pdf"],
                height=100
            )
        
        # 处理按钮
        with gr.Row():
            process_btn = gr.Button(
                "🚀 开始处理", 
                variant="primary", 
                size="lg"
            )
        
        # 结果显示区域
        with gr.Row():
            result_display = gr.Textbox(
                label="处理结果",
                lines=12,
                max_lines=15,
                interactive=False,
                placeholder="点击开始处理按钮查看结果..."
            )
        
        # 绑定处理事件
        process_btn.click(
            fn=process_pdf_upload,
            inputs=[pdf_file],
            outputs=[result_display]
        )
    
    return demo

def main():
    """主函数"""
    print("🚀 启动PDF智能处理系统")
    print("📋 核心功能: 文档上传 → 文字提取 → 图片提取 → HTML转换")
    
    try:
        demo = create_interface()
        
        print("\n✅ 系统就绪!")
        print("🌐 访问地址: http://localhost:7860")
        print("⚠️  按Ctrl+C停止服务\n")
        
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 系统已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
