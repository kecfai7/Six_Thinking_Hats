# Six Thinking Hats Backend (Flask)

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from markdown2 import markdown
import pdfkit
import json
import urllib.parse

# 환경 변수 로드
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

app = Flask(__name__)
CORS(app)

# wkhtmltopdf 경로를 명시적으로 지정
WKHTMLTOPDF_PATH = r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

@app.route('/api/solve', methods=['POST'])
def solve():
    data = request.json
    user_problem = data.get('problem')
    user_email = data.get('email')
    email_status = None  # 기본값 할당
    # Google AI Studio API 호출
    # 프롬프트 리팩토링: 각 모자별 조건/예시/안내 강화, 존중, 연령, 심각한 문제 등 반영
    prompt = f"""
    아래의 문제를 심리학적 관점에서, 동기부여와 문제해결 전문가의 입장으로 분석해 주세요.
    반드시 아래 6가지 색깔 모자별로 각각 소제목(한글/영문 모두 표기)과 답변을 모두 작성해 주세요.
    모든 답변은 존중과 배려를 바탕으로, 연령대가 드러나면 그에 맞는 예시를 포함해 주세요.
    만약 자해, 범죄, 극단적 선택 등 심각한 문제라면 직접 답변하지 말고 전문 상담기관, AI 등으로 안내해 주세요.

    1. 흰색 모자 (White Hat):
      - 문제의 사실을 객관적으로 분리하여 정리해 주세요.
      - 예시: "친구와 싸웠어요. 화해하고 싶어요" → "친구와 싸웠다(사실)", "화해하고 싶다(의도)" 등으로 구분
      - 추가로, 왜 그런 일이 발생했는지 질문을 던져 주세요. (예: "왜 싸웠을까요?")
      - "이런 추가 정보를 입력해주시면 더 깊은 분석이 가능합니다."라는 안내 멘트를 마지막에 추가

    2. 빨간색 모자 (Red Hat):
      - 감정, 직관, 느낌을 존중하며, 공감의 언어로 300자 내외로 답변

    3. 검은색 모자 (Black Hat):
      - 비판적 사고, 위험, 문제점 등을 300자 내외로 제시

    4. 노란색 모자 (Yellow Hat):
      - 긍정적 시각, 장점, 기회, 희망적 요소를 300자 내외로 제시

    5. 초록색 모자 (Green Hat):
      - 창의적 아이디어, 새로운 대안, 신선한 시각을 300자 내외로 제시

    6. 파란색 모자 (Blue Hat):
      - 지금까지의 분석을 종합하여, 전문가적 관점(필요시 의사, 회계사, 건축사 등 역할 포함)에서 500자 이상, 중복 없이(MECE 원칙) 깊이 있게 결론과 조언을 제시
      - 질문 유형(상담, 재무, 진로 등)에 따라 그에 맞는 종합적 시각을 담아 주세요.
      - 다른 모자에서는 전문가 역할을 언급하지 않습니다.

    문제: {user_problem}
    """
    headers = {'Content-Type': 'application/json'}
    params = {'key': GOOGLE_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(GOOGLE_API_URL, headers=headers, params=params, json=payload, timeout=20)
        response.raise_for_status()
        print("[Google API 응답]", response.text)  # 응답 전체 로그 출력
        ai_content = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

        # 더욱 유연한 패턴(번호, *, 괄호, 영문/한글 혼용, 공백 등 모두 대응)
        hats = {
            'white': '', 'red': '', 'black': '', 'yellow': '', 'green': '', 'blue': ''
        }
        import re
        patterns = [
            (r'(하얀|흰|white)[ ]*모자|white hat', 'white'),
            (r'(빨간|red)[ ]*모자|red hat', 'red'),
            (r'(검은|black)[ ]*모자|black hat', 'black'),
            (r'(노란|yellow)[ ]*모자|yellow hat', 'yellow'),
            (r'(초록|green)[ ]*모자|green hat', 'green'),
            (r'(파란|blue)[ ]*모자|blue hat', 'blue'),
        ]
        lines = ai_content.split('\n')
        current = None
        for line in lines:
            line_strip = line.strip().lower()
            for pat, hat in patterns:
                if re.search(pat, line_strip, re.I):
                    current = hat
                    break
            else:
                if current:
                    hats[current] += (line + '\n')
        for k in hats:
            hats[k] = hats[k].strip()
        # 모든 모자별 답변이 비어 있으면 전체 답변을 white에라도 넣음
        if all(not v for v in hats.values()):
            hats['white'] = ai_content.strip()

        # --- 이메일 전송 기능 ---
        if user_email and '@' in user_email:
            try:
                # 마크다운 -> HTML 변환
                html_table = """
                <table style='width:100%;border-collapse:collapse;'>
                """
                for hat, label, color in [
                    ("white", "흰색 모자 (White Hat)", "#e3e3e3"),
                    ("red", "빨간색 모자 (Red Hat)", "#ffeaea"),
                    ("black", "검은색 모자 (Black Hat)", "#f0f0f0"),
                    ("yellow", "노란색 모자 (Yellow Hat)", "#fffde7"),
                    ("green", "초록색 모자 (Green Hat)", "#e8f5e9"),
                    ("blue", "파란색 모자 (Blue Hat)", "#e3f2fd"),
                ]:
                    html_table += f"<tr><td style='background:{color};padding:10px 20px;vertical-align:top;'><b>{label}</b><br>" + markdown(hats[hat]) + "</td></tr>"
                html_table += "</table>"
                msg = MIMEMultipart("alternative")
                msg["Subject"] = "Six Thinking Hats AI 분석 결과"
                msg["From"] = EMAIL_ADDRESS
                msg["To"] = user_email
                html = f"""
                <html>
                <head>
                <meta charset='utf-8'>
                <style>
                  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f7fa; margin:0; padding:0; }}
                  .container {{ max-width: 700px; margin: 30px auto; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px #0001; padding: 32px; }}
                  .logo-title {{ display: flex; align-items: center; margin-bottom: 24px; }}
                  .logo-circle {{ width: 48px; height: 48px; background: #6a1b9a; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 28px; font-weight: bold; margin-right: 16px; }}
                  h2 {{ color: #6a1b9a; margin-bottom: 8px; }}
                  .problem {{ background: #f3e5f5; padding: 12px 18px; border-radius: 8px; margin-bottom: 24px; font-size: 1.08em; }}
                  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
                  td {{ border-radius: 12px; vertical-align: top; padding: 18px 22px; font-size: 1.02em; }}
                  .footer {{ color: #888; font-size: 0.97em; text-align: right; margin-top: 18px; }}
                  @media (max-width: 600px) {{
                    .container {{ padding: 8px; }}
                    td {{ padding: 10px 6px; font-size: 0.98em; }}
                  }}
                </style>
                </head>
                <body>
                  <div class="container">
                    <div class="logo-title">
                      <div class="logo-circle">🧠</div>
                      <h2>Six Thinking Hats AI 분석 결과</h2>
                    </div>
                    <div class="problem"><b>문제/상황:</b> {user_problem}</div>
                    {html_table}
                    <div class="footer">Powered by Six Thinking Hats AI · <a href='mailto:{EMAIL_ADDRESS}' style='color:#6a1b9a;'>Contact</a></div>
                  </div>
                </body>
                </html>
                """
                msg.attach(MIMEText(html, "html"))
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                    server.sendmail(EMAIL_ADDRESS, user_email, msg.as_string())
                email_status = 'sent'  # 성공 시
            except Exception as e:
                print("이메일 전송 오류:", e)
                email_status = 'fail'  # 실패 시
        else:
            email_status = 'skipped'  # 이메일 없을 때

    except Exception as e:
        print("[API 에러]", str(e))  # 에러 로그 출력
        ai_content = f"AI API 오류: {str(e)}"
        hats = {k: ai_content for k in ['white','red','black','yellow','green','blue']}
        email_status = 'fail'

    return jsonify({
        'status': 'success',
        'problem': user_problem,
        'email': user_email,
        'ai_answer': ai_content,
        'hat_answers': hats,
        'email_status': email_status
    })

@app.route('/api/send_email_with_pdf', methods=['POST'])
def send_email_with_pdf():
    email = request.form.get('email')
    problem = request.form.get('problem')
    answers = request.form.get('answers')
    answers_dict = None
    try:
        answers_dict = json.loads(answers)
    except Exception:
        answers_dict = {}
    # 로고 파일의 절대경로 생성 (URL 인코딩)
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "royalbot_logo.png"))
    logo_url = "file:///" + urllib.parse.quote(logo_path.replace("\\", "/"))
    # Markdown -> HTML 변환
    for k in answers_dict:
        if isinstance(answers_dict[k], str):
            answers_dict[k] = markdown(answers_dict[k])
    # HTML 템플릿 (로고, 스타일, 파스텔톤 등 추가)
    html_template = '''
    <html><head><meta charset="utf-8"><style>
    body { font-family: "Malgun Gothic", Arial, sans-serif; background: #f0f4fc; }
    .container { background: #fff; border-radius: 18px; padding: 32px; margin: 16px; box-shadow: 0 2px 12px #0001; }
    .logo-title { display: flex; align-items: center; margin-bottom: 20px; }
    .logo-title img { height: 48px; margin-right: 18px; }
    h1 { color: #37508c; font-size: 2.1em; margin: 0; }
    .hat { margin-bottom: 22px; border-left: 8px solid #eee; padding-left: 16px; }
    .White { border-color: #e0e0e0; }
    .Red { border-color: #ef9a9a; }
    .Black { border-color: #212121; }
    .Yellow { border-color: #ffd600; }
    .Green { border-color: #43a047; }
    .Blue { border-color: #1565c0; }
    .hat-title { font-weight: bold; font-size: 1.1em; margin-bottom: 6px; }
    </style></head><body>
    <div class="container">
      <div class="logo-title">
        <img src="{{ logo_url }}" alt="logo" />
        <h1>Six Thinking Hats AI 분석 결과</h1>
      </div>
      <p><b>문제/상황:</b><br>{{ problem }}</p>
      {% for hat, label, color, desc in hats %}
        <div class="hat {{ color }}">
          <div class="hat-title">{{ label }} 모자 ({{ color }} Hat): {{ desc }}</div>
          <div>{{ answers.get(color.lower(), '답변 없음')|safe }}</div>
        </div>
      {% endfor %}
    </div></body></html>
    '''
    hats = [
        ('white', '흰색', 'White', '정보, 사실, 데이터'),
        ('red', '빨간색', 'Red', '감정, 직관, 느낌'),
        ('black', '검은색', 'Black', '비판적 사고, 위험, 문제점'),
        ('yellow', '노란색', 'Yellow', '긍정적 시각, 장점, 기회'),
        ('green', '초록색', 'Green', '창의적 사고, 대안'),
        ('blue', '파란색', 'Blue', '사고 관리, 종합, 메타')
    ]
    rendered_html = render_template_string(
        html_template,
        problem=problem,
        answers=answers_dict,
        hats=hats,
        logo_url=logo_url
    )
    # HTML -> PDF 변환
    pdf_bytes = pdfkit.from_string(rendered_html, False, options={
        'encoding': 'UTF-8',
        'page-size': 'A4',
        'margin-top': '16mm',
        'margin-bottom': '16mm',
        'margin-left': '12mm',
        'margin-right': '12mm',
        'no-outline': None,
        'enable-local-file-access': None
    }, configuration=PDFKIT_CONFIG)
    filename = 'SixThinkingHats.pdf'
    # 이메일 본문(텍스트)
    subject = '[Six Thinking Hats] AI 분석 결과 PDF 첨부'
    body = f"""
    안녕하세요, 요청하신 AI 분석 결과 PDF 파일을 첨부드립니다.\n\n문제/상황:\n{problem}\n\n분석 결과는 첨부된 PDF 파일을 확인해 주세요.\n\n감사합니다.
    """
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    # PDF 첨부
    part = MIMEApplication(pdf_bytes, _subtype='pdf')
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(part)
    # 메일 발송
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        return jsonify({'status': 'success', 'message': '이메일이 PDF 첨부와 함께 발송되었습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def index():
    return 'Six Thinking Hats API Server Running!'

if __name__ == '__main__':
    app.run(debug=True)
