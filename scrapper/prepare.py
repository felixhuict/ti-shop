import os
import re
import json
import shutil
from bs4 import BeautifulSoup

def extract_product_data_from_html(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    soup = BeautifulSoup(content, "html.parser")

    # --- Product name ---
    h1 = soup.find("h1")
    product_name = h1.get_text(strip=True) if h1 else None

    # --- Price ---
    price_match = re.search(r'price:\s*([\d.,]+ ?€)', content, re.IGNORECASE)
    price = price_match.group(1).strip() if price_match else None

    # --- Drawer number ---
    drawer_match = re.search(r'where:\s*drawer\s*(\d+)', content, re.IGNORECASE)
    drawer = drawer_match.group(1).strip() if drawer_match else None

    # --- Canvas size ---
    canvas = soup.find("canvas")
    canvas_size = {}
    if canvas and canvas.has_attr("width") and canvas.has_attr("height"):
        try:
            canvas_size["width"] = int(canvas["width"])
            canvas_size["height"] = int(canvas["height"])
        except ValueError:
            pass

    # --- Main image filename from JS ---
    image = None
    js_scripts = soup.find_all("script")
    for script in js_scripts:
        if script.string:
            img_match = re.search(r'img\.src\s*=\s*"([^"]+)"', script.string)
            if img_match:
                image = img_match.group(1).strip()
                break

    # --- Fallback image if needed ---
    if not image:
        img_tag = soup.find("img", class_="test")
        if img_tag:
            image = img_tag.get("src")

    # --- Description: first <p> after canvas ---
    description = None
    if canvas:
        next_p = canvas.find_next("p")
        if next_p:
            description = next_p.get_text(strip=True)

    # --- Extract first ctx.arc coordinate only ---
    coordinates = None
    arc_pattern = re.compile(r'ctx\.arc\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,')
    for script in js_scripts:
        if script.string:
            match = arc_pattern.search(script.string)
            if match:
                x, y, r = match.groups()
                coordinates = {"x": float(x), "y": float(y), "radius": float(r)}
                break

    # --- Extra <img class="test"> images (excluding main) ---
    extra_images = []
    for img_tag in soup.find_all("img", class_="test"):
        src = img_tag.get("src")
        if src and src != image:
            extra_images.append(src)

    # --- Skip incomplete entries ---
    if not all([product_name, price, drawer, image]):
        return None

    return {
        "product_name": product_name,
        "price": price,
        "drawer": drawer,
        "image": image,
        "canvas_size": canvas_size,
        "description": description,
        "coordinates": coordinates,
        "extra_images": extra_images
    }

def scrape_downloaded_pages(folder_path="scrapped_data"):
    data = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".html"):
            file_path = os.path.join(folder_path, filename)
            product_data = extract_product_data_from_html(file_path)
            if product_data:
                data.append(product_data)
    return data

def main():
    extracted_data = scrape_downloaded_pages("scrapped_data")

    out_dir = os.path.join("../","webshop", "data")
    os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join("../","webshop", "data.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)

    print(f"✅ {len(extracted_data)} items written to {output_file}")
    # Copy resource files (images, pdfs) from downloaded pages into the data folder
    exts = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.pdf'}
    src_dirs = ["scrapped_data"]
    seen_names = set()
    for src in src_dirs:
        if not os.path.isdir(src):
            continue
        for root, _, files in os.walk(src):
            for fname in files:
                _, ext = os.path.splitext(fname)
                if ext.lower() in exts:
                    src_path = os.path.join(root, fname)
                    dest_name = fname
                    # avoid overwriting files with same name
                    if dest_name in seen_names:
                        base, extension = os.path.splitext(fname)
                        i = 1
                        while True:
                            candidate = f"{base}_{i}{extension}"
                            if candidate not in seen_names:
                                dest_name = candidate
                                break
                            i += 1
                    dest_path = os.path.join(out_dir, dest_name)
                    try:
                        shutil.copy2(src_path, dest_path)
                        seen_names.add(dest_name)
                    except Exception as e:
                        print(f"[-] Failed to copy {src_path} -> {dest_path}: {e}")
    print(f"✅ Copied resources into {out_dir}")

if __name__ == "__main__":
    main()
