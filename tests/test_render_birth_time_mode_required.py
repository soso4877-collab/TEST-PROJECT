"""렌더 경계의 출생시간 모드 필수 전달 계약을 검증한다."""

from types import SimpleNamespace

import pytest

from sajugen import config as cfg
from sajugen.calc import engine
from sajugen.content import unknown_time_policy
from sajugen.render import pdf as render_pdf


def _report(text: str = "합성 본문입니다.") -> SimpleNamespace:
  """고객 정보 없이 렌더 경계만 통과하는 최소 리포트를 만든다."""

  section = SimpleNamespace(id="intro", title="합성 장", final_text=text)
  return SimpleNamespace(sections=[section])


def _known_saju() -> SimpleNamespace:
  """known 렌더에 필요한 최소 표지 메타만 제공한다."""

  return SimpleNamespace(input_civil="합성 입력")


def _three_pillar_saju():
  """삼주 provenance와 차트를 함께 가진 결정론 합성 결과를 만든다."""

  return engine.build(
    2000,
    1,
    15,
    None,
    None,
    is_male=False,
    birth_time_mode="three_pillar",
    horoscope_date="2026-07-12",
  )


def test_render_html_requires_birth_time_mode_keyword():
  """모드 미전달은 known 기본값으로 조용히 통과하지 않는다."""

  with pytest.raises(TypeError, match="birth_time_mode"):
    render_pdf.render_html(
      _report(),
      _known_saju(),
      brand=cfg.brand("default"),
    )


def test_render_html_rejects_explicit_none_mode():
  """명시적인 None도 normalize_mode의 known 폴백에 들어가지 않는다."""

  with pytest.raises(
    ValueError,
    match="birth_time_mode is required at render boundary",
  ):
    render_pdf.render_html(
      _report(),
      _known_saju(),
      birth_time_mode=None,
      brand=cfg.brand("default"),
    )


def test_provenance_cannot_infer_missing_birth_time_mode():
  """provenance 존재만으로 삼주 모드를 추론하던 경로를 제거한다."""

  saju = _three_pillar_saju()
  provenance = unknown_time_policy.serialize_provenance(saju.provenance)

  with pytest.raises(TypeError, match="birth_time_mode"):
    render_pdf.render_html(
      _report(),
      saju,
      three_pillar_provenance=provenance,
      brand=cfg.brand("default"),
    )


def test_explicit_three_pillar_mode_keeps_provenance_guard():
  """필수 인자화 뒤에도 삼주 금칙 사실은 렌더 전에 차단한다."""

  saju = _three_pillar_saju()
  provenance = unknown_time_policy.serialize_provenance(saju.provenance)
  report = _report("시주는 갑자로 확정했습니다.")

  with pytest.raises(ValueError, match="hour_pillar"):
    render_pdf.render_html(
      report,
      saju,
      birth_time_mode="three_pillar",
      three_pillar_provenance=provenance,
      brand=cfg.brand("default"),
    )
