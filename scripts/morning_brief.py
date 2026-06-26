"""Daily morning market brief: FX outlook + KR/US market summary, sent via Telegram."""
import os
import sys
import time
import feedparser
import requests
import yfinance as yf
from anthropic import Anthropic

INDICES = {
    "코스피": "^KS11",
    "코스닥": "^KQ11",
    "다우": "^DJI",
    "S&P500": "^GSPC",
    "나스닥": "^IXIC",
}

KR_STOCKS = {
    "삼성전자우": "005935.KS",
    "KODEX 반도체레버리지": "494310.KS",
    "SK하이닉스": "000660.KS",
    "KODEX 200": "069500.KS",
}

US_STOCKS = {
    "테슬라(TSLA)": "TSLA",
    "알파벳 Class C(GOOG)": "GOOG",
    "QQQI": "QQQI",
    "VOO": "VOO",
}

FX = {"USD/KRW": "KRW=X"}

NEWS_QUERIES = [
    "원달러 환율 전망",
    "코스피 마감",
    "나스닥 마감",
    "미국 증시 마감",
]


def fetch_quote(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if len(hist) < 2:
            return None
        last = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2]
        change = last - prev
        pct = change / prev * 100
        return {"price": last, "change": change, "pct": pct}
    except Exception as e:
        print(f"quote fetch failed for {ticker}: {e}", file=sys.stderr)
        return None


def fetch_quotes(name_ticker_map):
    out = {}
    for name, ticker in name_ticker_map.items():
        q = fetch_quote(ticker)
        if q:
            out[name] = q
        time.sleep(0.3)
    return out


def fetch_news(query, limit=4):
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:limit]]


def format_quotes(quotes, label):
    lines = [f"[{label}]"]
    for name, q in quotes.items():
        sign = "+" if q["change"] >= 0 else ""
        lines.append(f"- {name}: {q['price']:.2f} ({sign}{q['change']:.2f}, {sign}{q['pct']:.2f}%)")
    return "\n".join(lines)


def build_prompt():
    fx_quotes = fetch_quotes(FX)
    idx_quotes = fetch_quotes(INDICES)
    kr_quotes = fetch_quotes(KR_STOCKS)
    us_quotes = fetch_quotes(US_STOCKS)

    news_items = []
    for q in NEWS_QUERIES:
        news_items.extend(fetch_news(q))

    data_block = "\n\n".join([
        format_quotes(fx_quotes, "환율"),
        format_quotes(idx_quotes, "주요 지수"),
        format_quotes(kr_quotes, "국내 종목"),
        format_quotes(us_quotes, "미국 종목"),
    ])
    news_block = "\n".join(f"- {t}" for t in news_items)

    prompt = f"""아래는 오늘 아침 기준 시세 데이터와 관련 뉴스 헤드라인입니다.
이 내용을 바탕으로 부모님이 매일 아침 받아보실 시황 브리핑 메시지를 작성해주세요.

요구사항:
- 친근하고 쉬운 말투로, 전문 용어는 짧게 풀어서 설명
- 구성: 1) 원달러 환율 현황 및 전망 한 줄, 2) 국내 증시(코스피/코스닥) 요약, 3) 해외 증시(다우/S&P500/나스닥) 요약, 4) 보유 종목(국내/미국) 간단 코멘트, 5) 오늘 체크포인트 한 줄
- 너무 길지 않게, 텔레그램 메시지로 보내기 좋게 (이모지 약간 사용 가능)
- 숫자는 데이터에 있는 값을 그대로 사용하고 추측하지 말 것

[시세 데이터]
{data_block}

[관련 뉴스 헤드라인]
{news_block}
"""
    return prompt


def summarize_with_claude(prompt):
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def send_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, data={"chat_id": chat_id, "text": text})
    resp.raise_for_status()


def main():
    prompt = build_prompt()
    briefing = summarize_with_claude(prompt)
    send_telegram(briefing)


if __name__ == "__main__":
    main()
