# -*- coding: utf-8 -*-
"""고객 본문 톤 린터 — 외래어 hard-ban + 날것 계산표현 + 전문용어 밀도(H1.5 2026-06-16).

고객 PDF 본문(해석 산문)만 대상. 용어풀이 부록·명식표/근거표(차트)·내부 evidence/test/
handoff/code/log 는 비대상(호출부에서 본문 텍스트만 넘긴다).
- loanword_lint: 외래어 hard-ban(고객 본문 0건). compose 폴백 + verify gate.
- raw_calc_lint: 표제형 계산표현·원시 카운트(오행 분포·십성축·신강약·'목 2, 화 2…'). 자연어 풀이는 미매칭.
- term_hits: 명리 전문용어 밀도(보고만 — 첫 1회 자연어 풀이+괄호 허용 정책).
매칭은 (?<![가-힣]) 룩비하인드로 앞 글자가 한글이면 제외 → 접미사 '-다운'(남자다운)·합성어 오탐 차단.
조사(팀이/팀과)는 허용(트레일 룩어헤드 없음).
"""

from __future__ import annotations

import re

# 외래어 → 대체어(첫 번째가 기본 대체어). 드라이브 ≠ 드라이버 별도.
LOANWORDS: dict[str, list[str]] = {
    "포지션": ["역할", "맡을 자리", "서야 할 자리", "자리"],
    "리스크": ["위험", "부담", "조심할 부분", "손실 가능성"],
    "시스템": ["체계", "틀", "운영 구조", "흐름"],
    "드라이브": ["추진력", "밀고 나가는 힘"],
    "드라이버": ["주도하는 사람", "앞에서 끄는 사람", "방향을 잡는 사람", "밀고 나가는 사람"],
    "브레이크": ["제동", "속도 조절", "멈추는 힘"],
    "컨디션": ["몸 상태", "기력", "몸의 흐름"],
    "타입": ["성향", "기질", "부류"],
    "패턴": ["반복되는 흐름", "되풀이되는 모습", "버릇"],
    "콘텐츠": ["글", "말", "자료", "풀이", "작업물"],
    "파트너": ["동업자", "함께하는 사람", "곁의 사람"],
    "팀": ["세 사람", "이 조합", "함께 일하는 판"],
    "프로젝트": ["일", "작업", "판"],
    "프로세스": ["과정", "절차", "흐름"],
    "체크": ["확인", "점검"],
    "플랜": ["계획"],
    "데이터": ["자료", "근거", "수치"],
    "케이스": ["경우", "사례"],
    "스타일": ["방식", "말투", "느낌"],
    "밸런스": ["균형"],
    "타이밍": ["때", "시점", "흐름"],
    "프레임": ["틀", "관점"],
    "포인트": ["핵심", "짚을 부분"],
    "이슈": ["문제", "걸리는 부분", "남은 부분"],
    "모드": ["방식"],
    "피드백": ["의견", "되돌아온 말"],
    "인사이트": ["통찰", "짚이는 점"],
    "에너지": ["기운", "힘"],
    "아이디어": ["생각", "구상", "착안"],
    "매뉴얼": ["정해진 방식", "지침", "절차"],
    "다운": ["무너짐", "가라앉음", "떨어짐"],
    "챕터": ["장", "대목"],
    "카테고리": ["갈래", "분류"],
    "키워드": ["핵심어", "중심어"],
    "베이스": ["바탕"],
    "밸류": ["가치"],
    "솔루션": ["해결책", "방안"],
    "루틴": ["습관", "반복 흐름"],
    "스케줄": ["일정"],
    "플로우": ["흐름"],
    "세팅": ["설정", "자리 잡음"],
    "트리거": ["계기", "촉발점"],
    "디테일": ["세부", "자세한 부분"],
}
# 외래어 뒤에 올 수 있는 조사/어미 — 긴 꼬리 먼저(이라는>이라>이, 에서/에게>에, 이나>나).
# loanword_lint(검출)와 normalize_loanwords(순화)가 같은 집합을 쓰도록 단일 상수로 공유.
# → '팀이/타이밍이다/포지션에서/팀들끼리'는 처리, '팀장·메인팀·운영팀'(합성어)·'남자다운'(접미)은 미처리.
_TAIL_ALT = (
    r"입니다|이라는|이에요|이다|이고|이며|이라|이나|에서|에게|까지|부터|보다|마다|같은|적인|예요|으로|"
    r"이|가|은|는|을|를|과|와|로|에|도|만|의|나|들|쯤"
)
# 검출: 앞 한글 금지 룩비하인드 + 뒤(문장끝|비한글|조사/어미) 룩어헤드
_LOAN_RX = re.compile(
    r"(?<![가-힣])(" + "|".join(sorted(LOANWORDS, key=len, reverse=True)) + r")"
    r"(?=$|[^가-힣]|" + _TAIL_ALT + r")"
)


def loanword_lint(text: str) -> list[dict]:
    """외래어 hard-ban 위반 목록(빈 리스트면 통과)."""
    out: list[dict] = []
    for m in _LOAN_RX.finditer(text or ""):
        w = m.group(1)
        out.append({"type": "loanword", "match": w, "alt": LOANWORDS[w][0]})
    return out


def is_loanword_clean(text: str) -> bool:
    return not loanword_lint(text)


# 순화: loanword_lint 와 동일한 _TAIL_ALT 사용 → 검출 범위 = 순화 범위(폴백률↓).
# 구조: 외래어 뒤에 (조사/어미) 가 있으면 함께 잡아 보정, 아니면 (비한글|끝)일 때만 치환.
# → '팀들끼리'(꼬리 들 매칭, 끼리 보존)는 순화, '팀장'(꼬리도 경계도 아님)은 미치환.
_NORM_RX = re.compile(
    r"(?<![가-힣])(" + "|".join(sorted(LOANWORDS, key=len, reverse=True)) + r")"
    r"(?:(" + _TAIL_ALT + r")|(?![가-힣]))"
)

# '팀들' 특수: '팀'(=세 사람)은 이미 복수 뉘앙스라 '세 사람들'은 어색 → '세 사람' + 조사.
# 끼리 등 비조사가 뒤따라도 '팀들'을 통째 잡아 처리(트레일링 경계 없음). '운영팀들'은 룩비하인드로 제외.
_TEAM_PLURAL_RX = re.compile(r"(?<![가-힣])팀들(" + _TAIL_ALT + r")?")


def _has_batchim(word: str) -> bool | None:
    w = word.rstrip()
    if not w or not ("가" <= w[-1] <= "힣"):
        return None
    return (ord(w[-1]) - 0xAC00) % 28 != 0


def _fix_josa(repl: str, tail: str) -> str:
    """대체어 받침에 맞춰 조사/어미 형태 선택. 받침 무관형(입니다·같은·적인)은 그대로."""
    b = _has_batchim(repl)
    if b is None:
        return tail
    if tail in ("이", "가"):
        return "이" if b else "가"
    if tail in ("은", "는"):
        return "은" if b else "는"
    if tail in ("을", "를"):
        return "을" if b else "를"
    if tail in ("과", "와"):
        return "과" if b else "와"
    if tail in ("으로", "로"):  # 받침 없거나 ㄹ받침이면 '로', 그 외 받침이면 '으로'
        jong = (ord(repl.rstrip()[-1]) - 0xAC00) % 28
        return "로" if (not b or jong == 8) else "으로"
    if tail == "이다":
        return "이다" if b else "다"
    if tail in ("이에요", "예요"):
        return "이에요" if b else "예요"
    if tail == "이고":
        return "이고" if b else "고"
    if tail == "이며":
        return "이며" if b else "며"
    if tail == "이라":
        return "이라" if b else "라"
    if tail == "이라는":
        return "이라는" if b else "라는"
    if tail in ("이나", "나"):
        return "이나" if b else "나"
    return tail  # 입니다·에서·에게·까지·부터·보다·마다·같은·적인·에·도·만·의·들·쯤 등 받침 무관


def normalize_loanwords(text: str) -> str:
    """LLM 산문의 외래어를 기본 대체어로 1차 자동 순화 + 조사 보정(폴백 이전, H1.5.1).

    hard-ban 정책 유지 — 순화 후에도 남은 외래어(예: '팀장' 합성어)는 호출부 lint가 폴백.
    조사를 함께 잡아 '아이디어가→생각이'처럼 받침에 맞게 보정(문법 오류 방지).
    """

    text = text or ""

    # '팀들' 먼저 처리(→ '세 사람' + 조사) — 일반 순화의 '세 사람들' 어색함 방지.
    def team_repl(m: re.Match) -> str:
        repl = LOANWORDS["팀"][0]  # 세 사람
        tail = m.group(1)
        return repl + _fix_josa(repl, tail) if tail else repl

    text = _TEAM_PLURAL_RX.sub(team_repl, text)

    def repl(m: re.Match) -> str:
        word = LOANWORDS[m.group(1)][0]
        josa = m.group(2)
        return word + _fix_josa(word, josa) if josa else word

    return _NORM_RX.sub(repl, text)


# 날것 계산표현. 자연어 풀이("다섯 기운을 보면")는 미매칭.
# head = 표제형(오행 분포·십성축·신강약…) — 차트/근거표에 없어 verify 게이트 안전.
# count = 원시 카운트열 — 명식표 차트에도 나올 수 있어 게이트 대신 보고만.
_RAW_CALC_HEAD = [
    re.compile(r"오행\s*(?:의)?\s*분포"),  # '오행 분포'·'오행의 분포'(H1.5.2)
    re.compile(r"오행으?로?\s*세어\s*보면"),
    re.compile(r"오행을\s*세어\s*보면"),
    re.compile(r"오행(?:을|으로)?\s*보면"),
    re.compile(r"오행\s*중(?:에서|에|을|의)?"),
    re.compile(r"십성축"),
    re.compile(r"신강약"),
]
_RAW_CALC_COUNT = [
    re.compile(r"(?:목|화|토|금|수)\s*\d+(?:\s*[,·]\s*(?:목|화|토|금|수)\s*\d+)+"),
    re.compile(r"(?:목|화|토|금|수)(?:이|가)\s*(?:\d+|하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉)"),
    re.compile(r"(?:목|화|토|금|수)가\s*다섯(?:\s*자리|입니다)?"),
]


def raw_calc_headwords(text: str) -> list[dict]:
    """표제형 계산표현(게이트 대상) — 차트에 없는 날것 용어."""
    out: list[dict] = []
    for rx in _RAW_CALC_HEAD:
        for m in rx.finditer(text or ""):
            out.append({"type": "raw_calc_head", "match": m.group(0)})
    return out


def raw_calc_lint(text: str) -> list[dict]:
    """날것 계산표현 전체(표제형 + 카운트열). compose 가드·보고용."""
    out: list[dict] = raw_calc_headwords(text)
    for rx in _RAW_CALC_COUNT:
        for m in rx.finditer(text or ""):
            out.append({"type": "raw_calc_count", "match": m.group(0)})
    return out


# 명리 전문용어(밀도 보고용 — 게이트 아님). 첫 1회 풀이+괄호 허용 정책.
_TERMS = [
    "신약",
    "신강",
    "격국",
    "용신",
    "건록격",
    "편관격",
    "정관격",
    "식신생재",
    "재고",
    "지장간",
    "십이운성",
    "납음",
    "공망",
    "도화",
    "역마",
    "괴강",
    "백호",
]
_TERM_RX = re.compile(r"(?<![가-힣])(" + "|".join(_TERMS) + r")")


def term_hits(text: str) -> list[dict]:
    """전문용어 출현(보고용)."""
    return [{"type": "term", "match": m.group(1)} for m in _TERM_RX.finditer(text or "")]


# ───────────────── H1.5.3: 이름 호칭 정책 ─────────────────
# 고객 본문 산문은 짧은 호칭("태수 씨")을 쓰고, 전체 이름("김태수")은 첫 소개 1회만 허용.
# 표지/명식표/근거표/가운뎃점 나열은 예외(verify가 구역으로 분리). 복성 set는 rules와 동일(로컬 사본).
_DOUBLE_SURNAMES = {"남궁", "황보", "제갈", "선우", "독고", "사공", "서문", "동방", "어금", "망절"}
# 이름 뒤 조사(호칭화 검출·순화 공유). 긴 꼬리 먼저.
_NAME_TAIL = r"에게|에서|한테|으로|은|는|이|가|을|를|의|과|와|로|에|도|랑|께"


def given_name(full: str) -> str:
    """성 제외 이름 — '김태수'→'태수', 복성 4자→뒤 2자. 2자 이하/비정형은 그대로."""
    n = (full or "").strip()
    if n.endswith(("님", "씨")):
        n = n[:-1].strip()
    if len(n) == 4 and n[:2] in _DOUBLE_SURNAMES:
        return n[2:]
    if len(n) == 3:
        return n[1:]
    return n


def honor(full: str) -> str:
    """본문 일반 호칭 — '태수 씨'."""
    return f"{given_name(full)} 씨"


def intro(full: str) -> str:
    """첫 소개 호칭 — '김태수 씨'(성 포함, 사람당 1회)."""
    return f"{full} 씨"


def pair_label(a: str, b: str) -> str:
    """쌍 제목 — '태수와 태성'(받침 인식 와/과)."""
    ga, gb = given_name(a), given_name(b)
    gwa = "과" if _has_batchim(ga) else "와"
    return f"{ga}{gwa} {gb}"


def _josa_after_ssi(josa: str) -> str:
    """'씨'(받침 없음) 뒤 조사 보정 — 받침형은 무받침형으로."""
    return {
        "은": "는",
        "는": "는",
        "이": "가",
        "가": "가",
        "을": "를",
        "를": "를",
        "과": "와",
        "와": "와",
        "으로": "로",
        "로": "로",
    }.get(josa, josa)


def name_policy_lint(text: str, full_names: list[str]) -> list[dict]:
    """고객 본문에서 전체 이름 오용 검출(빈 리스트면 통과).

    허용: 사람당 첫 'FULL 씨' 1회, 'A · B · C' 가운뎃점 나열(표지). 그 외 FULL 출현은 위반.
    검출 종류: 조사·부호(,:)·명사형(FULL 명사)·단독·붙은씨(태수씨).
    """
    text = text or ""
    out: list[dict] = []
    for full in full_names:
        if not full:
            continue
        ssi_left = 1  # 첫 소개 1회 허용
        rx = re.compile(re.escape(full) + r"(\s*씨)?(" + _NAME_TAIL + r")?")
        for m in rx.finditer(text):
            i, j = m.start(), m.end()
            nb = text[max(0, i - 3) : i]
            na = text[j : j + 3]
            # 가운뎃점 나열(표지) → 허용
            if re.search(r"·\s*$", nb) or re.match(r"\s*·", na):
                continue
            ssi, josa = m.group(1), m.group(2)
            if ssi:  # 'FULL 씨'
                if ssi_left > 0:
                    ssi_left -= 1
                    continue
                out.append({"type": "name_policy", "match": m.group(0), "kind": "중복소개"})
                continue
            if josa:
                out.append({"type": "name_policy", "match": m.group(0), "kind": "조사"})
                continue
            if re.match(r"\s*[,:：]", na):
                out.append({"type": "name_policy", "match": full, "kind": "부호"})
                continue
            if re.match(r"\s+[가-힣]", na):
                out.append({"type": "name_policy", "match": full + na, "kind": "명사"})
                continue
            out.append({"type": "name_policy", "match": full, "kind": "단독"})
    # 붙은 씨(태수씨) — given+씨 직결, 앞이 한글이면 전체이름 일부라 제외
    for full in full_names:
        g = given_name(full)
        if not g:
            continue
        for m in re.finditer(r"(?<![가-힣])" + re.escape(g) + r"씨", text):
            out.append({"type": "name_policy", "match": m.group(0), "kind": "붙은씨"})
    return out


def _normalize_text(text: str, full_names: list[str], ssi_seen: set) -> str:
    """한 텍스트의 전체 이름을 호칭으로 순화. ssi_seen(이미 첫 소개한 이름 집합)을 공유해
    PDF 전체 기준 '첫 FULL 씨 1회'를 보장한다(단일 텍스트면 빈 set 전달 → 텍스트당 1회)."""
    text = text or ""
    # 쌍 먼저: 'FULL_a 와/과 FULL_b' → 'given_a와/과 given_b'(예 김태수와 김태성 → 태수와 태성).
    for a in full_names:
        for b in full_names:
            if a and b and a != b:
                text = re.sub(
                    re.escape(a) + r"\s*[와과]\s*" + re.escape(b),
                    pair_label(a, b),
                    text,
                )
    for full in full_names:
        if not full:
            continue
        g = given_name(full)
        # 붙은 씨 띄우기: 태수씨는 → 태수 씨는
        text = re.sub(r"(?<![가-힣])" + re.escape(g) + r"씨", g + " 씨", text)
        src = text
        rx = re.compile(re.escape(full) + r"(\s*씨)?(" + _NAME_TAIL + r")?")

        def repl(m: re.Match, _full=full, _g=g) -> str:
            i, j = m.start(), m.end()
            nb = src[max(0, i - 3) : i]
            na = src[j : j + 3]
            if re.search(r"·\s*$", nb) or re.match(r"\s*·", na):
                return m.group(0)  # 가운뎃점 나열 보존
            ssi, josa = m.group(1), m.group(2)
            if ssi:  # 'FULL 씨'
                if _full not in ssi_seen:
                    ssi_seen.add(_full)
                    return m.group(0)  # 첫 소개 1회 보존(PDF-wide)
                return f"{_g} 씨" + (josa or "")  # 2회째 → 호칭
            if josa:
                return f"{_g} 씨" + _josa_after_ssi(josa)
            return f"{_g} 씨"  # 부호·명사·단독

        text = rx.sub(repl, src)
    return text


def normalize_names(text: str, full_names: list[str]) -> str:
    """단일 텍스트(섹션 단위) 전체이름 → 호칭 순화. 첫 'FULL 씨'·가운뎃점 나열은 보존."""
    return _normalize_text(text, full_names, set())


def normalize_names_pdfwide(texts: list[str], full_names: list[str]) -> list[str]:
    """여러 섹션 텍스트를 순서대로 순화하되 '첫 FULL 씨'를 PDF 전체에서 사람당 1회만 보존(H1.5.3.1).

    섹션 단위 normalize_names 는 텍스트마다 첫 소개를 남겨 PDF-wide 중복소개가 생긴다 →
    이 함수가 ssi_seen 을 공유해 2회째부터 호칭(태수 씨)으로 강등. render 직전 최종 보증용.
    """
    ssi_seen: set = set()
    return [_normalize_text(t, full_names, ssi_seen) for t in texts]


# ───────────────── H1.5.3: 일간(day master) role 오류 ─────────────────
# LLM이 명식의 일간(중심 글자)을 다른 천간으로 오서술하는 것을 차단. 계산값(임수)만 정답.
# '계사 월운/계묘 대운/지장간 계/운에서 계가'는 일간 프레임 밖 → 허용.
_GAN_TERM = {
    "갑": "갑목",
    "을": "을목",
    "병": "병화",
    "정": "정화",
    "무": "무토",
    "기": "기토",
    "경": "경금",
    "신": "신금",
    "임": "임수",
    "계": "계수",
}
_CHEONGAN = "갑을병정무기경신임계"
_DM_ALT = "|".join(_GAN_TERM.values())  # 갑목|을목|...|계수


def gan_to_term(gan_ko: str) -> str:
    """천간 한글 1자 → 전체 일간명('임'→'임수')."""
    return _GAN_TERM.get(gan_ko, gan_ko)


def identity_role_lint(
    text: str,
    expected_gans,
    expected_terms,
    subject_specs=(),
) -> list[dict]:
    """일간 role 오서술 검출. expected(천간/일간명) 밖이면 위반.

    expected_gans/expected_terms: 허용 천간·일간명 집합(개인 단일, 궁합 합집합).
    subject_specs: [(aliases, expected_term)] — 주체별 정확 판정(D 프레임, 합집합 우회 방지).
    """
    text = text or ""
    eg, et = set(expected_gans), set(expected_terms)
    out: list[dict] = []

    def _add(m):
        out.append({"type": "identity_role", "match": m.group(0), "term": m.group(1)})

    # A: 일간/일주/중심 글자 + 일간명
    for m in re.finditer(
        r"(?:일간|일주|중심\s*글자)\s*(?:은|는|이|가|:)?\s*(" + _DM_ALT + r")", text
    ):
        if m.group(1) not in et:
            _add(m)
    # A': 키워드 + 단독 천간. 구분자(서술격 또는 공백)를 '필수'로 둬 목적격 조사 오인 방지
    # ('일간을'의 '을'을 천간 乙로 잘못 잡던 오탐 차단 — 천간 집합에 '을' 포함). 뒤는 한글 아님('임수'는 A 처리).
    for m in re.finditer(
        r"(?:일간|일주|중심\s*글자)(?:\s*(?:은|는|이|가|:)\s*|\s+)(["
        + _CHEONGAN
        + r"])(?![가-힣])",
        text,
    ):
        if m.group(1) not in eg:
            out.append(
                {"type": "identity_role", "match": m.group(0), "term": _GAN_TERM[m.group(1)]}
            )
    # B: 일간명 + 일간/일주
    for m in re.finditer(r"(" + _DM_ALT + r")\s*(?:인\s*)?(?:일간|일주)", text):
        if m.group(1) not in et:
            _add(m)
    # C/D: 주체별
    all_fulls = [a for aliases, _ in subject_specs for a in aliases if len(a) >= 3]
    for aliases, exp_term in subject_specs:
        alt = "|".join(re.escape(a) for a in aliases if a)
        if not alt:
            continue
        others = [f for f in all_fulls if f not in aliases]
        # C: 주체 + 서술격 + 일간명
        for m in re.finditer(
            r"(?:" + alt + r"|자기\s*자신|나\s*자신|본인|자신)"
            r"\s*(?:은|는|이|가|님은|씨는|님이|씨가)\s*(" + _DM_ALT + r")"
            r"(?!\s*(?:대운|세운|월운|운|해|기운))",
            text,
        ):
            if m.group(1) != exp_term:
                _add(m)
        # D: 주체 근접 일간 프레임 + 일간명(합집합 우회 방지 — 주체별 expected)
        for m in re.finditer(
            r"(?:"
            + alt
            + r")[^\n]{0,20}?(?:일간|일주|중심\s*글자|자기\s*자신)[^\n]{0,12}?("
            + _DM_ALT
            + r")",
            text,
        ):
            if m.group(1) == exp_term:
                continue
            if any(o in m.group(0) for o in others):  # 다른 주체 끼면 귀속 모호 → 보류
                continue
            _add(m)
    # 중복 제거(같은 match·term)
    seen, uniq = set(), []
    for h in out:
        k = (h["match"], h["term"])
        if k not in seen:
            seen.add(k)
            uniq.append(h)
    return uniq


# ───────────────── H1.5.3.2: 신강약(strength) group/role 오류 ─────────────────
# 사람별 신강약은 결정론 사실. LLM이 섞인 값(신약2·신강1)을 '세 사람 모두 신약'으로 일반화하거나
# 특정 사람의 신강약을 뒤집어 쓰는 것을 차단. '안정 쪽' 단독은 미검출(신약/강 리터럴 필수).
# group_all: 전체-3인 표지(세 사람/세 명/세 분/셋/전원/이 조합)일 때만 — bare '모두 신약'은 2인 한정이라 미검출.
_GROUP_ALL_RX = re.compile(
    r"(?:세\s*사람|세\s*명|세\s*분|셋|전원|이\s*조합)(?:은|는|이|가|도)?\s*(?:모두|다)?\s*신(약|강)"
)


def singang_role_lint(text: str, specs: list[dict]) -> list[dict]:
    """신강약 group/role 오류(빈 리스트면 통과).

    specs = [{"full","given","honor","singang"}]. singang ∈ {신약,신강,중화}.
    - group_all: 전체-3인 표지 + 신약/강 인접인데, 그 값이 전원 공유가 아니면 위반.
    - subject_mismatch: 주체 alias + (의 명식/사주/힘의 강약/신강약)? + 서술격 + 신약/강 이 그 사람 값과 다르면 위반.
    """
    text = text or ""
    out: list[dict] = []
    counts: dict[str, int] = {}
    for s in specs:
        sg = s.get("singang", "")
        if sg:
            counts[sg] = counts.get(sg, 0) + 1
    # A. group_all — 전원 공유가 아니면 위반(섞인 값을 '모두'로 일반화)
    for m in _GROUP_ALL_RX.finditer(text):
        val = "신" + m.group(1)
        if not (counts.get(val, 0) == len(specs) and len(specs) > 0):
            out.append(
                {
                    "type": "singang_role",
                    "kind": "group_all",
                    "match": m.group(0),
                    "expected": dict(counts),
                }
            )
    # B. subject_mismatch — 주체별 expected 와 다른 신강약
    for s in specs:
        aliases = [a for a in (s.get("full"), s.get("honor"), s.get("given")) if a]
        if not aliases:
            continue
        alt = "|".join(re.escape(a) for a in aliases)
        exp = s.get("singang", "")
        rx = re.compile(
            r"(?:" + alt + r")(?:\s*의)?\s*(?:명식|사주|힘의\s*강약|신강약)?"
            r"\s*(?:은|는|이|가|님은|씨는|님이|씨가)\s*신(약|강)"
        )
        for m in rx.finditer(text):
            got = "신" + m.group(1)
            if got != exp:
                out.append(
                    {
                        "type": "singang_role",
                        "kind": "subject_mismatch",
                        "subject": s.get("honor") or s.get("full"),
                        "match": m.group(0),
                        "expected": exp,
                        "got": got,
                    }
                )
    return out


# ───────────────── Phase 1: placeholder/masking residue ─────────────────
# 고객 문서에 남으면 안 되는 익명 placeholder/수신자 흐림 표현. 반환값은 rule/count
# 중심이며 고객 본문 원문을 넣지 않는다. "두 분" 자체는 관계/궁합 문서의 정상 표현일
# 수 있어 금지하지 않고, "두 분께" 같은 수신자 흐림 후보만 candidate 로 보고한다.
_PLACEHOLDER_RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("ordinal_person_placeholder", re.compile(r"첫\s*번째\s*분|두\s*번째\s*분|세\s*번째\s*분"), "hard"),
    ("generic_customer_address", re.compile(r"고객님|당신"), "hard"),
    ("operator_intake_label", re.compile(r"신청자|상담\s*대상"), "hard"),
    ("counterpart_placeholder", re.compile(r"상대\s*분"), "hard"),
    ("ambiguous_pair_recipient", re.compile(r"두\s*분께"), "candidate"),
]


def placeholder_residue_lint(text: str) -> list[dict]:
    """Placeholder/masking residue hits, aggregated without source text."""

    counts: dict[tuple[str, str], int] = {}
    for rule, rx, severity in _PLACEHOLDER_RULES:
        matches = rx.findall(text or "")
        if matches:
            key = (rule, severity)
            counts[key] = counts.get(key, 0) + len(matches)
    return [
        {
            "type": "placeholder_residue",
            "rule": rule,
            "severity": severity,
            "count": count,
        }
        for (rule, severity), count in sorted(counts.items())
    ]


def placeholder_residue_clean(text: str) -> bool:
    return not any(h.get("severity") == "hard" for h in placeholder_residue_lint(text))


# ───────────────── Integrated full: receiver perspective / honorific ─────────────────
def role_perspective_specs(full_names: list[str], receiver: str | None = None) -> list[dict]:
    """Build PII-bearing specs for runtime linting; lint hits never echo aliases."""

    receiver = (receiver or "").strip()
    specs: list[dict] = []
    for full in full_names:
        if not full:
            continue
        given = given_name(full)
        is_receiver = bool(receiver and full == receiver)
        expected = "님" if is_receiver else "씨"
        aliases = sorted({full, given, f"{full} 씨", f"{given} 씨", f"{full} 님", f"{given} 님"})
        specs.append(
            {
                "role": "receiver" if is_receiver else "subject",
                "aliases": aliases,
                "expected_honorific": expected,
            }
        )
    return specs


def _honorific_counts(text: str, spec: dict) -> dict[str, int]:
    counts = {"님": 0, "씨": 0}
    bases = set()
    for alias in spec.get("aliases") or []:
        alias = str(alias).strip()
        for suffix in ("님", "씨"):
            if alias.endswith(f" {suffix}"):
                bases.add(alias[: -len(f" {suffix}")].strip())
            elif alias.endswith(suffix):
                bases.add(alias[: -len(suffix)].strip())
            elif alias:
                bases.add(alias)
    for base in bases:
        for suffix in ("님", "씨"):
            rx = re.compile(
                rf"(?<![A-Za-z0-9가-힣]){re.escape(base)}\s*{suffix}"
                rf"(?=(?:\s|은|는|이|가|을|를|에게|한테|께|과|와|도|만|의|라|이라|,|\.|$))"
            )
            counts[suffix] += len(rx.findall(text or ""))
    return counts


def honorific_consistency_lint(text: str, specs: list[dict] | None) -> list[dict]:
    """Detect mixed/unexpected 님/씨 usage per subject without returning raw names."""

    out: list[dict] = []
    for spec in specs or []:
        counts = _honorific_counts(text or "", spec)
        expected = spec.get("expected_honorific")
        role = spec.get("role", "subject")
        if counts["님"] and counts["씨"]:
            out.append(
                {
                    "type": "honorific_consistency",
                    "rule": "mixed_honorific",
                    "role": role,
                    "count": counts["님"] + counts["씨"],
                }
            )
        for actual in ("님", "씨"):
            if expected and actual != expected and counts[actual]:
                out.append(
                    {
                        "type": "honorific_consistency",
                        "rule": "unexpected_honorific",
                        "role": role,
                        "expected": expected,
                        "actual": actual,
                        "count": counts[actual],
                    }
                )
    return out


def honorific_consistent(text: str, specs: list[dict] | None) -> bool:
    return not honorific_consistency_lint(text, specs)


def role_perspective_lint(text: str, specs: list[dict] | None) -> list[dict]:
    """Detect receiver described in third-person honorific form in integrated PDFs."""

    out: list[dict] = []
    for spec in specs or []:
        if spec.get("role") != "receiver":
            continue
        counts = _honorific_counts(text or "", spec)
        if counts["씨"]:
            out.append(
                {
                    "type": "role_perspective",
                    "rule": "receiver_third_person_honorific",
                    "role": "receiver",
                    "expected": spec.get("expected_honorific") or "님",
                    "actual": "씨",
                    "count": counts["씨"],
                }
            )
    return out


def role_perspective_clean(text: str, specs: list[dict] | None) -> bool:
    return not role_perspective_lint(text, specs)
