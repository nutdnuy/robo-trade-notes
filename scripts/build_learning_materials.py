from pathlib import Path
import json, io, contextlib, zipfile

root = Path(__file__).resolve().parents[1]
out = root / "public/downloads"
csv = (out / "demo_prices.csv").read_text()
lesson = (out / "lesson_01.py").read_text()
function = lesson[lesson.index("def build_signals"):lesson.index("\ndef main")].strip()
fence = chr(96) * 3
cells = []
def md(text):
    cells.append({"cell_type":"markdown","id":"cell-"+str(len(cells)),"metadata":{},"source":text.splitlines(True)})
def code(text):
    cells.append({"cell_type":"code","id":"cell-"+str(len(cells)),"metadata":{},"source":text.splitlines(True),"execution_count":None,"outputs":[]})

md("# บทที่ 01: จากข้อมูลราคา สู่สัญญาณแรก\n\nRobo Trade · Python + Webull OpenAPI\n\nNotebook นี้รันแบบออฟไลน์ ข้อมูล DEMO สร้างขึ้นเอง 120 แท่ง ไม่ใช่ราคาหุ้นจริง ไม่มีคำสั่งซื้อขาย และไม่รายงานผลตอบแทน\n\nเป้าหมาย: เข้าใจ SMA, สถานะเป้าหมาย, warm-up และเวลาเกิดสัญญาณ")
md("## 1. เตรียมเครื่องมือ\n\nติดตั้ง pandas==2.3.2 ใน environment ของคุณก่อนรัน ใช้ Kernel ใหม่แล้วรันจากบนลงล่างได้ ข้อมูลตัวอย่างฝังอยู่ในไฟล์นี้")
code("from io import StringIO\nimport pandas as pd\nprint('pandas', pd.__version__)")
md("## 2. ข้อมูลราคา\n\nแต่ละแถวเป็นหนึ่งแท่งรายวันสมมติ ไม่มีปฏิทินวันซื้อขายจริง หน่วยราคาคือ USD ในเชิงภาพประกอบ เราจะใช้ชุดเดียวกับห้องทดลองบนเว็บ")
code("csv_text = "+repr(csv)+"\ndata = pd.read_csv(StringIO(csv_text))\nassert len(data) == 120\nassert data['day'].is_unique and data['day'].is_monotonic_increasing\nassert data['close'].notna().all()\nprint(data.head().to_string(index=False))")
md("## 3. ตรวจด้วยมือก่อนเขียนกลยุทธ์\n\nSMA คือผลรวมราคาปิด n แท่งล่าสุดหารด้วย n โดยต้องมีข้อมูลครบช่วงก่อน")
code("example = [100, 102, 101, 103, 104]\nprint('SMA 5 =', sum(example) / len(example))\nassert sum(example) / len(example) == 102")
md("## 4. กติกา Long / Cash\n\nSMA สั้นอยู่เหนือ SMA ยาว: target=1; กรณีอื่น: target=0\nช่วงข้อมูลไม่ครบเส้นยาวเป็น warm-up เป้าหมายยังเป็นศูนย์ จุดเปลี่ยนแรกหลัง warm-up นับเมื่อเป้าหมายเปลี่ยนจากศูนย์เป็นหนึ่ง")
code(function)
code("signals = build_signals(data, short=5, long=20)\nprint(signals.tail(5).to_string(index=False))\nprint('จุดเปลี่ยนสถานะ:', signals.loc[signals['changed'], 'day'].tolist())\nassert signals.loc[signals['changed'], 'day'].tolist() == [20, 24, 52, 80, 108]")
md("## 5. เวลาเป็นส่วนหนึ่งของกติกา\n\nหลังรู้ราคาปิดแท่ง t แล้วจึงรู้ target[t] เป้าหมายนี้ใช้พิจารณาได้ภายหลัง ไม่ใช่ย้อนไปซื้อที่ราคาเปิดแท่ง t\n\nnext_open_target เป็นการเลื่อนเป้าหมายหนึ่งแท่ง ไม่ใช่หลักฐานว่ามี order หรือ fill")
code("print(signals.iloc[17:23][['day','close','target','next_open_target']].to_string(index=False))\nassert signals.loc[19, 'target'] == 1\nassert signals.loc[19, 'next_open_target'] == 0\nassert signals.loc[20, 'next_open_target'] == 1")
md("## 6. เปลี่ยนหนึ่งอย่าง แล้ววัดผล\n\nเปรียบเทียบจุดเปลี่ยนโดยใช้ข้อมูลชุดเดิม อย่าสรุปว่าจำนวนสัญญาณน้อยกว่าแปลว่ากำไรมากกว่า")
code("for short, long in [(5,20),(5,40),(15,50)]:\n    trial = build_signals(data, short, long)\n    print(short, long, 'changes =', int(trial['changed'].sum()), 'bars =', trial.loc[trial['changed'],'day'].tolist())")
md("## 7. ตรวจว่าไม่ได้ใช้ข้อมูลอนาคต\n\nผลคำนวณในอดีตต้องไม่เปลี่ยนเมื่อเราเติมแถวอนาคตเข้ามา")
code("past = build_signals(data.iloc[:70].copy(), 5, 20)\npd.testing.assert_frame_equal(past, signals.iloc[:70])\nprint('ผ่าน: การเพิ่มข้อมูลอนาคตไม่เปลี่ยนสัญญาณในอดีต')")
md("## 8. รูปแบบข้อมูลจาก Webull\n\nตัวอย่างถัดไปเป็น JSON จำลองที่มีโครงสร้างตาม Historical Bars API ไม่ใช่ผลเรียก API จริง\n\nแปลง time เป็น UTC และ OHLCV จาก string เป็นตัวเลข ตรวจข้อมูลซ้ำและค่าว่าง แล้วเรียงเวลา")
code("payload = {'result':[{'symbol':'DEMO','instrument_id':'SYNTHETIC','result':[{'time':'2026-01-05T21:00:00+0000','open':'100.00','high':'101.20','low':'99.60','close':'100.80','volume':'120000'}]}]}\nstock = next(x for x in payload['result'] if x['symbol']=='DEMO')\nbars = pd.DataFrame(stock['result'])\nbars['time'] = pd.to_datetime(bars['time'], utc=True, errors='raise')\nfor name in ['open','high','low','close','volume']:\n    bars[name] = pd.to_numeric(bars[name], errors='raise')\nassert not bars['time'].duplicated().any()\nassert not bars.isna().any().any()\nbars = bars.sort_values('time').reset_index(drop=True)\nprint(bars.to_string(index=False))")
md("## 9. การเชื่อมต่อ Webull เป็นขั้นตอนเพิ่มเติม\n\nโค้ดนี้ตรวจชื่อเมธอดกับ SDK 3.0.0 แต่ยังไม่ได้เชื่อมต่อบัญชีของคุณ ใช้กุญแจเฉพาะบนเครื่อง Python และทำ 2FA กับ Webull เมื่อถูกขอ\n\nดาวน์โหลด webull_bars.py จากชุดไฟล์ประกอบ ตั้ง WEBULL_APP_KEY และ WEBULL_APP_SECRET โดยไม่เผยในประวัติคำสั่ง แล้วรัน:\n\n"+fence+"text\npython webull_bars.py --fetch --environment uat --output webull_bars.json\n"+fence+"\n\nUAT: th-api.uat.webullbroker.com\nProduction: api.webull.co.th\n\nใช้ Market Data entitlement สำหรับ OpenAPI แยกจากสิทธิ์ในแอป และตรวจเวลาปิดแท่งจริง การตั้ง real_time_required=True เพียงอย่างเดียวไม่ทดแทนการตรวจ session/calendar")
md("## แบบฝึกหัด\n\n1. ใช้ SMA 5/40 แล้วเปรียบเทียบกับ 5/20: warm-up เปลี่ยนไปกี่แท่ง? ยกวันเปลี่ยนสถานะสองวัน\n2. ทำไมไม่ควรเรียก target ว่า position ที่ถือจริง?\n3. ลองป้อนราคาคงที่ทุกแท่ง เส้นเฉลี่ยควรเท่ากัน และกติกาควรให้สถานะอะไร?\n\nเฉลยย่อ: warm-up ก่อนมีค่าครบเพิ่มจาก 19 เป็น 39 แท่ง; target ยังไม่ผ่านขั้นตอน order/fill; ราคาคงที่ให้ CASH ตามกติกาที่กำหนด\n\nยังไม่มีการจำลองต้นทุน การจับคู่ หรือผลตอบแทน จึงยังตัดสินความสามารถทำกำไรไม่ได้")
md("## แหล่งอ้างอิง\n\n- Yves Hilpisch, Python for Algorithmic Trading, บท 3-4; https://github.com/yhilpisch/py4at\n- https://developer.webull.co.th/apis/docs/sdk\n- https://developer.webull.co.th/apis/docs/authentication/overview\n- https://developer.webull.co.th/apis/docs/reference/trade-api/historical-bars\n- https://github.com/webull-inc/webull-openapi-python-sdk\n\nบทเรียนและโค้ดเขียนขึ้นใหม่ ไม่มีโค้ดหรือ PDF ต้นฉบับหนังสือแนบมา ตรวจเอกสาร 10 กันยายน 2026")
namespace = {}
counter = 0
for cell in cells:
    if cell["cell_type"] != "code":
        continue
    counter += 1
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        exec(compile("".join(cell["source"]), "<notebook-cell-"+str(counter)+">", "exec"), namespace)
    cell["execution_count"] = counter
    text = capture.getvalue()
    if text:
        cell["outputs"] = [{"output_type":"stream","name":"stdout","text":text.splitlines(True)}]
notebook={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"},"robo_trade":{"data":"synthetic","network_executed":False}},"nbformat":4,"nbformat_minor":5}
(out/"robo-trade-01.ipynb").write_text(json.dumps(notebook,ensure_ascii=False,indent=2))
notice="Robo Trade learning website - third-party notices\n\nOriginal Thai lesson and examples. No Hilpisch book code or QuantGirl artwork redistributed.\n\nReact Bits: CountUp, AnimatedList, Stepper from official registry, retrieved 2026-09-10. Modified within this app: Material 2 tokens, local keyboard interaction, reduced motion, accessible numeric text and quiz semantics.\n\n"
notice+=(root/"references/licenses/react-bits.txt").read_text()+"\n\n"
for package in ["react","react-dom","motion","react-markdown","remark-gfm","@tabler/icons-react","@fontsource/roboto","@fontsource/noto-sans-thai","@fontsource/roboto-mono"]:
    folder=root/"node_modules"/package
    candidates=[p for p in folder.iterdir() if p.name.upper().startswith(("LICENSE","OFL")) and p.is_file()]
    notice+="\nPACKAGE: "+package+"\n"
    for p in candidates:
        notice+=p.read_text(errors="replace")+"\n"
(root/"public/THIRD_PARTY_NOTICES.txt").write_text(notice)
with zipfile.ZipFile(out/"robo-trade-01-materials.zip","w",zipfile.ZIP_DEFLATED) as z:
    for name in ["README.md","lesson_01.py","webull_bars.py","requirements.txt","demo_prices.csv","robo-trade-01.ipynb"]:
        z.write(out/name, "robo-trade-01/"+name)
print("Notebook:",len(cells),"cells;",counter,"code cells executed offline. Teaching ZIP ready.")
