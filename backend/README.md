# Six Thinking Hats Backend

이 디렉토리는 Flask 기반의 API 서버입니다.

## 실행 방법

1. 의존성 설치
```
pip install -r requirements.txt
```

2. 서버 실행
```
python app.py
```

## 주요 엔드포인트
- `/api/solve` : 문제와 이메일을 받아 처리합니다 (POST)
- `/` : 서버 상태 확인 (GET)
