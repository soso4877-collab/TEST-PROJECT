# -*- coding: utf-8 -*-
"""자미두수 독립 오라클 — iztro 를 쓰지 않고 고전 공식으로 재도출.

공식(전통 排盤訣):
- 命宮 = 寅起正月 順數至生月, 該宮起子時 逆數至生時
        -> 지지 index = (2 + (음력월-1) - 시지index) mod 12
- 身宮 = 寅起正月 順數至生月, 該宮起子時 順數至生時
        -> 지지 index = (2 + (음력월-1) + 시지index) mod 12
- 五行局 = 命宮 간지의 納音五行 (命宮 천간은 五虎遁으로 연간에서 도출)
- 紫微 위치 = 起紫微訣: n=최소정수(局數*n >= 生日), 差=局數*n-生日,
        差 짝수면 寅+(n-1)+差, 홀수면 寅+(n-1)-差 (順數)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
KZHI = "자축인묘진사오미신유술해"
WUHU = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}

# 60납음 오행 (30쌍 순서) — 표준 納音表
NAYIN30 = list("金火木土金火水土金木水土火木水金火木土金火水土金木水土火木水")
JU = {"水": "水二局", "木": "木三局", "金": "金四局", "土": "土五局", "火": "火六局"}
JUNUM = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}


def nayin_elem(gz_idx: int) -> str:
    return NAYIN30[gz_idx // 2]


def soul_body(lunar_month: int, hour_zhi_idx: int):
    s = (2 + (lunar_month - 1) - hour_zhi_idx) % 12
    b = (2 + (lunar_month - 1) + hour_zhi_idx) % 12
    return s, b


def five_class(year_gan_idx: int, soul_zhi_idx: int):
    """命宮 천간 = 五虎遁(연간->寅궁천간)에서 順行. 命宮 간지 납음 -> 국."""
    steps = (soul_zhi_idx - 2) % 12
    gan_i = (WUHU[year_gan_idx] + steps) % 10
    # 60갑자 index 복원
    for n in range(60):
        if n % 10 == gan_i and n % 12 == soul_zhi_idx:
            gz = n
            break
    e = nayin_elem(gz)
    return GAN[gan_i] + ZHI[soul_zhi_idx], JU[e], JUNUM[e]


def ziwei_pos(ju_num: int, lunar_day: int) -> int:
    n = -(-lunar_day // ju_num)  # ceil
    diff = ju_num * n - lunar_day
    if diff % 2 == 0:
        return (2 + (n - 1) + diff) % 12
    return (2 + (n - 1) - diff) % 12


def han_lunar_to_nums(s: str):
    """iztro 한자 음력 문자열 -> (월, 일, 윤달여부). 예 '二〇一四年七月十七'."""
    body = s.split("年", 1)[1]
    leap = body.startswith("闰")
    if leap:
        body = body[1:]
    mon_s, day_s = body.split("月", 1)
    MON = {
        "正": 1, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
        "七": 7, "八": 8, "九": 9, "十": 10, "冬": 11, "腊": 12,
    }
    m = 12 if mon_s == "腊" else (11 if mon_s == "冬" else None)
    if m is None:
        m = 10 if mon_s == "十" else (
            10 + MON[mon_s[1]] if mon_s.startswith("十") else MON[mon_s]
        )
    DIG = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    if day_s.startswith("初"):
        d = DIG[day_s[1]]
    elif day_s.startswith("廿"):
        d = 20 + (DIG[day_s[1]] if len(day_s) > 1 else 0)
    elif day_s.startswith("三十"):
        d = 30
    elif day_s.startswith("十"):
        d = 10 + (DIG[day_s[1]] if len(day_s) > 1 else 0)
    elif day_s.startswith("二十"):
        d = 20 + (DIG[day_s[2]] if len(day_s) > 2 else 0)
    else:
        d = DIG[day_s]
    return m, d, leap


if __name__ == "__main__":
    from datetime import datetime

    from sajugen.calc import engine  # noqa: E402

    src = json.loads(Path("tmp/_verify_out.json").read_text(encoding="utf-8"))
    rows = []
    for r in src:
        date_s, time_s, _, g = r["input"].split()
        y, mo, d = (int(x) for x in date_s.split("-"))
        h, mi = (int(x) for x in time_s.split(":"))
        res = engine.build(y, mo, d, h, mi, is_male=(g == "남"), horoscope_date="2026-06-01")
        zw = res.ziwei
        ts = datetime.strptime(res.true_solar, "%Y-%m-%d %H:%M:%S")
        hb = ((ts.hour + 1) // 2) % 12  # 시지 index (23시=子)
        lm, ld, leap = han_lunar_to_nums(zw.lunar_date)
        # 자미 윤달 정책: 15일 분할법(1~15 본월, 16~ 익월) — 절대규칙 5
        eff_m = lm + 1 if (leap and ld >= 16) else lm
        s_i, b_i = soul_body(eff_m, hb)
        ygan = GAN.index(res.myeongni.year.ganzhi[0])
        soul_gz, ju, junum = five_class(ygan, s_i)
        zpos = ziwei_pos(junum, ld)

        eng_soul = next((p.branch for p in zw.palaces if p.is_soul), "")
        eng_body = next((p.branch for p in zw.palaces if p.is_body), "")
        eng_zw_pos = next(
            (p.branch for p in zw.palaces for st in p.major_stars if st.name == "자미"), ""
        )
        rows.append(
            {
                "tag": r["tag"],
                "input": r["input"],
                "lunar": f"{'윤' if leap else ''}{lm}월 {ld}일 (적용월 {eff_m})",
                "hour_zhi": KZHI[hb],
                "soul_engine": eng_soul,
                "soul_oracle": KZHI[s_i],
                "soul_ok": eng_soul == KZHI[s_i],
                "body_engine": eng_body,
                "body_oracle": KZHI[b_i],
                "body_ok": eng_body == KZHI[b_i],
                "class_engine": zw.five_elements_class,
                "class_oracle": ju,
                "class_ok": zw.five_elements_class == ju,
                "soul_palace_gz": soul_gz,
                "ziwei_engine": eng_zw_pos,
                "ziwei_oracle": KZHI[zpos],
                "ziwei_ok": eng_zw_pos == KZHI[zpos],
            }
        )
    Path("tmp/_ziwei_oracle.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    for k in ("soul_ok", "body_ok", "class_ok", "ziwei_ok"):
        print(k, sum(1 for x in rows if x[k]), "/", len(rows))
