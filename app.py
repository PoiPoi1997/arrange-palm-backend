import os
import requests
from flask import Flask, request, Response
from dotenv import load_dotenv

# Tải biến môi trường (chứa API key của OCR.space)
load_dotenv()

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

def format_ocr_response_as_html(ocr_result):
    """
    Hàm này nhận kết quả từ OCR.space và chuyển nó thành HTML.
    """
    full_text = ""
    # Kiểm tra xem kết quả có hợp lệ và chứa văn bản không
    if ocr_result and not ocr_result.get('IsErroredOnProcessing'):
        for res in ocr_result.get('ParsedResults', []):
            full_text += res.get('ParsedText', '')
            
    if not full_text:
        full_text = "Không nhận dạng được văn bản hoặc đã xảy ra lỗi."

    html_output = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kết quả nhận dạng</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; padding: 15px; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; font-size: 16px; }}
        </style>
    </head>
    <body>
        <pre>{full_text}</pre>
    </body>
    </html>
    """
    return html_output

@app.route('/process-image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return "Không tìm thấy file ảnh", 400

    file = request.files.get('image')
    if not file:
        return "Chưa chọn file nào", 400

    try:
        # Lấy API key từ biến môi trường
        api_key = os.getenv('OCR_SPACE_API_KEY')
        if not api_key:
            raise Exception("API key của OCR.space không được tìm thấy.")

        # Gọi đến API của OCR.space
        ocr_url = 'https://api.ocr.space/parse/image'
        payload = {'apikey': api_key, 'language': 'eng'}
        
        response = requests.post(
            ocr_url,
            files={file.filename: file.read()},
            data=payload,
        )
        response.raise_for_status()  # Báo lỗi nếu có vấn đề về kết nối
        
        # Chuyển đổi kết quả nhận được thành HTML
        html_string = format_ocr_response_as_html(response.json())
        
        return Response(html_string, mimetype='text/html; charset=utf-8')

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        return f"Đã xảy ra lỗi phía server: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)