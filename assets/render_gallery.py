"""Build a labeled gallery from real native Origin exports; no UI recording."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1000, 840
DURATION_MS = 3000
FRAMES = [
    ('real-0p5mg-mt.png', '0.5 mg · MT 升温 / warming'),
    ('real-0p5mg-mh.png', '0.5 mg · 3 K DC 回线 / loop'),
    ('real-0p5mg-multitemperature.png', '0.5 mg · 多温度 / multiple temperatures'),
    ('real-24mg-multitemperature.png', '24 mg · 多温度 / multiple temperatures'),
]


def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', size)


def main():
    frames, sources = [], []
    for i, (filename, label) in enumerate(FRAMES, 1):
        source = ROOT / filename
        with Image.open(source) as opened:
            opened.load()
            plot = ImageOps.contain(opened.convert('RGB'), (WIDTH, 710), Image.Resampling.LANCZOS)
        canvas = Image.new('RGB', (WIDTH, HEIGHT), 'white')
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, WIDTH, 81), fill='#eff4f8')
        draw.text((22, 7), '真实 Origin 导出结果轮播', font=font(25), fill='#15304b')
        draw.text((22, 42), 'Gallery of native Origin exports', font=font(21), fill='#506a80')
        canvas.paste(plot, ((WIDTH-plot.width)//2, 84+(710-plot.height)//2))
        draw.line((22, 800, WIDTH-22, 800), fill='#d4e0e9', width=1)
        draw.text((22, 806), f'{i} / {len(FRAMES)}   {label}', font=font(18), fill='#15304b')
        draw.text((816, 806), '3 秒 / 3 seconds', font=font(17), fill='#506a80')
        frames.append(canvas.quantize(colors=256))
        sources.append({'frame':i, 'file':filename, 'sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'caption':label})
    destination = ROOT / 'origin-results-gallery.gif'
    frames[0].save(destination, save_all=True, append_images=frames[1:], duration=DURATION_MS,
                   loop=0, disposal=2, optimize=False)
    with Image.open(destination) as gallery:
        assert gallery.n_frames == len(FRAMES)
        for i in range(gallery.n_frames):
            gallery.seek(i)
            gallery.load()
            assert gallery.info['duration'] == DURATION_MS
            if '--qa' in sys.argv:
                gallery.convert('RGB').save(ROOT / f'.gallery-qa-{i+1}.png')
    assert destination.stat().st_size < 5 * 1024 * 1024
    manifest = {
        'identity':'Gallery of native Origin exports; a result slideshow, not a UI recording',
        'source_export_date':'2026-11-18', 'width':WIDTH, 'height':HEIGHT,
        'duration_ms_per_frame':DURATION_MS, 'loop':True, 'sources':sources,
        'gallery_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
        'bytes':destination.stat().st_size, 'license':'CC-BY-4.0',
    }
    (ROOT/'gallery.sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frames':len(FRAMES),'bytes':destination.stat().st_size,'duration_ms_per_frame':DURATION_MS}))


if __name__ == '__main__':
    main()
