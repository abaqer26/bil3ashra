#!/usr/bin/env python3
"""يجهّز مجلد site/ للنشر على استضافة ثابتة (مثل GitHub Pages): نسخة من اللعبة باسم index.html وبنك الأسئلة."""
import os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
os.makedirs(OUT, exist_ok=True)
shutil.copyfile(os.path.join(HERE, "fazaa.html"), os.path.join(OUT, "index.html"))
shutil.copyfile(os.path.join(HERE, "bank.js"), os.path.join(OUT, "bank.js"))
open(os.path.join(OUT, ".nojekyll"), "w").close()
print("site/ جاهز:", sorted(os.listdir(OUT)))
