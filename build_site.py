#!/usr/bin/env python3
"""يجهّز مجلد site/ للنشر على استضافة ثابتة (مثل GitHub Pages): نسخة من اللعبة باسم index.html وبنك الأسئلة."""
import hashlib, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
os.makedirs(OUT, exist_ok=True)
# رقم نسخة للبنك من محتواه: لما يتغير البنك يتغير الرابط، فالمتصفح ما يعلق على نسخة قديمة
ver = hashlib.md5(open(os.path.join(HERE, "bank.js"), "rb").read()).hexdigest()[:8]
html = open(os.path.join(HERE, "fazaa.html"), encoding="utf-8").read().replace('<script src="bank.js"></script>', f'<script src="bank.js?v={ver}"></script>')
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
shutil.copyfile(os.path.join(HERE, "bank.js"), os.path.join(OUT, "bank.js"))
open(os.path.join(OUT, ".nojekyll"), "w").close()
print("site/ جاهز:", sorted(os.listdir(OUT)))
