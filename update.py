import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from google import genai

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "lesson.json"
HISTORY_DIR = ROOT / "history"
HISTORY_INDEX = HISTORY_DIR / "index.json"
KST = ZoneInfo("Asia/Seoul")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

TOPICS = [
    "공항 체크인과 좌석 요청",
    "입국심사에서 여행 목적 설명",
    "수하물이 나오지 않을 때",
    "호텔 체크인과 예약 확인",
    "호텔 방에 문제가 있을 때",
    "식당에서 주문하고 요청사항 말하기",
    "카페에서 원하는 음료 정확히 주문하기",
    "택시에서 목적지와 경로 말하기",
    "길을 잃었을 때 길 묻기",
    "쇼핑 중 사이즈와 재고 묻기",
    "가격·할인·결제 방법 묻기",
    "렌터카 픽업과 보험 확인",
    "기차역에서 플랫폼과 시간 확인",
    "관광지에서 티켓과 운영시간 묻기",
    "사진을 부탁하고 위치 조정하기",
    "약국에서 증상을 간단히 설명하기",
    "응급상황에서 도움 요청하기",
    "분실물 센터에서 물건 설명하기",
    "항공편 지연·변경 문의하기",
    "호텔 체크아웃과 짐 보관 요청"
]

REVIEW_OFFSETS = {1: 2, 3: 2, 6: 2, 13: 3}

def read_history_index():
    if not HISTORY_INDEX.exists():
        return []
    try:
        data = json.loads(HISTORY_INDEX.read_text(encoding="utf-8"))
        return data.get("items", [])
    except Exception:
        return []

def choose_topic():
    history = read_history_index()
    used = [x.get("topic") for x in history[-20:]]
    for topic in TOPICS:
        if topic not in used:
            return topic
    return TOPICS[len(history) % len(TOPICS)]

def parse_json(text):
    text = (text or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("JSON 응답을 찾지 못했습니다.")
    return json.loads(text[start:end+1])

def build_review_items(today):
    items = []
    for days_ago, count in REVIEW_OFFSETS.items():
        source_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        path = HISTORY_DIR / f"{source_date}.json"
        if not path.exists():
            continue
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            sentences = old.get("sentences", [])
            for sentence in sentences[:count]:
                items.append({
                    "source_date": source_date,
                    "english": sentence.get("english", ""),
                    "korean": sentence.get("korean", ""),
                    "tip": f"{days_ago}일 전 배운 표현입니다. 정답을 보기 전에 먼저 말해보세요."
                })
        except Exception:
            continue
    return items[:5]

def validate(data):
    if len(data.get("sentences", [])) != 5:
        raise ValueError("핵심 문장은 정확히 5개여야 합니다.")
    if len(data.get("words", [])) != 5:
        raise ValueError("단어는 정확히 5개여야 합니다.")
    if len(data.get("quiz", [])) != 2:
        raise ValueError("퀴즈는 정확히 2개여야 합니다.")
    if len(data.get("retrieval", [])) != 3:
        raise ValueError("기억에서 꺼내기는 정확히 3개여야 합니다.")
    if not isinstance(data.get("pattern"), dict):
        raise ValueError("pattern이 필요합니다.")
    return data

def generate_lesson(topic):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY가 없습니다.")

    prompt = f"""
한국인 성인이 여행 직전에 공부하는 실전 영어 콘텐츠를 만들어라.

오늘 상황: {topic}

학습자 수준:
- 영어 회화 초보이지만 'Thank you', 'Hello', 'Yes', 'No', 'Please' 같은 표현은 이미 안다.
- 너무 쉬운 단어나 한 단어짜리 인사 표현을 학습 항목으로 넣지 않는다.
- 대략 A2~B1 수준에서 여행 중 실제로 말문이 막힐 만한 표현을 우선한다.

핵심 원칙:
- '보는 공부'보다 기억에서 직접 꺼내는 연습을 중심으로 한다.
- 문법 설명은 길게 하지 않는다.
- 여행에서 여러 상황에 재사용 가능한 패턴을 하나 포함한다.
- 핵심 문장 5개는 자연스럽고 실제로 자주 쓸 만한 표현이어야 한다.
- 단어 5개도 thank you, hotel, taxi처럼 너무 쉬운 것은 제외한다.
- 대화는 실제 여행에서 일어날 법한 4~6턴으로 만든다.
- retrieval은 핵심 문장 중 중요한 3개를 골라 한국어를 보고 영어를 떠올릴 수 있게 구성한다.
- 퀴즈는 단순 단어 뜻 맞히기가 아니라 '이 상황에서 무엇이라고 말하는 게 자연스러운가?' 형식의 객관식 2문제로 만든다.
- 미국/영국 등에서 무난하게 통하는 표현을 우선한다.
- 번역투보다 실제 회화에서 자연스러운 영어를 쓴다.
- 설명은 한국어로 짧고 쉽게 한다.

반드시 JSON만 출력:
{{
  "topic": "{topic}",
  "intro": "오늘 상황에서 무엇을 연습하는지 1~2문장",
  "sentences": [
    {{
      "english": "실전 영어 문장",
      "korean": "자연스러운 한국어 뜻",
      "tip": "언제 쓰는지 또는 뉘앙스"
    }}
  ],
  "pattern": {{
    "form": "Could you + 동사 ...?",
    "meaning": "패턴의 쉬운 한국어 설명",
    "examples": ["변형 예문 1", "변형 예문 2"]
  }},
  "words": [
    {{
      "word": "실전 단어/표현",
      "meaning": "한국어 뜻"
    }}
  ],
  "dialogue": [
    {{
      "speaker": "Staff 또는 You",
      "english": "영어",
      "korean": "한국어"
    }}
  ],
  "retrieval": [
    {{
      "english": "정답 영어",
      "korean": "영어로 떠올릴 한국어 문장",
      "tip": "정답 확인 후 짧은 포인트"
    }}
  ],
  "quiz": [
    {{
      "question": "실제 상황형 질문",
      "options": ["선택지 1","선택지 2","선택지 3"],
      "answer_index": 0,
      "explanation": "왜 이 표현이 가장 자연스러운지 짧게 설명"
    }}
  ]
}}
"""
    client = genai.Client(api_key=key)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    if not response.text:
        raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")
    return validate(parse_json(response.text))

def archive(final):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    date_str = final["date"]

    (HISTORY_DIR / f"{date_str}.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    items = [x for x in read_history_index() if x.get("date") != date_str]
    items.append({"date": date_str, "topic": final["topic"]})
    items = sorted(items, key=lambda x: x["date"])

    HISTORY_INDEX.write_text(
        json.dumps({"items": items}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def main():
    now = datetime.now(KST)
    topic = choose_topic()
    lesson = generate_lesson(topic)
    lesson["review_items"] = build_review_items(now)

    final = {
        "date": now.strftime("%Y-%m-%d"),
        "updated_at": now.strftime("%H:%M KST"),
        **lesson
    }

    OUTPUT.write_text(
        json.dumps(final, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    archive(final)

    print(f"Updated: {final['topic']}")
    print(f"Review items: {len(final['review_items'])}")

if __name__ == "__main__":
    main()
