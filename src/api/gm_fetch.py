from google import genai
    
GOOGLE_API_KEY = ''


ARTICLE_PATH = 'src/document/article.pdf'
client = genai.Client(api_key=GOOGLE_API_KEY)

def translate_fetch(article_path = ARTICLE_PATH):
    prompt = f"接下来上传的文件是一篇论文。" + \
    "请你将这篇论文全篇翻译为中文，\
    形式要求：以html形式输出，\
    原文与翻译文本间隔分段输出，\
    格式为原文-翻译文本-原文-翻译文本...\
    保留原文图片,\
    保持原有排版不变。"
    try:
        myfile = client.files.upload(file=article_path)
    except Exception as e:
        raise e
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro", 
            contents=[prompt, myfile],
        )
    except Exception as e:
        raise e
    return response.text
