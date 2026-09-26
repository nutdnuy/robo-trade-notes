"""Render illustrative backtest-type charts locally; no market data or network."""
from pathlib import Path
from html import escape
import argparse, base64, json, random

parser=argparse.ArgumentParser()
parser.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--output-dir',type=Path)
args=parser.parse_args(); root=args.project_root
out=args.output_dir or root/'public/images';out.mkdir(parents=True,exist_ok=True)
fontdir=root/'node_modules/@fontsource/noto-sans-thai/files'
fontcss=''
for subset,unicode_range in [('thai','U+0E00-0E7F'),('latin','U+0000-00FF,U+2000-206F,U+2190-21FF,U+2212')]:
    for weight in [400,500]:
        data=base64.b64encode((fontdir/f'noto-sans-thai-{subset}-{weight}-normal.woff2').read_bytes()).decode()
        fontcss+=f"@font-face{{font-family:Lesson;font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2');unicode-range:{unicode_range};}}"
COLORS={'p':'#6200EE','q':'#00796B','text':'#212121','muted':'#666666','line':'#DDDDDD'}
returns=[-.01,.02,.01,-.02,-.01,.01,.02,0,-.01,.01,-.02,.02]
def prices(rs):
    values=[100]
    for r in rs:values.append(values[-1]*(1+r))
    return values
history=prices(returns)
rng=random.Random(20260926)
mc_returns=[[rng.choice([-.02,.02]) for _ in range(12)] for _ in range(100)]
mc=[prices(rs) for rs in mc_returns]
assert all(len(p)==13 and p[0]==100 and all(v>0 for v in p) for p in [history]+mc)
blocks={'A':returns[0:3],'B':returns[3:6],'C':returns[6:9],'D':returns[9:12]}
orders=[['A','B','C','D'],['B','D','D','A'],['C','A','B','C']]

def t(x,y,s,size=18,color='#212121',anchor='start',weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>'
def rect(x,y,w,h,fill,stroke='none',radius=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" rx="{radius}"/>'
def line(x1,y1,x2,y2,color='#DDDDDD',width=1,dash=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def wrap_svg(w,h,title,desc,body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc><defs><style>{fontcss}text{{font-family:Lesson,sans-serif;}}</style></defs>'+rect(0,0,w,h,'#FFFFFF')+body+'</svg>'
def chart(kind,mobile):
    w,h=(360,430) if mobile else (760,430)
    title='Historical / walk-forward' if kind=='historical' else 'Monte Carlo'
    header=t(20,36,title,22 if mobile else 26,weight=500)
    header+=t(20,70,'ดัชนีราคา · เริ่มที่ 100',18,color=COLORS['muted'])
    left,right,top,bottom=52,w-24,116,330
    lo,hi=80,120
    x=lambda i:left+i/12*(right-left)
    y=lambda v:bottom-(v-lo)/(hi-lo)*(bottom-top)
    body=header
    for v in [80,90,100,110,120]:
        body+=line(left,y(v),right,y(v),COLORS['q'] if v==100 else COLORS['line'],1,'4 4' if v==100 else '')
        body+=t(left-10,y(v)+6,v,16,COLORS['muted'],'end')
    for i in [0,6,12]:body+=t(x(i),bottom+26,i,17,COLORS['muted'],'middle')
    body+=t(right,bottom+53,'ช่วงเวลา',17,COLORS['muted'],'end')
    paths=[history] if kind=='historical' else mc
    for idx,path in enumerate(paths):
        pts=' '.join(f'{x(i):.2f},{y(v):.2f}' for i,v in enumerate(path))
        stroke=COLORS['p'] if kind=='historical' or idx==0 else COLORS['q'] if idx%2 else '#7B6D99'
        body+=f'<polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{3 if kind=="historical" or idx==0 else 1.2}" stroke-opacity="{1 if kind=="historical" or idx==0 else .28}" stroke-linejoin="round"/>'
    if kind=='historical':
        for i,v in enumerate(history):body+=f'<circle cx="{x(i)}" cy="{y(v)}" r="3.2" fill="#6200EE"/>'
    body+=t(20,410,'ข้อมูลสมมติ · 1 เส้นทาง / 12 ช่วง' if kind=='historical' else 'ข้อมูลสมมติ · 100 เส้น / 12 ช่วง',18,weight=500)
    desc='เส้นทางสมมติหนึ่งเส้น เรียงจากช่วง0ถึง12 เพื่อแทนการอ่านข้อมูลอดีตตามลำดับเวลา' if kind=='historical' else 'เส้นทางสมมติ100เส้น เริ่มที่100 ใช้โอกาสขึ้น2เปอร์เซ็นต์หรือลง2เปอร์เซ็นต์เท่ากันในแต่ละช่วง และสุ่มแต่ละช่วงอย่างอิสระ'
    return wrap_svg(w,h,title,desc,body)
def legend(y, mobile):
    body=rect(20,y-14,18,16,'#6200EE')+t(46,y,'ช่วงฝึก (in-sample)',16)
    x=20 if mobile else 310; yy=y+29 if mobile else y
    return body+rect(x,yy-14,18,16,'#00796B')+t(x+26,yy,'ช่วงทดสอบ (out-of-sample)',16)

def historical(mobile):
    w,h=(360,535) if mobile else (760,505)
    body=t(20,36,'Historical / walk-forward',22 if mobile else 26,weight=500)
    body+=t(20,69,'ฝึกจากอดีต แล้วทดสอบช่วงถัดไป',17,COLORS['muted'])
    left,right=64,w-22; cw=(right-left)/10; top=117; rh=34
    for k in range(11):
        body+=line(left+k*cw,top-6,left+k*cw,top+7*rh,'#E8E8E8')
    for k in range(10):
        body+=t(left+(k+.5)*cw,top-16,k+1,13 if mobile else 16,COLORS['muted'],'middle')
    for row in range(7):
        y=top+row*rh
        body+=t(20,y+20,f'{row+1}',16,COLORS['muted'])
        body+=rect(left+row*cw,y,3*cw,27,'#6200EE')
        body+=rect(left+(row+3)*cw,y,cw,27,'#00796B')
    body+=t(20,top-16,'รอบ',14,COLORS['muted'])
    body+=t(right,top+7*rh+25,'ช่วงเวลา →',16,COLORS['muted'],'end')
    body+=legend(422,mobile)
    body+=t(20,491 if mobile else 468,'ตัวอย่างสมมติ · ฝึก 3 ช่วง / ทดสอบ 1 ช่วง',15 if mobile else 18,weight=500)
    return wrap_svg(w,h,'Historical / walk-forward','แผนภาพ sliding window บนข้อมูลอดีตชุดเดียว เจ็ดรอบ แต่ละรอบใช้สามช่วงก่อนหน้าเพื่อฝึกแล้วทดสอบช่วงถัดไปหนึ่งช่วง ไม่มีข้อมูลอนาคตในชุดฝึก',body)

def resampling(mobile):
    w,h=(360,1040) if mobile else (900,515)
    body=t(20,36,'Resampling',24 if mobile else 26,weight=500)
    body+=t(20,69,'สร้างชุดใหม่ แล้วแบ่งช่วงฝึก–ทดสอบ',16 if mobile else 18,COLORS['muted'])
    body+=t(20,105,'ข้อมูลเดิม: 12 ช่วง แบ่งเป็น 4 บล็อก',16,weight=500)
    fills={'A':'#F0E8FE','B':'#E0F0EC','C':'#F3EBDD','D':'#E9E9EF'}
    ox,ow=20,w-40
    for j,name in enumerate('ABCD'):
        x=ox+j*ow/4
        body+=rect(x,118,ow/4-4,32,fills[name],COLORS['line'])+t(x+(ow/4-4)/2,140,name,18,COLORS['text'],'middle',500)
    body+=t(20,176,'1 บล็อก = 3 ช่วงติดกัน · หยิบซ้ำได้',16,COLORS['muted'])
    sample_orders=[['B','D','D','A'],['C','A','B','C'],['A','D','C','B']]
    for n,order in enumerate(sample_orders):
        px=20 if mobile else 20+n*292; py=207+n*244 if mobile else 211; pw=320 if mobile else 276
        body+=t(px,py,f'ชุดใหม่ {n+1}',19,weight=500)
        for j,name in enumerate(order):
            x=px+j*pw/4
            body+=rect(x,py+15,pw/4-3,28,fills[name],COLORS['line'])+t(x+(pw/4-3)/2,py+35,name,17,COLORS['text'],'middle',500)
        body+=t(px,py+66,'แบ่งช่วงภายในชุดนี้',15,COLORS['muted'])
        for r,start in enumerate([0,2,4,8]):
            y=py+80+r*24; cell=pw/12
            body+=line(px,y+9,px+pw,y+9,'#EEEEEE')
            body+=rect(px+start*cell,y,3*cell,18,'#6200EE')
            body+=rect(px+(start+3)*cell,y,cell,18,'#00796B')
        body+=t(px+pw,py+194,'ลำดับในชุดใหม่ →',14,COLORS['muted'],'end')
    body+=legend(963 if mobile else 453,mobile)
    body+=t(20,1020 if mobile else 495,'ข้อมูลสมมติ · คงลำดับภายในแต่ละบล็อก',15 if mobile else 17,COLORS['muted'])
    return wrap_svg(w,h,'Resampling: หลายชุดจากข้อมูลเดิม','แบ่งข้อมูลเดิมเป็นบล็อก A B C D เลือกบล็อกพร้อมคืนกลับเป็นสามชุด BDDA CABC ADCB แล้วแสดงตัวอย่างช่วงฝึกและทดสอบภายในแต่ละชุด ลำดับนี้เป็นลำดับของชุดที่จัดใหม่ ไม่ใช่ประวัติศาสตร์จริงอีกเส้นทาง',body)

variants={}
for kind in ['historical','resampling','monte-carlo']:
    for mobile in [False,True]:
        content=resampling(mobile) if kind=='resampling' else historical(mobile) if kind=='historical' else chart('monte-carlo',mobile)
        name=f'backtest-type-{kind}'+('-mobile' if mobile else '')+'.svg'
        (out/name).write_text(content)
    key=f'images/backtest-type-{kind}.svg'
    variants[key]={'width':900 if kind=='resampling' else 760,'height':515 if kind=='resampling' else 505 if kind=='historical' else 430,'mobile':f'images/backtest-type-{kind}-mobile.svg','mobileWidth':360,'mobileHeight':1040 if kind=='resampling' else 535 if kind=='historical' else 430}
metadata_dir=out if args.output_dir else root/'references'
metadata_dir.mkdir(parents=True,exist_ok=True)
(metadata_dir/'backtest-types-visuals.json').write_text(json.dumps(variants,indent=2))
manifest={'route':'no-image-generator','designSystem':'QuantCorner / QuantSeras light','dataStatus':'All numbers are invented teaching examples; no market observations or external data','historical':{'method':'Rolling historical windows, train 3 intervals then test 1, advance 1 interval per round','periods':10,'splits':[{'train':list(range(i+1,i+4)),'test':[i+4]} for i in range(7)]},'resampling':{'method':'Illustrative block-bootstrap selections; sample return blocks with replacement; this is not a generic cross-validation diagram','blocks':blocks,'blockOrders':[['B','D','D','A'],['C','A','B','C'],['A','D','C','B']],'illustrativeSplits':[{'train':list(range(i+1,i+4)),'test':[i+4]} for i in [0,2,4,8]],'preserveWithinBlockOrder':True},'monteCarlo':{'model':'Independent simple returns of -2% or +2%, equal probabilities','seed':20260926,'periods':12,'paths':mc,'returns':mc_returns},'source':'User-edited table, two user-supplied reference images dated 2026-09-26, and supplied The Three Types of Backtests, PDF pages3-5; original explanatory diagrams, not literal reproductions','fonts':'Existing bundled Noto Sans Thai 5.2.8, embedded; notices retained under public/images/fonts'}
(metadata_dir/'backtest-types-provenance.json').write_text(json.dumps(manifest,indent=2))
print('Rendered6SVG files and reproducible specifications:',out)
