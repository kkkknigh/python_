from document.content_get import text_ocr, pic_extract, text_extract

def main():
    try:
        images = pic_extract()
        textOCR = text_ocr()
        text = text_extract()

    except Exception as e:
        print(f"{e}")

if __name__ == "__main__":
    main()