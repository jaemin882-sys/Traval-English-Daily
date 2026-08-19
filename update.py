import json, os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from google import genai

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'lesson.json'
HIST=ROOT/'history'
INDEX=HIST/'index.json'
KST=ZoneInfo('Asia/Seoul')
MODEL=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
TOPICS=['공항 체크인','입국심사','수하물 찾기','호텔 체크인','호텔 문제 요청','식당 주문','카페 주문','택시 타기','길 묻기','쇼핑','가격 묻기','렌터카','기차역','관광지 매표소','사진 부탁하기','약국','응급상황','분실물 문의','공항 출국','호텔 체크아웃']

def history():
    if not INDEX.exists(): return []
    try: return json.loads(INDEX.read_text(encoding='utf-8')).get('items',[])
    except: return []

def topic():
    used=[x.get('topic') for x in history()[-20:]]
    for t in TOPICS:
        if t not in used: return t
    return TOPICS[len(history())%len(TOPICS)]

def parse(text):
    s=text.find('{'); e=text.rfind('}')
    return json.loads(text[s:e+1])

def make_lesson(t):
    key=os.getenv('GEMINI_API_KEY')
    if not key: raise RuntimeError('GEMINI_API_KEY 없음')
    prompt=f'''여행 영어를 처음 공부하는 한국인을 위한 10분 학습 콘텐츠를 만들어라.
오늘 상황: {t}
실제 여행에서 바로 쓸 수 있는 쉬운 표현만 사용한다.
핵심 문장 5개, 단어 5개, 짧은 대화 4~6줄, 객관식 퀴즈 3개를 만든다.
영어와 자연스러운 한국어 뜻을 함께 제공한다.
마크다운 없이 아래 JSON만 출력한다.
{{
"topic":"{t}",
"intro":"오늘 상황 설명 1~2문장",
"sentences":[{{"english":"문장","korean":"뜻","tip":"짧은 사용 팁"}}],
"words":[{{"word":"단어","meaning":"뜻"}}],
"dialogue":[{{"speaker":"Staff","english":"문장","korean":"뜻"}}],
"quiz":[{{"question":"질문","options":["보기1","보기2","보기3"],"answer_index":0,"explanation":"짧은 설명"}}]
}}'''
    c=genai.Client(api_key=key)
    r=c.models.generate_content(model=MODEL,contents=prompt)
    d=parse(r.text)
    if len(d.get('sentences',[]))!=5 or len(d.get('words',[]))!=5 or len(d.get('quiz',[]))!=3:
        raise ValueError('생성 형식 오류')
    return d

def archive(d):
    HIST.mkdir(exist_ok=True)
    date=d['date']
    (HIST/f'{date}.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    items=[x for x in history() if x.get('date')!=date]
    items.append({'date':date,'topic':d['topic']})
    INDEX.write_text(json.dumps({'items':sorted(items,key=lambda x:x['date'])},ensure_ascii=False,indent=2),encoding='utf-8')

now=datetime.now(KST)
lesson=make_lesson(topic())
final={'date':now.strftime('%Y-%m-%d'),'updated_at':now.strftime('%H:%M KST'),**lesson}
OUT.write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
archive(final)
print('updated',final['topic'])
