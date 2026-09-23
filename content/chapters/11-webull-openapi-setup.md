# เริ่มต้นใช้ Webull OpenAPI ทีละขั้น

มีบัญชี Webull แล้ว ทำอย่างไรให้ Python เรียกข้อมูลได้? บทนี้พาอ่านภาพจาก Webull API Builders Club ทีละขั้น ตั้งแต่สมัคร OpenAPI สร้าง App Key / App Secret เปิดสิทธิ์ข้อมูลตลาด ไปจนถึงยืนยันตัวตนและตรวจคำตอบจาก API

## ก่อนเริ่ม: เรากำลังเปิดสิทธิ์อะไร {#before-start}

เป้าหมายแรกคือ **เรียกข้อมูลได้และอธิบายได้ว่าคำตอบนั้นหมายถึงอะไร** ยังไม่จำเป็นต้องเริ่มจากการส่งคำสั่งซื้อขาย เตรียมบัญชี Webull Thailand ที่พร้อมใช้งาน โทรศัพท์สำหรับยืนยันตัวตน และ Python บนเครื่องของตัวเอง หากยังไม่มีบัญชี ดู [ขั้นตอนเตรียมบัญชีในหน้า Welcome](#/welcome/webull-start)

ภาพในบทคัดเฉพาะส่วนจากโพสต์ของ **Nonthawat Laonan ใน Webull API Builders Club วันที่ 3 กรกฎาคม 2026** และวางคำอธิบายใหม่ให้อ่านตามได้ [เปิดโพสต์ต้นฉบับ](https://www.facebook.com/share/p/1F4FzavWPj/) ภาพเป็นบันทึกหน้าจอในเวลานั้น ชื่อเมนู ราคาแพ็กเกจ และเงื่อนไขอาจเปลี่ยนได้ รายละเอียดประกอบตรวจเทียบเอกสาร Webull Thailand วันที่ **23 กันยายน 2026**

แยกสิ่งต่อไปนี้ออกจากกันก่อน จะช่วยหาสาเหตุได้เมื่อขั้นตอนใดขั้นตอนหนึ่งยังไม่ผ่าน

| สิ่งที่เตรียม | ใช้ทำอะไร | หลักฐานที่ควรตรวจ |
| --- | --- | --- |
| สิทธิ์ OpenAPI | อนุญาตให้แอปของเราเข้าถึงบริการ API ตามขอบเขตที่ได้รับ | สถานะคำขอใน My Application |
| App Key / App Secret | ระบุแอปและใช้เซ็นคำขอ | สร้าง Key ได้หลังคำขออนุมัติ |
| สิทธิ์ Market Data สำหรับ OpenAPI | อนุญาตให้ใช้ชุดข้อมูลตลาดที่เลือก | แพ็กเกจและสถานะใน OpenAPI Advanced Quotes |
| Access Token | ใช้กับการยืนยันตัวตนของ API | Token ผ่านการยืนยันและมีสถานะใช้งานได้ |

Market Data API ใช้อ่านราคาและข้อมูลตลาด ส่วน Trading API มีทั้งการอ่านบัญชี/สถานะ และการสร้างหรือแก้ไขคำสั่งซื้อขาย การเรียกข้อมูลบัญชีสำเร็จจึงยังไม่ยืนยันว่าสิทธิ์ข้อมูลตลาดครบ และไม่ได้แปลว่ามีคำสั่งซื้อขายเกิดขึ้น

## ขั้นที่ 1: สมัคร OpenAPI และสร้าง Key {#create-key}

### 1.1 เข้า Developer Tool

เข้าสู่ระบบที่ [เว็บไซต์ Webull Thailand](https://www.webull.co.th/) แล้วเปิดเมนูบัญชีด้านขวาบน เลือก **Developer Tool** เพื่อไปศูนย์นักพัฒนา

[![ภาพย่อยจากโพสต์: เมนู Developer Tool ในเมนูบัญชี Webull](images/webull-openapi-setup/01-developer-tool.jpg)](images/webull-openapi-setup/01-developer-tool.jpg)

*ภาพ 1 — ตำแหน่งเมนู Developer Tool ในภาพต้นทาง แตะภาพเพื่อดูขนาดเต็ม*

### 1.2 ยื่นคำขอใช้งาน API

เข้า **API Management → My Application** แล้วเลือก **Apply for API Service** กรอกข้อมูลตามแบบฟอร์ม การสมัครในขั้นนี้เป็นการขอสิทธิ์ ยังไม่ได้รับ App Key ทันที

[![ภาพย่อยจากโพสต์: หน้า My Application และปุ่ม Apply for API Service](images/webull-openapi-setup/02-apply-for-api.jpg)](images/webull-openapi-setup/02-apply-for-api.jpg)

*ภาพ 2 — ยื่นคำขอ OpenAPI ก่อนลงทะเบียนแอป*

ภาพเดิมเขียนว่ารอ 1–3 วันทำการ ขณะที่เอกสารปัจจุบันระบุประมาณ 1–2 วันทำการในกรณีเร็วที่สุด จึงควรดู **สถานะจริงใน My Application และอีเมล** เป็นหลัก เมื่อยังไม่อนุมัติให้ติดตามกับ Webull ตามช่องทาง Support ที่แสดงในแอป [คู่มือสมัครอย่างเป็นทางการ](https://developer.webull.co.th/apis/docs/authentication/individual-application/)

### 1.3 ลงทะเบียนแอป

เมื่ออนุมัติแล้ว เข้า **API Management → API Keys Management** ตั้งชื่อแอปให้สื่อวัตถุประสงค์ เช่น `Robo Notes Learning` ชื่อนี้เป็นตัวอย่างที่ตั้งเอง ไม่ใช่ค่าที่ระบบกำหนดตายตัว

[![ภาพย่อยจากโพสต์: แบบฟอร์มตั้งชื่อแอปสำหรับ API Key](images/webull-openapi-setup/03-register-app.jpg)](images/webull-openapi-setup/03-register-app.jpg)

*ภาพ 3 — ลงทะเบียนแอปที่จะใช้เรียก API*

### 1.4 สร้างและเก็บ Key

เลือก **Generate Key / สร้าง Key** แล้วทำการยืนยันตัวตนบน Webull ด้วยตนเอง เอกสารระบุว่าขั้นตอนนี้ใช้รหัส SMS และรหัสผ่านการซื้อขาย หลังสำเร็จจะได้ App Key และ App Secret

[![ภาพย่อยจากโพสต์: รายการแอปและปุ่มสร้าง Key](images/webull-openapi-setup/04-generate-key.jpg)](images/webull-openapi-setup/04-generate-key.jpg)

*ภาพ 4 — การมีชื่อแอปในรายการกับการสร้าง Key เป็นคนละขั้นตอน*

**App Secret ใช้คำนวณลายเซ็นคำขอ ไม่ใช่ค่าที่นำไปใส่ใน HTTP header โดยตรง** หากใช้ SDK ทางการ SDK จะจัดการส่วนนี้ให้ เก็บ Key/Secret แยกจากโค้ดที่เผยแพร่ และอย่าใส่ค่าจริงในภาพหน้าจอ GitHub หรือ Notebook ที่แชร์ [Authentication Overview](https://developer.webull.co.th/apis/docs/authentication/overview/)

## ขั้นที่ 2: เปิดสิทธิ์ข้อมูลตลาดสำหรับ OpenAPI {#market-data}

ในภาพต้นทาง หน้า API Keys มีลิงก์ **เรียนรู้เพิ่มเติมและสมัครใช้งาน** ใต้รายการแอป ซึ่งพาไปดูบริการข้อมูลตลาด

[![ภาพย่อยจากโพสต์: ลิงก์เรียนรู้เพิ่มเติมและสมัครใช้งานข้อมูลตลาดในหน้า API Keys](images/webull-openapi-setup/05-market-data-link.jpg)](images/webull-openapi-setup/05-market-data-link.jpg)

*ภาพ 5 — ทางเข้าบริการข้อมูลตลาดจากหน้า API Keys ตามภาพต้นทาง*

เอกสารปัจจุบันอธิบายทางเข้าผ่านเมนูโปรไฟล์ **Advanced Quotes** บนเว็บไซต์ที่ลิงก์ไว้ใน [Subscribe Advanced Quotes](https://developer.webull.co.th/apis/docs/market-data-api/subscribe-quotes/) จากนั้นเลือกแท็บ **OpenAPI Advanced Quotes** และตรวจบริการที่บัญชีมีสิทธิ์ใช้

[![ภาพย่อยจากโพสต์: แท็บ Open API Advanced Quotes และปุ่ม Claim ของ Nasdaq Basic](images/webull-openapi-setup/06-openapi-quotes.jpg)](images/webull-openapi-setup/06-openapi-quotes.jpg)

*ภาพ 6 — โพสต์เดิมแสดง Claim ของ Nasdaq Basic และแพ็กเกจอื่น ราคาและสิทธิ์ในภาพเป็นข้อมูล ณ เวลาของโพสต์ ให้ตรวจเงื่อนไขปัจจุบันบน Webull ก่อนเลือก*

จุดที่มักสับสนคือ การมีแพ็กเกจข้อมูลบนแอปมือถือหรือโปรแกรม Desktop ไม่ได้ทำให้ OpenAPI ใช้แพ็กเกจเดียวกันโดยอัตโนมัติ เอกสารระบุว่าต้องมีสิทธิ์สำหรับ **OpenAPI แยกต่างหาก** หากเมนูของบัญชีแสดง Claim ให้ตรวจและรับสิทธิ์ตามเงื่อนไขนั้น หากเป็นบริการเสียเงินให้พิจารณาค่าใช้จ่ายที่แสดงจริง ไม่อ้างราคาจากภาพเก่า [Market Data FAQ](https://developer.webull.co.th/apis/docs/market-data-api/faq/)

## ขั้นที่ 3: ติดตั้ง SDK และยืนยันตัวตน {#sdk-and-token}

SDK คือชุดโค้ดที่ช่วยเรียก API โดยดูแลรายละเอียดอย่างลายเซ็นและกระบวนการ Token ให้ เราจึงเริ่มจาก SDK ทางการได้โดยไม่ต้องเขียนระบบเซ็นคำขอเอง

[![ภาพย่อยจากโพสต์: คำสั่งติดตั้ง Webull Official SDK สำหรับ Python](images/webull-openapi-setup/07-install-sdk.jpg)](images/webull-openapi-setup/07-install-sdk.jpg)

*ภาพ 7 — คำสั่งติดตั้งจากโพสต์เดิม ตัวอย่างบทนี้เลือก Python 3.12 ซึ่งอยู่ในช่วงเวอร์ชันที่ระบุทั้งในภาพและเอกสารที่ตรวจ*

สร้าง virtual environment สำหรับงานนี้ก่อน เพื่อลดการชนกับไลบรารีของงานอื่น ตัวอย่าง macOS / Linux:

```shell
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade webull-openapi-python-sdk
python -m pip show webull-openapi-python-sdk
```

บน Windows ใช้ `py -3.12 -m venv .venv` และเปิด environment ด้วย `.venv\Scripts\Activate.ps1` ใน PowerShell หากติดตั้งหลาย Python ให้ตรวจว่า `python -m pip` กับ Python ที่รันไฟล์เป็น environment เดียวกัน บันทึกเวอร์ชัน SDK ที่ติดตั้งไว้ด้วย เพราะคำสั่ง `--upgrade` อาจได้คนละเวอร์ชันเมื่อรันต่างวัน [SDKs and Tools](https://developer.webull.co.th/apis/docs/sdk/)

### เลือก environment ให้ตรงกับ Key

| Environment | HTTP host ของ Trading และ Market Data | ใช้เมื่อ |
| --- | --- | --- |
| Test / UAT | `th-api.uat.webullbroker.com` | ทดสอบ integration ด้วย credentials ของ test environment |
| Production | `api.webull.co.th` | ใช้บริการกับบัญชีจริงและ credentials ของ production |

Host ในภาพโค้ดเดิมเป็น **production** สำหรับการฝึกเริ่มต้นให้เลือก test และใช้ test credentials ตาม [หน้า SDK ทางการ](https://developer.webull.co.th/apis/docs/sdk/#test-accounts) บัญชีทดสอบที่เอกสารเผยแพร่เป็นบัญชีร่วม ข้อมูลอาจเปลี่ยนจากการใช้งานของผู้อื่น อย่านำผลจากบัญชีร่วมไปตีความเป็นพอร์ตของตัวเอง

### ยืนยัน Token บนแอป Webull

เอกสารอธิบายว่า SDK จัดการการสร้างและตรวจ Token โดยผู้ใช้ทำขั้นตอนยืนยันในแอป สำหรับ production เมื่อมีคำขอที่ต้องยืนยัน ให้ตรวจ **Menu → Messages → OpenAPI Notifications** เปิดข้อความล่าสุด เลือก **Check Now** แล้วกรอก SMS ที่ Webull ส่งให้ในแอป

[![ภาพย่อยจากโพสต์: เปิด OpenAPI Notice เลือก Check Now และยืนยันในแอป Webull](images/webull-openapi-setup/08-verify-in-app.jpg)](images/webull-openapi-setup/08-verify-in-app.jpg)

*ภาพ 8 — การยืนยันเกิดบน Webull เว็บไซต์ Robo Trade Notes ไม่รับ OTP หรือ credentials*

Token เริ่มที่ `PENDING` และเปลี่ยนเป็น `NORMAL` หลังยืนยัน เอกสารที่ตรวจระบุว่าการยืนยันต้องเสร็จภายใน 5 นาที มิฉะนั้นจะเป็น `EXPIRED`; Token ที่ไม่ได้ใช้งานต่อเนื่อง 15 วันอาจเป็น `INVALID` ส่วน test environment ไม่ต้องทำ 2FA แบบ production [Token lifecycle](https://developer.webull.co.th/apis/docs/authentication/token/)

ภาพต้นทางยังกล่าวถึงไฟล์ `token.txt` ที่ SDK สร้าง ให้ถือไฟล์ Token เป็นข้อมูลลับและตรวจพฤติกรรมของ SDK รุ่นที่ติดตั้ง ไม่พิมพ์ Token เพื่อพิสูจน์ว่าระบบสำเร็จ และไม่อัปโหลดไฟล์ดังกล่าวไปพร้อมงานเรียน

## ทดลองครั้งแรก: อ่านรายการบัญชี {#first-call}

บันทึกโค้ดต่อไปนี้เป็น `verify_webull.py` แล้วรันใน environment ที่ติดตั้ง SDK โค้ดปรับจากตัวอย่างทางการให้รับ Key แบบซ่อนการพิมพ์ และแสดงเฉพาะสถานะ ไม่พิมพ์ข้อมูลบัญชีทั้งชุด การเรียกเมธอดนี้อ่านรายการบัญชี และอาจเริ่มกระบวนการยืนยัน Token ของ SDK

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

รันด้วย `python verify_webull.py` การได้ HTTP 200 และ JSON เป็นจุดตรวจว่าคำขอนี้สำเร็จในระดับ HTTP ขั้นถัดไปต้องอ่านโครงสร้างคำตอบและตรวจว่ามีบัญชีที่คาดไว้จริง ถ้ารายการว่างให้ตรวจบัญชีและ environment ต่อ **ยังสรุปไม่ได้ว่าสิทธิ์ Market Data พร้อม** หรือระบบพร้อมซื้อขายจริง [ตัวอย่าง Account List](https://developer.webull.co.th/apis/docs/trade-api/getting-started/)

โค้ดในส่วนนี้ตรวจรูปแบบกับเอกสารแล้ว แต่ไม่ได้รันกับบัญชีหรือ credentials ของผู้อ่าน หาก SDK แสดงรายละเอียดเพิ่มเติมระหว่างยืนยัน ให้ทำตามขั้นตอนบน Webull และปกปิดข้อมูลลับก่อนแชร์ log

## อ่านคำตอบ API ให้เป็นก่อนต่อเข้ากลยุทธ์ {#read-response}

### Snapshot คือข้อมูลตลาด ณ จุดหนึ่ง

[![ภาพย่อยจากโพสต์: ตัวอย่าง JSON จาก Snapshot API มี symbol ราคา bid ask และเวลา](images/webull-openapi-setup/09-snapshot-response.jpg)](images/webull-openapi-setup/09-snapshot-response.jpg)

*ภาพ 9 — ตัวอย่าง Snapshot จากโพสต์ ไม่ใช่ราคาปัจจุบันและไม่ใช่ผลรันใหม่ของบทนี้*

สังเกตว่า `price`, `bid`, `ask` และตัวเลขหลายช่องอยู่ในเครื่องหมายคำพูด จึงอาจเข้ามาเป็น string ต้องแปลงชนิดก่อนคำนวณ อีกจุดคือ `last_trade_time` กับ `quote_time` อาจเป็นคนละเวลา ราคาซื้อขายล่าสุดจึงไม่จำเป็นต้องตรงกับ bid/ask ปัจจุบันในคำตอบเดียวกัน

ตัวอย่างใหม่ด้านล่างเป็น **ข้อมูลสมมติ** ใช้ฝึกคำนวณส่วนต่าง ask − bid หน่วย USD ต่อหุ้น ไม่ใช่ข้อมูลที่เรียกจาก Webull และไม่ใช่การคาดการณ์กำไร

```python
from decimal import Decimal

snapshot = {"symbol": "DEMO", "bid": "99.98", "ask": "100.02"}
bid = Decimal(snapshot["bid"])
ask = Decimal(snapshot["ask"])
spread = ask - bid
print(f"Spread: {spread:.2f} USD per share")
```

ผลคือ `Spread: 0.04 USD per share` แต่ก่อนใช้ข้อมูลจริงยังต้องตรวจ symbol, หน่วย, ตลาด, เวลาอ้างอิง และความสดของข้อมูลตาม schema ของ endpoint นั้น ดูวิธีเริ่มอ่าน Historical Bars ใน [Market Data Getting Started](https://developer.webull.co.th/apis/docs/market-data-api/getting-started/)

### ประวัติคำสั่งคือสิ่งที่เคยเกิดขึ้น

[![ภาพย่อยจากโพสต์: คำตอบประวัติ Order มีสถานะ FILLED จำนวนที่จับคู่ และเวลา โดย ID ถูกปิดไว้ในภาพเดิม](images/webull-openapi-setup/10-order-history.jpg)](images/webull-openapi-setup/10-order-history.jpg)

*ภาพ 10 — ภาพต้นทางปิด ID บางส่วนไว้แล้ว คงการปิดข้อมูลตามต้นฉบับ*

การอ่าน Order history ต่างจากการส่ง Order ใหม่ เวลา `place_time` กับ `filled_time` บอกคนละเหตุการณ์ จำนวนที่ขอ `total_quantity` กับจำนวนที่จับคู่ `filled_quantity` ก็ต้องตรวจแยกกัน ตัวเลขในภาพเป็นตัวอย่างย้อนหลัง ใช้ศึกษารูปแบบข้อมูล ไม่ใช่คำแนะนำให้ส่งคำสั่งตามภาพ

## ถ้ายังเรียกไม่ได้ ให้ตรวจจากอาการ {#troubleshooting}

| อาการ | เริ่มตรวจตรงไหน | สิ่งที่ไม่ควรด่วนสรุป |
| --- | --- | --- |
| `ModuleNotFoundError: webull` | Python และ pip อยู่ใน environment เดียวกันหรือไม่ | Key ผิด |
| ไม่เห็นปุ่มสร้าง Key | สถานะคำขอและการลงทะเบียนแอป | เปิดบัญชีแล้วจะได้รับ API อัตโนมัติ |
| Token ยัง `PENDING` | ข้อความ OpenAPI ในแอปและกรอบเวลายืนยัน | การเรียก API รอบแรกเสร็จสมบูรณ์แล้ว |
| HTTP 403 เมื่อขอราคา | Authentication, Token และสิทธิ์ OpenAPI Market Data | ต้องซื้อแพ็กเกจเพิ่มเสมอ |
| อ่านรายการบัญชีได้ แต่ข้อมูลราคาไม่ได้ | ทดสอบสิทธิ์ของ endpoint ข้อมูลตลาดแยก | ทุก API ใช้ได้เมื่อ Account List ผ่าน |
| ข้อมูลมาแต่เวลาไม่ตรง | หน่วย timestamp, timezone, trading session และเวลาของแต่ละฟิลด์ | ราคาในภาพคือราคาล่าสุด |

ตารางนี้เป็นลำดับตรวจเบื้องต้น ไม่ใช่การจับคู่ error กับสาเหตุเดียว โดยเฉพาะ 403 เอกสารระบุได้ทั้ง header ไม่ครบ credentials ใช้ไม่ได้ และสิทธิ์ข้อมูลไม่เพียงพอ [Market Data FAQ](https://developer.webull.co.th/apis/docs/market-data-api/faq/)

ก่อนส่งคำถามให้ Support ให้จด environment, SDK version, ชื่อ endpoint, HTTP status และเวลาที่เกิดเหตุ โดยตัด Key, Secret, Token และข้อมูลระบุตัวบัญชีออกจากข้อความหรือภาพที่จะเผยแพร่

## ลองฝึกแบบออฟไลน์ {#practice}

Notebook ของบทนี้มี 5 ตัวอย่าง: เลือก host, อ่านสถานะ Token, คำนวณ spread จาก JSON จำลอง, แปลงเวลา UTC และแยกการอ่านบัญชีออกจากสิทธิ์ Market Data ทุก cell ใช้ Python standard library ไม่เรียกเครือข่ายและไม่ต้องใช้ Key

ลองเปลี่ยนสถานะ Token เป็น `PENDING` แล้วอธิบายว่าขั้นตอนใดยังไม่เสร็จ จากนั้นสมมติว่า Account List ได้ 200 แต่สิทธิ์ Market Data ยังไม่พร้อม คำตอบที่ถูกคือทดสอบ/ตรวจสิทธิ์ข้อมูลต่อ ไม่ใช้ผลของ Account List แทนหลักฐานการเรียกราคา

[ดาวน์โหลด Notebook พร้อมผลรัน](downloads/robo-trade-11.ipynb) · [ดาวน์โหลด Python ออฟไลน์](downloads/lesson_11.py) · [ดาวน์โหลดต้นฉบับบทเรียน Markdown](downloads/content/chapters/11-webull-openapi-setup.md)

## ทบทวนความเข้าใจ {#quiz}

::: quiz

## แหล่งที่มาและสิ่งที่ตรวจสอบ {#references}

1. [Nonthawat Laonan — Webull API Builders Club](https://www.facebook.com/groups/27377504935217042/permalink/27627684326865767/), โพสต์วันที่ 3 กรกฎาคม 2026: ภาพคู่มือ “3 ขั้นตอน เริ่มต้นใช้ Webull Open API” คัดภาพย่อย 10 ภาพจาก 4 ภาพในชุดเดิม ภาพและเครื่องหมายการค้าคงสิทธิ์ของเจ้าของต้นฉบับ
2. Webull Thailand: [Individual Application Process](https://developer.webull.co.th/apis/docs/authentication/individual-application/), [Getting Started](https://developer.webull.co.th/apis/docs/getting-started/) และ [SDKs and Tools](https://developer.webull.co.th/apis/docs/sdk/) — ขั้นตอนสมัคร การติดตั้งและ host ของแต่ละ environment
3. Webull Thailand: [Authentication Overview](https://developer.webull.co.th/apis/docs/authentication/overview/) และ [Token](https://developer.webull.co.th/apis/docs/authentication/token/) — การเซ็นคำขอและยืนยัน Token
4. Webull Thailand: [Subscribe Advanced Quotes](https://developer.webull.co.th/apis/docs/market-data-api/subscribe-quotes/), [Market Data FAQ](https://developer.webull.co.th/apis/docs/market-data-api/faq/) และ [Market Data Getting Started](https://developer.webull.co.th/apis/docs/market-data-api/getting-started/) — สิทธิ์ข้อมูลและการแยกจากแพ็กเกจในแอป

ตรวจเอกสารวันที่ 23 กันยายน 2026 ภาพ UI มาจากโพสต์เดิม ส่วนคำอธิบาย แบบทบทวน และตัวอย่างออฟไลน์เขียนใหม่ ผล Notebook มาจากการรันข้อมูลสมมติ ไม่ใช่ผลเชื่อมต่อบัญชี Webull จริง
