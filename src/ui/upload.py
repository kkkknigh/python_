'''
文档上传界面，获取PDF后存储到article.pdf的位置
'''
import gradio as gr
import os

SAVE_PATH = "src/document/article.pdf"

def save_pdf_file(file):
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, "wb") as f:
        f.write(file.read())
    return f"✅ 文件已保存到：{SAVE_PATH}"

with gr.Blocks(title="PDF 上传") as demo:
    gr.Markdown("## 📄 上传 PDF 文件（将保存为 article.pdf）")
    with gr.Row():
        pdf_input = gr.File(label="选择 PDF", file_types=[".pdf"])
        upload_btn = gr.Button("📤 上传并保存")

    result = gr.Textbox(label="上传结果")

    upload_btn.click(fn=save_pdf_file, inputs=pdf_input, outputs=result)

if __name__ == "__main__":
    demo.launch(share=True)
