#!/usr/bin/env python3
"""Deterministic synthetic Alpha/Beta teaching chart; no real market observations.

Run with Python 3, numpy, matplotlib, fonttools installed:
  python generate_alpha_beta.py --font-root node_modules/@fontsource --output-dir OUTPUT

The SVGs retain editable text and embed the project's locally installed fonts.
"""
from pathlib import Path
import argparse
import base64
import csv
import json
import os
import tempfile
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('--font-root', type=Path, default=Path.cwd() / 'node_modules/@fontsource')
parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--data-dir', type=Path, help='CSV destination; defaults to output-dir')
args = parser.parse_args()
out = args.output_dir.resolve()
out.mkdir(parents=True, exist_ok=True)
data_out = args.data_dir.resolve() if args.data_dir else out
data_out.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(out / '.matplotlib-cache'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib import patheffects
from fontTools.ttLib import TTFont

PURPLE = '#6200EE'
TEAL = '#03DAC6'
TEAL_EDGE = '#007D73'
INK = '#212121'
SECONDARY = '#616161'
GRID = '#E5E5E5'
FONT_FILES = [
    ('Roboto', args.font_root / 'roboto/files/roboto-latin-400-normal.woff2'),
    ('Noto Sans Thai', args.font_root / 'noto-sans-thai/files/noto-sans-thai-thai-400-normal.woff2'),
]
css = []
with tempfile.TemporaryDirectory(prefix='alpha-beta-fonts-', dir=out) as font_dir:
    for i, (family, woff) in enumerate(FONT_FILES):
        if not woff.exists():
            raise FileNotFoundError(f'Local project font missing: {woff}')
        font = TTFont(woff.with_suffix('.woff'))
        font.flavor = None
        ttf = Path(font_dir) / f'font-{i}.ttf'
        font.save(ttf)
        fm.fontManager.addfont(ttf)
        font_range = 'U+0E00-0E7F,U+200C-200D,U+25CC' if family == 'Noto Sans Thai' else 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'
        encoded = base64.b64encode(woff.read_bytes()).decode('ascii')
        css.append(f"@font-face{{font-family:'{family}';font-style:normal;font-weight:400;src:url(data:font/woff2;base64,{encoded}) format('woff2');unicode-range:{font_range};}}")

    plt.rcParams.update({
        'font.family': ['Roboto', 'Noto Sans Thai', 'DejaVu Sans'],
        'font.size': 16, 'text.color': INK, 'axes.labelcolor': INK,
        'xtick.color': SECONDARY, 'ytick.color': SECONDARY,
        'svg.fonttype': 'none', 'svg.hashsalt': 'quantara-alpha-beta-v1',
        'axes.unicode_minus': False, 'figure.facecolor': 'white',
        'savefig.facecolor': 'white',
    })

    periods = 60
    seed = 42026
    rng = np.random.default_rng(seed)
    t = np.arange(1, periods + 1)
    market = 0.005 + 0.012*np.sin(t*0.29) + 0.008*np.cos(t*0.85) + rng.normal(0, 0.009, periods)
    market[17:23] -= 0.025
    market[42:47] -= 0.031
    design = np.column_stack([np.ones(periods), market])

    def make_returns(alpha, beta, residual_std):
        raw = rng.normal(0, 1, periods)
        # Project out the intercept and market component, for an exact teaching example.
        epsilon = raw - design @ np.linalg.lstsq(design, raw, rcond=None)[0]
        epsilon = epsilon / epsilon.std(ddof=0) * residual_std
        values = alpha + beta * market + epsilon
        estimate = np.linalg.lstsq(design, values, rcond=None)[0]
        assert np.allclose(estimate, [alpha, beta], atol=1e-12)
        assert abs(epsilon.mean()) < 1e-12
        assert abs(np.dot(epsilon, market)) < 1e-12
        return values, epsilon, estimate

    alpha_returns, alpha_noise, alpha_ols = make_returns(0.002, 1.0, 0.004)
    beta_returns, beta_noise, beta_ols = make_returns(0.0, 1.3, 0.003)

    def wealth(returns):
        assert np.all(returns > -1)
        return np.r_[100.0, 100.0*np.cumprod(1+returns)]

    benchmark = wealth(market)
    alpha_path = wealth(alpha_returns)
    beta_path = wealth(beta_returns)
    for path in [benchmark, alpha_path, beta_path]:
        assert path[0] == 100 and np.any(np.diff(path) < 0) and np.any(np.diff(path) > 0)

    with (data_out/'why-robo-alpha-beta.csv').open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['period', 'benchmark_return', 'alpha_strategy_return', 'beta_strategy_return', 'benchmark_value', 'alpha_strategy_value', 'beta_strategy_value'])
        for i in range(periods+1):
            writer.writerow([i, *(['','',''] if i == 0 else [f'{market[i-1]:.12f}', f'{alpha_returns[i-1]:.12f}', f'{beta_returns[i-1]:.12f}']), f'{benchmark[i]:.12f}', f'{alpha_path[i]:.12f}', f'{beta_path[i]:.12f}'])

    svg_ns = 'http://www.w3.org/2000/svg'
    ET.register_namespace('', svg_ns)
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    chart_description = ('ข้อมูลสมมติ 60 ช่วง เริ่มมูลค่า 100 อัตราปลอดความเสี่ยงเป็นศูนย์ '
        'กราฟซ้ายใช้ alpha 0.20% ต่อช่วง และ beta 1 กราฟขวาใช้ alpha 0 และ beta 1.3 '
        'เส้นทึบสีม่วงคือ Strategy เส้นประสีเขียวอมฟ้าคือ Benchmark ทั้งสองกราฟใช้แกนตั้ง 90 ถึง 130 เหมือนกัน '
        'ค่าพารามิเตอร์กำหนดขึ้นเพื่อสอน ไม่ใช่ผลการซื้อขายจริง และภาพเส้นมูลค่าเพียงอย่างเดียวพิสูจน์ alpha ไม่ได้')

    def enhance_svg(path, width, height):
        tree = ET.parse(path)
        root = tree.getroot()
        root.set('width', str(width))
        root.set('height', str(height))
        root.set('role', 'img')
        root.set('aria-labelledby', 'alpha-beta-title alpha-beta-desc')
        title = ET.Element(f'{{{svg_ns}}}title', {'id':'alpha-beta-title'})
        title.text = 'Alpha และ Beta: ตัวอย่างข้อมูลสมมติ'
        desc = ET.Element(f'{{{svg_ns}}}desc', {'id':'alpha-beta-desc'})
        desc.text = chart_description
        root.insert(0, title)
        root.insert(1, desc)
        defs = root.find(f'{{{svg_ns}}}defs')
        style = ET.SubElement(defs, f'{{{svg_ns}}}style', {'type':'text/css'})
        style.text = '\n'.join(css)
        tree.write(path, encoding='utf-8', xml_declaration=True)

    def render(kind, width, height):
        fig = plt.figure(figsize=(width/72, height/72), dpi=72)
        # Pixel-like placement keeps 16–18px type at each target width.
        def label(x, y, text, size=16, **kwargs):
            return fig.text(x/width, 1-y/height, text, fontsize=size, va='top', **kwargs)
        label(16, 16, 'ข้อมูลสมมติ', size=18)
        label(width-16, 18, '60 periods · Rf = 0', ha='right', color=SECONDARY)
        benchmark_effects = [patheffects.Stroke(linewidth=4.0, foreground=TEAL_EDGE), patheffects.Normal()]
        legend = [Line2D([0],[0],color=PURPLE,lw=2.8,label='Strategy'),
                  Line2D([0],[0],color=TEAL,lw=2.8,ls=(0,(5,3)),label='Benchmark',path_effects=benchmark_effects)]
        fig.legend(handles=legend, loc='upper left', bbox_to_anchor=(16/width,1-46/height),
                   ncol=2, frameon=False, fontsize=16, handlelength=2.2, columnspacing=1.5, borderaxespad=0)
        if kind == 'desktop':
            panels = [(67,146,304,230), (451,146,304,230)]
            titles = [(67,91), (451,91)]
        else:
            panels = [(67,145,277,200), (67,464,277,200)]
            titles = [(67,92), (67,411)]
        for i, ((left,top,panel_width,panel_height),(tx,ty)) in enumerate(zip(panels,titles)):
            label(tx,ty, 'ตัวอย่าง α > 0, β = 1' if i == 0 else 'ตัวอย่าง α = 0, β = 1.3', size=18)
            label(tx,ty+27, 'α = 0.20% per period' if i == 0 else 'α = 0% per period', color=SECONDARY)
            ax = fig.add_axes([left/width,(height-top-panel_height)/height,panel_width/width,panel_height/height])
            ax.plot(np.arange(periods+1),benchmark,color=TEAL,lw=2.8,ls=(0,(5,3)),zorder=3,path_effects=benchmark_effects)
            ax.plot(np.arange(periods+1),alpha_path if i==0 else beta_path,color=PURPLE,lw=2.8,zorder=4)
            ax.set_xlim(0,60);ax.set_ylim(90,130)
            ax.set_xticks([0,20,40,60]);ax.set_yticks([90,100,110,120,130])
            ax.set_xlabel('Period', fontsize=16, labelpad=9)
            ax.set_ylabel('Value (start = 100)', fontsize=16, labelpad=9)
            ax.tick_params(axis='both',labelsize=16,length=0,pad=7)
            ax.grid(axis='y',color=GRID,lw=0.7,zorder=0)
            ax.axhline(100,color='#A6A6A6',lw=0.8,zorder=1)
            for spine in ax.spines.values():spine.set_visible(False)
            ax.spines['bottom'].set_visible(True);ax.spines['bottom'].set_color('#A6A6A6')
        file = out/('why-robo-alpha-beta' if kind == 'desktop' else 'why-robo-alpha-beta-mobile')
        fig.savefig(file.with_suffix('.svg'),format='svg',metadata={'Date':None,'Title':'Alpha and Beta — synthetic teaching data','Description':chart_description})
        fig.savefig(file.with_suffix('.png'),format='png',dpi=72)
        plt.close(fig)
        enhance_svg(file.with_suffix('.svg'),width,height)

    render('desktop',780,450)
    render('mobile',360,735)

    def metrics(path):
        return {'final_value':float(path[-1]),'minimum_value':float(path.min()),'maximum_value':float(path.max()),
                'max_drawdown_sample_not_annualized':float((path/np.maximum.accumulate(path)-1).min()),
                'up_periods':int((np.diff(path)>0).sum()),'down_periods':int((np.diff(path)<0).sum())}
    spec = {
        'name':'Alpha and Beta: original teaching illustration',
        'route':'no-image-generator',
        'design_system':'QuantCorner / QuantSeras, light book theme',
        'question':'How do deliberately different alpha and beta parameters produce different sample value paths?',
        'data_status':'Entirely synthetic, not real returns and not a strategy recommendation',
        'source':'Generated locally by generate_alpha_beta.py',
        'observation_count':60,'path_points':61,'time_axis':'Unitless period index 0–60; no calendar dates or annualization',
        'seed':seed,'numpy_rng':'default_rng PCG64',
        'market_return_formula':'0.005 + 0.012*sin(t*0.29) + 0.008*cos(t*0.85) + Normal(0,0.009); subtract0.025 for periods18–23 and0.031 for43–47',
        'model':'r_strategy,t = alpha + beta*r_benchmark,t + epsilon_t; Rf = 0 for every period',
        'wealth_formula':'V0=100; Vt=V(t-1)*(1+r_t); simple returns, identical compounding basis',
        'residual_construction':'Seeded Gaussian vector projected orthogonal to [constant,market_return], then scaled to stated population standard deviation. Forces sample OLS intercept/beta to the chosen model values by design.',
        'left':{'alpha_per_period':0.002,'alpha_percent_per_period':0.2,'beta':1,'residual_std':0.004,'OLS_intercept':float(alpha_ols[0]),'OLS_beta':float(alpha_ols[1]),**metrics(alpha_path)},
        'right':{'alpha_per_period':0,'beta':1.3,'residual_std':0.003,'OLS_intercept':float(beta_ols[0]),'OLS_beta':float(beta_ols[1]),**metrics(beta_path)},
        'benchmark':metrics(benchmark),
        'same_scale':{'x':[0,60],'y':[90,130]},
        'exports':{'desktop':[780,450],'mobile':[360,735]},
        'encoding':{'Strategy':{'stroke':PURPLE,'line':'solid'},'Benchmark':{'stroke':TEAL,'line':'dashed','contrast_outline':TEAL_EDGE,'outline_width':4.0,'inner_width':2.8}},
        'font_sources':['@fontsource/roboto/files/roboto-latin-400-normal.woff2','@fontsource/noto-sans-thai/files/noto-sans-thai-thai-400-normal.woff2'],
        'font_handling':'Original project WOFF2 embedded in SVG; native editable SVG text. Greek fallback uses DejaVu Sans/system sans-serif.',
        'limitations':['Chosen synthetic parameters, not fitted to real performance.', 'Orthogonalized residuals are an illustration device, not evidence about live model errors.', 'Cumulative value curves alone do not establish alpha or skill.', 'The plot omits trading costs, portfolio constraints and live execution.'],
        'alt_text':chart_description,
        'qa':{'numeric_checks':'Passed OLS equality, residual orthogonality, start100, positive wealth factors and both up/down moves.',
              'visual_checks':'Pending human/model view of exports.'}
    }
    (out/'why-robo-alpha-beta.spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:spec[key] for key in ['left','right','benchmark','exports']},ensure_ascii=False,indent=2))
