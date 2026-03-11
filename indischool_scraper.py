"""
indischool_scraper.py - 인디스쿨 자동 로그인 + 검색 + 수집
사용법: python indischool_scraper.py --query "감각적 표현 시감상" --pages 3
"""

import os
import time
import sqlite3
import argparse
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()  # .env 파일에서 아이디/비번 로드

# ── 설정 ──────────────────────────────────
INDISCHOOL_ID = os.getenv("INDISCHOOL_ID")
INDISCHOOL_PW = os.getenv("INDISCHOOL_PW")
DB_PATH = "data.db"

LOGIN_URL    = "https://indischool.com/member/login"
SEARCH_URL   = "https://indischool.com/search?query={query}&page={page}"


# ── DB 초기화 ──────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT,
            url        TEXT UNIQUE,
            keywords   TEXT,
            summary    TEXT,
            site       TEXT,
            scraped_at TEXT
        )
    """)
    conn.commit()
    return conn


# ── 드라이버 준비 (Selenium 4.6+ 자동 드라이버) ──
def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--lang=ko-KR")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)   # Selenium Manager 자동 다운로드
    return driver


# ── 로그인 ─────────────────────────────────
def login(driver):
    print("[1/3] 인디스쿨 로그인 중...")
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 10)

    # 아이디 / 비번 입력
    wait.until(EC.presence_of_element_located((By.NAME, "member_id")))
    driver.find_element(By.NAME, "member_id").send_keys(INDISCHOOL_ID)
    driver.find_element(By.NAME, "member_pw").send_keys(INDISCHOOL_PW)

    # 로그인 버튼
    driver.find_element(By.CSS_SELECTOR, "button[type=submit], input[type=submit]").click()
    time.sleep(2)

    if "logout" in driver.page_source.lower() or "마이페이지" in driver.page_source:
        print("  ✅ 로그인 성공")
        return True
    else:
        print("  ❌ 로그인 실패 — .env의 INDISCHOOL_ID/PW 확인")
        return False


# ── 검색 결과 수집 ─────────────────────────
def scrape_search_results(driver, query, max_pages=3):
    print(f"[2/3] '{query}' 검색 결과 수집 중 ({max_pages}페이지)...")
    results = []

    for page in range(1, max_pages + 1):
        url = SEARCH_URL.format(query=query, page=page)
        driver.get(url)
        time.sleep(2)

        # 검색 결과 항목 파싱 (인디스쿨 구조에 맞게 조정)
        items = driver.find_elements(By.CSS_SELECTOR, ".search-list li, .board-list li, .result-item")

        if not items:
            # 구조가 다를 경우 폭넓게 탐색
            items = driver.find_elements(By.CSS_SELECTOR, "article, .post-item, .list-item")

        if not items:
            print(f"  페이지 {page}: 결과 없음 또는 구조 불일치 → 중단")
            break

        for item in items:
            try:
                # 제목 + 링크
                link_el = item.find_element(By.CSS_SELECTOR, "a")
                title = link_el.text.strip() or item.text.strip()[:80]
                href = link_el.get_attribute("href") or ""

                if not href or not title:
                    continue

                # 요약 (있으면)
                try:
                    summary_el = item.find_element(By.CSS_SELECTOR, ".desc, .summary, p, .content")
                    summary = summary_el.text.strip()[:500]
                except Exception:
                    summary = title

                results.append({
                    "title": title,
                    "url": href,
                    "keywords": query,
                    "summary": summary,
                    "site": "indischool.com",
                })
            except Exception:
                continue

        print(f"  페이지 {page}: {len(results)}개 누적")
        time.sleep(3)  # 속도 제한

    return results


# ── DB 저장 ────────────────────────────────
def save_to_db(conn, results):
    print(f"[3/3] DB 저장 중...")
    saved = 0
    scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for r in results:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO pages (title, url, keywords, summary, site, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (r["title"], r["url"], r["keywords"], r["summary"], r["site"], scraped_at))
            saved += 1
        except Exception:
            pass
    conn.commit()
    print(f"  ✅ {saved}개 저장 완료")
    return saved


# ── 메인 ───────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="인디스쿨 자동 수집기")
    parser.add_argument("--query", default="감각적 표현 시감상 3학년", help="검색어")
    parser.add_argument("--pages", type=int, default=3, help="수집할 페이지 수")
    parser.add_argument("--show", action="store_true", help="브라우저 창 표시 (디버그용)")
    args = parser.parse_args()

    if not INDISCHOOL_ID or not INDISCHOOL_PW:
        print("❌ .env 파일에 INDISCHOOL_ID, INDISCHOOL_PW를 입력하세요.")
        print("   cp .env.example .env  →  .env 파일 열어서 입력")
        return

    conn = init_db()
    driver = get_driver(headless=not args.show)

    try:
        if not login(driver):
            return
        results = scrape_search_results(driver, args.query, args.pages)
        saved = save_to_db(conn, results)
        print(f"\n✅ 완료: {saved}개 수집됨")
        print("다음 단계: python indexer.py → python search_app.py")
    finally:
        driver.quit()
        conn.close()


if __name__ == "__main__":
    main()
