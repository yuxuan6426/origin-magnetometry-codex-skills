"""Render the bilingual, code-maintained repository architecture diagrams."""
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 1000, 730
BACKGROUND = '#f5f8fb'
INK = '#15304b'
MUTED = '#506a80'
BLUE = '#235eaa'
TEAL = '#087f80'

TEXT = {
    'zh': (
        '从测量记录到原生图形',
        '本机处理 · 逐行追溯 · 独立核对',
        [
            ('实测或教学输入', 'DAT + 确认的样品质量', '合成示例有明确身份'),
            ('解析与连续分段', '保留采集顺序与磁矩源列', '按模式、温度与扫场整理'),
            ('可追溯的数据包', 'XLSX · CSV · 原生 OGS', '原始磁矩 + 归一化值 + 源行'),
            ('独立数值核对', '直接解析输入并检查保存值', '核对单位与完整记录覆盖'),
            ('专属 Origin 实例', '核对实例拥有权与独立握手', '本机原生导入、绘图与排版'),
            ('原生工程与图形', 'OPJU 保存重开 + MCP 回读', 'PNG · PDF · 运行验收摘要'),
        ],
        '固定的 MCP 源码快照  +  每次运行的可核对证据',
    ),
    'en': (
        'From measurements to native figures',
        'Local processing · Row provenance · Independent checks',
        [
            ('Measurement or teaching input', 'DAT + confirmed sample mass', 'Synthetic input is labeled'),
            ('Parse and segment', 'Acquisition order + moment source', 'Modes, temperatures and sweeps'),
            ('Traceable data package', 'XLSX · CSV · native OGS', 'Raw + normalized values + rows'),
            ('Independent numerical audit', 'Parse input and check saved values', 'Units and complete record coverage'),
            ('Dedicated Origin instance', 'Owned session + private handshake', 'Native import, plots and layout'),
            ('Native project and figures', 'Save/reopen OPJU + MCP readback', 'PNG · PDF · validation summary'),
        ],
        'Pinned MCP source snapshot  +  Verifiable evidence for each run',
    ),
}

BOXES = [(45,110),(535,110),(535,300),(45,300),(45,490),(535,490)]
ARROWS = [[(465,175),(535,175)],[(745,240),(745,300)],[(535,365),(465,365)],[(255,430),(255,490)],[(465,555),(535,555)]]


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc', size)


def render(lang, text):
    title, subtitle, nodes, footer = text
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
             f'<title id="title">{escape(title)}</title>',
             f'<desc id="desc">{escape(subtitle)}. DAT to Python data packages, independent audit, dedicated Origin session, OPJU and figure exports.</desc>',
             '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,1 L8,5 L0,9" fill="none" stroke="#6b879e" stroke-width="1.5"/></marker></defs>',
             f'<rect width="{W}" height="{H}" rx="24" fill="{BACKGROUND}"/>',
             '<g font-family="Segoe UI,Microsoft YaHei,Noto Sans CJK SC,sans-serif">',
             f'<text x="45" y="50" font-size="30" font-weight="700" fill="{INK}">{escape(title)}</text>',
             f'<text x="45" y="80" font-size="18" fill="{MUTED}">{escape(subtitle)}</text>']
    image = Image.new('RGB',(W,H),BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((45,15),title,font=font(30,True),fill=INK)
    draw.text((45,57),subtitle,font=font(18),fill=MUTED)
    for line in ARROWS:
        start,end = line
        parts.append(f'<path d="M{start[0]},{start[1]} L{end[0]},{end[1]}" fill="none" stroke="#6b879e" stroke-width="2.5" marker-end="url(#arrow)"/>')
        draw.line([start,end],fill='#6b879e',width=3)
        x,y = end
        if start[0] < x:
            triangle=[(x,y),(x-10,y-6),(x-10,y+6)]
        elif start[0] > x:
            triangle=[(x,y),(x+10,y-6),(x+10,y+6)]
        else:
            triangle=[(x,y),(x-6,y-10),(x+6,y-10)]
        draw.polygon(triangle,fill='#6b879e')
    for i,((x,y),node) in enumerate(zip(BOXES,nodes),1):
        accent = BLUE if i <= 3 else TEAL
        heading,a,b = node
        parts.extend([f'<rect x="{x}" y="{y}" width="420" height="130" rx="15" fill="white" stroke="#d4e0e9" stroke-width="1.5"/>',
                      f'<rect x="{x}" y="{y+17}" width="5" height="96" rx="2" fill="{accent}"/>',
                      f'<text x="{x+22}" y="{y+32}" font-size="16" font-weight="700" fill="{accent}">{i:02d}</text>',
                      f'<text x="{x+62}" y="{y+34}" font-size="21" font-weight="700" fill="{INK}">{escape(heading)}</text>',
                      f'<text x="{x+22}" y="{y+72}" font-size="18" fill="{MUTED}">{escape(a)}</text>',
                      f'<text x="{x+22}" y="{y+101}" font-size="18" fill="{MUTED}">{escape(b)}</text>'])
        draw.rounded_rectangle((x,y,x+420,y+130),radius=15,fill='white',outline='#d4e0e9',width=2)
        draw.rounded_rectangle((x,y+17,x+5,y+113),radius=2,fill=accent)
        draw.text((x+22,y+13),f'{i:02d}',font=font(16,True),fill=accent)
        draw.text((x+62,y+9),heading,font=font(21,True),fill=INK)
        draw.text((x+22,y+47),a,font=font(18),fill=MUTED)
        draw.text((x+22,y+77),b,font=font(18),fill=MUTED)
    parts.extend([f'<line x1="45" y1="655" x2="955" y2="655" stroke="#d4e0e9"/>',
                  f'<text x="45" y="692" font-size="18" fill="{MUTED}">{escape(footer)}</text>','</g></svg>'])
    draw.line((45,655,955,655),fill='#d4e0e9',width=1)
    draw.text((45,668),footer,font=font(18),fill=MUTED)
    (ROOT/f'pipeline.{lang}.svg').write_text('\n'.join(parts),encoding='utf-8')
    image.save(ROOT/f'pipeline.{lang}.png')


if __name__ == '__main__':
    for lang,text in TEXT.items():
        render(lang,text)
