import os
from flask import Flask, request, Response
from google.cloud import vision
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env (chứa đường dẫn tới key của Google)
load_dotenv()

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

def format_vision_response_as_html(response):
    """
    Hàm này nhận kết quả từ Google Vision và chuyển nó thành một chuỗi HTML đơn giản.
    """
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(response.error.message))

    # Lấy toàn bộ văn bản mà Google nhận dạng được
    full_text = response.full_text_annotation.text
    
    # Bọc toàn bộ văn bản trong thẻ <pre> của HTML để giữ lại định dạng
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
    """
    Đây là API endpoint chính mà ứng dụng Android sẽ gọi tới.
    """
    # 1. Kiểm tra xem có file ảnh được gửi lên không
    if 'image' not in request.files:
        return "Không tìm thấy file ảnh", 400

    file = request.files['image']
    if file.filename == '':
        return "Chưa chọn file nào", 400

    try:
        # 2. Đọc nội dung của file ảnh
        content = file.read()

        # 3. Gọi API của Google Cloud Vision
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=content)

        # Sử dụng document_text_detection để có kết quả OCR tốt nhất cho tài liệu
        response = client.document_text_detection(image=image)
        
        # 4. Chuyển đổi kết quả nhận được thành HTML
        html_string = format_vision_response_as_html(response)
        
        # 5. Trả chuỗi HTML về cho ứng dụng Android
        return Response(html_string, mimetype='text/html; charset=utf-8')

    except Exception as e:
        # In lỗi ra để gỡ rối và trả về thông báo lỗi
        print(f"Đã xảy ra lỗi: {e}")
        return f"Đã xảy ra lỗi phía server: {e}", 500

if __name__ == '__main__':
    # Chạy ứng dụng ở chế độ debug để dễ dàng sửa lỗi
    app.run(debug=True, host='0.0.0.0', port=5000)