"""Crop the first-viewport 'fold' from each session's first screenshot -> fold-first.jpg
Five-second tests must be answered from these (what a visitor sees before scrolling)."""
import os, json
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = os.path.join(ROOT, 'captures')
made = 0
for theme in os.listdir(CAP):
    tdir = os.path.join(CAP, theme)
    if not os.path.isdir(tdir): continue
    for journey in os.listdir(tdir):
        jdir = os.path.join(tdir, journey)
        for device in os.listdir(jdir):
            ddir = os.path.join(jdir, device)
            if not os.path.isdir(ddir): continue
            steps = sorted(f for f in os.listdir(ddir) if f.startswith('step-01'))
            if not steps: continue
            src = os.path.join(ddir, steps[0])
            fold_h = 844 if device == 'mobile' else 900
            try:
                im = Image.open(src)
                im.crop((0, 0, im.width, min(fold_h, im.height))).save(os.path.join(ddir, 'fold-first.jpg'), quality=72)
                made += 1
            except Exception as e:
                print('fail', src, e)
print('folds made:', made)
