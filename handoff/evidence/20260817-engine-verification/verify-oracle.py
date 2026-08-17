# -*- coding: utf-8 -*-
"""독립 오라클 — lunar-python/iztro 를 쓰지 않고 사주 4기둥을 자체 재도출.

원리(순수 산술, 라이브러리 무관):
- 일주: 그레고리력 -> JDN -> (JDN+49)%60. 앵커는 외부 확인 대상.
- 연주: 명리년=(입춘 이후 ? year : year-1), index=(명리년-4)%60.
- 월간: 五虎遁(연간->인월 천간). 월지: 절기 구간.
- 시주: 五鼠遁(일간->자시 천간) + 시지.
- 대운 방향: 양년남/음년여=순행.
절기 시각만 Skyfield(엔진과 공유)를 쓰므로, 절기는 별도 외부 대조 항목으로 분리한다.
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


def gz(n: int) -> str:
    """60갑자 index -> 간지 문자열."""
    return GAN[n % 10] + ZHI[n % 12]


def jdn(y: int, m: int, d: int) -> int:
    """그레고리력 -> 율리우스일수(정수, 정오 기준). 표준 공식 자체 구현."""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def day_index(y: int, m: int, d: int) -> int:
    """일주 60갑자 index. 앵커: 2000-01-01 = 戊午(54) -> (JDN+49)%60."""
    return (jdn(y, m, d) + 49) % 60


# 五虎遁: 연간 -> 인(寅)월 천간 index
WUHU = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}
# 五鼠遁: 일간 -> 자(子)시 천간 index
WUSHU = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}


def hour_branch_index(h: int) -> int:
    """진태양시 시각 -> 시지 index (23시부터 子)."""
    return ((h + 1) // 2) % 12


def main(cases):
    from sajugen.calc import solarterms  # 절기 시각만 공유(별도 외부 대조 대상)

    out = []
    for tag, y, mo, d, h, mi, male, true_solar in cases:
        ts = datetime.strptime(true_solar, "%Y-%m-%d %H:%M:%S")
        utc = datetime(y, mo, d, h, mi, tzinfo=ZoneInfo("Asia/Seoul")).astimezone(
            ZoneInfo("UTC")
        ).replace(tzinfo=None)

        # 연주: 입춘(황경 315도) 기준
        ipchun = solarterms.solar_term_time(utc.year, 315)
        myeongni_year = utc.year if utc >= ipchun else utc.year - 1
        y_idx = (myeongni_year - 4) % 60
        year_gz = gz(y_idx)

        # 월지: 절기 구간 (엔진과 동일 Skyfield 소스 — 외부 대조는 별도)
        mzhi, _, _ = solarterms.month_pillar_branch(utc)
        mzhi_i = ZHI.index(mzhi)
        # 월간 = 五虎遁: 인월 천간부터 월지 순번만큼 전진
        steps = (mzhi_i - 2) % 12
        month_gan_i = (WUHU[y_idx % 10] + steps) % 10
        month_gz = GAN[month_gan_i] + mzhi

        # 일주: 진태양시 날짜 + 자시정책(JST_2300: 진태양시 23시 이후 = 익일 일주)
        dy, dmo, dd = ts.year, ts.month, ts.day
        d_idx = day_index(dy, dmo, dd)
        if ts.hour >= 23:
            d_idx = (d_idx + 1) % 60
        day_gz = gz(d_idx)

        # 시주: 五鼠遁
        hb = hour_branch_index(ts.hour)
        hour_gan_i = (WUSHU[d_idx % 10] + hb) % 10
        hour_gz = GAN[hour_gan_i] + ZHI[hb]

        # 대운 방향: 양년(연간 index 짝수)남 / 음년여 = 순행
        yang_year = (y_idx % 10) % 2 == 0
        forward = (yang_year and male) or ((not yang_year) and (not male))

        out.append(
            {
                "tag": tag,
                "oracle_bazi": f"{year_gz} {month_gz} {day_gz} {hour_gz}",
                "oracle_daewoon_forward": forward,
                "myeongni_year": myeongni_year,
                "utc": utc.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return out


if __name__ == "__main__":
    src = json.loads(
        (Path(__file__).with_name("_verify_out.json")).read_text(encoding="utf-8")
    )
    cases = []
    for r in src:
        inp = r["input"]
        date_s, time_s, _, g = inp.split()
        y, mo, d = (int(x) for x in date_s.split("-"))
        h, mi = (int(x) for x in time_s.split(":"))
        cases.append((r["tag"], y, mo, d, h, mi, g == "남", r["true_solar"]))
    res = main(cases)
    # 대조
    rows = []
    for r, o in zip(src, res):
        rows.append(
            {
                "tag": r["tag"],
                "input": r["input"],
                "engine": r["bazi"],
                "oracle": o["oracle_bazi"],
                "bazi_match": r["bazi"] == o["oracle_bazi"],
                "engine_forward": r["daewoon_forward"],
                "oracle_forward": o["oracle_daewoon_forward"],
                "forward_match": r["daewoon_forward"] == o["oracle_daewoon_forward"],
                "utc": o["utc"],
                "true_solar": r["true_solar"],
                "eot_min": r["eot_min"],
            }
        )
    Path(__file__).with_name("_oracle_out.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    ok = sum(1 for x in rows if x["bazi_match"])
    okf = sum(1 for x in rows if x["forward_match"])
    print("bazi_match %d/%d  forward_match %d/%d" % (ok, len(rows), okf, len(rows)))
