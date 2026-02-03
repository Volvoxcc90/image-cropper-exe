import json, os
from PIL import Image, ImageEnhance

with open("config.json") as f:
    cfg = json.load(f)

with open("templates/custom_template.json") as f:
    tpl = json.load(f)

def enhance(img):
    img = ImageEnhance.Contrast(img).enhance(cfg["enhance"]["contrast"])
    img = ImageEnhance.Sharpness(img).enhance(cfg["enhance"]["sharpness"])
    img = ImageEnhance.Brightness(img).enhance(cfg["enhance"]["brightness"])
    return img

for file in os.listdir("input"):
    if not file.lower().endswith((".jpg", ".png")):
        continue

    img = Image.open(f"input/{file}").convert("RGB")
    name = os.path.splitext(file)[0]
    os.makedirs(f"output/{name}", exist_ok=True)

    for i, box in enumerate(tpl["crops"], 1):
        part = img.crop(box)
        part = enhance(part)
        part.thumbnail(cfg["resize"])
        part.save(f"output/{name}/{i}.jpg", quality=95)
