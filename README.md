# 🔍 EduSearch — 개인용 웹 스크래퍼 + 로컬 검색 시스템

여러 사이트를 돌아다니지 않고, **수집한 자료를 내 PC에서 한 번에 검색**하는 시스템입니다.

---

## 📁 파일 구조

```
edusearch/
├── scraper.py      ← 웹 페이지 수집 (requests + Selenium 지원)
├── indexer.py      ← Whoosh 검색 인덱스 생성 (BM25F, 가중치 적용)
├── search_app.py   ← 로컬 검색 웹앱 (Flask, http://localhost:5000)
├── config.json     ← 설정 파일 (URL 목록, 크롤링 설정)
├── requirements.txt← 필요 라이브러리 목록
├── data.db         ← SQLite DB (자동 생성)
└── index_dir/      ← Whoosh 인덱스 폴더 (자동 생성)
```

---

## ⚙️ 1단계: 설치

```bash
pip install -r requirements.txt
```

**Selenium (동적/로그인 페이지) 사용 시 ChromeDriver도 설치:**
1. https://chromedriver.chromium.org/downloads 에서 Chrome 버전과 일치하는 드라이버 다운로드
2. `C:\chromedriver\` 폴더에 `chromedriver.exe` 저장
3. `config.json`의 `chromedriver_path`를 해당 경로로 수정

---

## 🔧 2단계: config.json 설정

```json
{
  "target_sites": [
    { "url": "https://사이트A.com/page1", "use_selenium": false },
    { "url": "https://사이트B.com/page2", "use_selenium": true }
  ],
  "delay_seconds": 5,
  "chromedriver_path": "C:/chromedriver/chromedriver.exe"
}
```

| 옵션 | 설명 |
|------|------|
| `use_selenium: false` | 일반 정적 페이지 (빠름, ChromeDriver 불필요) |
| `use_selenium: true` | 로그인/동적 페이지 (ChromeDriver 필요) |
| `delay_seconds` | 요청 간 대기 시간 (서버 부하 방지, 기본 5초) |

---

## 🚀 3단계: 실행 순서

### 1) 자료 수집
```bash
python scraper.py
```

단일 URL만 빠르게 테스트:
```bash
python scraper.py --url https://example.com
```

### 2) 인덱스 생성
```bash
python indexer.py
```

### 3) 검색앱 실행
```bash
python search_app.py
```
→ 브라우저에서 **http://localhost:5000** 접속

---

## 🔍 검색 기능

- **BM25F 랭킹** — 최신 검색 알고리즘 적용 (제목 2배, 키워드 1.5배 가중)
- **다중 필드 검색** — 제목·키워드·본문 동시 검색
- **퍼지 검색** — 오타가 있어도 유사 결과 반환

---

## ⚠️ 주의사항 (필독)

1. **robots.txt 자동 확인** — 차단된 사이트는 자동으로 스킵됨
2. **속도 제한** — 기본 5초 대기 (서버 부하 방지, 줄이지 마세요)
3. **개인용 한정** — 수집한 자료를 외부에 공유하지 마세요
4. **저작권** — 메타데이터(제목, URL, 키워드) 위주로 활용 권장
5. **로그인 사이트** — Selenium 사용 전 해당 사이트 이용약관 확인

---

## 🔄 새 자료 추가 워크플로우

```
1. config.json에 URL 추가
2. python scraper.py   (수집)
3. python indexer.py   (인덱스 재생성)
4. search_app.py는 계속 켜둬도 됨
```

---

## 🛠️ 확장 아이디어

| 아이디어 | 방법 |
|----------|------|
| **한국어 형태소 분석** | `pip install konlpy` 후 Okt 분석기 적용 |
| **URL 자동 수집** | Chrome 확장(SingleFile 등)으로 방문 페이지 자동 저장 |
| **정기 자동 수집** | Windows 작업 스케줄러로 `scraper.py` 매일 실행 |
| **태그/분류** | DB에 `tag` 컬럼 추가 후 수동 분류 |
| **전문 본문 저장** | `max_summary_chars` 늘리거나 PDF 다운로드 연동 |
