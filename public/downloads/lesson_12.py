# -*- coding: utf-8 -*-
# Why Robo Trade: แบบฝึกออฟไลน์จากข้อมูลสมมติ
# รันด้วย Python 3 โดยไม่ต้องติดตั้งแพ็กเกจเพิ่ม


# # Why Robo Trade — เขียนกฎให้หุ่นอ่านรู้เรื่อง
#
# แบบฝึกออฟไลน์ในโรงช่าง Deltaris: หุ่นเสนอซื้ออะไหล่ทองเหลืองตามกฎที่ช่างเขียนไว้ ทุกตัวเลขเป็นข้อมูลสมมติ ไม่มีข้อมูลตลาด ไม่มีการเชื่อมต่อบัญชี และไม่มีการส่งคำสั่งซื้อขาย
#
# เราจะตรวจว่ากฎให้ข้อเสนอที่สอดคล้องกันหรือไม่ การผ่านแบบฝึกนี้ไม่ได้พิสูจน์ว่ากฎทำกำไรได้
#
# **กติกา**: ราคาอะไหล่มากกว่า 0 และไม่เกิน 100 หน่วยราคาต่อชิ้น อายุราคาไม่เกิน 60 วินาที และจำนวนที่ถือรวมข้อเสนอต้องไม่เกิน 10 ชิ้น เมื่อผ่านทุกเงื่อนไข ให้เสนอจำนวนเท่ากับพื้นที่ที่เหลือจนถึงเพดาน ข้อมูลราคาและอายุต้องเป็นตัวเลขจำกัด; จำนวนที่ถือต้องเป็นจำนวนเต็มตั้งแต่ 0 ถึง 10 ข้อมูลผิดรูปแบบหรือเก่าเกินไปให้ `HALT` พร้อมจำนวน 0
#
# `PROPOSE_BUY` คือข้อเสนอที่ฟังก์ชันคืนค่าไว้ให้อ่าน ยังไม่ใช่คำสั่งที่ส่งไปที่ใด `HOLD` หมายถึงไม่มีข้อเสนอใหม่

# ## 1. กำหนดหน่วยและเกณฑ์
#
# เกณฑ์ 100, 60 และ 10 ใช้ฝึกเขียนเงื่อนไข ไม่มีการเลือกจากผลตอบแทนย้อนหลัง

from math import isfinite
from decimal import Decimal

# อะไหล่ทองเหลืองและหน่วยราคาในแบบฝึกนี้เป็นสิ่งสมมติ
PRICE_LIMIT = 100
MAX_QUOTE_AGE = 60  # วินาที
MAX_HELD = 10      # ชิ้น
print(f"ราคาไม่เกิน {PRICE_LIMIT}; อายุราคาไม่เกิน {MAX_QUOTE_AGE} วินาที; ถือได้ไม่เกิน {MAX_HELD} ชิ้น")


# ## 2. เขียนฟังก์ชันตัดสินใจ
#
# ราคา 0 และราคาติดลบถือเป็นข้อมูลใช้ไม่ได้ในแบบฝึกนี้ ตรวจข้อมูลก่อนตรวจราคาเข้าเกณฑ์ เพื่อไม่ให้ข้อมูลเก่าหรือข้อมูลเสียกลายเป็นข้อเสนอซื้อ

def propose_brass_purchase(price, quote_age_seconds, held):
    """คืนข้อเสนอจากข้อมูลสมมติเท่านั้น ไม่มีการส่งคำสั่งหรือเรียก API."""
    def finite_number(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)

    if not finite_number(price) or price <= 0:
        return {"action": "HALT", "reason": "invalid_price", "quantity": 0}
    if not finite_number(quote_age_seconds) or quote_age_seconds < 0:
        return {"action": "HALT", "reason": "invalid_quote_age", "quantity": 0}
    if not isinstance(held, int) or isinstance(held, bool) or not 0 <= held <= MAX_HELD:
        return {"action": "HALT", "reason": "invalid_held", "quantity": 0}
    if quote_age_seconds > MAX_QUOTE_AGE:
        return {"action": "HALT", "reason": "stale_quote", "quantity": 0}
    if held == MAX_HELD:
        return {"action": "HOLD", "reason": "at_capacity", "quantity": 0}
    if price > PRICE_LIMIT:
        return {"action": "HOLD", "reason": "price_above_limit", "quantity": 0}
    return {"action": "PROPOSE_BUY", "reason": "rule_met", "quantity": MAX_HELD - held}

print(propose_brass_purchase(price=100, quote_age_seconds=60, held=8))


# ## 3. อ่านเหตุผลทีละกรณี
#
# ลองทาย action, quantity และ reason ก่อนรัน แล้วเทียบคำตอบกับผลลัพธ์

scenarios = [
    ("เข้าเงื่อนไข", 99, 10, 0),
    ("เหลือที่ว่างสองชิ้น", 100, 60, 8),
    ("ราคาเกินเกณฑ์", 101, 10, 0),
    ("ราคาเก่าเกินไป", 99, 61, 0),
    ("ถือเต็มแล้ว", 99, 10, 10),
    ("ราคาหายไป", None, 10, 0),
]
for label, price, age, held in scenarios:
    result = propose_brass_purchase(price, age, held)
    print(f"{label}: {result['action']}, quantity={result['quantity']}, reason={result['reason']}")


# ## 4. ตรวจขอบเขตและข้อมูลผิดรูปแบบ
#
# ถ้าเงื่อนไขตรวจไม่ผ่าน Python จะหยุดที่ `AssertionError` การทดสอบครอบคลุมกฎที่ตั้งไว้ในแบบฝึก ไม่ได้ครอบคลุมปัญหาของระบบซื้อขายจริงทุกชนิด

# จุดขอบของกฎเป็นส่วนหนึ่งของสัญญา: 100 และ 60 ยังผ่าน
assert propose_brass_purchase(100, 60, 8) == {
    "action": "PROPOSE_BUY", "reason": "rule_met", "quantity": 2
}
assert propose_brass_purchase(100.01, 60, 8)["action"] == "HOLD"
assert propose_brass_purchase(100, 60.01, 8)["reason"] == "stale_quote"
assert propose_brass_purchase(99, 10, 10)["quantity"] == 0

for invalid_price in (None, float("nan"), float("inf"), -1, 0, "99", True):
    assert propose_brass_purchase(invalid_price, 10, 0)["action"] == "HALT"
for invalid_age in (None, float("nan"), float("inf"), -1, "10", True):
    assert propose_brass_purchase(99, invalid_age, 0)["action"] == "HALT"
for invalid_held in (None, -1, 11, 2.5, True):
    assert propose_brass_purchase(99, 10, invalid_held)["action"] == "HALT"

# ตรวจเพดานทุกสถานะที่ถูกต้อง และตรวจว่าข้อมูลเดิมให้ข้อเสนอเดิม
for held in range(MAX_HELD + 1):
    result = propose_brass_purchase(99, 10, held)
    assert held + result["quantity"] <= MAX_HELD
    assert result == propose_brass_purchase(99, 10, held)
print("PASS: boundary values, invalid data, capacity, and repeatability")


# ## 5. นับต้นทุนให้ครบสองขา
#
# สมมติราคาที่ใช้อ้างอิงเปลี่ยนจาก 100 เป็น 101 จำนวน 10 ชิ้น ส่วนต่างก่อนต้นทุนคือ 10 หน่วยราคา กำหนดค่าธรรมเนียม 0.10 และ slippage 0.05 หน่วยราคาต่อชิ้นต่อขา จึงต้องคูณ 2 ทั้งคู่ เมื่อใช้ค่าตั้งต้นนี้จะได้ส่วนต่างหลังต้นทุน 7 หน่วยราคา
#
# ในตัวอย่างนี้ slippage หมายถึงต้นทุนจากราคาที่ได้แย่กว่าราคาอ้างอิง การคำนวณนี้แยกจากฟังก์ชันข้อเสนอด้านบน ยังไม่ได้สร้างกฎขายหรือจำลองเส้นทางราคา ค่าใช้จ่ายทั้งหมดกำหนดขึ้นเพื่อฝึกเลข ไม่ใช่อัตราค่าธรรมเนียมหรือผลการซื้อขายของ Webull หรือโบรกเกอร์ใด

# ตัวอย่างต้นทุนที่กำหนดขึ้นเพื่อฝึกคำนวณ ไม่ใช่อัตราของโบรกเกอร์ใด
entry_reference = Decimal("100")
exit_reference = Decimal("101")
quantity = 10
commission_per_unit_per_side = Decimal("0.10")
slippage_per_unit_per_side = Decimal("0.05")

gross = (exit_reference - entry_reference) * quantity
commission = commission_per_unit_per_side * quantity * 2
slippage = slippage_per_unit_per_side * quantity * 2
net = gross - commission - slippage
print(f"ส่วนต่างราคาก่อนต้นทุน = {gross:.2f} หน่วยราคา")
print(f"ค่าธรรมเนียมสองขา = {commission:.2f}; slippage สองขา = {slippage:.2f}")
print(f"ส่วนต่างหลังต้นทุนสมมติ = {net:.2f} หน่วยราคา")


# ## 6. เปลี่ยนทีละอย่าง
#
# เปลี่ยนอายุราคาจาก 60 เป็น 61 วินาที แล้วคืนค่าเดิมก่อนเปลี่ยนจำนวนที่ถือจาก 8 เป็น 9 ชิ้น สังเกตว่าเหตุผลและจำนวนเปลี่ยนจากตัวแปรใด

# เปลี่ยนทีละตัวเพื่อแยกสาเหตุของข้อเสนอ
baseline = propose_brass_purchase(price=100, quote_age_seconds=60, held=8)
older_quote = propose_brass_purchase(price=100, quote_age_seconds=61, held=8)
more_held = propose_brass_purchase(price=100, quote_age_seconds=60, held=9)
print("เดิม:", baseline)
print("เพิ่มอายุราคา 1 วินาที:", older_quote)
print("เพิ่มจำนวนที่ถือ 1 ชิ้น:", more_held)
assert older_quote["action"] == "HALT"
assert more_held["quantity"] == 1


# ## ลองเขียนคำตอบก่อนแก้โค้ด
#
# 1. ถ้าถืออยู่ 9 ชิ้น ราคา 100 และอายุราคา 60 วินาที หุ่นควรเสนออีกกี่ชิ้น เพราะอะไร?
# 2. ถ้าราคาลดเป็น 90 แต่อายุราคา 61 วินาที ข้อเสนอควรเปลี่ยนหรือไม่?
# 3. ถ้าเปลี่ยนเครื่องหมาย `<=` เป็น `<` โดยไม่ได้บอกผู้อ่าน กรณีขอบใดจะให้คำตอบต่างจากเดิม?
# 4. ถ้า slippage สมมติเพิ่มเป็น 0.15 ต่อชิ้นต่อขา ส่วนต่างหลังต้นทุนเหลือเท่าไร? แก้เฉพาะค่าตัวนี้และรันเซลล์ต้นทุนอีกครั้ง
#
# ก่อนเพิ่มเงื่อนไขใหม่ เขียนให้ได้ว่าข้อมูลเข้า หน่วย เกณฑ์ และกรณีที่ต้องหยุดคืออะไร การทำให้แต่ละคำตอบตรวจสอบได้คือสิ่งที่กำลังฝึกในบทนี้

# ## 7. ชนะตลาด 2 จุดร้อยละ แต่เทียบกับความเสี่ยงแบบใด?
#
# กำหนดตัวเลขสมมติสำหรับช่วงเวลาเดียวกัน: พอร์ตให้ผลตอบแทนที่เกิดขึ้นแล้ว 12% ตลาดให้ 10% อัตราปลอดความเสี่ยง 2% และ **สมมติ** beta ของพอร์ตเท่ากับ 1.5 เราหาผลต่างสองแบบ:
#
# - ผลตอบแทนพอร์ตลบตลาด: 12% − 10% = 2 จุดร้อยละ
# - เกณฑ์จากแบบจำลอง: 2% + 1.5 × (10% − 2%) = 14% พอร์ตจึงต่ำกว่าเกณฑ์นี้ 2 จุดร้อยละ
#
# Beta บอกความไวของผลตอบแทนส่วนเกินพอร์ตต่อผลตอบแทนส่วนเกินตลาดในแบบจำลอง ค่า 1.5 ไม่มีหน่วยและไม่ใช่ผลตอบแทน 1.5% ในที่นี้กำหนดขึ้นมาเพื่อฝึกคำนวณ ยังไม่ได้ประมาณ beta จากข้อมูล
#
# ส่วนต่างจากฐานแบบจำลอง −2 จุดร้อยละมาจากการนำผลตอบแทนของช่วงเดียวไปเทียบกับเกณฑ์ที่คำนวณจากผลตอบแทนตลาดช่วงนั้น จึงยังไม่ใช่การประมาณ alpha จาก regression และใช้พิสูจน์ฝีมือไม่ได้ การประมาณ regression ต้องใช้ข้อมูลหลายช่วง พร้อมตรวจแบบจำลองและความไม่แน่นอนของค่าที่ประมาณ
#
# ลองเปลี่ยน `assumed_beta` จาก 1.5 เป็น 1 เกณฑ์จะเปลี่ยนเป็น 10% และส่วนต่างจากฐานแบบจำลองเป็น +2 จุดร้อยละ โดยผลตอบแทนพอร์ตและตลาดยังเท่าเดิม

def compare_one_period(portfolio_return, market_return, risk_free_rate, beta):
    """เลขสมมติหนึ่งช่วง: ผลต่างจากตลาด, เกณฑ์แบบจำลอง, ส่วนต่างจากฐานแบบจำลอง."""
    raw_outperformance = portfolio_return - market_return
    model_baseline = risk_free_rate + beta * (market_return - risk_free_rate)
    one_period_residual = portfolio_return - model_baseline
    return raw_outperformance, model_baseline, one_period_residual

# ตรวจกรณีอ้างอิงคงที่แยกจากค่าที่ผู้เรียนจะเปลี่ยนด้านล่าง
assert compare_one_period(Decimal("0.12"), Decimal("0.10"), Decimal("0.02"), Decimal("1.5")) == (
    Decimal("0.02"), Decimal("0.14"), Decimal("-0.02")
)
assert compare_one_period(Decimal("0.12"), Decimal("0.10"), Decimal("0.02"), Decimal("1")) == (
    Decimal("0.02"), Decimal("0.10"), Decimal("0.02")
)

portfolio_return = Decimal("0.12")
market_return = Decimal("0.10")
risk_free_rate = Decimal("0.02")
assumed_beta = Decimal("1.5")
raw_outperformance, model_baseline, one_period_residual = compare_one_period(
    portfolio_return, market_return, risk_free_rate, assumed_beta
)
print(f"ผลตอบแทนพอร์ตลบตลาด = {raw_outperformance * 100:+.2f} จุดร้อยละ")
print(f"เกณฑ์แบบจำลองเมื่อสมมติ beta = {assumed_beta} คือ {model_baseline * 100:.2f}%")
print(f"ส่วนต่างจากฐานแบบจำลองหนึ่งช่วง = {one_period_residual * 100:+.2f} จุดร้อยละ")
print("ส่วนต่างจากฐานแบบจำลองนี้ยังไม่ใช่การประมาณ regression alpha หรือหลักฐานพิสูจน์ฝีมือ")


# ## 8. ผสมค่าพยากรณ์ที่วัดสิ่งเดียวกัน
#
# ช่างสองคนใน Deltaris ส่งค่าพยากรณ์ผลตอบแทนของสินทรัพย์สมมติชิ้นเดียวกันสำหรับ **สัปดาห์หน้า** คนแรกให้ +0.6% คนที่สองให้ −0.2% เมื่อให้น้ำหนักคนละ 50% ค่าเฉลี่ยถ่วงน้ำหนักเท่ากับ +0.2%
#
# ทั้งสองสัญญาณต้องมีหน่วย ฐานราคา ช่วงเวลาเป้าหมาย และเวลาที่ใช้ข้อมูลสอดคล้องกัน จึงนำมาผสมแบบนี้ได้ ตัวอย่างนี้ใช้ค่าพยากรณ์ผลตอบแทนโดยตรง ถ้าเป็นคะแนนที่ไม่มีหน่วยผลตอบแทน ต้องกำหนดวิธีแปลงก่อน การเฉลี่ยคะแนนไม่ได้ทำให้คะแนนกลายเป็นเปอร์เซ็นต์ผลตอบแทน
#
# +0.2% เป็นค่าพยากรณ์ก่อนต้นทุน ผลตอบแทนที่เกิดขึ้นจริงอาจต่างออกไป และตัวเลขนี้ยังไม่ระบุจำนวนที่จะซื้อ พอร์ตเดิม ข้อจำกัดความเสี่ยง และต้นทุนซื้อขายต้องเข้าสู่ขั้นตอนตัดสินใจด้วย
#
# ลองเปลี่ยน `weight_a` เป็น 0.75 อีกน้ำหนักจะลดเป็น 0.25 และค่าพยากรณ์รวมจะเป็น +0.4% น้ำหนักที่เพิ่มขึ้นเพียงทำให้ค่าเฉลี่ยใกล้คนแรกมากขึ้น ยังไม่มีการทดสอบว่าคนแรกพยากรณ์แม่นกว่า

def blend_same_horizon_forecasts(forecasts, weights):
    """ผสม Decimal ที่เป็นผลตอบแทนพยากรณ์ของสินทรัพย์และช่วงเวลาเดียวกัน."""
    if not forecasts or len(forecasts) != len(weights):
        raise ValueError("ต้องมีค่าพยากรณ์และน้ำหนักจำนวนเท่ากัน")
    if any(not x.is_finite() for x in forecasts + weights):
        raise ValueError("ค่าพยากรณ์และน้ำหนักต้องเป็นตัวเลขจำกัด")
    if any(w < 0 for w in weights) or sum(weights) != Decimal("1"):
        raise ValueError("แบบฝึกนี้ใช้น้ำหนักไม่ติดลบและรวมเท่ากับ 1")
    return sum((forecast * weight for forecast, weight in zip(forecasts, weights)), Decimal("0"))

# กรณีอ้างอิงคงที่ตรวจการคำนวณ โดยไม่ผูกกับน้ำหนักที่แก้ด้านล่าง
assert blend_same_horizon_forecasts(
    [Decimal("0.006"), Decimal("-0.002")], [Decimal("0.5"), Decimal("0.5")]
) == Decimal("0.002")
assert blend_same_horizon_forecasts(
    [Decimal("0.006"), Decimal("-0.002")], [Decimal("0.75"), Decimal("0.25")]
) == Decimal("0.004")

next_week_forecasts = [Decimal("0.006"), Decimal("-0.002")]
weight_a = Decimal("0.5")
weight_b = Decimal("1") - weight_a
combined_forecast = blend_same_horizon_forecasts(next_week_forecasts, [weight_a, weight_b])
print(f"น้ำหนักสองสัญญาณ = {weight_a * 100:.0f}% / {weight_b * 100:.0f}%")
print(f"ค่าพยากรณ์ผลตอบแทนสัปดาห์หน้ารวม = {combined_forecast * 100:+.2f}% ก่อนต้นทุน")
print("ยังไม่มีผลตอบแทนจริง และยังไม่ได้สร้างหรือส่งคำสั่งซื้อขาย")


# ## ลองอธิบายผลโดยไม่ดูตัวเลขอย่างเดียว
#
# 1. พอร์ตได้ 12% มากกว่าตลาด 10% เหตุใดการเปลี่ยน beta ที่สมมติจึงเปลี่ยนส่วนต่างจากฐานแบบจำลองได้?
# 2. ต้องมีข้อมูลและการตรวจอะไรเพิ่ม ก่อนเรียกค่าที่ประมาณจาก regression ว่า alpha ที่เชื่อถือได้?
# 3. ถ้าสัญญาณแรกทำนายสัปดาห์หน้า แต่สัญญาณที่สองทำนายปีหน้า จะนำมาเฉลี่ย 50/50 เหมือนตัวอย่างได้หรือไม่?
# 4. ถ้าพอร์ตถือสินทรัพย์นี้ถึงเพดานแล้ว ค่าพยากรณ์ +0.2% เพียงตัวเดียวตอบได้หรือไม่ว่าควรเพิ่มอีกกี่หน่วย?
#
# เขียนคำตอบแต่ละข้อให้ระบุข้อมูลที่ขาดหรือสมมติฐานที่ใช้ แล้วจึงแก้ค่าทีละตัวในเซลล์ที่เกี่ยวข้อง
