from flask import Flask, jsonify
import os
import requests
from bs4 import BeautifulSoup
import json

def get_elbotola_matches():
    url = "https://m.elbotola.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # 1. إرسال الطلب وجلب الـ response
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # 2. استخراج الـ JSON من وسم __NEXT_DATA__
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not next_data_script:
            print("لم يتم العثور على وسم __NEXT_DATA__")
            return []

        full_data = json.loads(next_data_script.string)

        # 3. استخراج المباريات من مسار البيانات (حسب هيكل Next.js المعتاد للموقع)
        # ملاحظة: المسار قد يختلف قليلاً بناءً على تحديثات الموقع، غالباً يكون في props -> pageProps
        matches_raw = full_data.get('props', {}).get('pageProps', {}).get('matches', [])
        
        # إذا لم تكن في المسار أعلاه، نطبق استخراج عام من البيانات المهيكلة (Schema.org) المتوفرة في الـ HTML
        if not matches_raw:
            # محاولة الاستخراج من وسم application/ld+json إذا كان متاحاً في الهيكل المرفق
            ld_json_scripts = soup.find_all('script', type='application/ld+json')
            for script in ld_json_scripts:
                data = json.loads(script.string)
                if '@graph' in data:
                    matches_raw = [item for item in data['@graph'] if item.get('@type') == 'SportsEvent']
                    break

        # 4. بناء الـ jsonarray الجديد بالبيانات المطلوبة
        extracted_matches = []
        for match in matches_raw:
            # استخراج المعلومات بناءً على الهيكل المتاح
            match_info = {
                "match_name": match.get('name'),
                "league": match.get('location', {}).get('name') if isinstance(match.get('location'), dict) else match.get('location'),
                "start_time": match.get('startDate'),
                "status": match.get('eventStatus'),
                "score": next((prop.get('value') for prop in match.get('additionalProperty', []) if prop.get('name') == 'finalScore'), "N/A"),
                "teams": []
            }

            # استخراج أسماء وصور الفرق (إذا كانت متوفرة في الـ JSON)
            competitors = match.get('competitor', [])
            for team in competitors:
                match_info["teams"].append({
                    "name": team.get('name'),
                    "profile_url": team.get('url'),
                    "image": team.get('image')  # قد لا يتوفر رابط الصورة دائماً في الـ JSON الأساسي
                })

            extracted_matches.append(match_info)

        return extracted_matches

    except Exception as e:
        print(f"حدث خطأ: {e}")
        return []


app = Flask(__name__)


@app.route('/')
def index():
    return json.dumps(get_elbotola_matches(), ensure_ascii=False, indent=4)

@app.route('/hilal')
def hilal():
    return "Hello Hilal"


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
