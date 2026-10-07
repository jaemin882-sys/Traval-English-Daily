import json
import os
import re
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

# 같은 장소라도 실제 여행에서는 여러 문제가 생기므로
# "큰 카테고리"가 아니라 구체적인 장면 단위로 넓게 구성한다.
TOPICS = [
    # Airport / flight
    "공항 체크인에서 통로석·앞쪽 좌석 요청하기",
    "공항 체크인에서 수하물 무게 초과 해결하기",
    "온라인 체크인이 안 되어 카운터에서 도움받기",
    "보안검색에서 전자기기·액체류 질문하기",
    "탑승구가 바뀌었는지 확인하기",
    "항공편 지연 이유와 예상 출발시간 묻기",
    "연결편 시간이 촉박할 때 직원에게 도움 요청하기",
    "항공편 취소 후 대체편 문의하기",
    "기내에서 좌석을 바꿔도 되는지 묻기",
    "기내에서 담요·물·식사 옵션 요청하기",
    "수하물이 나오지 않을 때 신고하기",
    "수하물이 파손됐을 때 보상 절차 문의하기",

    # Immigration / arrival
    "입국심사에서 여행 목적과 체류기간 설명하기",
    "입국심사에서 숙소 주소를 설명하기",
    "세관에서 신고할 물품이 있는지 질문받기",
    "공항에서 유심·eSIM 개통 문의하기",
    "공항에서 시내 가는 가장 쉬운 방법 묻기",

    # Hotel
    "호텔 체크인과 예약 확인하기",
    "얼리 체크인이 가능한지 정중하게 묻기",
    "예약한 객실 타입과 다른 방을 받았을 때 말하기",
    "방이 너무 시끄러워 객실 변경 요청하기",
    "에어컨·난방이 작동하지 않을 때 요청하기",
    "샤워기·온수 등 객실 시설 문제 설명하기",
    "추가 수건·생수·어메니티 요청하기",
    "조식 포함 여부와 시간을 확인하기",
    "레이트 체크아웃 가능한지 묻기",
    "체크아웃 후 짐을 맡길 수 있는지 묻기",
    "호텔 청구서에 모르는 금액이 있을 때 문의하기",

    # Restaurant / cafe
    "예약 없이 식당에 갔을 때 대기시간 묻기",
    "식당에서 메뉴 추천받기",
    "알레르기·못 먹는 재료를 설명하기",
    "메뉴의 재료와 조리방식 묻기",
    "주문한 음식이 나오지 않을 때 확인하기",
    "주문과 다른 음식이 나왔을 때 말하기",
    "음식 간을 조절해달라고 요청하기",
    "사이드 메뉴나 소스를 다른 것으로 바꾸기",
    "포장 가능한지 요청하기",
    "계산서를 나눠 결제할 수 있는지 묻기",
    "카페에서 우유 종류·샷·당도 등을 바꿔 주문하기",
    "테이크아웃 주문이 잘못 나왔을 때 수정 요청하기",

    # Transport
    "택시에서 목적지와 선호 경로 말하기",
    "택시가 목적지와 다른 방향으로 갈 때 확인하기",
    "택시 카드 결제 가능 여부 묻기",
    "기차표를 당일 다른 시간으로 변경하기",
    "기차 플랫폼과 환승 위치 확인하기",
    "버스를 잘못 탔는지 기사에게 확인하기",
    "대중교통 카드 충전 방법 묻기",
    "렌터카 픽업 시 보험 보장범위 확인하기",
    "렌터카에 흠집이 있어 출발 전 기록 요청하기",
    "렌터카 반납 장소와 연료 규정 확인하기",

    # Shopping
    "쇼핑 중 다른 사이즈·색상 재고 묻기",
    "입어봐도 되는지와 피팅룸 위치 묻기",
    "면세 가능 여부와 절차 묻기",
    "가격표와 계산 금액이 다를 때 확인하기",
    "환불·교환 조건 묻기",
    "카드 결제가 거절됐을 때 다른 결제수단 문의하기",
    "제품 두 개의 차이를 직원에게 물어보기",

    # Sightseeing / activities
    "관광지 티켓 종류와 포함사항 비교하기",
    "예약 시간보다 늦었을 때 입장 가능한지 묻기",
    "투어 집합 장소와 시간을 다시 확인하기",
    "매진된 티켓의 취소표나 다른 시간대 묻기",
    "사진을 부탁하면서 구도를 간단히 설명하기",
    "현지인에게 근처 추천 장소를 물어보기",
    "붐비지 않는 시간대를 물어보기",

    # Problems / emergencies
    "길을 잃었을 때 현재 위치와 방향 확인하기",
    "휴대폰을 잃어버렸을 때 도움 요청하기",
    "지갑·여권을 분실했을 때 신고하기",
    "약국에서 감기·두통·소화불량 증상 설명하기",
    "복용 중인 약과 함께 먹어도 되는지 묻기",
    "병원에서 증상 시작 시점과 정도 설명하기",
    "응급상황에서 주변 사람에게 도움 요청하기",
    "예약 확인 메일이 없을 때 예약 여부 확인하기",
    "인터넷·와이파이가 작동하지 않을 때 문의하기",

    # More natural social travel situations
    "현지인과 가벼운 스몰토크 시작하기",
    "추천받은 장소가 어떤 분위기인지 더 물어보기",
    "상대방 말을 못 알아들었을 때 자연스럽게 다시 묻기",
    "말이 너무 빠를 때 천천히 말해달라고 부탁하기",
    "내가 이해한 내용이 맞는지 다시 확인하기",
    "두 가지 선택지 중 무엇이 더 나은지 의견 묻기",
    "예정보다 시간이 더 걸리는지 확인하기",
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

def read_recent_lessons(limit=30):
    history = read_history_index()
    lessons = []
    for item in history[-limit:]:
        date = item.get("date")
        if not date:
            continue
        path = HISTORY_DIR / f"{date}.json"
        if not path.exists():
            continue
        try:
            lessons.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return lessons

def choose_topic():
    history = read_history_index()
    # 최근 60개에서는 같은 주제를 되도록 반복하지 않는다.
    used = [x.get("topic") for x in history[-60:] if x.get("topic")]
    for topic in TOPICS:
        if topic not in used:
            return topic

    # 전체 풀을 모두 소진한 경우에도 바로 처음으로 돌아가지 않고
    # 가장 오래 전에 공부한 주제를 선택한다.
    last_used = {}
    for idx, item in enumerate(history):
        topic = item.get("topic")
        if topic:
            last_used[topic] = idx

    return min(TOPICS, key=lambda t: last_used.get(t, -1))

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

def collect_recent_language():
    lessons = read_recent_lessons(30)

    topics = []
    patterns = []
    sentences = []
    words = []

    for lesson in lessons:
        topic = lesson.get("topic")
        if topic:
            topics.append(topic)

        pattern = lesson.get("pattern", {})
        form = pattern.get("form") if isinstance(pattern, dict) else None
        if form:
            patterns.append(form)

        for s in lesson.get("sentences", []):
            english = s.get("english", "")
            if english:
                sentences.append(english)

        for w in lesson.get("words", []):
            word = w.get("word", "")
            if word:
                words.append(word)

    # 프롬프트가 너무 길어지지 않게 최근 것만 보낸다.
    return {
        "topics": topics[-20:],
        "patterns": patterns[-20:],
        "sentences": sentences[-60:],
        "words": words[-50:],
    }

def normalize_start(sentence):
    s = (sentence or "").strip().lower()
    s = re.sub(r"[^a-z' ]", "", s)
    return " ".join(s.split()[:3])

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

    # 다섯 문장이 모두 같은 시작 방식으로 생성되는 것을 방지
    starts = [normalize_start(x.get("english", "")) for x in data.get("sentences", [])]
    starts = [x for x in starts if x]
    if len(set(starts)) < 4:
        raise ValueError("핵심 문장의 표현 구조가 너무 단조롭습니다.")

    return data

def generate_lesson(topic):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY가 없습니다.")

    recent = collect_recent_language()

    prompt = f"""
한국인 성인이 해외여행 직전에 공부하는 '실제 회화용' 영어 콘텐츠를 만들어라.

오늘 상황:
{topic}

학습자 수준:
- A2~B1 사이지만 너무 초보적인 표현은 이미 알고 있다.
- Hello, Thank you, Yes, No, Please, Excuse me 같은 표현을 학습 항목으로 넣지 않는다.
- 단순히 'Could you...?', 'I'd like...', 'Can I...?'만 반복하는 교재식 영어를 피한다.
- 여행 현장에서 실제로 바로 써먹을 수 있는 자연스럽고 다양한 문장을 우선한다.
- 학습이 쌓일수록 조금씩 B1에 가까운 표현과 뉘앙스를 섞는다.

최근 학습 기록:
- 최근 주제: {json.dumps(recent["topics"], ensure_ascii=False)}
- 최근 대표 패턴: {json.dumps(recent["patterns"], ensure_ascii=False)}
- 최근 핵심 문장: {json.dumps(recent["sentences"], ensure_ascii=False)}
- 최근 단어/표현: {json.dumps(recent["words"], ensure_ascii=False)}

중복 방지 규칙:
1. 최근 핵심 문장을 그대로 또는 거의 같은 형태로 다시 만들지 않는다.
2. 최근 대표 패턴과 동일한 패턴은 가능하면 피한다.
3. 오늘 핵심 문장 5개는 최소 4가지 서로 다른 문장 시작/구조를 사용한다.
4. 'Could you...'로 시작하는 문장은 최대 1개.
5. 'I'd like...'로 시작하는 문장은 최대 1개.
6. 'Can I...'로 시작하는 문장은 최대 1개.
7. 다섯 문장이 모두 요청문이 되지 않게 한다.
   요청 + 확인 + 문제 설명 + 재확인 + 대안 질문 등을 섞는다.
8. 같은 뜻의 표현을 단어만 바꿔 5개 만드는 식은 금지한다.

표현 다양성 예시:
아래 표현을 반드시 쓰라는 뜻이 아니라, 이런 정도의 자연스러운 다양성을 목표로 한다.
- Would it be possible to ...?
- Is there any chance ...?
- I was wondering if ...
- Do you happen to know ...?
- Just to make sure, ...
- I seem to have ...
- I'm afraid ...
- What would be the best way to ...?
- Would you mind ...?
- Is that included in ...?
- How soon would ...?
- Am I right in thinking ...?
- Is there another option?
- Could I get ... instead?
- I don't think this is what I ordered.
- I'm not sure I understood that correctly.

핵심 원칙:
- '보는 공부'보다 기억에서 직접 꺼내는 연습을 중심으로 한다.
- 문법 설명은 길게 하지 않는다.
- 오늘 상황에서 여러 번 응용할 수 있는 대표 패턴 하나를 고른다.
- 대표 패턴은 최근 학습 패턴과 겹치지 않도록 한다.
- 핵심 문장 5개는 각각 역할이 달라야 한다.
- 단어 5개는 단순 명사보다 실제 여행에서 자주 쓰는 표현, 구동사, 짧은 관용표현도 포함한다.
- 대화는 실제 상황처럼 5~7턴으로 만든다.
- Staff/You가 서로 질문하고 답하는 흐름이 자연스러워야 한다.
- retrieval은 핵심 문장 중 실전성이 높은 3개를 고른다.
- 퀴즈는 단어 뜻 문제가 아니라 실제 상황에서 자연스러운 말을 고르는 문제로 만든다.
- 미국/영국 등 어디서도 무난하게 통하는 표현을 우선한다.
- 번역투를 피한다.
- 한국어 설명은 짧고 명확하게 한다.

오늘 핵심 문장의 역할 예시:
1) 처음 상황을 꺼내는 말
2) 구체적인 요청/질문
3) 문제가 있음을 설명
4) 상대방 답을 재확인
5) 대안이나 다음 행동을 묻기

반드시 JSON만 출력:
{{
  "topic": "{topic}",
  "intro": "오늘 상황에서 무엇을 연습하는지 1~2문장",
  "sentences": [
    {{
      "english": "자연스러운 실전 영어 문장",
      "korean": "자연스러운 한국어 뜻",
      "tip": "언제 쓰는지 또는 뉘앙스"
    }}
  ],
  "pattern": {{
    "form": "오늘의 대표 패턴",
    "meaning": "패턴의 쉬운 한국어 설명",
    "examples": ["서로 다른 상황의 변형 예문 1", "변형 예문 2"]
  }},
  "words": [
    {{
      "word": "실전 단어/짧은 표현",
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

    # 표현 다양성 검사에서 걸리면 Gemini에게 한 번 더 생성 기회를 준다.
    last_error = None
    for attempt in range(2):
        try:
            response = client.models.generate_content(model=MODEL, contents=prompt)
            if not response.text:
                raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")
            return validate(parse_json(response.text))
        except ValueError as e:
            last_error = e
            if attempt == 0:
                prompt += f"""

이전 생성 결과가 다음 이유로 품질검사를 통과하지 못했다:
{e}

이번에는 문장 시작과 표현 구조를 더 다양하게 해서 전체 JSON을 새로 생성하라.
"""
            else:
                raise

    raise last_error or RuntimeError("학습 생성에 실패했습니다.")

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
