import gradio as gr
import re
from pathlib import Path
    
def create_reader_ui(
    get_temp_dir,          # 获取/temp路径
    load_html,   # 获取html内容
    start_pdf_processing,  # 开始文档处理
    check_processing_status,  # 返回文档处理状态
    api_chat
):
    """创建UI"""
    temp_path = get_temp_dir()

    # CSS样式
    modern_css = """
    <style>
    /* 全局盒模型和基础设置 */
    * {
        box-sizing: border-box !important;
    }

    html, body {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }

    .gradio-container {
        background: #ffffff !important;
        color: #000000 !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
        width: 100% !important;
        min-height: 100vh !important;
        padding: 1rem !important;
        margin: 0 !important;
    }

    /* 确保flexbox布局正常工作 */
    .block {
        position: relative !important;
        z-index: 1 !important;
    }

    button {
        pointer-events: auto !important;
        cursor: pointer !important;
        position: relative !important;
        z-index: 10 !important;
    }

    /* 标题 */
    h1 {
        background: #007acc;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 2rem;
        text-align: center;
        margin: 0.5rem 0;
    }

    /* 文档显示区域 */
    .document-viewer {
        background: #f0f0f0;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 15px;
        min-height: 60vh;
        max-height: 80vh;
        overflow-y: auto;
        overflow-x: hidden;
        height: auto;
    }

    /* 聊天界面 */
    .chat-container {
        background: #f0f0f0;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        overflow-y: auto;
        overflow-x: hidden;
        height: 30vh;
        max-height: 40vh;
        min-height: 200px;
    }

    /* 翻页按钮 */
    .page-btn {
        background: #e0e0e0;
        border: 1px solid #d0d0d0;
        border-radius: 12px;
        color: #000000;
        font-weight: 600;
        padding: 10px 20px;
        cursor: pointer;
    }

    .page-btn:hover {
        background: #d8d8d8;
    }

    /* 输入框 */
    .modern-input {
        background: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 15px;
        color: #000000;
        padding: 12px 16px;
    }

    .modern-input:focus {
        border-color: #007acc;
        box-shadow: 0 0 5px rgba(0, 122, 204, 0.3);
    }
    
    /* 按钮 */
    .btn-modern {
        background: #007acc;
        border: none;
        border-radius: 15px;
        color: white;
        font-weight: 600;
        padding: 12px 24px;
    }

    .btn-modern:hover {
        background: #005fa3;
    }

    /* 响应式设计 */
    @media (max-width: 768px) {
        h1 {
            font-size: 1.8rem;
        }
        
        .document-viewer {
            min-height: 50vh;
            max-height: 70vh;
        }
        
        .chat-container {
            height: 25vh;
            max-height: 30vh;
        }
    }
    </style>
    """
    
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title="AI Reader",
        head=modern_css,
        css="""
        /* 强制Gradio根元素全宽 */
        .gradio-container {
            display: flex;
            flex-direction: column;
            width: 100% !important;
            max-width: 100% !important;
        }
        .main-container {
            display: flex;
            flex-direction: row;
            width: 100% !important;
            flex-grow: 1;
        }
        """
    ) as demo:
        
        # 标题区域
        gr.HTML("<h1>AI Reader</h1>")
        
        # 状态变量
        page_index = gr.State(0)
        html_contents_state = gr.State([])
        processed_page_num = gr.State(0)
        
        # 加载初始文档内容
        initial_contents = load_html(temp_path)
        html_contents_state.value = initial_contents

        # PDF上传区域
        with gr.Column():
            with gr.Row():
                pdf_upload = gr.File(
                    label="上传PDF",
                    file_types=[".pdf"],
                    file_count="single",
                    elem_classes=["modern-input"]
                )
                upload_btn = gr.Button(
                    "开始处理", 
                    variant="primary",
                    elem_classes=["btn-modern"],
                    scale=0
                )
            
            # PDF处理状态页面
            upload_status = gr.Textbox(
                label="正在处理中...",
                lines=1,
                interactive=False,
                value="请上传PDF并点击处理",
                elem_classes=["modern-input"]
            )
        
        with gr.Row(elem_classes=["main-container"]):
            # 论文阅读区域 - 左侧主要内容
            with gr.Column(scale=3):
                html_display = gr.HTML(
                    value=f"""
                    <div class="document-viewer">
                        {initial_contents[0] if initial_contents else '''
                        <div style="text-align: center; color: rgba(0,0,0,0.6); padding: 4rem 2rem;">
                            <div style="font-size: 4rem; margin-bottom: 1rem;">📄</div>
                            <h3 style="margin-bottom: 1rem;">准备就绪</h3>
                            <p>上传PDF文件开始阅读</p>
                        </div>
                        '''}
                    </div>
                    """,
                    elem_classes=["document-viewer"]
                )
                
                # 翻页控制
                with gr.Row():
                    prev_btn = gr.Button(
                        "上一页", 
                        elem_classes=["page-btn"],
                        scale=1
                    )
                    
                    page_info = gr.HTML(
                        f"""
                        <div style="text-align: center; padding: 10px; color: #007acc; font-weight: 600; font-size: 1.1rem;">
                            第 1 页 / 共 {len(initial_contents)} 页
                        </div>
                        """ if initial_contents else """
                        <div style="text-align: center; padding: 10px; color: rgba(0,0,0,0.5); font-weight: 600;">
                            第 - 页 / 共 0 页
                        </div>
                        """
                    )
                    
                    next_btn = gr.Button(
                        "下一页", 
                        elem_classes=["page-btn"],
                        scale=1
                    )
            
            # AI聊天区域 - 右侧辅助功能
            with gr.Column(scale=1):
                
                chat_history = gr.Chatbot(
                    elem_classes=["chat-container"],
                    show_label=False,
                    avatar_images=("👤", "🤖"),
                    value=[[None, "你好！你有什么问题吗？"]]
                )
                
                with gr.Row():
                    user_input = gr.Textbox(
                        placeholder="向AI提问...",
                        label="",
                        scale=4,
                        lines=2,
                        elem_classes=["modern-input"]
                    )
                    send_btn = gr.Button(
                        "发送", 
                        scale=1, 
                        variant="primary",
                        elem_classes=["btn-modern"]
                    )
        
        def handle_pdf_upload(file):
            """处理PDF上传"""
            if file is None:
                return {
                    upload_status: gr.update(value="错误：未选择任何文件"),
                    html_contents_state: [],
                    html_display: gr.update(value="<p>请选择PDF文件</p>"),
                    page_index: 0,
                    page_info: gr.update(value="第 - 页 / 共 0 页")
                }
            
            # 启动PDF处理
            try:
                status_message = start_pdf_processing(file)
                
                return {
                        upload_status: gr.update(value="开始处理PDF，请稍候..."),
                }
            except Exception as e:
                return {
                    upload_status: gr.update(value=f"处理启动失败: {str(e)}"),
                }
        
        def check_processing_progress():
            """检查处理进度"""
            try:
                # 调用检查状态函数
                status_message, completed, progress, completed_pages = check_processing_status()
                
                if completed:
                    # 处理完成，加载全部结果并停止定时器
                    new_contents = load_html(temp_path)
                    if new_contents:
                        # TODO
                        page_idx = 0
                        page_html = new_contents[page_idx] if new_contents else "<p>无内容</p>"
                        page_info_html = f"""
                        <div style="text-align: center; padding: 10px; color: #007acc; font-weight: 600; font-size: 1.1rem;">
                            第 {page_idx + 1} 页 / 共 {len(new_contents)} 页
                        </div>
                        """
                        
                        return {
                            upload_status: gr.update(value=status_message),
                            html_contents_state: new_contents,
                            html_display: gr.update(value=f'<div class="document-viewer">{page_html}</div>'),
                            page_index: page_idx,
                            page_info: gr.update(value=page_info_html),
                            timer: gr.update(active=False)  # 停止定时器
                        }
                    else:
                        return {
                            upload_status: gr.update(value="处理完成但未找到内容"),
                            timer: gr.update(active=False)  # 停止定时器
                        }
                else:
                    # 仍在处理中，实时加载已完成的页面
                    new_contents = load_html(temp_path)
                    if new_contents and len(new_contents) > 0:
                        page_idx = 0
                        first_page_html = new_contents[page_idx]
                        page_info_html = f"""
                        <div style="text-align: center; padding: 10px; color: #ff6b35; font-weight: 600; font-size: 1.1rem;">
                            处理中: 第 {page_idx + 1} 页 / 共 {len(new_contents)} 页 (进度: {int(progress)}%)
                        </div>
                        """
                        
                        return {
                            upload_status: gr.update(value=f"{status_message} (进度: {int(progress)}%)"),
                            html_contents_state: new_contents,
                            html_display: gr.update(value=f'<div class="document-viewer">{first_page_html}</div>'),
                            page_index: page_idx,
                            page_info: gr.update(value=page_info_html),
                            timer: gr.update()  # 继续运行定时器
                        }
                    else:
                        # 没有内容时只更新状态
                        return {
                            upload_status: gr.update(value=f"{status_message} (进度: {int(progress)}%)"),
                            timer: gr.update()  # 继续运行定时器
                        }
            except Exception as e:
                return {
                    upload_status: gr.update(value=f"状态检查失败: {str(e)}"),
                    timer: gr.update(active=False)  # 出错时停止定时器
                }
        
        def update_page_view(page_idx, all_htmls):
            """翻页视图更新"""
            if not all_htmls:
                return """
                <div class="document-viewer">
                    <div style="text-align: center; color: rgba(0,0,0,0.6); padding: 4rem 2rem;">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">📄</div>
                        <h3>无内容</h3>
                    </div>
                </div>
                """, 0, """
                <div style="text-align: center; padding: 10px; color: rgba(0,0,0,0.5);">
                    第 - 页 / 共 0 页
                </div>
                """
            
            page_idx = max(0, min(page_idx, len(all_htmls) - 1))
            html_content = f'<div class="document-viewer">{all_htmls[page_idx]}</div>'
            
            page_label_html = f"""
            <div style="text-align: center; padding: 10px; color: #007acc; font-weight: 600; font-size: 1.1rem;">
                第 {page_idx + 1} 页 / 共 {len(all_htmls)} 页
            </div>
            """
            
            return html_content, page_idx, page_label_html
        
        def prev_page(current_idx, all_htmls):
            return update_page_view(current_idx - 1, all_htmls)
        
        def next_page(current_idx, all_htmls):
            return update_page_view(current_idx + 1, all_htmls)
        
        def chat_with_ai(message, history, current_page_idx, all_htmls):
            """AI聊天"""
            if not message.strip():
                return history, ""
            
            try:
                current_page_text = ""
                if all_htmls and current_page_idx < len(all_htmls):
                    current_page_html = all_htmls[current_page_idx]
                    current_page_text = re.sub(r'<[^>]+>', '', current_page_html)
                    current_page_text = re.sub(r'\s+', ' ', current_page_text).strip()
                
                # 如果当前页没有文本，可以考虑使用全文作为上下文，这里简化为仅用当前页
                ai_response = api_chat(message, current_page_text)
                
                history.append([message, ai_response])
                return history, ""
                
            except Exception as e:
                error_msg = f"AI服务暂时不可用: {str(e)}"
                history.append([message, error_msg])
                return history, ""
        
        # 绑定事件
        upload_btn.click(
            handle_pdf_upload,
            inputs=[pdf_upload],
            outputs=[
                upload_status,
                html_contents_state,
                html_display,
                page_index,
                page_info
            ]
        )
        
        # 创建定时器 - 每20秒检查一次处理状态
        timer = gr.Timer(10)
        timer.tick(
            check_processing_progress,
            inputs=[],
            outputs=[
                upload_status,
                html_contents_state,
                html_display,
                page_index,
                page_info,
                timer
            ]
        )
        
        # 翻页事件 - 增强交互
        prev_btn.click(
            prev_page, 
            inputs=[page_index, html_contents_state], 
            outputs=[html_display, page_index, page_info]
        )

        next_btn.click(
            next_page, 
            inputs=[page_index, html_contents_state], 
            outputs=[html_display, page_index, page_info]
        )
        
        # AI聊天事件 - 现代化交互
        send_btn.click(
            chat_with_ai, 
            inputs=[user_input, chat_history, page_index, html_contents_state], 
            outputs=[chat_history, user_input]
        )
        user_input.submit(
            chat_with_ai, 
            inputs=[user_input, chat_history, page_index, html_contents_state], 
            outputs=[chat_history, user_input]
        )
    
    return demo
