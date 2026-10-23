#!/usr/bin/env python3
import urllib.request
import re
import time
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

DOC_EXTENSIONS = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv')

def get_sitemap_links():
    url = 'https://www.apple.com/sitemap/'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    links = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html)
    clean_links = set()
    for l in links:
        if l.startswith('#') or l.startswith('javascript:'):
            continue
        clean = l.split('?')[0].split('#')[0]
        full = urljoin(url, clean)
        if 'apple.com' in full:
            clean_links.add(full)
    return sorted(clean_links)

def scan_page_for_docs(page_url):
    docs = set()
    req = urllib.request.Request(page_url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            # check content-type
            ctype = resp.headers.get('Content-Type', '')
            if any(ext[1:] in ctype.lower() for ext in DOC_EXTENSIONS):
                docs.add(page_url)
                return docs
            html = resp.read().decode('utf-8', errors='ignore')
            
        for m in re.findall(r'href=[\"\']([^\"\']+)[\"\']', html, re.IGNORECASE):
            clean_m = m.split('?')[0].split('#')[0]
            if clean_m.lower().endswith(DOC_EXTENSIONS):
                full_doc_url = urljoin(page_url, clean_m)
                if 'apple.com' in full_doc_url or 'apple' in full_doc_url:
                    docs.add(full_doc_url)
    except Exception:
        pass
    return docs

def main():
    start = time.time()
    sitemap_links = get_sitemap_links()
    total_pages = len(sitemap_links)
    print(f">>> Found {total_pages} sitemap pages to scan.")
    
    all_docs = set()
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_url = {executor.submit(scan_page_for_docs, url): url for url in sitemap_links}
        done = 0
        for fut in as_completed(future_to_url):
            res = fut.result()
            all_docs.update(res)
            done += 1
            if done % 50 == 0 or done == total_pages:
                print(f"[{done}/{total_pages}] Scanned. Current found documents: {len(all_docs)}")
                
    print(f"\n==========================================")
    print(f"CRAWL COMPLETE in {time.time() - start:.1f}s")
    print(f"Total unique document files found: {len(all_docs)}")
    print(f"==========================================")
    
    with open("sitemap_found_docs.txt", "w", encoding="utf-8") as f:
        for d in sorted(all_docs):
            f.write(d + "\n")
            print(d)

if __name__ == "__main__":
    main()
