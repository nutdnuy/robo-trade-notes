# Welcome

พื้นที่สำหรับเรียนรู้การสร้างระบบซื้อขายด้วย Python และ Webull OpenAPI

## เปิดบัญชี Webull และเตรียม API Key {#webull-start}

**[เปิดบัญชี Webull ผ่านลิงก์ QuantCorner →](https://www.webull.co.th/k/QuantCorner)**

ใช้ลิงก์แนะนำของ QuantCorner ด้านบน แล้วทำขั้นตอนเปิดบัญชีและยืนยันตัวตนบน Webull ตามเงื่อนไขที่แสดง ผู้ที่มีบัญชีอยู่แล้วเริ่มจากการเข้าสู่ระบบได้เลย

การเปิดบัญชีและการอนุมัติ OpenAPI เป็นคนละขั้นตอน

**[อ่านคู่มือภาพ: เริ่มต้นใช้ Webull OpenAPI ทีละขั้น →](#/chapter-11)** — ภาพย่อย 10 ภาพ ครอบคลุมการขอ Key สิทธิ์ข้อมูลตลาด การยืนยัน Token และตัวอย่าง Python

### ขอ API Key ใน 5 ขั้นตอน

1. **เตรียมบัญชีและเข้าสู่ระบบ** เปิดบัญชีให้เรียบร้อย จากนั้นเข้า [เว็บไซต์ Webull Thailand](https://www.webull.co.th/) แล้วเลือก **Developer Tool** จากเมนูบัญชี
2. **สมัครสิทธิ์ OpenAPI** เข้า **API Management → My Application** กรอกข้อมูลและส่งคำขอ
3. **รอผลอนุมัติ** ตรวจสถานะใน **My Application** และอีเมล เมื่อ Webull อนุมัติแล้วจึงไปขั้นถัดไป
4. **ลงทะเบียนแอป** เข้า **API Management → API Keys Management** แล้วตั้งชื่อแอปสำหรับงานของคุณ
5. **สร้างและเก็บ Key** เลือก **Generate Key** และยืนยันตัวตนบน Webull ด้วยตนเอง จากนั้นเก็บ **App Key / App Secret** ในที่ปลอดภัย หลีกเลี่ยงการใส่ค่าจริงใน GitHub หรือ Notebook ที่แชร์

เว็บไซต์นี้ไม่รับ Key, Secret หรือ OTP ส่วนสิทธิ์ข้อมูลตลาดสำหรับ OpenAPI ต้องตรวจแยกจากการสมัครข้อมูลผ่านแอป Webull ตาม [Market Data API FAQ](https://developer.webull.co.th/apis/docs/market-data-api/faq/)

อ้างอิง [คู่มือ Webull Thailand: Individual Application Process](https://developer.webull.co.th/apis/docs/authentication/individual-application/) — ตรวจเอกสารวันที่ 13 กันยายน 2026 ชื่อเมนูและหน้าจอจริงอาจต่างจากคู่มือ
