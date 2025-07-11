import os
import requests
import cv2  # Thư viện OpenCV
import numpy as np # Thư viện NumPy
from flask import Flask, request, Response
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

def format_ocr_response_as_html(ocr_result):
    """Hàm này nhận kết quả từ OCR.space và chuyển nó thành HTML."""
    full_text = ""
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
        # --- BẮT ĐẦU PHẦN TIỀN XỬ LÝ ẢNH BẰNG OPENCV ---
        image_stream = file.read()
        np_array = np.frombuffer(image_stream, np.uint8)
        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        # 1. Chuyển sang ảnh xám để xử lý
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Áp dụng Adaptive Thresholding để làm chữ nổi bật lên, rất hiệu quả với ảnh có ánh sáng không đều
        processed_img = cv2.adaptiveThreshold(
            gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Mã hóa lại ảnh đã xử lý thành định dạng PNG để gửi đi
        success, encoded_image = cv2.imencode('.png', processed_img)
        if not success:
            raise Exception("Không thể mã hóa lại ảnh sau khi xử lý")
        
        image_bytes = encoded_image.tobytes()
        # --- KẾT THÚC PHẦN TIỀN XỬ LÝ ---

        api_key = os.getenv('OCR_SPACE_API_KEY')
        if not api_key:
            raise Exception("API key của OCR.space không được tìm thấy.")

        # Gọi OCR.space với ảnh đã được cải thiện
        ocr_url = 'https://api.ocr.space/parse/image'
        payload = {
            'apikey': api_key,
            'language': 'eng',
            'OCREngine': '5', # Dùng engine mạnh nhất
        }
        
        response = requests.post(
            ocr_url,
            files={'file': ('processed_image.png', image_bytes, 'image/png')},
            data=payload,
        )
        response.raise_for_status()
        
        html_string = format_ocr_response_as_html(response.json())
        return Response(html_string, mimetype='text/html; charset=utf-8')

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        return f"Đã xảy ra lỗi phía server: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)