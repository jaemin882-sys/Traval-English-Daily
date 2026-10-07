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

TOPICS = [
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
    "입국심사에서 여행 목적과 체류기간 설명하기",
    "입국심사에서 숙소 주소를 설명하기",
    "세관에서 신고할 물품이 있는지 질문받기",
    "공항에서 유심·eSIM 개통 문의하기",
    "공항에서 시내 가는 가장 쉬운 방법 묻기",
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
    "쇼핑 중 다른 사이즈·색상 재고 묻기",
    "입어봐도 되는지와 피팅룸 위치 묻기",
    "면세 가능 여부와 절차 묻기",
    "가격표와 계산 금액이 다를 때 확인하기",
    "환불·교환 조건 묻기",
    "카드 결제가 거절됐을 때 다른 결제수단 문의하기",
    "제품 두 개의 차이를 직원에게 물어보기",
    "관광지 티켓 종류와 포함사항 비교하기",
    "예약 시간보다 늦었을 때 입장 가능한지 묻기",
    "투어 집합 장소와 시간을 다시 확인하기",
    "매진된 티켓의 취소표나 다른 시간대 묻기",
    "사진을 부탁하면서 구도를 간단히 설명하기",
    "현지인에게 근처 추천 장소를 물어보기",
    "붐비지 않는 시간대를 물어보기",
    "길을 잃었을 때 현재 위치와 방향 확인하기",
    "휴대폰을 잃어버렸을 때 도움 요청하기",
    "지갑·여권을 분실했을 때 신고하기",
    "약국에서 감기·두통·소화불량 증상 설명하기",
    "복용 중인 약과 함께 먹어도 되는지 묻기",
    "병원에서 증상 시작 시점과 정도 설명하기",
    "응급상황에서 주변 사람에게 도움 요청하기",
    "예약 확인 메일이 없을 때 예약 여부 확인하기",
    "인터넷·와이파이가 작동하지 않을 때 문의하기",
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
        return json.loads(HISTORY_INDEX.read_text(encoding="utf-8")).get("items", [])
    except Exception:
        return []

def read_recent_lessons(limit=30):
    out = []
    for item in read_history_index()[-limit:]:
        date = item.get("date")
        if not date:
            continue
        p = HISTORY_DIR / f"{date}.json"
        if not p.exists():
            continue
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out

def choose_topic():
    history = read_history_index()
    used = [x.get("topic") for x in history[-60:] if x.get("topic")]
    for topic in TOPICS:
        if topic not in used:
            return topic
    last_used = {}
    for i, item in enumerate(history):
        if item.get("topic"):
            last_used[item["topic"]] = i
    return min(TOPICS, key=lambda t: last_used.get(t, -1))

def parse_json(text):
    text = (text or "").strip()
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("JSON 응답을 찾지 못했습니다.")
    return json.loads(text[a:b+1])

def build_review_items(today):
    items = []
    for days_ago, count in REVIEW_OFFSETS.items():
        date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        p = HISTORY_DIR / f"{date}.json"
        if not p.exists():
            continue
        try:
            old = json.loads(p.read_text(encoding="utf-8"))
            for s in old.get("sentences", [])[:count]:
                items.append({
                    "source_date": date,
                    "english": s.get("english", ""),
                    "pronunciation": s.get("pronunciation", ""),
                    "korean": s.get("korean", ""),
                    "tip": f"{days_ago}일 전 배운 표현입니다. 정답을 보기 전에 먼저 말해보세요."
                })
        except Exception:
            pass
    return items[:5]

def recent_language():
    topics, patterns, sentences, words = [], [], [], []
    for lesson in read_recent_lessons(30):
        if lesson.get("topic"):
            topics.append(lesson["topic"])
        p = lesson.get("pattern", {})
        if isinstance(p, dict) and p.get("form"):
            patterns.append(p["form"])
        sentences += [x.get("english","") for x in lesson.get("sentences",[]) if x.get("english")]
        words += [x.get("word","") for x in lesson.get("words",[]) if x.get("word")]
    return {
        "topics": topics[-20:], "patterns": patterns[-20:],
        "sentences": sentences[-60:], "words": words[-50:]
    }

def normalize_start(s):
    s = re.sub(r"[^a-z' ]", "", (s or "").lower())
    return " ".join(s.split()[:3])

def validate(d):
    if len(d.get("sentences", [])) != 5:
        raise ValueError("핵심 문장은 정확히 5개여야 합니다.")
    if len(d.get("words", [])) != 5:
        raise ValueError("단어/표현은 정확히 5개여야 합니다.")
    if len(d.get("retrieval", [])) != 3:
        raise ValueError("기억에서 꺼내기는 정확히 3개여야 합니다.")
    if len(d.get("alternatives", [])) != 3:
        raise ValueError("다른 표현은 정확히 3개여야 합니다.")
    if not isinstance(d.get("pattern"), dict):
        raise ValueError("pattern이 필요합니다.")
    starts = [normalize_start(x.get("english","")) for x in d["sentences"]]
    if len(set(x for x in starts if x)) < 4:
        raise ValueError("핵심 문장의 표현 구조가 너무 단조롭습니다.")
    return d

def generate_lesson(topic):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY가 없습니다.")
    recent = recent_language()

    prompt = f"""
한국인 성인이 해외여행 직전에 공부하는 실제 회화용 영어 콘텐츠를 만들어라.

오늘 상황: {topic}

학습자 수준:
- A2~B1. Hello, Thank you, Yes, No, Please 같은 초급 표현은 학습 항목으로 넣지 않는다.
- 여행 현장에서 실제로 쓰는 자연스럽고 다양한 표현을 우선한다.
- Could you / I'd like / Can I 만 반복하지 않는다.
- 요청, 확인, 문제 설명, 재확인, 대안 질문을 섞는다.
- 최근 학습과 비슷한 문장이나 패턴을 반복하지 않는다.

최근 주제: {json.dumps(recent["topics"], ensure_ascii=False)}
최근 패턴: {json.dumps(recent["patterns"], ensure_ascii=False)}
최근 문장: {json.dumps(recent["sentences"], ensure_ascii=False)}
최근 단어/표현: {json.dumps(recent["words"], ensure_ascii=False)}

표현 다양성:
- 핵심 문장 5개는 최소 4가지 서로 다른 시작/구조.
- Could you / I'd like / Can I 로 시작하는 문장은 각각 최대 1개.
- 같은 뜻을 단어만 바꿔 반복하지 않는다.
- 자연스러운 예: Would it be possible to... / Is there any chance... / I was wondering if...
  / Just to make sure... / I seem to have... / What would be the best way to...
  / Is there another option? / I'm not sure I understood that correctly.

한글 발음 표기:
- 모든 영어 학습 항목에 pronunciation 필드를 반드시 넣는다.
- IPA가 아니라 한국인이 보고 바로 따라 읽을 수 있는 한글 표기.
- 철자를 한 글자씩 옮기지 말고 자연스러운 미국 영어 발음에 가깝게 적는다.
- 필요하면 하이픈(-)이나 띄어쓰기로 리듬을 표시한다.
- 예: apple → 애-쁠 / Would it be possible? → 우딧 비 파서블?
- 완벽한 음성학 표기가 아니라 초보자의 발음 보조용이다.

구성:
- 핵심 문장 5개
- 재사용 패턴 1개 + 변형 예문 2개
- 단어/짧은 표현 5개
- 실제 대화 5~7턴
- 기억에서 꺼내기 3개
- 퀴즈는 만들지 않는다.
- 대신 alternatives를 3개 만든다. 오늘 핵심 표현과 같은 의도를 다른 말투로 표현하는 자연스러운 대체 표현이다.
  각 alternative에는 어떤 차이가 있는지 note로 짧게 설명한다.

반드시 JSON만 출력:
{{
  "topic": "{topic}",
  "intro": "오늘 상황 설명",
  "sentences": [
    {{"english":"영어","pronunciation":"한글 발음","korean":"뜻","tip":"뉘앙스/사용법"}}
  ],
  "pattern": {{
    "form":"패턴",
    "pronunciation":"한글 발음",
    "meaning":"뜻",
    "examples":[
      {{"english":"예문","pronunciation":"한글 발음","korean":"뜻"}},
      {{"english":"예문","pronunciation":"한글 발음","korean":"뜻"}}
    ]
  }},
  "words":[
    {{"word":"단어/표현","pronunciation":"한글 발음","meaning":"뜻"}}
  ],
  "dialogue":[
    {{"speaker":"Staff 또는 You","english":"영어","pronunciation":"한글 발음","korean":"뜻"}}
  ],
  "retrieval":[
    {{"english":"정답 영어","pronunciation":"한글 발음","korean":"한국어 문제","tip":"포인트"}}
  ],
  "alternatives":[
    {{"english":"다른 자연스러운 표현","pronunciation":"한글 발음","korean":"뜻","note":"원래 표현과의 뉘앙스 차이"}}
  ]
}}
"""
    client = genai.Client(api_key=key)
    last = None
    for attempt in range(2):
        try:
            r = client.models.generate_content(model=MODEL, contents=prompt)
            if not r.text:
                raise RuntimeError("Gemini가 빈 응답을 반환했습니다.")
            return validate(parse_json(r.text))
        except ValueError as e:
            last = e
            if attempt == 0:
                prompt += f"\n이전 결과가 품질검사를 통과하지 못했다: {e}\n전체 JSON을 다시 생성하라."
            else:
                raise
    raise last or RuntimeError("생성 실패")

def archive(final):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    date = final["date"]
    (HISTORY_DIR / f"{date}.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    items = [x for x in read_history_index() if x.get("date") != date]
    items.append({"date": date, "topic": final["topic"]})
    items.sort(key=lambda x: x["date"])
    HISTORY_INDEX.write_text(
        json.dumps({"items": items}, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    now = datetime.now(KST)
    topic = choose_topic()
    lesson = generate_lesson(topic)
    lesson["review_items"] = build_review_items(now)
    final = {"date": now.strftime("%Y-%m-%d"), "updated_at": now.strftime("%H:%M KST"), **lesson}
    OUTPUT.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    archive(final)
    print(f"Updated: {final['topic']}")
    print(f"Review items: {len(final['review_items'])}")

if __name__ == "__main__":
    main()
