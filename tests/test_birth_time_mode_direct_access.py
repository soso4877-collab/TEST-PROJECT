from types import SimpleNamespace

import pytest

from sajugen import integrated
from sajugen.calc import engine
from sajugen.content import builder, client_tone_lint, factcheck, rules


def test_personal_identity_spec_requires_birth_time_mode_keyword() -> None:
  # 모드 생략을 조용히 known으로 해석하지 않고 공개 함수 계약에서 즉시 차단한다.
  saju = SimpleNamespace(myeongni=SimpleNamespace(day_master="甲"))

  with pytest.raises(TypeError, match="birth_time_mode"):
    builder.personal_identity_spec(saju, None)


def test_personal_identity_spec_three_pillar_requires_matching_attribute() -> None:
  # 명시된 삼주 모드와 객체 표면이 어긋나면 known 속성으로 후퇴하지 않는다.
  saju = SimpleNamespace(myeongni=SimpleNamespace(day_master="甲"))

  with pytest.raises(AttributeError, match="three_pillar"):
    builder.personal_identity_spec(saju, None, birth_time_mode="three_pillar")


def test_render_integrated_requires_mode_when_keyword_is_omitted(monkeypatch) -> None:
  # 합성 객체에도 정본 모드 속성을 요구해 렌더 경계의 암묵적 known 기본값을 제거한다.
  monkeypatch.setattr(
    integrated.render_pdf,
    "render_pdf",
    lambda *_args, **_kwargs: "synthetic.pdf",
  )
  monkeypatch.setattr(
    integrated.render_verify,
    "verify",
    lambda *_args, **_kwargs: {"gate_pass": True},
  )

  with pytest.raises(AttributeError, match="birth_time_mode"):
    integrated._render_integrated(
      SimpleNamespace(sections=[]),
      names=["DOC_A"],
      ref_year=2026,
      situation="합성 맥락",
      identity=(set(), set(), []),
      singang=[],
      role_specs=[],
      brand="default",
      out_name="synthetic.pdf",
      out_dir=None,
    )


def test_allowed_tokens_requires_birth_time_mode_attribute() -> None:
  # 사실 토큰 경계도 모드 없는 합성 객체를 known으로 추론하지 않고 즉시 차단한다.
  saju = SimpleNamespace(myeongni=SimpleNamespace())

  with pytest.raises(AttributeError, match="birth_time_mode"):
    factcheck.allowed_tokens(saju)


@pytest.mark.parametrize(
  ("hour", "minute", "birth_time_mode"),
  [(12, 0, "known"), (None, None, "three_pillar")],
)
def test_canonical_engine_results_preserve_mode_dependent_outputs(
  hour: int | None,
  minute: int | None,
  birth_time_mode: str,
) -> None:
  # 두 정본 엔진 결과의 실제 속성에서 기대값을 계산해 교정 전 문안 값을 고정하지 않는다.
  saju = engine.build(
    2000,
    1,
    15,
    hour,
    minute,
    is_male=True,
    horoscope_date="2026-06-01",
    birth_time_mode=birth_time_mode,
  )
  mode_result = saju.three_pillar if birth_time_mode == "three_pillar" else saju.myeongni

  gan = rules._GAN_KO.get(mode_result.day_master, "")
  term = client_tone_lint.gan_to_term(gan)
  assert builder.personal_identity_spec(
    saju,
    None,
    birth_time_mode=birth_time_mode,
  ) == (
    {gan},
    {term},
    [(["자기 자신", "나 자신", "본인", "자신"], term)],
  )

  # 허용 간지는 모드가 선택한 실제 명식 속성과 정확히 동치여야 한다.
  expected_ganzhi = {
    mode_result.year.ganzhi,
    mode_result.month.ganzhi,
    mode_result.day.ganzhi,
  }
  if birth_time_mode == "known":
    expected_ganzhi.add(mode_result.hour.ganzhi)
    expected_ganzhi |= {item.ganzhi for item in mode_result.daewoon}
  expected_ganzhi |= {ganzhi for _, ganzhi in getattr(mode_result, "seun", [])}
  expected_ganzhi |= {ganzhi for _, ganzhi in getattr(mode_result, "worun", [])}
  assert factcheck.allowed_tokens(saju)["ganzhi"] == expected_ganzhi

  # 명시 모드와 정본 속성 모드가 만드는 전체 룰 문안은 두 방향에서 동일하다.
  assert rules.build_all(saju, ref_year=2026) == rules.build_all(
    saju,
    ref_year=2026,
    birth_time_mode=birth_time_mode,
  )
