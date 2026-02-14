from flask import Flask, request, Response, stream_with_context
import requests
import base64

app = Flask(__name__)

OPERA_SERVER_URL = "http://mini5.opera-mini.net/"

@app.route('/', methods=['GET'])
def opera_tunnel():
    encrypted_body = request.args.get('body')

    if not encrypted_body:
        return "Error: No body parameter found", 400

    # دالة المولد (Generator) التي ستضخ البيانات
    def generate_stream():
        try:
            # 1. تجهيز البيانات
            body_fixed = encrypted_body.replace(" ", "+")
            raw_payload = base64.b64decode(body_fixed)

            headers = {
                "Content-Type": "application/xml",
                "User-Agent": request.headers.get('User-Agent', "Dalvik/2.1.0 (Linux; U; Android 10)"),
                "Host": "mini5.opera-mini.net",
                "Accept-Encoding": "gzip",
                "Connection": "Keep-Alive"
            }

            # 2. فتح الاتصال مع أوبرا بوضع stream=True
            # هذا يمنع بايثون من تحميل الملف كاملاً في الرام
            with requests.post(
                OPERA_SERVER_URL, 
                data=raw_payload, 
                headers=headers, 
                stream=True,  # مهم جداً
                timeout=30
            ) as req:

                # إرسال بداية ملف HTML
                yield """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta property="og:site_name" content=\""""

                # 3. قراءة البيانات وتشفيرها وإرسالها فوراً
                # نستخدم 3072 لأنه من مضاعفات 3 (1024 * 3) لتجنب مشاكل Base64 Padding
                for chunk in req.iter_content(chunk_size=3072):
                    if chunk:
                        # تشفير القطعة وإرسالها كنص
                        encoded_chunk = base64.b64encode(chunk).decode('utf-8')
                        yield encoded_chunk

                # إرسال نهاية ملف HTML
                yield "\""" />
    <title>Tunnel</title>
</head>
<body>Opera Tunnel Stream Active</body>
</html>"

        except Exception as e:
            # في حالة الخطأ أثناء الضخ، لا يمكننا تغيير الـ Status Code
            # لأننا بدأنا الإرسال بالفعل، لكن يمكننا طباعة الخطأ في الصفحة
            yield f"\"> Error: {str(e)}"

    # 4. إرجاع استجابة من نوع Stream
    return Response(stream_with_context(generate_stream()), mimetype='text/html')

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
