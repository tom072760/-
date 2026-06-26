# 매일 아침 시황 브리핑

원달러 환율 전망, 국내/해외 주요 지수, 지정 종목 시세를 모아 Claude로 요약한 뒤
매일 아침 9시(KST) 텔레그램으로 보내는 시스템입니다.

## 동작 방식

- GitHub Actions가 매일 00:00 UTC(=09:00 KST)에 `scripts/morning_brief.py`를 실행
- `yfinance`로 환율/지수/종목 시세 조회, Google News RSS로 관련 헤드라인 수집
- Claude API로 브리핑 메시지 작성 후 Telegram Bot API로 전송

## 설정 (GitHub Secrets)

저장소 Settings → Secrets and variables → Actions → New repository secret 에서 아래 3개를 등록하세요.

| Secret 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `TELEGRAM_BOT_TOKEN` | BotFather에서 발급받은 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 메시지를 받을 chat id |

## 수동 실행

Actions 탭 → "Daily Morning Market Brief" → Run workflow 로 즉시 테스트할 수 있습니다.

## 종목 구성

- 지수: 코스피, 코스닥, 다우, S&P500, 나스닥
- 환율: USD/KRW
- 국내: 삼성전자우, KODEX 반도체레버리지, SK하이닉스, KODEX 200
- 미국: 테슬라(TSLA), 알파벳 Class C(GOOG), QQQI, VOO

종목을 추가/변경하려면 `scripts/morning_brief.py`의 `KR_STOCKS`, `US_STOCKS` 딕셔너리를 수정하세요.
