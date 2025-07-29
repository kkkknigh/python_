#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF智能分析系统 - 简化版

核心功能：
- PDF文件上传
- 文字提取（OCR + 原生文本）
- 图片提取
- 截图
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
    from src.document.content_get import text_extract
    from src.api.ds_fetch import html_convert
    from src.document.picture_get import pic_extract, fig_screenshot
    from src.api.ds_fetch import translate
    from src.document.content_integrate import html_pic_replace, batch_replace_html_images
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def process_pdf_upload(file):
    """
    PDF完整处理流程 - 测试版（支持分步输出）
    
    Args:
        file: Gradio文件对象
    
    Returns:
        str: 处理结果详情
    """
    if file is None:
        return "❌ 请选择PDF文件"
    
    # 使用生成器函数实现分步输出
    def process_steps():
        results = []
        
        try:
            # 步骤1: 文件准备
            results.append("🚀 开始PDF处理流程")
            yield "\n".join(results)
            
            temp_dir = os.path.join(current_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            file_name = os.path.basename(file.name)
            pdf_path = os.path.join(temp_dir, file_name)
            shutil.copy2(file.name, pdf_path)
            results.append(f"✅ 文件保存: {file_name}")
            yield "\n".join(results)
            
            # 步骤2: 文本提取
            results.append("\n📝 步骤2: 文本提取")
            results.append("🔄 正在提取PDF文本内容...")
            yield "\n".join(results)
            
            try:
                pages = text_extract(pdf_path)
                if pages and any(pages):
                    results.append(f"✅ 提取文本: {len(pages)} 页，共 {sum(len(p) for p in pages)} 字符")
                    best_pages = pages
                else:
                    results.append("⚠️ 未提取到文本内容")
                    best_pages = []
            except Exception as e:
                results.append(f"❌ 文本提取失败: {str(e)}")
                best_pages = []
            yield "\n".join(results)
            
            # 步骤3: 图片提取
            results.append("\n🖼️ 步骤3: 图片提取")
            results.append("🔄 正在扫描PDF中的图片...")
            yield "\n".join(results)
            
            try:
                # 提取常规图片
                results.append("📸 提取常规图片中...")
                yield "\n".join(results)
                
                images = pic_extract(pdf_path)
                results.append(f"✅ 常规图片: {len(images)} 张")
                yield "\n".join(results)
                
                # 提取图表截图
                results.append("📊 生成图表截图中...")
                yield "\n".join(results)
                
                figures = fig_screenshot(pdf_path)
                results.append(f"✅ 图表截图: {len(figures)} 个")
                
                # 显示保存路径
                if images:
                    results.append(f"📁 图片目录: {os.path.dirname(images[0])}")
                if figures:
                    results.append(f"📁 截图目录: {os.path.dirname(figures[0]['screenshot_path'])}")
                    
            except Exception as e:
                results.append(f"❌ 图片提取失败: {str(e)}")
            yield "\n".join(results)
            
            # 步骤4: HTML转换
            results.append("\n🌐 步骤4: HTML转换")
            yield "\n".join(results)
            
            if best_pages:
                try:
                    results.append("🔄 正在将文本转换为HTML格式...")
                    yield "\n".join(results)
                    
                    html_convert(best_pages)
                    results.append("✅ HTML转换完成")
                except Exception as e:
                    results.append(f"❌ HTML转换失败: {str(e)}")
            else:
                results.append("⚠️ 无文本内容，跳过HTML转换")
            yield "\n".join(results)
            
            # 步骤5: HTML翻译
            results.append("\n🌍 步骤5: HTML翻译")
            results.append("🔄 正在检查HTML文件...")
            yield "\n".join(results)
            
            html_dir = "html"
            translated_dir = "temp/html/translated"
            os.makedirs(translated_dir, exist_ok=True)
            
            if os.path.exists(html_dir):
                html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
                html_files.sort()
                
                if html_files:
                    results.append(f"📄 找到HTML文件: {len(html_files)} 个")
                    results.append("🌍 开始批量翻译...")
                    yield "\n".join(results)
                    
                    success = 0
                    for i, html_file in enumerate(html_files, 1):
                        try:
                            results.append(f"🔄 翻译中 [{i}/{len(html_files)}]: {html_file}")
                            yield "\n".join(results)
                            
                            input_path = os.path.join(html_dir, html_file)
                            output_path = os.path.join(translated_dir, html_file)
                            
                            with open(input_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            translated = str(translate(content))
                            
                            with open(output_path, 'w', encoding='utf-8') as f:
                                f.write(translated)
                            
                            results.append(f"✅ 完成: {html_file}")
                            success += 1
                            yield "\n".join(results)
                            
                        except Exception as e:
                            results.append(f"❌ 翻译失败 {html_file}: {str(e)}")
                            yield "\n".join(results)
                    
                    results.append(f"✅ 翻译完成: {success}/{len(html_files)} 个文件")
                else:
                    results.append("⚠️ 未找到HTML文件")
            else:
                results.append("⚠️ HTML目录不存在")
            yield "\n".join(results)
            
            # 步骤6: 图片替换
            results.append("\n🔄 步骤6: 图片替换")
            results.append("🔄 正在准备图片替换...")
            yield "\n".join(results)
            
            final_dir = "temp/html/final"
            os.makedirs(final_dir, exist_ok=True)
            
            if os.path.exists(translated_dir):
                try:
                    results.append("🖼️ 正在替换HTML中的图片占位符...")
                    yield "\n".join(results)
                    
                    processed = batch_replace_html_images(translated_dir, final_dir)
                    if processed:
                        results.append(f"✅ 图片替换完成: {len(processed)} 个文件")
                        yield "\n".join(results)
                        
                        for processed_file in processed:
                            file_name = os.path.basename(processed_file)
                            results.append(f"📄 已处理: {file_name}")
                            yield "\n".join(results)
                    else:
                        results.append("⚠️ 无需图片替换")
                        yield "\n".join(results)
                except Exception as e:
                    results.append(f"❌ 图片替换失败: {str(e)}")
                    yield "\n".join(results)
            else:
                results.append("⚠️ 跳过图片替换")
                yield "\n".join(results)
            
            # 完成总结
            results.append("\n" + "="*50)
            results.append("🎉 处理流程完成!")
            results.append(f"📂 最终输出: {final_dir}/")
            results.append("🧪 所有功能测试完毕")
            yield "\n".join(results)
            
        except Exception as e:
            results.append(f"\n❌ 流程异常: {str(e)}")
            yield "\n".join(results)
    
    # 执行生成器并返回最终结果
    final_result = ""
    for step_result in process_steps():
        final_result = step_result
    
    return final_result

def create_interface():
    """创建支持实时更新的Gradio界面"""
    
    with gr.Blocks(title="PDF处理系统", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # 📄 PDF智能处理系统 - 测试版
        
        **完整处理流程：**
        1. 📤 文件上传与保存
        2. 📝 文本提取（原生文本）
        3. 🖼️ 图片提取（常规图片 + 图表截图）
        4. 🌐 HTML格式转换
        5. 🌍 HTML内容翻译
        6. 🔄 图片路径替换
        
        **特色功能：** 实时显示处理进度，分步更新状态
        """)
        
        # 文件上传区域
        with gr.Row():
            pdf_file = gr.File(
                label="📁 选择PDF文件进行测试",
                file_types=[".pdf"],
                height=120
            )
        
        # 处理按钮
        with gr.Row():
            process_btn = gr.Button(
                "🧪 开始完整流程测试", 
                variant="primary", 
                size="lg"
            )
        
        # 结果显示区域
        with gr.Row():
            result_display = gr.Textbox(
                label="📊 实时处理进度与测试报告",
                lines=25,
                max_lines=30,
                interactive=False,
                placeholder="上传PDF文件并点击测试按钮，实时查看处理进度...",
                show_copy_button=True
            )
        
        # 处理状态提示
        with gr.Row():
            status_display = gr.HTML(
                value="<div style='text-align: center; color: #666;'>系统就绪，等待处理任务</div>"
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
    print("🧪 启动PDF处理系统 - 测试版")
    print("📋 完整流程: 文件上传 → 文本提取 → 图片提取 → HTML转换 → 翻译 → 图片替换")
    
    try:
        demo = create_interface()
        
        print("\n✅ 测试系统就绪!")
        print("🌐 访问地址: http://localhost:7860")
        print("🧪 用于测试所有功能模块")
        print("⚠️  按Ctrl+C停止服务\n")
        
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 测试系统已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()
    '''
    translated_dir = "temp/html/translated"
    final_dir = "temp/html/final"
    os.makedirs(final_dir, exist_ok=True)
 
    if os.path.exists(translated_dir):
        processed = batch_replace_html_images(translated_dir, final_dir)
        for processed_file in processed:
            file_name = os.path.basename(processed_file)
    '''