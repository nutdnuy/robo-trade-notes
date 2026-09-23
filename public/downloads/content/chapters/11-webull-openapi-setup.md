# เริ่มต้นใช้ Webull OpenAPI ทีละขั้น

ก่อนให้ Python เรียกข้อมูลจาก Webull ต้องสมัคร OpenAPI สร้าง Key และยืนยัน Token ให้ครบ ส่วนข้อมูลราคาต้องตรวจสิทธิ์ Market Data เพิ่มด้วย เราจะตั้งค่าทีละส่วน แล้วลองอ่านรายการบัญชีเพื่อตรวจการเชื่อมต่อ

![ภาพประกอบแขนกลถือกุญแจแก้วเหนือสมุด พร้อมคำคม: เข้าใจก่อนเขียนโค้ด ทดสอบก่อนเทรดจริง](images/webull-openapi-setup/learning-before-automation.webp)

## เตรียมบัญชีและสิทธิ์ใช้งาน {#before-start}

เตรียมบัญชี Webull Thailand ที่พร้อมใช้งาน โทรศัพท์สำหรับยืนยันตัวตน และ Python บนเครื่อง หากยังไม่มีบัญชี ดู [ขั้นตอนเตรียมบัญชีในหน้า Welcome](#/welcome/webull-start)

สิทธิ์และข้อมูลที่ใช้เชื่อมต่อมีหน้าที่ต่างกัน ตรวจให้ครบทั้งสี่รายการ:

| สิ่งที่เตรียม | ใช้ทำอะไร | ตรวจที่ไหน |
| --- | --- | --- |
| สิทธิ์ OpenAPI | ให้แอปเข้าถึงบริการ API ตามขอบเขตที่ได้รับ | สถานะคำขอใน My Application |
| App Key / App Secret | ระบุแอปและใช้เซ็นคำขอ | API Keys Management หลังคำขออนุมัติ |
| สิทธิ์ Market Data สำหรับ OpenAPI | ให้แอปอ่านชุดข้อมูลตลาดที่เลือก | แพ็กเกจและสถานะใน OpenAPI Advanced Quotes |
| Access Token | ใช้ยืนยันตัวตนในการเรียก API | สถานะ Token หลังยืนยันในแอป |

Market Data API ใช้อ่านราคาและข้อมูลตลาด ส่วน Trading API มีทั้งการอ่านบัญชี ตรวจสถานะ และส่งหรือแก้ไขคำสั่งซื้อขาย แต่ละคำขอทำงานตาม endpoint ที่เรียก เช่น Account List ใช้อ่านรายการบัญชี การตรวจสิทธิ์ข้อมูลราคาจึงต้องเรียก endpoint ของ Market Data แยกอีกครั้ง

## ขั้นที่ 1: สมัคร OpenAPI และสร้าง Key {#create-key}

### 1.1 เข้า Developer Tool

เข้าสู่ระบบที่ [เว็บไซต์ Webull Thailand](https://www.webull.co.th/) เปิดเมนูบัญชีด้านขวาบน แล้วเลือก **Developer Tool**

[![เมนู Developer Tool ในเมนูบัญชี Webull](images/webull-openapi-setup/01-developer-tool.jpg)](images/webull-openapi-setup/01-developer-tool.jpg)

*ภาพ 1: เมนู Developer Tool แตะภาพเพื่อดูขนาดเต็ม*

### 1.2 ยื่นคำขอใช้งาน API

เข้า **API Management → My Application** เลือก **Apply for API Service** แล้วกรอกแบบฟอร์ม ต้องรอให้คำขออนุมัติก่อนจึงจะสร้าง App Key ได้

[![หน้า My Application และปุ่ม Apply for API Service](images/webull-openapi-setup/02-apply-for-api.jpg)](images/webull-openapi-setup/02-apply-for-api.jpg)

*ภาพ 2: แบบฟอร์มขอใช้ OpenAPI*

ติดตามผลใน My Application และอีเมล เอกสาร Webull ระบุว่ากรณีเร็วที่สุดใช้ประมาณ 1–2 วันทำการ ส่วนภาพคู่มือเดือนกรกฎาคมระบุ 1–3 วันทำการ ให้ยึดสถานะคำขอของบัญชีเป็นหลัก หากยังไม่อนุมัติให้สอบถาม Support ผ่านช่องทางในแอป [คู่มือสมัคร OpenAPI](https://developer.webull.co.th/apis/docs/authentication/individual-application/)

### 1.3 ลงทะเบียนแอป

เมื่อคำขออนุมัติแล้ว เข้า **API Management → API Keys Management** ตั้งชื่อแอปตามการใช้งาน เช่น `Robo Notes Learning`

[![แบบฟอร์มตั้งชื่อแอปสำหรับ API Key](images/webull-openapi-setup/03-register-app.jpg)](images/webull-openapi-setup/03-register-app.jpg)

*ภาพ 3: ลงทะเบียนแอปที่จะใช้เรียก API*

### 1.4 สร้างและเก็บ Key

เลือก **Generate Key / สร้าง Key** แล้วยืนยันตัวตนด้วยรหัส SMS และรหัสผ่านการซื้อขายบน Webull เมื่อสำเร็จจะได้ App Key และ App Secret

[![รายการแอปและปุ่มสร้าง Key](images/webull-openapi-setup/04-generate-key.jpg)](images/webull-openapi-setup/04-generate-key.jpg)

*ภาพ 4: ปุ่มสร้าง Key หลังลงทะเบียนแอป*

App Secret ใช้คำนวณลายเซ็นคำขอ โดย SDK ทางการจัดการขั้นตอนนี้ให้ เก็บ Key และ Secret แยกจากโค้ดที่เผยแพร่ อย่าส่ง App Secret เป็นค่าใน HTTP header โดยตรง หรือใส่ค่าจริงในภาพหน้าจอ GitHub และ Notebook ที่แชร์ [รายละเอียดการยืนยันตัวตน](https://developer.webull.co.th/apis/docs/authentication/overview/)

## ขั้นที่ 2: เปิดสิทธิ์ข้อมูลตลาดสำหรับ OpenAPI {#market-data}

หากหน้า API Keys แสดงลิงก์ **เรียนรู้เพิ่มเติมและสมัครใช้งาน** ใต้รายการแอป ให้เปิดลิงก์นั้นเพื่อไปหน้าบริการข้อมูลตลาด

[![ลิงก์สมัครใช้งานข้อมูลตลาดใต้รายการ API Keys](images/webull-openapi-setup/05-market-data-link.jpg)](images/webull-openapi-setup/05-market-data-link.jpg)

*ภาพ 5: ลิงก์ไปหน้าบริการข้อมูลตลาด*

อีกทางหนึ่งคือเปิดเมนูโปรไฟล์ **Advanced Quotes** บนเว็บไซต์ที่ระบุใน [คู่มือ Subscribe Advanced Quotes](https://developer.webull.co.th/apis/docs/market-data-api/subscribe-quotes/) แล้วเลือกแท็บ **OpenAPI Advanced Quotes** เพื่อตรวจบริการที่บัญชีมีสิทธิ์ใช้

[![แท็บ Open API Advanced Quotes และปุ่ม Claim ของ Nasdaq Basic](images/webull-openapi-setup/06-openapi-quotes.jpg)](images/webull-openapi-setup/06-openapi-quotes.jpg)

*ภาพ 6: ปุ่ม Claim ของ Nasdaq Basic และรายการแพ็กเกจ ณ กรกฎาคม 2026 ตรวจราคาและเงื่อนไขบน Webull อีกครั้งก่อนเลือก*

แพ็กเกจข้อมูลบนแอปมือถือหรือ Desktop แยกจากแพ็กเกจสำหรับ OpenAPI จึงต้องตรวจสิทธิ์ในแท็บนี้ด้วย หากมีปุ่ม Claim ให้รับสิทธิ์ตามเงื่อนไขของบัญชี หากเลือกบริการเสียเงินให้ตรวจค่าใช้จ่ายที่แสดงขณะสมัคร [รายละเอียดสิทธิ์ข้อมูลตลาด](https://developer.webull.co.th/apis/docs/market-data-api/faq/)

## ขั้นที่ 3: ติดตั้ง SDK และยืนยันตัวตน {#sdk-and-token}

SDK คือชุดโค้ดสำหรับเรียก API ที่ช่วยจัดการลายเซ็นคำขอและ Token ตัวอย่างต่อไปนี้ใช้ SDK ทางการของ Webull กับ Python 3.12 ซึ่งอยู่ในช่วงเวอร์ชันที่เอกสารรองรับ

[![คำสั่งติดตั้ง Webull Official SDK สำหรับ Python](images/webull-openapi-setup/07-install-sdk.jpg)](images/webull-openapi-setup/07-install-sdk.jpg)

*ภาพ 7: ชื่อแพ็กเกจ Python SDK ที่ใช้ติดตั้ง*

สร้าง virtual environment เพื่อแยกไลบรารีของงานนี้ออกจากงานอื่น บน macOS หรือ Linux ใช้คำสั่งต่อไปนี้:

```shell
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade webull-openapi-python-sdk
python -m pip show webull-openapi-python-sdk
```

บน Windows ใช้ `py -3.12 -m venv .venv` แล้วเปิด environment ด้วย `.venv\Scripts\Activate.ps1` ใน PowerShell หากติดตั้ง Python หลายรุ่น ให้ตรวจว่า `python -m pip` กับ Python ที่รันไฟล์อยู่ใน environment เดียวกัน จดเวอร์ชัน SDK ที่ติดตั้งไว้ด้วย เพราะ `--upgrade` อาจได้คนละเวอร์ชันเมื่อรันต่างวัน [SDKs and Tools](https://developer.webull.co.th/apis/docs/sdk/)

### เลือก environment ให้ตรงกับ Key

| Environment | HTTP host ของ Trading และ Market Data | ใช้เมื่อ |
| --- | --- | --- |
| Test / UAT | `th-api.uat.webullbroker.com` | ทดสอบการเชื่อมต่อด้วย credentials ของ test environment |
| Production | `api.webull.co.th` | ใช้บริการกับบัญชีจริงและ credentials ของ production |

เริ่มฝึกด้วย test environment และใช้ test credentials จาก [หน้า SDK ทางการ](https://developer.webull.co.th/apis/docs/sdk/#test-accounts) บัญชีทดสอบที่ Webull เผยแพร่เป็นบัญชีร่วม ข้อมูลจึงอาจเปลี่ยนเมื่อคนอื่นใช้งาน และต้องแยกจากข้อมูลพอร์ตของเรา

### ยืนยัน Token บนแอป Webull

SDK จัดการการสร้างและตรวจ Token ส่วนการยืนยันตัวตนใน production ต้องทำในแอป เมื่อมีคำขอให้ยืนยัน เปิด **Menu → Messages → OpenAPI Notifications** เลือกข้อความล่าสุด กด **Check Now** แล้วกรอกรหัส SMS ที่ Webull ส่งให้

[![ข้อความ OpenAPI ปุ่ม Check Now และหน้ากรอก SMS ในแอป Webull](images/webull-openapi-setup/08-verify-in-app.jpg)](images/webull-openapi-setup/08-verify-in-app.jpg)

*ภาพ 8: ขั้นตอนยืนยันตัวตนในแอป Webull*

Token เริ่มที่ `PENDING` และเปลี่ยนเป็น `NORMAL` หลังยืนยัน ต้องทำให้เสร็จภายใน 5 นาที มิฉะนั้นจะเป็น `EXPIRED` ส่วน Token ที่ไม่ได้ใช้งานต่อเนื่อง 15 วันอาจเป็น `INVALID` สำหรับ test environment ไม่ต้องทำ 2FA แบบ production [วงจรสถานะ Token](https://developer.webull.co.th/apis/docs/authentication/token/)

หาก SDK รุ่นที่ใช้บันทึก Token ลงไฟล์ เช่น `token.txt` ให้เก็บไฟล์นั้นเป็นข้อมูลลับด้วย ตรวจพฤติกรรมของรุ่นที่ติดตั้ง และตัดไฟล์ Token ออกจากชุดงานที่จะอัปโหลดหรือแชร์

## ทดลองครั้งแรก: อ่านรายการบัญชี {#first-call}

บันทึกโค้ดต่อไปนี้เป็น `verify_webull.py` แล้วรันใน environment ที่ติดตั้ง SDK ตัวอย่างปรับจากเอกสารทางการให้รับ Key แบบซ่อนการพิมพ์ และแสดงเฉพาะสถานะการตอบกลับ ข้อมูลบัญชีจะเก็บอยู่ในตัวแปร `payload` การเรียกครั้งนี้อาจเริ่มกระบวนการยืนยัน Token ของ SDK ด้วย

```python
from getpass import getpass
from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient

# Use credentials issued for the selected environment.
environment = input("Environment [test/production]: ").strip().lower()
hosts = {
    "test": "th-api.uat.webullbroker.com",
    "production": "api.webull.co.th",
}
if environment not in hosts:
    raise SystemExit("Choose test or production explicitly.")

app_key = getpass("App Key: ")
app_secret = getpass("App Secret: ")
if not app_key or not app_secret:
    raise SystemExit("Credentials are required.")

api_client = ApiClient(app_key, app_secret, "th")
api_client.add_endpoint("th", hosts[environment])
trade_client = TradeClient(api_client)

try:
    response = trade_client.account_v2.get_account_list()
    print("Environment:", environment)
    print("HTTP status:", response.status_code)
    if response.status_code == 200:
        payload = response.json()
        print("JSON received. Review the account list privately.")
    else:
        print("Check authentication, token status and API permissions.")
except Exception:
    raise SystemExit("Request failed. Inspect details locally; redact credentials before sharing.") from None
```

รันด้วย `python verify_webull.py` ถ้าได้ HTTP 200 และอ่าน JSON ได้ ให้ตรวจต่อว่า `payload` มีรายการบัญชีที่คาดไว้หรือไม่ หากรายการว่าง ให้กลับไปตรวจบัญชีและ environment ส่วนสิทธิ์ Market Data ต้องทดสอบด้วยคำขอข้อมูลราคาแยกต่างหาก [ตัวอย่าง Account List](https://developer.webull.co.th/apis/docs/trade-api/getting-started/)

หาก SDK แสดงข้อความให้ยืนยันตัวตน ให้ทำตามขั้นตอนบน Webull ก่อน ปกปิด Key, Secret, Token และข้อมูลบัญชีเมื่อต้องแชร์ log เพื่อขอความช่วยเหลือ

## อ่านข้อมูลราคาและประวัติคำสั่ง {#read-response}

### ตรวจราคาและเวลาใน Snapshot

[![ตัวอย่าง JSON จาก Snapshot API มี symbol ราคา bid ask และเวลา](images/webull-openapi-setup/09-snapshot-response.jpg)](images/webull-openapi-setup/09-snapshot-response.jpg)

*ภาพ 9: ตัวอย่าง Snapshot ในโพสต์เดือนกรกฎาคม 2026 ใช้ศึกษารูปแบบคำตอบ*

ค่า `price`, `bid`, `ask` และตัวเลขหลายช่องอาจมาเป็น string ต้องแปลงชนิดก่อนคำนวณ เวลา `last_trade_time` กับ `quote_time` ก็อาจต่างกัน จึงต้องอ่านเวลาควบคู่กับราคาเมื่อเปรียบเทียบราคาซื้อขายล่าสุดกับ bid/ask

ลองคำนวณส่วนต่าง ask − bid จาก JSON สมมตินี้ ราคามีหน่วย USD ต่อหุ้น และกำหนดขึ้นเพื่อฝึกคำนวณ:

```python
from decimal import Decimal

snapshot = {"symbol": "DEMO", "bid": "99.98", "ask": "100.02"}
bid = Decimal(snapshot["bid"])
ask = Decimal(snapshot["ask"])
spread = ask - bid
print(f"Spread: {spread:.2f} USD per share")
```

ผลคือ `Spread: 0.04 USD per share` ซึ่งเป็นส่วนต่างราคาเสนอซื้อกับเสนอขาย กำไรจากการซื้อขายจริงยังสรุปจากตัวเลขนี้ไม่ได้ เมื่อเรียกข้อมูลจริง ให้ตรวจ symbol หน่วย ตลาด เวลาอ้างอิง และความสดของข้อมูลตาม schema ของ endpoint ที่ใช้ด้วย สำหรับ Historical Bars ดู [คู่มือเริ่มอ่านข้อมูลตลาด](https://developer.webull.co.th/apis/docs/market-data-api/getting-started/)

### แยกเวลาส่งคำสั่งออกจากเวลาจับคู่

[![ประวัติ Order สถานะ FILLED จำนวนที่จับคู่ และเวลา โดยปิด ID บางส่วนไว้](images/webull-openapi-setup/10-order-history.jpg)](images/webull-openapi-setup/10-order-history.jpg)

*ภาพ 10: ตัวอย่างประวัติ Order โดยคงการปิด ID ตามภาพต้นฉบับ*

Order history ใช้อ่านคำสั่งที่ผ่านมา ฟิลด์ `place_time` บอกเวลาส่งคำสั่ง ส่วน `filled_time` บอกเวลาจับคู่ ตรวจจำนวนที่ขอใน `total_quantity` เทียบกับจำนวนที่จับคู่ใน `filled_quantity` ด้วย ภาพนี้ใช้ศึกษาฟิลด์ของคำตอบ คำขออ่านประวัติจะไม่ส่ง Order ใหม่

## ตรวจปัญหาตามอาการ {#troubleshooting}

| อาการ | เริ่มตรวจตรงไหน |
| --- | --- |
| `ModuleNotFoundError: webull` | Python ที่รันไฟล์กับ pip ที่ติดตั้ง SDK อยู่ใน environment เดียวกันหรือไม่ |
| ไม่เห็นปุ่มสร้าง Key | คำขอ OpenAPI อนุมัติแล้วหรือยัง และลงทะเบียนแอปครบหรือไม่ |
| Token ยัง `PENDING` | ข้อความ OpenAPI ในแอปและกรอบเวลายืนยัน 5 นาที |
| HTTP 403 เมื่อขอราคา | Authentication, Token และสิทธิ์ OpenAPI Market Data |
| อ่านรายการบัญชีได้ แต่ข้อมูลราคาไม่ได้ | สิทธิ์และผลตอบกลับของ endpoint ข้อมูลตลาดที่เรียก |
| ข้อมูลมาแต่เวลาไม่ตรง | หน่วย timestamp, timezone, trading session และเวลาของแต่ละฟิลด์ |

HTTP 403 เกิดได้หลายสาเหตุ เช่น header ไม่ครบ credentials ใช้ไม่ได้ หรือสิทธิ์ข้อมูลไม่เพียงพอ ตรวจรายละเอียดคำตอบประกอบก่อนเปลี่ยนการตั้งค่าหรือซื้อแพ็กเกจเพิ่ม [Market Data FAQ](https://developer.webull.co.th/apis/docs/market-data-api/faq/)

เมื่อติดต่อ Support ให้ระบุ environment, SDK version, ชื่อ endpoint, HTTP status และเวลาที่เกิดเหตุ ตัด Key, Secret, Token และข้อมูลระบุตัวบัญชีออกจากข้อความหรือภาพก่อนส่ง

## ลองฝึกแบบออฟไลน์ {#practice}

Notebook มี 5 ตัวอย่าง: เลือก host อ่านสถานะ Token คำนวณ spread จาก JSON จำลอง แปลงเวลา UTC และตรวจสิทธิ์อ่านบัญชีกับ Market Data ทุก cell ใช้ Python standard library รันได้โดยไม่ต้องเชื่อมต่อเครือข่ายหรือใช้ Key

ลองเปลี่ยน Token จาก `PENDING` เป็น `NORMAL` แล้วอธิบายว่าต้องผ่านขั้นตอนใดจึงจะเปลี่ยนสถานะนี้ได้ จากนั้นดูตัวอย่างที่ Account List ได้ HTTP 200 แต่สิทธิ์ Market Data ยังไม่พร้อม ระบุสิ่งที่ต้องตรวจเพิ่มก่อนเรียกราคา

[ดาวน์โหลด Notebook พร้อมผลรัน](downloads/robo-trade-11.ipynb) · [ดาวน์โหลด Python ออฟไลน์](downloads/lesson_11.py) · [ดาวน์โหลดต้นฉบับบทเรียน Markdown](downloads/content/chapters/11-webull-openapi-setup.md)

## ทบทวนความเข้าใจ {#quiz}

::: quiz
