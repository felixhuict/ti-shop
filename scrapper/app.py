import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

visited = set()

def is_valid_url(url, base_netloc):
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and parsed.netloc == base_netloc

def sanitize_filename(url):
    path = urlparse(url).path
    if path == '' or path == '/':
        return 'index.html'
    if path.endswith('/'):
        path += 'index.html'

    # Removing the first two parts of the url.
    return "/".join(path.strip('/').split('/')[2:])

def save_page(url, content, output_dir="downloaded_pages"):
    os.makedirs(output_dir, exist_ok=True)
    filename = sanitize_filename(url)
    filepath = os.path.join(output_dir, filename)

    # Write file into the directory
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[+] Saved {url} → {filepath}")

def crawl(url, base_url, base_netloc):
    if url in visited:
        return
    visited.add(url)
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"[-] Skipping {url}: status {response.status_code}")
            return
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return  # Skip non-HTML
        save_page(url, response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            full_url = urljoin(url, href)
            if is_valid_url(full_url, base_netloc):
                crawl(full_url, base_url, base_netloc)
        time.sleep(1)  # Be polite
    except requests.RequestException as e:
        print(f"[-] Failed to crawl {url}: {e}")

if __name__ == "__main__":
    start_url = "https://hu-hbo-ict.gitlab.io/turing-lab/ti-lab-shop/"
    parsed_start = urlparse(start_url)
    crawl(start_url, start_url, parsed_start.netloc)
