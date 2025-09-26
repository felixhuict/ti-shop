import os
import re
import json
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

def scrape_downloaded_pages(folder_path="downloaded_pages"):
    data = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".html"):
            file_path = os.path.join(folder_path, filename)
            product_data = extract_product_data_from_html(file_path)
            if product_data:
                data.append(product_data)
    return data

def main():
    output_file = "data.json"
    extracted_data = scrape_downloaded_pages("downloaded_pages")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)

    print(f"✅ {len(extracted_data)} items written to {output_file}")

if __name__ == "__main__":
    main()
