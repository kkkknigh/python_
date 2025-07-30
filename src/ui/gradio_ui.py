import gradio as gr
import re
from pathlib import Path
    
def create_reader_ui(
    get_temp_dir,
    load_html,
    start_pdf_processing,
    check_processing_status,
    api_chat
):
    """创建AI Reader的Gradio界面"""
    temp_path = get_temp_dir()

    modern_css = """
    <style>
    /* 全局盒模型设置 - 作用对象: 所有HTML元素 */
    * {
        box-sizing: border-box !important;
    }

    /* 页面基础设置 - 作用对象: HTML根元素和body */
    html, body {
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow-x: hidden !important;
    }

    /* Gradio主容器样式 - 作用对象: Gradio框架的核心容器元素 */
    .gradio-container, 
    .gradio-container > .main,
    .gradio-container > .main > .wrap,
    .app {
        background: #ffffff !important;
        color: #000000 !important;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
        width: calc(100vw - 4rem) !important;
        max-width: calc(100vw - 4rem) !important;
        min-width: calc(100vw - 4rem) !important;
        min-height: 100vh !important;
        padding: 1rem 2rem !important;
        margin: 0 auto !important;
        left: 0 !important;
        right: 0 !important;
        top: 0 !important;
        position: relative !important;
    }

    /* Gradio内部容器元素 - 作用对象: 根容器、数据测试容器、界面容器 */
    #root, 
    [data-testid="block-container"],
    .contain,
    .gradio-interface {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Gradio布局元素 - 作用对象: 块级元素、行容器、列容器 */
    .block, .gradio-row, .gradio-column {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    /* 防止列超出容器 - 作用对象: 所有Gradio列组件 */
    .gradio-column {
        flex-shrink: 1 !important;
        overflow: hidden !important;
    }

    /* Gradio HTML组件 - 作用对象: HTML显示组件容器 */
    .gradio-html {
        width: 100% !important;
        max-width: 100% !important;
    }

    /* 主要内容容器 - 作用对象: 文档阅读区和聊天区的父容器 */
    .main-container {
        display: flex !important;
        flex-direction: row !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 100% !important;
        flex-grow: 1 !important;
        gap: 1rem !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    /* PDF文档显示区域 - 作用对象: 显示PDF内容的主要区域 */
    .document-viewer {
        background: #f0f0f0 !important;
        border-radius: 10px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 15px !important;
        min-height: 70vh !important;
        max-height: 75vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        flex-shrink: 1 !important;
    }

    /* 文档区域内所有元素 - 作用对象: PDF内容的所有子元素 */
    .document-viewer * {
        max-width: 100% !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        color: inherit !important;
        background: inherit !important;
    }

    /* 文档区域图片 - 作用对象: PDF中的图片元素 */
    .document-viewer img {
        max-width: 100% !important;
        height: auto !important;
    }

    /* AI聊天对话区域 - 作用对象: 聊天机器人界面容器 */
    .chat-container {
        background: #f0f0f0 !important;
        border-radius: 10px !important;
        border: 1px solid #e0e0e0 !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: 70vh !important;
        max-height: 75vh !important;
        min-height: 400px !important;
        width: 100% !important;
        max-width: 100% !important;
        margin-bottom: 1rem !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        box-sizing: border-box !important;
    }

    /* 页面主体元素 - 作用对象: 防止页面缩放和位移 */
    body {
        zoom: 1 !important;
        transform: scale(1) !important;
        transform-origin: 0 0 !important;
        position: relative !important;
        left: 0 !important;
        right: 0 !important;
    }

    /* Gradio容器定位重置 - 作用对象: 移除Gradio默认的定位偏移 */
    .gradio-container {
        position: relative !important;
        left: 0 !important;
        right: 0 !important;
        top: 0 !important;
        transform: none !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    /* 移动端响应式布局 - 作用对象: 屏幕宽度小于768px的设备 */
    @media (max-width: 768px) {
        /* 主容器垂直布局 - 作用对象: 移动端的主内容容器 */
        .main-container {
            flex-direction: column !important;
        }
        
        /* 移动端容器内边距 - 作用对象: 移动端的Gradio主容器 */
        .gradio-container {
            width: calc(100vw - 2rem) !important;
            max-width: calc(100vw - 2rem) !important;
            padding: 0.5rem 1rem !important;
        }
        
        /* 移动端标题字体大小 - 作用对象: 移动端的所有h1标题 */
        h1 {
            font-size: 1.8rem;
        }
        
        /* 移动端文档查看器 - 作用对象: 移动端的PDF显示区域 */
        .document-viewer {
            min-height: 60vh;
            max-height: 65vh;
            padding: 10px !important;
        }
        
        /* 移动端聊天容器 - 作用对象: 移动端的AI聊天区域 */
        .chat-container {
            height: 60vh;
            max-height: 65vh;
        }
    }

    /* 防止任何元素超出父容器 - 作用对象: 所有可能溢出的元素 */
    * {
        box-sizing: border-box !important;
    }

    /* 确保所有输入框和按钮不超出容器 - 作用对象: 表单元素 */
    input, textarea, button, select {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }

    /* 确保右侧列不超出 - 作用对象: 右侧聊天区域的列容器 */
    [data-testid="column"]:last-child {
        flex-shrink: 1 !important;
        min-width: 0 !important;
        overflow: hidden !important;
    }

    /* 隐藏页面按钮的加载指示器 - 作用对象: 上一页下一页按钮的加载状态 */
    .page-btn .loading {
        display: none !important;
    }

    /* 隐藏按钮点击时的进度条 - 作用对象: 所有按钮的进度指示器 */
    .page-btn [data-testid="loading-status"] {
        display: none !important;
    }

    /* 加快页面切换动画 - 作用对象: 文档查看器的内容更新 */
    .document-viewer {
        transition: none !important;
    }
    </style>
    """
    
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title="AI Reader",
        head=modern_css,
        css="""
        /* Gradio主容器布局 - 作用对象: 覆盖默认的Gradio容器样式 */
        .gradio-container {
            display: flex !important;
            flex-direction: column !important;
            width: calc(100vw - 4rem) !important;
            max-width: calc(100vw - 4rem) !important;
            min-width: calc(100vw - 4rem) !important;
            margin: 0 auto !important;
            padding: 1rem 2rem !important;
            left: 0 !important;
            right: 0 !important;
            position: relative !important;
        }
        
        /* 主内容区域布局 - 作用对象: 文档和聊天区域的父容器 */
        .main-container {
            display: flex !important;
            flex-direction: row !important;
            width: 100% !important;
            max-width: 100% !important;
            flex-grow: 1 !important;
            gap: 1rem !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
            overflow: hidden !important;
        }
        
        /* 页面根元素 - 作用对象: HTML根元素、body和根容器 */
        body, html, #root {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow-x: hidden !important;
        }

    /* 隐藏不必要的加载指示器 - 作用对象: 页面切换时的加载状态 */
        [data-testid="loading-status"],
        .loading-container,
        .gradio-loading {
            display: none !important;
        }

        /* 隐藏聊天发送按钮的加载状态 - 作用对象: AI聊天发送按钮 */
        .btn-modern [data-testid="loading-status"],
        .btn-modern .loading,
        button[variant="primary"] [data-testid="loading-status"],
        button[variant="primary"] .loading {
            display: none !important;
        }
        """
    ) as demo:
        
        gr.HTML("<h1>AI Reader</h1>")
        
        page_index = gr.State(0)
        html_contents_state = gr.State([])
        processed_page_num = gr.State(0)
        
        initial_contents = load_html(temp_path)
        html_contents_state.value = initial_contents

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
            
            upload_status = gr.Textbox(
                label="正在处理中...",
                lines=1,
                interactive=False,
                value="请上传PDF并点击处理",
                elem_classes=["modern-input"]
            )
        
        with gr.Row(elem_classes=["main-container"]):
            with gr.Column(scale=2):
                html_display = gr.HTML(
                    value=f"""
                    <div class="document-viewer">
                        {initial_contents[0] if initial_contents else '''
                        <div style="text-align: center; padding: 4rem 2rem;">
                            <div style="font-size: 4rem; margin-bottom: 1rem;">📄</div>
                            <h3 style="margin-bottom: 1rem;">准备就绪</h3>
                            <p>上传PDF文件开始阅读</p>
                        </div>
                        '''}
                    </div>
                    """,
                    elem_classes=["document-viewer"]
                )
                
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
            
            with gr.Column(scale=1):
                
                chat_history = gr.Chatbot(
                    elem_classes=["chat-container"],
                    show_label=False,
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
                    html_contents_state: gr.update(),
                    html_display: gr.update(),
                    page_index: gr.update(),
                    page_info: gr.update()
                }
            
            try:
                status_message = start_pdf_processing(file)
                
                return {
                    upload_status: gr.update(value="开始处理PDF，请稍候..."),
                    html_contents_state: gr.update(),
                    html_display: gr.update(),
                    page_index: gr.update(),
                    page_info: gr.update()
                }
            except Exception as e:
                return {
                    upload_status: gr.update(value=f"处理启动失败: {str(e)}"),
                    html_contents_state: gr.update(),
                    html_display: gr.update(),
                    page_index: gr.update(),
                    page_info: gr.update()
                }
        
        def update_page_view(page_idx, all_htmls):
            """更新页面显示"""
            if not all_htmls:
                return """
                <div class="document-viewer" style="width: 100%; max-width: 100%; position: relative;">
                    <div style="text-align: center; padding: 4rem 2rem;">
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
            html_content = f'''<div class="document-viewer" style="width: 100%; max-width: 100%; position: relative;">{all_htmls[page_idx]}</div>'''
            
            page_label_html = f"""
            <div style="text-align: center; padding: 10px; color: #007acc; font-weight: 600; font-size: 1.1rem;">
                第 {page_idx + 1} 页 / 共 {len(all_htmls)} 页
            </div>
            """
            
            return html_content, page_idx, page_label_html

        def check_processing_progress(current_page_idx):
            """检查PDF处理进度"""
            try:
                status_message, completed, progress, completed_pages = check_processing_status()
                
                # 如果处于空闲状态，不进行任何更新
                if status_message == "请上传PDF并点击处理":
                    return {
                        upload_status: gr.update(),
                        html_contents_state: gr.update(),
                        html_display: gr.update(),
                        page_index: gr.update(),
                        page_info: gr.update(),
                        timer: gr.update()
                    }
                
                if completed:
                    new_contents = load_html(temp_path)
                    if new_contents:
                        # 保持当前页面或调整到有效范围
                        page_idx = max(0, min(current_page_idx, len(new_contents) - 1))
                        page_html = new_contents[page_idx] if new_contents else "<p>无内容</p>"
                        page_info_html = f"""
                        <div style="text-align: center; padding: 10px; color: #007acc; font-weight: 600; font-size: 1.1rem;">
                            第 {page_idx + 1} 页 / 共 {len(new_contents)} 页
                        </div>
                        """
                        
                        return {
                            upload_status: gr.update(value=status_message),
                            html_contents_state: new_contents,
                            html_display: gr.update(value=f'<div class="document-viewer" style="width: 100%; max-width: 100%; position: relative;">{page_html}</div>'),
                            page_index: page_idx,
                            page_info: gr.update(value=page_info_html),
                            timer: gr.update(active=False)
                        }
                    else:
                        return {
                            upload_status: gr.update(value="处理完成但未找到内容"),
                            timer: gr.update(active=False)
                        }
                else:
                    new_contents = load_html(temp_path)
                    if new_contents and len(new_contents) > 0:
                        # 保持当前页面或调整到有效范围
                        page_idx = max(0, min(current_page_idx, len(new_contents) - 1))
                        current_page_html = new_contents[page_idx]
                        page_info_html = f"""
                        <div style="text-align: center; padding: 10px; color: #007acc; font-weight: 600; font-size: 1.1rem;">
                            第 {page_idx + 1} 页 / 共 {len(new_contents)} 页
                        </div>
                        """
                        
                        return {
                            upload_status: gr.update(value=f"{status_message} (进度: {int(progress)}%)"),
                            html_contents_state: new_contents,
                            html_display: gr.update(value=f'<div class="document-viewer" style="width: 100%; max-width: 100%; position: relative;">{current_page_html}</div>'),
                            page_index: page_idx,
                            page_info: gr.update(value=page_info_html),
                            timer: gr.update()
                        }
                    else:
                        return {
                            upload_status: gr.update(value=f"{status_message} (进度: {int(progress)}%)"),
                            timer: gr.update()
                        }
            except Exception as e:
                return {
                    upload_status: gr.update(value=f"状态检查失败: {str(e)}"),
                    timer: gr.update(active=False)
                }
        
        def prev_page(current_idx, all_htmls):
            """快速切换到上一页"""
            return update_page_view(current_idx - 1, all_htmls)
        
        def next_page(current_idx, all_htmls):
            """快速切换到下一页"""
            return update_page_view(current_idx + 1, all_htmls)
        
        def chat_with_ai(message, history, current_page_idx, all_htmls):
            """处理AI聊天"""
            if not message.strip():
                return history, ""
            
            try:
                current_page_text = ""
                if all_htmls and current_page_idx < len(all_htmls):
                    current_page_html = all_htmls[current_page_idx]
                    current_page_text = re.sub(r'<[^>]+>', '', current_page_html)
                    current_page_text = re.sub(r'\s+', ' ', current_page_text).strip()
                
                ai_response = api_chat(message, current_page_text)
                
                history.append([message, ai_response])
                return history, ""
                
            except Exception as e:
                error_msg = f"AI服务暂时不可用: {str(e)}"
                history.append([message, error_msg])
                return history, ""
        
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
        
        timer = gr.Timer(10)
        timer.tick(
            check_processing_progress,
            inputs=[page_index],
            outputs=[
                upload_status,
                html_contents_state,
                html_display,
                page_index,
                page_info,
                timer
            ]
        )
        
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
        
        send_btn.click(
            chat_with_ai, 
            inputs=[user_input, chat_history, page_index, html_contents_state], 
            outputs=[chat_history, user_input],
            show_progress=False
        )
        user_input.submit(
            chat_with_ai, 
            inputs=[user_input, chat_history, page_index, html_contents_state], 
            outputs=[chat_history, user_input],
            show_progress=False
        )
    
    return demo
