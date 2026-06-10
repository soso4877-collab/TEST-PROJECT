# -*- coding: utf-8 -*-
"""KASI(공공데이터포털) 캐시 리더 + 3원 교차검증 확장.

절대규칙 4: KASI는 런타임 실시간 API 의존 금지 — 사전 캐싱(data/kasi_cache.sqlite)만 참조.
이 모듈은 캐시를 **읽기만** 한다(네트워크 호출 없음). 캐시 적재는 scripts/kasi_dump.py.

내용:
- 스키마/빌더: init_db, upsert_lunar_rows, upsert_solarterm_rows (dump·테스트 공용).
- 리더: KasiCache — 음양력(일별 간지·윤달) 조회, 절기 KST 시각 조회.
- 3원 교차: crosscheck3_year — 기존 2원(lunar↔Skyfield)에 KASI 열을 더해
  Skyfield↔KASI 절입시각 차이를 분 단위로 비교(허용 2분, calc.md 규칙).

절기 가용 범위: KASI 특일 API는 2000~약 2027년만 제공(실측 2026-06-10).
범위 밖/캐시 부재 시 KASI 열은 비고, 기존 2원 결과를 그대로 유지(폴백).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import crosscheck as _xc
from . import solarterms as _st

_KST = ZoneInfo("Asia/Seoul")

# 기본 캐시 경로(런타임 빌드 산출물, .gitignore). 테스트는 별도 픽스처 경로 주입.
DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "kasi_cache.sqlite"

# KASI 특일 API 절기의 알려진 원본 결함(2026-06-10 2000~2027 전수 스캔 확정).
# Skyfield(DE440)+lunar-python 두 계산엔진이 ≤0.03분으로 일치하는데 KASI만 어긋난 행 = KASI 입력오류.
# 절기 timing 권위 = Skyfield(검증=lunar-python). KASI 절기는 3차 교차참조이며 라이브 명리
# 엔진(월주·세운 경계)은 Skyfield(solarterms.py)를 쓰므로 이 결함은 사주 계산에 영향 없음.
# 교차검증에서 아래 행은 '기지 결함'으로 분류 → 주문 차단(CALC_MISMATCH) 대상에서 제외.
KNOWN_KASI_TERM_DEFECTS = {
    (2011, "大寒"): "KASI 2011-01-21 19:18 → 정정 01-20 19:18 (일자 +1 오타)",
    (2011, "立冬"): "KASI 2011-11-08 09:26 → 정정 11-08 03:34 (시각 약 6h 오차)",
    (2015, "夏至"): "KASI 2015-06-22 01:58 → 정정 06-22 01:37 (시각 약 20분 오차)",
}

# KASI 절기명(한글) → Skyfield TERMS의 한자명. 절기 시각 매칭/정규화에 사용.
KO_TO_HANJA = {
    "입춘": "立春",
    "우수": "雨水",
    "경칩": "驚蟄",
    "춘분": "春分",
    "청명": "清明",
    "곡우": "穀雨",
    "입하": "立夏",
    "소만": "小滿",
    "망종": "芒種",
    "하지": "夏至",
    "소서": "小暑",
    "대서": "大暑",
    "입추": "立秋",
    "처서": "處暑",
    "백로": "白露",
    "추분": "秋分",
    "한로": "寒露",
    "상강": "霜降",
    "입동": "立冬",
    "소설": "小雪",
    "대설": "大雪",
    "동지": "冬至",
    "소한": "小寒",
    "대한": "大寒",
}


# ─────────────────────────── 스키마/빌더 (dump·테스트 공용) ───────────────────────────


def init_db(conn: sqlite3.Connection) -> None:
    """캐시 스키마 생성(idempotent)."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS lunar (
            sol_ymd  INTEGER PRIMARY KEY,   -- 양력 YYYYMMDD (예: 19900520)
            lun_year INTEGER, lun_month INTEGER, lun_day INTEGER,
            leap     INTEGER,               -- 0=평달, 1=윤달
            secha    TEXT,                  -- 세차(연 간지) '경오(庚午)'
            wolgeon  TEXT,                  -- 월건(월 간지) '신사(辛巳)'
            iljin    TEXT,                  -- 일진(일 간지) '병인(丙寅)'
            sol_jd   INTEGER                -- 율리우스적일
        );
        CREATE TABLE IF NOT EXISTS solarterm (
            year     INTEGER,
            term     TEXT,                  -- 정규화된 한자 절기명(立春…) — Skyfield 최근접 도출
            locdate  INTEGER,               -- 절입일 YYYYMMDD
            kst_min  INTEGER,               -- 절입시각: 자정 기준 분(KST)
            raw_name TEXT,                  -- KASI 원본 dateName(한글, 결함 감사용)
            PRIMARY KEY (year, term)
        );
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY, value TEXT
        );
        """
    )
    conn.commit()


def _parse_leap(v: str) -> int:
    return 1 if str(v).strip() in ("윤", "1") else 0


def upsert_lunar_rows(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """getLunCalInfo item 리스트를 lunar 테이블에 upsert. 적재 건수 반환."""
    n = 0
    for it in rows:
        sol_ymd = int(it["solYear"]) * 10000 + int(it["solMonth"]) * 100 + int(it["solDay"])
        conn.execute(
            """INSERT INTO lunar
               (sol_ymd, lun_year, lun_month, lun_day, leap, secha, wolgeon, iljin, sol_jd)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(sol_ymd) DO UPDATE SET
                 lun_year=excluded.lun_year, lun_month=excluded.lun_month,
                 lun_day=excluded.lun_day, leap=excluded.leap, secha=excluded.secha,
                 wolgeon=excluded.wolgeon, iljin=excluded.iljin, sol_jd=excluded.sol_jd""",
            (
                sol_ymd,
                int(it["lunYear"]),
                int(it["lunMonth"]),
                int(it["lunDay"]),
                _parse_leap(it.get("lunLeapmonth", "평")),
                str(it.get("lunSecha", "")).strip(),
                str(it.get("lunWolgeon", "")).strip(),
                str(it.get("lunIljin", "")).strip(),
                int(it.get("solJd", 0)),
            ),
        )
        n += 1
    conn.commit()
    return n


def _kst_min(kst_raw: str) -> int:
    """'1723      ' → 17*60+23 = 1043 (KASI kst는 HHMM + 패딩)."""
    s = str(kst_raw).strip()[:4].zfill(4)
    return int(s[:2]) * 60 + int(s[2:])


def normalize_solarterm_rows(year: int, rows: list[dict]) -> list[tuple]:
    """KASI 24절기 item을 Skyfield 절입시각에 최근접 매칭해 한자 절기명으로 정규화.

    KASI 원본 dateName 결함(예: 2000-02 우수 행이 '입춘'으로 오기)을 우회하기 위해
    이름이 아니라 **시각**으로 어느 절기인지 판정한다. 각 행의 KST 시각을 UTC로 바꿔
    그 해 24절기 Skyfield 예측시각 중 가장 가까운 것의 한자명을 부여.
    반환: (year, term_hanja, locdate, kst_min, raw_name) 튜플 리스트.
    """
    sky = _st.all_terms_utc(year)  # {한자명: UTC naive}
    out: list[tuple] = []
    used: set[str] = set()
    for it in rows:
        locdate = int(it["locdate"])
        kmin = _kst_min(it["kst"])
        y, mo, d = locdate // 10000, (locdate // 100) % 100, locdate % 100
        kst_dt = datetime(y, mo, d, kmin // 60, kmin % 60, tzinfo=_KST)
        utc = kst_dt.astimezone(timezone.utc).replace(tzinfo=None)
        # 그 해 24절기 Skyfield 시각 중 최근접(미사용 우선) 매칭
        best = min(
            sky.items(),
            key=lambda kv: (kv[0] in used, abs((kv[1] - utc).total_seconds())),
        )
        term = best[0]
        used.add(term)
        out.append((year, term, locdate, kmin, str(it.get("dateName", "")).strip()))
    return out


def upsert_solarterm_rows(conn: sqlite3.Connection, year: int, rows: list[dict]) -> int:
    """정규화 후 solarterm 테이블에 upsert. 적재 건수 반환."""
    norm = normalize_solarterm_rows(year, rows)
    for r in norm:
        conn.execute(
            """INSERT INTO solarterm (year, term, locdate, kst_min, raw_name)
               VALUES (?,?,?,?,?)
               ON CONFLICT(year, term) DO UPDATE SET
                 locdate=excluded.locdate, kst_min=excluded.kst_min,
                 raw_name=excluded.raw_name""",
            r,
        )
    conn.commit()
    return len(norm)


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    conn.commit()


# ─────────────────────────────── 리더 ───────────────────────────────


class KasiCache:
    """KASI sqlite 캐시 읽기전용 리더(네트워크 호출 없음)."""

    def __init__(self, path: str | Path = DEFAULT_CACHE):
        self.path = Path(path)
        self._conn: sqlite3.Connection | None = None

    @property
    def exists(self) -> bool:
        return self.path.exists()

    def _c(self) -> sqlite3.Connection:
        if self._conn is None:
            # 읽기전용 + 즉시 실패(파일 없으면 에러)
            self._conn = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def lunar_of(self, year: int, month: int, day: int) -> dict | None:
        """양력 날짜의 음력·간지·윤달 정보. 없으면 None."""
        ymd = year * 10000 + month * 100 + day
        row = self._c().execute("SELECT * FROM lunar WHERE sol_ymd=?", (ymd,)).fetchone()
        return dict(row) if row else None

    def solar_of_lunar(
        self, lun_year: int, lun_month: int, lun_day: int, is_leap: bool = False
    ) -> dict | None:
        """음력(년/월/일/윤달) → 양력 날짜 역방향 조회(KASI 1차 기준). 없으면 None.

        반환: {'sol_ymd','year','month','day','leap','iljin','secha'}.
        음력 1일은 양력 1일에 유일 대응하므로 결과는 0 또는 1건.
        """
        leap = 1 if is_leap else 0
        row = (
            self._c()
            .execute(
                "SELECT * FROM lunar WHERE lun_year=? AND lun_month=? AND lun_day=? AND leap=?",
                (lun_year, lun_month, lun_day, leap),
            )
            .fetchone()
        )
        if not row:
            return None
        s = int(row["sol_ymd"])
        return {
            "sol_ymd": s,
            "year": s // 10000,
            "month": (s // 100) % 100,
            "day": s % 100,
            "leap": int(row["leap"]),
            "iljin": row["iljin"],
            "secha": row["secha"],
        }

    def solar_term_years(self) -> tuple[int, int] | None:
        """캐시에 절기가 있는 연도 [min, max]. 없으면 None."""
        row = self._c().execute("SELECT MIN(year) lo, MAX(year) hi FROM solarterm").fetchone()
        if row is None or row["lo"] is None:
            return None
        return (int(row["lo"]), int(row["hi"]))

    def solar_terms_kst(self, year: int) -> dict[str, datetime]:
        """그 해 절기 한자명 → 절입 KST datetime(tz-aware). 없으면 빈 dict."""
        out: dict[str, datetime] = {}
        for row in self._c().execute(
            "SELECT term, locdate, kst_min FROM solarterm WHERE year=?", (year,)
        ):
            loc, km = int(row["locdate"]), int(row["kst_min"])
            y, mo, d = loc // 10000, (loc // 100) % 100, loc % 100
            out[row["term"]] = datetime(y, mo, d, km // 60, km % 60, tzinfo=_KST)
        return out


# ─────────────────────────── 3원 교차검증 ───────────────────────────


def crosscheck3_year(
    year: int,
    *,
    cache: KasiCache | None = None,
    tolerance_min: float = 5.0,
    kasi_tolerance_min: float = 2.0,
) -> dict:
    """3원 교차(lunar-python ↔ Skyfield ↔ KASI) 그 해 절기 비교.

    기존 2원 결과(crosscheck.crosscheck_year)를 토대로, 캐시가 있고 해당 연도 절기가
    있으면 각 행에 KASI 절입시각(KST)·Skyfield↔KASI 분차(diff_kasi_min)·kasi_ok를 추가.
    캐시 부재/연도 범위 밖이면 kasi_available=False로 2원 결과를 그대로 반환(폴백).

    허용(기본 2분) 초과 행은 KNOWN_KASI_TERM_DEFECTS(기지 KASI 원본오류)와 대조한다.
    - 기지 결함: kasi_defect_known=True로 표시, all_kasi_ok 실패로 치지 않음(문서화 완료분).
    - 미지 불일치: kasi_ok=False로 all_kasi_ok 실패 → 새 KASI 결함 후보(조사 필요).
    """
    base = _xc.crosscheck_year(year, tolerance_min=tolerance_min)
    base["mode"] = "2원(lunar↔Skyfield)"
    base["kasi_available"] = False

    if cache is None or not cache.exists:
        return base
    kst_terms = cache.solar_terms_kst(year)
    if not kst_terms:
        rng = cache.solar_term_years()
        base["kasi_note"] = (
            f"KASI 절기 미수록 연도(캐시 범위 {rng[0]}~{rng[1]})"
            if rng
            else "KASI 절기 캐시 비어있음"
        )
        return base

    base["mode"] = "3원(lunar↔Skyfield↔KASI)"
    base["kasi_available"] = True
    max_kasi = 0.0
    all_kasi_ok = True
    known_defects: list[str] = []
    unknown_mismatches: list[str] = []
    for r in base["rows"]:
        if "skyfield_kst" not in r:
            continue
        term = r["term"]
        kst_dt = kst_terms.get(term)
        if kst_dt is None:
            r["kasi_status"] = "kasi_missing"
            if (year, term) in KNOWN_KASI_TERM_DEFECTS:
                r["kasi_defect_known"] = True
                known_defects.append(f"{term}(missing)")
            else:
                unknown_mismatches.append(f"{term}(missing)")
                all_kasi_ok = False
            continue
        sky_kst = datetime.strptime(r["skyfield_kst"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=_KST)
        # KASI는 분 해상도(초 없음) → 비교 시 분차만 의미. 30초 반올림 영향 흡수.
        diff = abs((sky_kst - kst_dt).total_seconds()) / 60.0
        max_kasi = max(max_kasi, diff)
        within = diff <= kasi_tolerance_min
        r["kasi_kst"] = kst_dt.strftime("%Y-%m-%d %H:%M")
        r["diff_kasi_min"] = round(diff, 2)
        if within:
            r["kasi_ok"] = True
        elif (year, term) in KNOWN_KASI_TERM_DEFECTS:
            # 기지 KASI 원본오류 — 계산엔진(Skyfield+lunar) 일치, KASI만 어긋남. 차단 안 함.
            r["kasi_ok"] = True
            r["kasi_defect_known"] = True
            known_defects.append(f"{term}(+{round(diff, 1)}분)")
        else:
            r["kasi_ok"] = False
            unknown_mismatches.append(f"{term}(+{round(diff, 1)}분)")
            all_kasi_ok = False
    base["max_kasi_diff_min"] = round(max_kasi, 2)
    base["all_kasi_ok"] = all_kasi_ok  # 미지 불일치만 실패로 침(기지 결함 제외)
    base["kasi_known_defects"] = known_defects
    base["kasi_unknown_mismatches"] = unknown_mismatches
    return base
