# -*- coding: utf-8 -*-
"""KASI 캐시(외부 원본: 한국천문연구원) 전수 대조.

목적 3가지:
1. 내 JDN 오라클((JDN+49)%60)이 KASI 일진과 1900~2050 전 구간 일치하는가
   -> 일주 앵커의 외부 확정. 라이브러리 무관 순수 산술 vs 외부 기관 데이터.
2. KASI 'wolgeon'(월건)의 정의가 절기월인가 음력월인가 -> 대조 가능 여부 판정.
3. KASI 원본 결측(빈 값) 규모 측정.
"""
import json
import sqlite3
from pathlib import Path

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
KGAN = "갑을병정무기경신임계"
KZHI = "자축인묘진사오미신유술해"


def jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def k2idx(s):
    """'을묘(乙卯)' -> 60갑자 index. 한글부만 사용."""
    if not s or "(" not in s:
        return None
    k = s.split("(")[0].strip()
    if len(k) != 2 or k[0] not in KGAN or k[1] not in KZHI:
        return None
    g, z = KGAN.index(k[0]), KZHI.index(k[1])
    for n in range(60):
        if n % 10 == g and n % 12 == z:
            return n
    return None


# 五虎遁: 연간 index -> 인월 천간 index
WUHU = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}

c = sqlite3.connect("data/kasi_cache.sqlite")
rows = c.execute(
    "select sol_ymd,lun_year,lun_month,lun_day,leap,secha,wolgeon,iljin from lunar order by sol_ymd"
).fetchall()

n = len(rows)
iljin_ok = iljin_bad = iljin_missing = 0
bad_samples = []
wolgeon_missing = 0
secha_missing = 0
# 월건 정의 판정: 음력월 간지 가설과의 일치율
wg_lunar_hit = wg_total = 0

for sol, ly, lm, ld, leap, secha, wolgeon, iljin in rows:
    s = str(sol)
    y, m, d = int(s[:4]), int(s[4:6]), int(s[6:])
    mine = (jdn(y, m, d) + 49) % 60
    ki = k2idx(iljin)
    if ki is None:
        iljin_missing += 1
    elif ki == mine:
        iljin_ok += 1
    else:
        iljin_bad += 1
        if len(bad_samples) < 10:
            bad_samples.append(
                {"date": s, "kasi": iljin, "oracle": GAN[mine % 10] + ZHI[mine % 12]}
            )

    si = k2idx(secha)
    if si is None:
        secha_missing += 1
    wi = k2idx(wolgeon)
    if wi is None:
        wolgeon_missing += 1
        continue
    # 가설: wolgeon = 음력월 간지 (음력 1월=寅). 연간은 secha(음력 연간지) 기준.
    if si is not None and 1 <= lm <= 12:
        zhi_i = (lm + 1) % 12  # 음력1월->寅(2)
        gan_i = (WUHU[si % 10] + (lm - 1)) % 10
        wg_total += 1
        if gan_i == wi % 10 and zhi_i == wi % 12:
            wg_lunar_hit += 1

out = {
    "rows": n,
    "date_range": [str(rows[0][0]), str(rows[-1][0])],
    "iljin_match_vs_JDN_oracle": iljin_ok,
    "iljin_mismatch": iljin_bad,
    "iljin_missing_or_unparsed": iljin_missing,
    "iljin_mismatch_samples": bad_samples,
    "secha_missing": secha_missing,
    "wolgeon_missing": wolgeon_missing,
    "wolgeon_lunar_month_hypothesis": f"{wg_lunar_hit}/{wg_total}",
}
Path("tmp/_kasi_wide.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
)
print(json.dumps({k: v for k, v in out.items() if k != "iljin_mismatch_samples"}, ensure_ascii=True))
