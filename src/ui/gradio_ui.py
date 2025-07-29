import gradio as gr

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📄 AI驱动的PDF深度阅读与分析器 (通用API版)")

    # 状态变量
    page_count_state = gr.State(0)
    page_index = gr.State(0)
    extracted_texts_state = gr.State([])
    html_contents_state = gr.State([])

    with gr.Accordion("📄 上传PDF & 通用API设置", open=True):
        with gr.Row():
            with gr.Column(scale=2):
                pdf_input = gr.File(label="上传你的 PDF 文件", type="filepath")
                extraction_method = gr.Radio(["快速提取 (推荐)", "OCR 提取 (适用于扫描件)"], label="文本提取方式", value="快速提取 (推荐)")
                upload_btn = gr.Button("上传并由AI渲染文档", variant="primary")
            with gr.Column(scale=3):
                # 【核心改动】通用API设置界面
                gr.Markdown("### 通用API设置")
                api_url_input = gr.Textbox(label="API 请求地址 (URL)", placeholder="例如: https://api.deepseek.com/chat/completions")
                api_headers_input = gr.Textbox(label="请求 Headers (JSON格式)", lines=3, placeholder='例如: {"Content-Type": "application/json", "Authorization": "Bearer sk-..."}')
                api_body_template_input = gr.Textbox(label="请求 Body 模板 (必须包含 {prompt} 占位符)", lines=5, placeholder='例如: {"model": "deepseek-chat", "messages": [{"role": "user", "content": "{prompt}"}]}')
                upload_status = gr.Textbox(label="处理状态", interactive=False, lines=2)

    with gr.Row(equal_height=True):
        with gr.Column(scale=3):
            html_display = gr.HTML("请上传PDF文件，AI将为您渲染文档。")
            with gr.Row():
                prev_btn = gr.Button("⬅ 上一页")
                next_btn = gr.Button("下一页 ➡")
                page_num_display = gr.Markdown("第 **-** 页")
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("🤖 AI助教"):
                    chatbot = gr.Chatbot(label="对话历史", height=400, type="messages")
                    chat_input = gr.Textbox(placeholder="基于当前页面内容提问...", label="你的问题")
                    send_chat_btn = gr.Button("发送", variant="primary")
    
    # --- 后端事件处理逻辑 ---
    
    def chat_with_ai(query, history, current_page_idx, all_texts, api_url, api_headers, api_body):
        if not query or not query.strip(): return history, ""
        page_text_context = all_texts[current_page_idx] if all_texts and current_page_idx < len(all_texts) else ""
        if not page_text_context:
            gr.Warning("当前页面没有文本内容可供提问。")
            return history, ""
        
        # 构建一个适合聊天的prompt
        chat_prompt = f"""基于以下上下文回答问题。
        上下文: "{page_text_context}"
        问题: "{query}"
        """
        
        # 调用通用API函数
        api_response_str = call_custom_api(chat_prompt, api_url, api_headers, api_body)
        
        # 同样，尝试解析常见的回复格式
        try:
            response_data = json.loads(api_response_str)
            ai_response = response_data['choices'][0]['message']['content']
        except (json.JSONDecodeError, KeyError, IndexError):
            ai_response = f"收到API原始回复:\n{api_response_str}"
            
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": ai_response})
        return history, ""

    send_chat_btn.click(
        chat_with_ai, 
        inputs=[chat_input, chatbot, page_index, extracted_texts_state, api_url_input, api_headers_input, api_body_template_input], 
        outputs=[chatbot, chat_input]
    )

    def update_page_view(page_idx, all_htmls):
        page_idx = max(0, min(page_idx, len(all_htmls) - 1)) if all_htmls else 0
        html_content = all_htmls[page_idx] if all_htmls and page_idx < len(all_htmls) else "<p>无内容</p>"
        page_label = f"第 **{page_idx + 1}** 页"
        return html_content, page_idx, page_label

    def prev_page(current_idx, all_htmls): return update_page_view(current_idx - 1, all_htmls)
    def next_page(current_idx, all_htmls): return update_page_view(current_idx + 1, all_htmls)
    prev_btn.click(prev_page, inputs=[page_index, html_contents_state], outputs=[html_display, page_index, page_num_display])
    next_btn.click(next_page, inputs=[page_index, html_contents_state], outputs=[html_display, page_index, page_num_display])
    
    def process_and_render_pdf(pdf_temp_file, method, api_url, api_headers, api_body, progress=gr.Progress(track_tqdm=True)):
        if pdf_temp_file is None:
            return "⚠️ 没有选择文件", 0, [], [], "请先上传PDF。", 0, "第 **-** 页"
        
        progress(0, desc="正在保存文件...")
        PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(pdf_temp_file, PDF_PATH)
        
        progress(0.2, desc="正在提取文本...")
        all_texts = text_extract(PDF_PATH) if "快速" in method else text_ocr(PDF_PATH)
        total_pages = len(all_texts)
        
        # 调用AI渲染HTML，传入所有API设置
        all_htmls = html_convert(all_texts, api_url, api_headers, api_body, progress=progress)
        
        progress(0.9, desc="正在更新界面...")
        first_page_html, page_idx, page_label = update_page_view(0, all_htmls)
        
        status = f"✅ AI渲染完成，共 {total_pages} 页。"
        return status, total_pages, all_texts, all_htmls, first_page_html, page_idx, page_label

    upload_btn.click(
        process_and_render_pdf, 
        inputs=[pdf_input, extraction_method, api_url_input, api_headers_input, api_body_template_input], 
        outputs=[upload_status, page_count_state, extracted_texts_state, html_contents_state, html_display, page_index, page_num_display]
    )
    
if __name__ == "__main__":
    demo.launch()
