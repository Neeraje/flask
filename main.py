from flask import Flask, request
import requests
import base64

app = Flask(__name__)

# رابط خادم أوبرا ميني الرسمي (كما في الصورة التي أرسلتها)
OPERA_SERVER_URL = "http://mini5.opera-mini.net/"

@app.route('/', methods=['GET'])
def opera_tunnel():
    # 1. استلام البيانات المشفرة من الرابط
    # مثال: http://your-server.com/?body=SDASDzxc...
    encrypted_body = request.args.get('body')

    if not encrypted_body:
        return "Error: No body parameter found", 400

    try:
        # تصحيح الرموز التي قد تتغير في الرابط (مثل + يتحول لمسافة)
        encrypted_body = encrypted_body.replace(" ", "+")
        
        # 2. فك التشفير للحصول على بيانات OBML الخام
        raw_payload = base64.b64decode(encrypted_body)

        # 3. تجهيز الهيدرز لتبدو وكأنها قادمة من تطبيق أوبرا ميني الحقيقي
        # (بناءً على الصورة التي أرسلتها: Content-Type: application/xml)
        headers = {
            "Content-Type": "application/xml",
            "User-Agent": request.headers.get('User-Agent', "Dalvik/2.1.0 (Linux; U; Android 10)"),
            "Host": "mini5.opera-mini.net",
            "Accept-Encoding": "gzip",
            "Connection": "Keep-Alive"
        }

        # 4. إرسال الطلب لسيرفر أوبرا (Forwarding)
        opera_response = requests.post(
            OPERA_SERVER_URL, 
            data=raw_payload, 
            headers=headers,
            timeout=30 # مهلة زمنية
        )

        # 5. استلام الرد وتشفيره بـ Base64
        # نستخدم content للحصول على الرد الخام (Binary)
        response_b64 = base64.b64encode(opera_response.content).decode('utf-8')

        # 6. تغليف الرد داخل HTML ليقرأه فيسبوك
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta property="og:site_name" content="{response_b64}" />
            <title>Tunnel</title>
        </head>
        <body>
            Opera Tunnel Active
        </body>
        </html>
        """

        return html_response

    except Exception as e:
        return f"Server Error: {str(e)}", 500

if __name__ == '__main__':
    # تشغيل السرفر
    app.run(debug=True, port=os.getenv("PORT", default=5000))
