# -*- coding: utf-8 -*-
"""Native integrated_full product orchestration.

Personal reading sections and relationship/gunghap sections are assembled into
one report before rendering, so no hand-edited HTML/PDF baseline is needed.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import typer

from . import config as cfg
from . import gunghap
from . import modules as integrated_modules
from .calc import engine
from .content import builder, client_tone_lint, llm_usage, postprocess
from .refdate import default_ref_date_iso
from .render import pdf as render_pdf
from .render import verify as render_verify

PRODUCT = "integrated_full"
MODULE_SCHEMA_VERSION = integrated_modules.MODULE_SCHEMA_VERSION
module_schema_version = MODULE_SCHEMA_VERSION
_LAYOUT_VARIANTS = (
    ("14.5pt", "1.8"),
    ("13.8pt", "1.68"),
)
# 반복어 선치환 단일 소스 이전(2026-07-04): content/postprocess.style_safe_text 가 원본.
# 개인 경로(builder)도 같은 치환을 쓰므로 경로별 드리프트 방지를 위해 여기서는 참조만.
_STYLE_REPLACEMENTS = postprocess._STYLE_REPLACEMENTS
_QUALITY_PATTERN_REPLACEMENTS = postprocess._QUALITY_PATTERN_REPLACEMENTS
_LOW_DENSITY_ONLY_CLEAN_FLAGS = (
    "text_layer_ok",
    "fonts_embedded",
    "tagged",
    "markdown_clean",
    "daewoon_consistent",
    "quality_clean",
    "temporal_clean",
    "no_orphan",
    "loanword_clean",
    "raw_calc_head_clean",
    "customer_meta_clean",
    "placeholder_residue_clean",
    "style_clean",
    "role_perspective_clean",
    "honorific_consistency_clean",
    "name_policy_clean",
    "identity_role_clean",
    "singang_role_clean",
)
_SPARSE_SECTION_MIN_CHARS = 700
_SPARSE_TAIL_SECTION_IDS = {"closing", "appendix_terms", "colophon"}
_NO_LLM_DEPTH_SECTION_ID = "integrated_full_depth"
_NO_LLM_DEPTH_SECTION_TITLE = "통합 판단의 실제 적용"
_NO_LLM_DEPTH_PARAGRAPHS = (
    "통합 판단은 개인의 생활 방식과 관계 안에서 생기는 반응을 따로 떼어 보지 않는다. 한 사람의 선택 습관, 책임을 맡는 방식, 돈과 시간을 쓰는 기준, 가까운 사람과 말이 오가는 속도를 함께 놓고 보아야 실제 생활에서 쓸 수 있는 결론이 나온다. 개인 장에서는 스스로의 기본 호흡을 확인하고, 관계 장에서는 그 호흡이 다른 사람의 방식과 만날 때 어디서 힘이 붙고 어디서 조율이 필요한지를 본다. 그래서 이 통합 장은 앞의 개인 해설과 뒤의 관계 해설을 생활 기준으로 이어 주는 역할을 한다.",
    "먼저 확인할 부분은 결정의 순서다. 마음이 급할 때 바로 답을 내리기보다 기록, 돈, 일정, 약속을 차례로 점검하면 관계의 부담이 줄어든다. 중요한 선택은 감정의 온도가 높을 때 확정하지 말고 하루의 생활 흐름이 안정된 시간에 다시 보는 편이 낫다. 특히 집, 일, 사람, 재물처럼 서로 맞물리는 문제는 어느 하나만 크게 보지 말고 작은 조건을 나누어 살펴야 한다. 이 방식은 결정을 늦추기 위한 것이 아니라, 나중에 뒤집을 필요가 적은 결정을 만들기 위한 절차다.",
    "관계에서는 말의 양보다 확인의 순서가 중요하다. 필요한 말을 한 번에 몰아붙이면 상대가 방어적으로 받아들일 수 있고, 반대로 너무 오래 미루면 오해가 커진다. 먼저 사실을 짧게 확인하고, 그다음 감정과 바라는 점을 나누는 방식이 좋다. 돈이나 일정처럼 책임이 따르는 주제는 말로만 남기지 말고 날짜와 역할을 적어 두면 분쟁의 여지가 작아진다. 가까운 사이라고 해도 기록은 차가운 태도가 아니라 서로의 기억을 보호하는 장치가 될 수 있다.",
    "일과 재물의 판단은 속도 조절이 핵심이다. 수입을 늘리는 선택, 지출을 줄이는 선택, 새로운 책임을 맡는 선택은 각각 다른 압박을 만든다. 한꺼번에 넓히면 외형은 커져도 실제 감당력이 따라오지 못할 수 있다. 먼저 고정 지출, 약속된 일정, 돌봄이나 가족 책임처럼 매달 반복되는 항목을 적어 보고, 그 위에 새 계획을 올리는 순서가 안정적이다. 재물은 큰 방향만 맞는다고 지켜지는 것이 아니라, 작은 누수와 반복 지출을 줄일 때 오래 남는다.",
    "집과 생활 터전에 관한 판단은 마음의 안정과 현실 조건을 함께 봐야 한다. 머물 곳을 바꾸거나 생활 반경을 조정할 때는 위치의 장점만 보지 말고 이동 시간, 관리 비용, 주변 사람과의 거리, 갑작스러운 일정 변경 가능성을 같이 살펴야 한다. 생활 터전은 단순한 배경이 아니라 몸의 피로와 마음의 여유를 매일 만드는 조건이다. 당장의 인상이 좋아도 유지 비용이 크면 시간이 지나 부담이 되고, 반대로 화려하지 않아도 반복 생활이 편하면 장기적으로 힘이 된다.",
    "가까운 관계에서 가장 조심할 점은 역할이 한쪽으로 굳어지는 것이다. 한 사람은 계속 설명하고 다른 사람은 계속 판단만 하거나, 한 사람은 계속 양보하고 다른 사람은 익숙하게 받기만 하면 균형이 흐트러진다. 그래서 부탁과 거절, 기다림과 요청, 배려와 책임을 번갈아 놓을 필요가 있다. 관계가 오래 가려면 좋은 마음만으로는 부족하고, 실제 생활에서 각자가 맡을 수 있는 몫이 분명해야 한다. 이 몫이 분명할수록 감정의 소모가 줄어든다.",
    "2026년을 기준으로 볼 때, 큰 선택은 한 번에 결론을 내리기보다 분기별로 점검하는 편이 안정적이다. 봄에는 계획을 정돈하고, 여름에는 사람과 일정의 반응을 살피며, 가을에는 돈과 책임의 무게를 다시 계산하고, 겨울에는 다음 해로 넘길 것과 마무리할 것을 구분하는 식이 좋다. 이 구분은 운을 단정하기 위한 것이 아니라 생활의 압박을 나누기 위한 기준이다. 같은 일도 어느 시점에 다루느냐에 따라 부담과 성과가 달라진다.",
    "자미두수 관점에서는 집, 일, 사람, 재물의 연결을 함께 살필 때 실용성이 커진다. 집이 편해야 일이 오래가고, 일이 안정되어야 돈의 관리가 흔들리지 않으며, 사람과의 약속이 정돈되어야 생활의 피로가 줄어든다. 어느 한 영역이 크게 움직이면 나머지 영역에도 반응이 생기므로, 변화를 선택할 때는 최소 세 가지 영역을 같이 점검하는 것이 좋다. 이때 필요한 질문은 단순하다. 지금의 선택이 몸의 피로를 줄이는지, 돈의 누수를 줄이는지, 관계의 설명 비용을 줄이는지 확인하면 된다.",
    "명리 관점에서는 강하게 밀어붙이는 때와 물러서서 살피는 때를 구분하는 것이 중요하다. 마음이 앞설수록 말이 빨라지고 결정이 커질 수 있으므로, 중요한 대화 전에는 준비한 문장을 줄이고 핵심만 남기는 편이 낫다. 반대로 너무 오래 생각만 하면 기회를 놓칠 수 있으니, 실행할 수 있는 작은 단계를 정해 두어야 한다. 한 달 안에 확인할 일, 세 달 안에 조정할 일, 반년 안에 결론 낼 일을 나누면 과한 부담 없이 움직일 수 있다.",
    "서로 다른 사람의 생활 방식이 만날 때는 옳고 그름보다 우선순위가 다를 때가 많다. 한쪽은 안정감을 먼저 보고, 다른 한쪽은 가능성을 먼저 볼 수 있다. 한쪽은 돈의 안전을 중시하고, 다른 한쪽은 관계의 분위기를 더 크게 볼 수 있다. 이 차이를 성격 문제로만 보면 대화가 좁아진다. 각자가 무엇을 먼저 보호하려는지 확인하면 상대의 말이 공격처럼 들리는 순간이 줄어든다. 관계의 조율은 상대를 바꾸는 일이 아니라 우선순위를 번역하는 일에 가깝다.",
    "생활의 부담은 대개 큰 사건 하나보다 작은 미확인이 쌓일 때 커진다. 답장을 언제 할지, 비용을 누가 먼저 낼지, 약속을 어느 정도까지 열어 둘지 같은 사소한 문제가 반복되면 마음의 피로가 커진다. 그래서 가까운 사이일수록 작은 규칙을 미리 정해 두는 편이 좋다. 정해 둔 규칙은 상대를 묶기 위한 장치가 아니라 서로의 불안을 낮추는 기준이 된다. 같은 기준을 여러 번 확인하면 불필요한 추측이 줄고, 말의 온도도 안정된다.",
    "돈의 문제는 감정의 문제와 따로 움직이지 않는다. 여유가 줄어들면 말투가 짧아지고, 말투가 짧아지면 관계의 거리도 달라진다. 그러므로 재물 판단은 수입과 지출의 숫자만 보지 말고, 그 숫자가 생활 태도와 관계의 대화에 어떤 압박을 주는지 함께 봐야 한다. 꼭 필요한 지출, 미룰 수 있는 지출, 설명이 필요한 지출을 나누면 서로에게 요구하는 말도 구체적이 된다. 구체적인 말은 서운함을 줄이고 책임의 범위를 분명하게 만든다.",
    "일의 문제에서는 역할이 넓어질수록 회복 시간을 함께 확보해야 한다. 새로운 일을 맡거나 책임이 커질 때, 겉으로는 좋은 기회처럼 보여도 몸이 따라가지 못하면 관계 안에서 예민함이 늘어난다. 일정표에는 해야 할 일만 적지 말고 쉬는 시간과 정리 시간을 같이 넣어야 한다. 쉬는 시간이 비어 있지 않으면 대화가 날카로워지고, 중요한 판단도 짧은 인상에 기대기 쉽다. 회복 시간은 게으름이 아니라 판단력을 지키는 조건이다.",
    "집과 일, 관계와 돈은 서로 다른 칸에 있어도 실제 생활에서는 한 묶음으로 움직인다. 이동 시간이 길어지면 대화 시간이 줄고, 대화 시간이 줄면 오해를 바로잡을 기회도 줄어든다. 고정비가 커지면 선택의 여유가 줄고, 여유가 줄면 작은 요청도 부담스럽게 들릴 수 있다. 그래서 어떤 선택을 볼 때는 그 선택 하나의 장점보다 그 선택이 다른 생활 항목에 남기는 부담을 같이 계산해야 한다. 좋은 선택은 멋져 보이는 선택이 아니라 오래 유지할 수 있는 선택이다.",
    "가족이나 가까운 지인과 얽힌 문제는 선의를 앞세우기보다 경계를 분명히 하는 편이 안정적이다. 도와주고 싶은 마음이 있어도 금액, 시간, 책임의 범위가 흐려지면 나중에는 좋은 마음보다 부담이 크게 남는다. 도움을 주거나 받을 때는 어디까지 가능한지, 언제 다시 확인할지, 어떤 경우에는 멈출지를 미리 말해 두어야 한다. 이런 선은 차가운 거절이 아니라 관계를 오래 보존하기 위한 약속이다. 선이 있을 때 오히려 마음을 덜 다치게 된다.",
    "관계가 좋아지는 순간에도 점검은 필요하다. 분위기가 부드러울 때 모든 문제가 해결된 것처럼 느끼기 쉽지만, 생활의 조건이 그대로라면 같은 문제가 다시 올라올 수 있다. 좋은 때에는 감사와 약속을 남기고, 어려운 때에는 원망보다 사실을 먼저 확인하는 방식이 도움이 된다. 감정이 좋은 날에는 다음 약속을 정하고, 감정이 어려운 날에는 말의 양을 줄이는 식으로 기준을 달리하면 불필요한 충돌을 줄일 수 있다.",
    "선택을 앞둔 시기에는 세 가지 질문을 남겨 두면 좋다. 이 선택이 생활을 단순하게 만드는지, 돈과 시간을 더 복잡하게 만드는지, 가까운 사람과의 설명을 줄이는지 늘리는지 확인한다. 세 질문 중 두 가지 이상이 무거워진다면 바로 확정하지 말고 조건을 줄이는 편이 낫다. 반대로 세 질문이 대체로 가벼워진다면 작은 실행부터 시작해도 된다. 작은 실행은 부담이 적고, 잘못되었을 때 되돌릴 수 있는 폭도 넓다.",
    "통합 판단은 좋은 말만 모아 놓는 방식이 아니다. 힘이 되는 부분과 조심할 부분을 같은 크기로 보아야 실제 선택에 도움이 된다. 장점만 보면 무리한 기대가 생기고, 주의점만 보면 움직임이 멈춘다. 장점은 실행의 근거로 쓰고, 주의점은 속도를 조절하는 기준으로 쓰면 된다. 이렇게 나누어 보면 한 가지 결론에 매달리지 않고 여러 선택지의 무게를 비교할 수 있다.",
    "대화를 다시 시작해야 하는 때에는 과거의 모든 일을 한 번에 꺼내기보다 지금 가장 중요한 한 가지부터 다루는 편이 낫다. 오래 묵은 서운함을 모두 말하면 듣는 쪽도 방어하게 되고, 말하는 쪽도 핵심을 잃기 쉽다. 먼저 확인할 사실, 지금 느끼는 부담, 앞으로 바라는 행동을 나누어 말하면 대화의 길이가 줄어든다. 말이 짧아져도 내용이 분명하면 관계는 더 안정적으로 움직인다. 설명이 길어질수록 상대를 설득하려는 힘이 커지므로, 중요한 말일수록 기준과 요청을 간단히 남기는 것이 좋다.",
    "혼자 결정할 일과 함께 정할 일을 구분하는 것도 중요하다. 개인의 건강, 수면, 일의 속도처럼 스스로 관리해야 할 부분은 먼저 자기 기준을 세워야 한다. 반대로 돈을 함께 쓰거나 일정을 맞추거나 생활 공간을 조정하는 문제는 상대와 확인하는 절차가 필요하다. 혼자 정할 일을 계속 허락받으려 하면 자신감이 줄고, 함께 정할 일을 혼자 확정하면 관계의 신뢰가 약해진다. 결정의 주체를 구분하면 불필요한 오해가 줄어든다.",
    "실제 적용에서는 세 가지 기록이 도움이 된다. 첫째, 돈과 일정은 숫자와 날짜로 적는다. 둘째, 관계에서 반복되는 말은 감정 표현과 요청 사항을 나누어 적는다. 셋째, 집과 일의 선택은 장점과 비용을 같은 줄에 적는다. 이렇게 적어 보면 막연히 좋거나 나쁘게 느껴졌던 일이 현실적인 크기로 보인다. 기록은 결정을 대신하지 않지만, 결정이 감정에만 끌려가지 않도록 붙잡아 준다.",
    "마지막으로, 통합 판단의 목적은 모든 답을 한 번에 정하는 데 있지 않다. 지금 당장 지켜야 할 기준, 조금 더 지켜볼 기준, 분명히 멈추어야 할 기준을 나누는 데 있다. 관계가 좋을 때도 점검은 필요하고, 관계가 흔들릴 때도 성급한 결론은 피해야 한다. 개인의 호흡과 관계의 반응을 함께 보면서 작은 약속부터 정돈하면 다음 선택의 부담이 줄어든다. 그렇게 해야 개인의 삶과 가까운 관계가 서로를 소모시키지 않고, 생활 안에서 지속 가능한 형태로 자리를 잡는다.",
)


def _parse_birth(s: str) -> tuple[int, int, int, int, int]:
    d, t = (s.strip().split() + ["12:00"])[:2]
    y, mo, da = (int(x) for x in d.split("-"))
    hh, mi = (int(x) for x in t.split(":"))
    return y, mo, da, hh, mi


def _is_male(g) -> bool:
    return str(g).strip().lower() not in ("여", "여자", "f", "female", "0")


def parse_person_arg(raw: str) -> tuple[str, tuple[int, int, int, int, int], bool]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) < 2:
        raise ValueError("--person 형식: 이름,YYYY-MM-DD,HH:MM,성별")
    name = parts[0]
    date = parts[1]
    time = parts[2] if len(parts) >= 3 and parts[2] else "12:00"
    gender = parts[3] if len(parts) >= 4 else "남"
    return name, _parse_birth(f"{date} {time}"), _is_male(gender)


def _copy_section(section, *, prefix: str | None = None):
    sid = f"{prefix}_{section.id}" if prefix else section.id
    return SimpleNamespace(
        id=sid,
        title=section.title,
        source_keys=list(getattr(section, "source_keys", []) or []),
        final_text=section.final_text,
    )


class _AssemblyResult(list[object]):
    """기존 list 계약을 유지하며 병합 전 모듈 커버리지 증거를 함께 보존한다."""

    def __init__(
        self,
        sections: list[object],
        *,
        premerge_section_ids: list[str],
        module_sections: dict[str, list[str]],
    ) -> None:
        super().__init__(sections)
        self.premerge_section_ids = premerge_section_ids
        self.module_sections = module_sections

    @property
    def sections(self) -> list[object]:
        """신규 메타 소비처용 명시적 이름. 값 자체는 기존과 같은 list다."""

        return self


def _compact_sparse_sections(sections: list[object]) -> list[object]:
    compacted: list[object] = []
    for section in sections:
        if not compacted:
            compacted.append(section)
            continue
        if _should_merge_sparse_section(section, compacted[-1]):
            _merge_section_into_previous(compacted[-1], section)
            continue
        compacted.append(section)
    return compacted


def _should_merge_sparse_section(section, previous) -> bool:
    sid = str(getattr(section, "id", "") or "")
    previous_id = str(getattr(previous, "id", "") or "")
    if sid in _SPARSE_TAIL_SECTION_IDS:
        return True
    if _section_text_chars(section) >= _SPARSE_SECTION_MIN_CHARS:
        return False
    section_group = _section_group(sid)
    return bool(section_group and section_group == _section_group(previous_id))


def _section_group(section_id: str) -> str:
    for prefix in ("personal_", "relationship_"):
        if section_id.startswith(prefix):
            return prefix.rstrip("_")
    return ""


def _section_text_chars(section) -> int:
    return len("".join((getattr(section, "final_text", "") or "").split()))


def _merge_section_into_previous(previous, section) -> None:
    title = (getattr(section, "title", "") or "").strip()
    body = (getattr(section, "final_text", "") or "").strip()
    addition = "\n".join(part for part in (title, body) if part).strip()
    if addition:
        previous.final_text = "\n\n".join(
            part for part in ((previous.final_text or "").rstrip(), addition) if part
        )
    previous.source_keys = list(
        dict.fromkeys(
            list(getattr(previous, "source_keys", []) or [])
            + list(getattr(section, "source_keys", []) or [])
        )
    )


def _with_no_llm_depth_section(sections: list[object]) -> list[object]:
    depth = SimpleNamespace(
        id=_NO_LLM_DEPTH_SECTION_ID,
        title=_NO_LLM_DEPTH_SECTION_TITLE,
        source_keys=["integrated_full"],
        final_text="\n\n".join(_NO_LLM_DEPTH_PARAGRAPHS),
    )
    out: list[object] = []
    inserted = False
    for section in sections:
        if not inserted and str(getattr(section, "id", "")).startswith("relationship_"):
            out.append(depth)
            inserted = True
        out.append(section)
    if not inserted:
        out.append(depth)
    return out


def _receiver_person(people_in: list[tuple], receiver_name: str | None) -> tuple:
    if not people_in:
        raise ValueError("integrated_full requires at least one --person")
    if not receiver_name:
        return people_in[0]
    for person in people_in:
        if person[0] == receiver_name:
            return person
    raise ValueError("receiver must match one of --person names")


def _assemble_sections(
    personal_report,
    relationship_sections: list[object],
    modules: list[str] | tuple[str, ...] | None = None,
) -> _AssemblyResult:
    """현행 독서 순서를 필터링하고, 그 뒤에만 레거시 sparse 병합을 적용한다.

    v3 불변식은 커버리지 판정 자료를 병합 전에 잡는 것이다. 병합은 섹션 ID를 없앨 수
    있으므로 ``module_sections``는 필터링 직후 목록에서 만들고 이후 절대 재계산하지 않는다.
    """

    selected = integrated_modules.normalize_modules(modules)
    personal_drop = {"cover", "toc"}
    closing_ids = {"closing", "appendix_terms", "colophon"}
    closing: list[object] = []
    body: list[object] = []
    module_sections = integrated_modules.empty_module_sections()
    for section in personal_report.sections:
        if section.id in personal_drop:
            continue
        if section.id not in integrated_modules.PERSONAL_SECTION_IDS:
            raise ValueError(f"unregistered integrated personal section: {section.id}")
        owners = integrated_modules.personal_section_modules(section.id, selected)
        if not owners:
            # 등록은 됐지만 선택되지 않은 love/work/health 섹션은 여기서 결정론적으로 제외한다.
            continue
        if section.id not in closing_ids:
            copied = _copy_section(section, prefix="personal")
            body.append(copied)
        else:
            copied = _copy_section(section)
            closing.append(copied)
        for module_id in owners:
            module_sections[module_id].append(copied.id)

    relationship: list[object] = []
    if "gunghap" in selected:
        for section in relationship_sections:
            copied = _copy_section(section, prefix="relationship")
            relationship.append(copied)
            module_sections["gunghap"].append(copied.id)

    sections = body + relationship + closing
    section_ids = [section.id for section in sections]
    duplicates = sorted(
        section_id for section_id in set(section_ids) if section_ids.count(section_id) > 1
    )
    if duplicates:
        raise ValueError(f"duplicate integrated section ids: {duplicates}")

    unexpected = [
        module_id
        for module_id in integrated_modules.SELECTABLE_MODULES
        if module_id not in selected and module_sections[module_id]
    ]
    if unexpected:
        raise ValueError(f"unexpected integrated module sections: {unexpected}")

    for section in sections:
        section.final_text = _integrated_style_safe_text(section.final_text)
    return _AssemblyResult(
        sections=_compact_sparse_sections(sections),
        premerge_section_ids=section_ids,
        module_sections=module_sections,
    )


def _integrated_style_safe_text(text: str) -> str:
    """반복어 선치환 — content/postprocess.style_safe_text 단일 소스 위임(2026-07-04)."""

    return postprocess.style_safe_text(text)


def _pii_free_verify_digest(verify_result: dict) -> dict:
    """게이트 실패 진단용 PII-free 요약(고객 이름·본문·장표제 미포함, 절대규칙17).

    verify_result 를 raw 로 예외 메시지에 담으면 고객 이름/장표제가 로그·트레이스로
    새므로, 실패 원인 파악에 필요한 rule/page/count/bool 만 추출한다."""
    dq = verify_result.get("delivery_quality") or {}
    return {
        "gate_pass": verify_result.get("gate_pass"),
        "failed_clean_flags": sorted(
            k for k, v in verify_result.items() if k.endswith("_clean") and v is False
        ),
        "delivery_failures": [f.get("rule") for f in (dq.get("failures") or [])],
        "low_density": [
            {"page": p.get("page"), "chars": p.get("chars")}
            for p in (verify_result.get("low_density_pages") or [])
        ],
    }


def _integrated_only_low_density_failure(verify_result: dict) -> bool:
    dq = verify_result.get("delivery_quality") or {}
    failures = dq.get("failures") or []
    if not failures:
        return False
    if any(failure.get("rule") != "premium_low_density_pages" for failure in failures):
        return False
    return all(bool(verify_result.get(flag)) for flag in _LOW_DENSITY_ONLY_CLEAN_FLAGS)


def _layout_only_failure(verify_result: dict) -> bool:
    """조판 부류 단독 실패(저밀도 dq 그리고/또는 orphan 스필 페이지) — 레이아웃 변형
    무과금 재렌더 대상. P6 실측(2026-07-05 v8): 13자 스필 1쪽(no_orphan 단독)으로 전체
    빌드가 파기돼 재compose 과금이 강제되던 갭. 게이트 완화 아님 — 최종적으로는 여전히
    gate_pass 가 필요하며, 다음 레이아웃 변형을 시도할 조건만 확대한다."""
    dq = verify_result.get("delivery_quality") or {}
    failures = dq.get("failures") or []
    if any(failure.get("rule") != "premium_low_density_pages" for failure in failures):
        return False
    other_flags = [f for f in _LOW_DENSITY_ONLY_CLEAN_FLAGS if f != "no_orphan"]
    if not all(bool(verify_result.get(flag)) for flag in other_flags):
        return False
    # 저밀도 dq 실패도, orphan 실패도 없으면 조판 부류 실패가 아님(다른 원인).
    return bool(failures) or not bool(verify_result.get("no_orphan"))


def _content_path(out_name: str, out_dir: str | Path | None) -> Path:
    base = Path(out_dir) if out_dir else Path(render_pdf._OUT)
    return base / f"{Path(out_name).stem}.content.json"


def _save_integrated_content(
    result: dict,
    *,
    situation: str,
    ref_year: int,
    brand: str,
    out_name: str,
    out_dir: str | Path | None,
    ref_date: str | None = None,
    premium: bool = True,
    model: str | None = None,
    layout_variant: dict | None = None,
) -> str:
    """compose 결과(본문 sections + 렌더/검증 파라미터)를 JSON 으로 영속.

    레이아웃/템플릿만 바꿔 재렌더할 때 재compose(LLM 과금) 없이 이 파일로 재렌더한다
    (2026-07-02). 고객 PII(이름·상황·본문)를 포함하므로 gitignore 대상 render/out 에만
    저장하고 채팅/커밋에 노출하지 않는다.

    T5.3/B-6·B-7: 재렌더 재현성·이력 메타(ref_date·premium·model·layout_variant)를 스키마에
    추가한다. 읽기 측은 전부 하위호환 기본값을 쓰므로 이 필드 없는 구 파일도 그대로 로드된다."""
    identity = result["identity"]
    selected_modules = integrated_modules.normalize_modules(result.get("modules"))
    module_sections = integrated_modules.normalize_module_sections(result.get("module_sections"))
    premerge_section_ids = result.get("premerge_section_ids")
    if premerge_section_ids is None:
        premerge_section_ids = list(
            dict.fromkeys(
                section_id for values in module_sections.values() for section_id in values
            )
        )
    bundle = {
        "product": PRODUCT,
        # Q7: 재렌더가 compose 당시와 같은 선택·커버리지 하한을 재현하도록 모듈 메타를
        # 본문과 함께 저장한다. 병합 전 목록도 저장해야 sparse 병합으로 사라진 ID를 오탐하지 않는다.
        "modules": list(selected_modules),
        "module_schema_version": MODULE_SCHEMA_VERSION,
        "premerge_section_ids": list(premerge_section_ids),
        "module_sections": module_sections,
        "receiver": result["receiver"],
        "names": [p["name"] for p in result["people"]],
        "ref_year": ref_year,
        # T5.3: 검증 기준일·프리미엄·작성 모델·확정 레이아웃 변형(재현성/이력).
        "ref_date": ref_date or f"{ref_year}-06-13",
        "premium": bool(premium),
        "model": model or "rule",
        "layout_variant": layout_variant,  # 렌더 후 확정 변형(초기 저장 시 None)
        "situation": situation,
        "brand": brand,
        "role_perspective": result["role_perspective"],
        "identity": [list(identity[0]), list(identity[1]), identity[2]],
        "singang": result["singang"],
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "source_keys": list(getattr(s, "source_keys", []) or []),
                "final_text": s.final_text,
            }
            for s in result["sections"]
        ],
    }
    path = _content_path(out_name, out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    result["content_path"] = str(path)
    return str(path)


def _render_integrated(
    report,
    *,
    names: list[str],
    ref_year: int,
    situation: str,
    identity,
    singang,
    role_specs,
    brand: str,
    out_name: str,
    out_dir: str | Path | None,
    selected_modules: list[str] | tuple[str, ...] | None = None,
    module_sections: dict[str, list[str]] | None = None,
    premerge_section_ids: list[str] | tuple[str, ...] | None = None,
    ref_date: str | None = None,
) -> tuple[str, dict, list]:
    """assemble 된 report 를 _LAYOUT_VARIANTS 로 렌더+게이트(compose 없음). build·재렌더 공용.

    ref_date: verify 월 시제 검사 앵커 — 미전달 시 기존 하드코딩과 동일한 연중 기본(6월 13일)."""
    ref_date = ref_date or f"{ref_year}-06-13"
    bp = dict(cfg.brand(brand))
    bp["cover_title"] = f"{bp['seal']} 통합 사주와 관계 풀이"
    fake_saju = SimpleNamespace(input_civil=" · ".join(names))
    pdf_path = ""
    verify_result: dict = {}
    attempts: list = []
    for idx, (body_font_size, body_line_height) in enumerate(_LAYOUT_VARIANTS):
        pdf_path = render_pdf.render_pdf(
            report,
            fake_saju,
            out_name,
            name="",
            brand=bp,
            body_font_size=body_font_size,
            body_line_height=body_line_height,
            # 장마다 새 페이지 시작(개인·궁합 리포트와 동일, 책/프리미엄 표준). 긴 장의
            # 짧은 조판 꼬리는 verify._starts_new_chapter 로 저밀도에서 제외(2026-07-02).
            chapter_breaks=True,
            out_dir=out_dir,
        )
        verify_result = render_verify.verify(
            pdf_path,
            ref_year=ref_year,
            names=names,
            name_full=names,
            identity=identity,
            singang=singang,
            product=PRODUCT,
            premium=True,
            concern=situation,
            ref_date=ref_date,
            role_perspective=role_specs,
            honorific=role_specs,
            # Q7 커버리지는 렌더 후 PDF 제목을 역추정하지 않고 조립기의 병합 전 목록을 쓴다.
            selected_modules=selected_modules,
            module_sections=module_sections,
            premerge_section_ids=premerge_section_ids,
        )
        low_density_only = _integrated_only_low_density_failure(verify_result)
        layout_only = _layout_only_failure(verify_result)  # P6: orphan 스필 포함(무과금 재렌더)
        attempts.append(
            {
                "body_font_size": body_font_size,
                "body_line_height": body_line_height,
                "gate_pass": bool(verify_result.get("gate_pass")),
                "low_density_only": low_density_only,
                "layout_only": layout_only,
            }
        )
        if verify_result.get("gate_pass"):
            break
        if idx < len(_LAYOUT_VARIANTS) - 1 and layout_only:
            continue
        raise RuntimeError(
            "integrated_full PDF 하드 게이트 실패(빌드 실패, PII 제외): "
            f"{_pii_free_verify_digest(verify_result)}"
        )
    return pdf_path, verify_result, attempts


def render_integrated_from_content(
    content_path: str | Path,
    *,
    brand: str | None = None,
    out_name: str | None = None,
    out_dir: str | Path | None = None,
) -> dict:
    """저장된 compose 본문(.content.json)에서 재compose 없이 재렌더(레이아웃/템플릿 변경용, LLM 0).

    template/CSS 를 바꿨을 때 API 과금 없이 기존 고객 본문을 새 레이아웃으로 다시 렌더한다."""
    data = json.loads(Path(content_path).read_text(encoding="utf-8"))
    stored_schema_version = data.get("module_schema_version", MODULE_SCHEMA_VERSION)
    if stored_schema_version != MODULE_SCHEMA_VERSION:
        raise ValueError(
            "unsupported integrated module schema version: "
            f"{stored_schema_version} (expected {MODULE_SCHEMA_VERSION})"
        )
    # 모듈 필드가 없던 구 번들은 선택 기능 이전 산출물이므로 5모듈 전체로 복원한다.
    # 이는 skipped가 아니라 당시 조립 계약을 명시적으로 적용하는 하위호환 경로다.
    selected_modules = integrated_modules.normalize_modules(data.get("modules"))
    module_sections = integrated_modules.normalize_module_sections(data.get("module_sections"))
    premerge_section_ids = list(
        data.get("premerge_section_ids")
        or dict.fromkeys(
            section_id for values in module_sections.values() for section_id in values
        )
    )
    report = SimpleNamespace(
        sections=[
            SimpleNamespace(
                id=s["id"],
                title=s["title"],
                source_keys=s.get("source_keys", []) or [],
                final_text=s["final_text"],
            )
            for s in data["sections"]
        ]
    )
    identity = (data["identity"][0], data["identity"][1], data["identity"][2])
    out = out_name or f"{Path(content_path).stem.replace('.content', '')}.pdf"
    pdf_path, verify_result, attempts = _render_integrated(
        report,
        names=data["names"],
        ref_year=data.get("ref_year", 2026),
        situation=data.get("situation", ""),
        identity=identity,
        singang=data.get("singang", []),
        role_specs=data["role_perspective"],
        brand=brand or data.get("brand", "sajudoryeong"),
        out_name=out,
        out_dir=out_dir,
        selected_modules=selected_modules,
        module_sections=module_sections,
        premerge_section_ids=premerge_section_ids,
        # T5.3 영속 ref_date 로 재렌더도 같은 월 시제 앵커 — 구 파일(필드 없음)은 연중 기본.
        ref_date=data.get("ref_date"),
    )
    return {
        "product": PRODUCT,
        "pdf_path": pdf_path,
        "verify": verify_result,
        "layout_attempts": attempts,
        "content_path": str(content_path),
        # T5.3 provenance — 구 content.json(필드 없음)은 하위호환 기본값으로 로드.
        "ref_date": data.get("ref_date", f"{data.get('ref_year', 2026)}-06-13"),
        "premium": data.get("premium", True),
        "model": data.get("model", "rule"),
        "layout_variant": data.get("layout_variant"),
        "modules": list(selected_modules),
        "module_schema_version": stored_schema_version,
        "module_sections": module_sections,
        "premerge_section_ids": premerge_section_ids,
    }


def build_integrated_full(
    people_in: list[tuple],
    *,
    receiver_name: str | None = None,
    situation: str = "",
    ref_year: int = 2026,
    out_name: str = "integrated_full.pdf",
    brand: str = "sajudoryeong",
    use_llm: bool = False,
    render: bool = True,
    out_dir: str | Path | None = None,
    ref_date: str | None = None,
    modules: list[str] | tuple[str, ...] | None = None,
) -> dict:
    selected_modules = integrated_modules.normalize_modules(modules)
    receiver = _receiver_person(people_in, receiver_name)
    if "gunghap" in selected_modules and len(people_in) < 2:
        raise ValueError("gunghap module requires at least two people")

    # 월 시제 닻(QI-2026-07-04-02 관계 상품 확장): 개인 장(build_report)·관계 장(build_gunghap)·
    # verify·content.json 영속에 같은 기준 일자를 배선. 미지정 시 기존 하드코딩과 동일한
    # 연중 기본(6월 13일) — 실주문은 생성 당일을 전달할 것.
    ref_date = ref_date or f"{ref_year}-06-13"
    receiver_name = receiver[0]
    y, mo, da, hh, mi = receiver[1]
    saju = engine.build(
        y,
        mo,
        da,
        hh,
        mi,
        is_male=bool(receiver[2]),
        horoscope_date=f"{ref_year}-06-01",
    )
    personal_report = builder.build_report(
        saju,
        use_llm=use_llm,
        ref_year=ref_year,
        name=receiver_name,
        product=PRODUCT,
        concern=situation,
        closing_sign=cfg.brand(brand)["closing_sign"],
        ref_date=ref_date,
        # work 챕터의 기존 ID와 가드 경로는 유지하고, 내부 제공자 텍스트만 선택한다.
        work_modules=integrated_modules.work_provider_modules(selected_modules),
        # 선택 밖 개인 챕터는 LLM 작성 후보에서도 제외해 비용과 비선택 문안 생성을 막는다.
        include_section_ids=integrated_modules.included_personal_sections(selected_modules),
    )

    # gunghap 미선택 경로는 관계 compose를 호출하지 않는다. 이 분기가 있어야 1인 입력의
    # love/job/wealth/health 조합이 가능하고, 선택하지 않은 관계 문안도 생성되지 않는다.
    relationship_sections: list[object] = []
    if "gunghap" in selected_modules:
        relationship_result = gunghap.build_gunghap(
            people_in,
            situation=situation,
            ref_year=ref_year,
            ref_date=ref_date,
            out_name=out_name,
            brand=brand,
            mode="relationship",
            use_llm=use_llm,
            receiver_perspective=True,
            receiver_name=receiver_name,
            product=PRODUCT,
            render=False,
        )
        people = relationship_result["people"]
        relationship_sections = relationship_result["sections"]
    else:
        people = [
            {
                "name": receiver_name,
                "day_master": saju.myeongni.day_master,
                "singang": saju.myeongni.singang,
            }
        ]

    assembly = _assemble_sections(personal_report, relationship_sections, selected_modules)
    sections = assembly.sections
    # 이 깊이 보강장은 기존 5모듈 무LLM 산출의 하위호환 장치다. 부분 조합에는 선택 밖
    # 영역 문단이 섞이지 않도록 넣지 않으며, None과 명시적 5모듈은 모두 같은 조건을 탄다.
    if not use_llm and selected_modules == integrated_modules.SELECTABLE_MODULES:
        sections = _with_no_llm_depth_section(sections)
    report = SimpleNamespace(sections=sections)
    names = [p["name"] for p in people]
    role_specs = client_tone_lint.role_perspective_specs(names, receiver=receiver_name)
    result = {
        "product": PRODUCT,
        "report": report,
        "sections": sections,
        "people": people,
        "receiver": receiver_name,
        "role_perspective": role_specs,
        "honorific": role_specs,
        "identity": gunghap._identity_spec(people),
        "singang": gunghap._singang_specs(people),
        "pdf_path": "",
        "verify": {},
        "layout_attempts": [],
        "modules": list(selected_modules),
        "module_schema_version": MODULE_SCHEMA_VERSION,
        "premerge_section_ids": assembly.premerge_section_ids,
        "module_sections": assembly.module_sections,
    }
    if not render:
        return result

    # 재compose 없이 재렌더할 수 있도록 compose 결과를 영속(2026-07-02) — 레이아웃/템플릿 변경이
    # API 과금(재compose)을 강제하지 않게 한다. 렌더 전에 먼저 저장(렌더 실패해도 재compose 방지).
    model = cfg.llm_model("compose") if use_llm else "rule"
    _save_kwargs = dict(
        situation=situation,
        ref_year=ref_year,
        brand=brand,
        out_name=out_name,
        out_dir=out_dir,
        ref_date=ref_date,
        premium=True,
        model=model,
    )
    _save_integrated_content(result, **_save_kwargs)
    pdf_path, verify_result, attempts = _render_integrated(
        report,
        names=names,
        ref_year=ref_year,
        situation=situation,
        identity=result["identity"],
        singang=result["singang"],
        role_specs=role_specs,
        brand=brand,
        out_name=out_name,
        out_dir=out_dir,
        selected_modules=selected_modules,
        module_sections=assembly.module_sections,
        premerge_section_ids=assembly.premerge_section_ids,
        ref_date=ref_date,
    )
    result["layout_attempts"] = attempts
    result["pdf_path"] = pdf_path
    result["verify"] = verify_result
    # 확정 레이아웃 변형을 content.json 이력에 반영해 재저장(재현성, T5.3) — 게이트 통과분만.
    won = next((a for a in reversed(attempts) if a.get("gate_pass")), None)
    if won is not None:
        _save_integrated_content(
            result,
            **_save_kwargs,
            layout_variant={
                "body_font_size": won.get("body_font_size"),
                "body_line_height": won.get("body_line_height"),
            },
        )
    return result


app = typer.Typer(add_completion=False, help="native integrated_full PDF product")


@app.command()
def gen(
    person: list[str] = typer.Option(..., "--person", help="이름,YYYY-MM-DD,HH:MM,성별 (반복)"),
    receiver: str | None = typer.Option(None, "--receiver", help="수신자 이름"),
    situation: str = typer.Option("", "--situation", help="합성/운영 상황 맥락"),
    ref_year: int = typer.Option(2026, "--ref-year"),
    ref_date: str = typer.Option(
        None,
        "--ref-date",
        help="풀이 기준 일자 YYYY-MM-DD(월 시제 닻, 실주문은 생성 당일). 미지정 시 연중 기본(6월 13일)",
    ),
    out: str = typer.Option("integrated_full.pdf", "--out"),
    brand: str = typer.Option("sajudoryeong", "--brand"),
    llm: bool = typer.Option(False, "--llm"),
):
    people = [parse_person_arg(p) for p in person]
    # Phase 0: 운영자 대면 CLI 미지정 시 '오늘' 주입(기억 의존 제거). 라이브러리
    # build_integrated_full 의 None→6-13 폴백은 유지(테스트 결정론) — 여기서만 today.
    if ref_date is None:
        ref_date = default_ref_date_iso()
    result = build_integrated_full(
        people,
        receiver_name=receiver,
        situation=situation,
        ref_year=ref_year,
        ref_date=ref_date,
        out_name=out,
        brand=brand,
        use_llm=llm,
        render=True,
    )
    typer.echo(f"PDF: {result['pdf_path']} ({len(result['people'])}인)")
    typer.echo(llm_usage.format_line())  # 사용량 관측(2026-07-05) — hrun 이 파싱해 summary 로


@app.command()
def render(
    content: str = typer.Option(..., "--content", help="저장된 compose 본문(.content.json) 경로"),
    out: str | None = typer.Option(None, "--out", help="출력 PDF 이름(미지정 시 content 기준)"),
    brand: str | None = typer.Option(None, "--brand", help="미지정 시 저장된 brand 사용"),
):
    """저장된 본문으로 재compose 없이 재렌더(레이아웃/템플릿 변경용, LLM/API 0)."""
    result = render_integrated_from_content(content, brand=brand, out_name=out)
    typer.echo(f"PDF: {result['pdf_path']} (재렌더, LLM 0)")


if __name__ == "__main__":
    app()
