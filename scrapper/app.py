import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import threading
import queue

visited = set()
visited_lock = threading.Lock()
downloaded_resources = set()
resource_lock = threading.Lock()
base_path_parts = []
output_root = None

def is_valid_url(url, base_netloc):
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc == base_netloc

def sanitize_filename(url):
    path = urlparse(url).path
    trailing_slash = path.endswith('/')
    parts = [p for p in path.strip('/').split('/') if p]

    # Remove base path prefix (e.g. /turing-lab/ti-lab-shop)
    if base_path_parts and parts[:len(base_path_parts)] == base_path_parts:
        parts = parts[len(base_path_parts):]

    if not parts:
        return 'index.html'

    if trailing_slash:
        parts.append('index.html')

    return "/".join(parts)

def save_page(url, content, output_dir=None):
    if output_dir is None:
        output_dir = output_root or os.path.join("scrapped_data")
    filename = sanitize_filename(url)
    if filename == '':
        filename = 'index.html'
    filepath = os.path.join(output_dir, filename)
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[+] Saved {url} → {filepath}")


def download_resource(url, output_dir=None):
    if output_dir is None:
        output_dir = output_root or os.path.join("scrapped_data")
    filename = sanitize_filename(url)
    if filename == '':
        filename = 'resource'
    filepath = os.path.join(output_dir, filename)
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    try:
        resp = requests.get(url, stream=True, timeout=10)
        if resp.status_code != 200:
            print(f"[-] Skipping resource {url}: status {resp.status_code}")
            return
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"[+] Saved resource {url} → {filepath}")
    except requests.RequestException as e:
        print(f"[-] Failed to download resource {url}: {e}")

def worker(base_netloc, q):
    while True:
        url = q.get()
        if url is None:
            q.task_done()
            break
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"[-] Skipping {url}: status {response.status_code}")
                continue
            if 'text/html' not in response.headers.get('Content-Type', ''):
                continue  # Skip non-HTML

            save_page(url, response.text)
            soup = BeautifulSoup(response.text, 'html.parser')
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                full_url = urljoin(url, href)
                if is_valid_url(full_url, base_netloc):
                    with visited_lock:
                        if full_url not in visited:
                            visited.add(full_url)
                            q.put(full_url)
            # Download images referenced on the page
            for img in soup.find_all('img', src=True):
                src = img['src']
                full_img = urljoin(url, src)
                if is_valid_url(full_img, base_netloc):
                    with resource_lock:
                        if full_img in downloaded_resources:
                            continue
                        downloaded_resources.add(full_img)
                    download_resource(full_img)
            time.sleep(1)  # Be polite
        except requests.RequestException as e:
            print(f"[-] Failed to crawl {url}: {e}")
        finally:
            q.task_done()

if __name__ == "__main__":
    start_url = "https://hu-hbo-ict.gitlab.io/turing-lab/ti-lab-shop/"
    parsed_start = urlparse(start_url)
    base_netloc = parsed_start.netloc
    # determine base path parts to strip from saved filenames
    base_path_parts = [p for p in parsed_start.path.strip('/').split('/') if p]
    # set output root to scrapped_data/<domain>
    output_root = os.path.join("scrapped_data")

    num_threads = 8
    q = queue.Queue()

    with visited_lock:
        visited.add(start_url)
    q.put(start_url)

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(base_netloc, q))
        t.start()
        threads.append(t)

    q.join()

    # Stop workers
    for _ in threads:
        q.put(None)
    for t in threads:
        t.join()
