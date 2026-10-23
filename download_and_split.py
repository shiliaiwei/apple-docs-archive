#!/usr/bin/env python3
import os
import re
import sys
import time
import json
import urllib.request
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # PyMuPDF

WORKSPACE_DIR = "/Users/Apple16/Documents/Social_Media/pple"
ORIGINALS_DIR = os.path.join(WORKSPACE_DIR, "original_pdfs")
SPLIT_DIR = os.path.join(WORKSPACE_DIR, "split_pages")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SEED_URLS = [
    "https://developer.apple.com/accessories/dimensional-drawings/",
    "https://developer.apple.com/accessories/",
    "https://developer.apple.com/accessories/Accessory-Design-Guidelines.pdf"
]

def fetch_pdf_urls():
    found_urls = set()
    found_urls.add("https://developer.apple.com/accessories/Accessory-Design-Guidelines.pdf")
    
    crawl_pages = [
        "https://developer.apple.com/accessories/dimensional-drawings/",
        "https://developer.apple.com/accessories/"
    ]
    
    for page_url in crawl_pages:
        req = urllib.request.Request(page_url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            for m in re.findall(r'href=[\"\']([^\"\']+)[\"\']', html, re.IGNORECASE):
                if ".pdf" in m.lower():
                    clean_m = m.split("?")[0].split("#")[0]
                    full_url = urljoin(page_url, clean_m)
                    found_urls.add(full_url)
        except Exception as e:
            print(f"[WARN] Failed fetching {page_url}: {e}")
            
    return sorted(found_urls)

def download_file(url, target_path, retries=3):
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()
                
            if len(content) == 0:
                raise ValueError("Empty file received")
            
            # verify PDF signature
            if not content.startswith(b"%PDF"):
                raise ValueError(f"Content does not start with %PDF header: {content[:30]}")
                
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(content)
            return True, len(content), None
        except Exception as e:
            if attempt < retries:
                time.sleep(2 * attempt)
            else:
                return False, 0, str(e)

def split_pdf(orig_path, target_folder, pdf_stem):
    try:
        doc = fitz.open(orig_path)
        total_pages = len(doc)
        if total_pages == 0:
            doc.close()
            return 0, "No pages found"
            
        os.makedirs(target_folder, exist_ok=True)
        digits = max(3, len(str(total_pages)))
        
        for idx in range(total_pages):
            page_num_str = f"{idx + 1:0{digits}d}"
            out_filename = f"{pdf_stem}_page_{page_num_str}.pdf"
            out_filepath = os.path.join(target_folder, out_filename)
            
            # extract single page
            sub_doc = fitz.open()
            sub_doc.insert_pdf(doc, from_page=idx, to_page=idx)
            sub_doc.save(out_filepath, garbage=4, deflate=True)
            sub_doc.close()
            
        doc.close()
        return total_pages, None
    except Exception as e:
        return 0, str(e)

def process_single_pdf(url):
    filename = url.split("/")[-1]
    pdf_stem = os.path.splitext(filename)[0]
    orig_path = os.path.join(ORIGINALS_DIR, filename)
    target_split_dir = os.path.join(SPLIT_DIR, pdf_stem)
    
    # 1. Download
    ok, size, err = download_file(url, orig_path)
    if not ok:
        return {
            "url": url,
            "filename": filename,
            "status": "failed_download",
            "error": err,
            "size_bytes": 0,
            "pages": 0
        }
        
    # 2. Split
    pages, split_err = split_pdf(orig_path, target_split_dir, pdf_stem)
    if split_err:
        return {
            "url": url,
            "filename": filename,
            "status": "failed_split",
            "error": split_err,
            "size_bytes": size,
            "pages": 0
        }
        
    return {
        "url": url,
        "filename": filename,
        "stem": pdf_stem,
        "status": "success",
        "size_bytes": size,
        "pages": pages,
        "original_path": orig_path,
        "split_folder": target_split_dir
    }

def main():
    start_time = time.time()
    print(">>> Discovering all Apple Developer Accessories PDF URLs...")
    pdf_urls = fetch_pdf_urls()
    total_count = len(pdf_urls)
    print(f">>> Found {total_count} unique PDF files to download and split.")
    
    results = []
    success_count = 0
    total_split_pages = 0
    total_download_bytes = 0
    
    # Execute with ThreadPoolExecutor
    print(">>> Starting concurrent download and page splitting...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_single_pdf, url): url for url in pdf_urls}
        done_count = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            done_count += 1
            if res["status"] == "success":
                success_count += 1
                total_split_pages += res["pages"]
                total_download_bytes += res["size_bytes"]
                print(f"[{done_count}/{total_count}] OK: {res['filename']} ({res['pages']} pages, {res['size_bytes']/(1024*1024):.2f} MB)")
            else:
                print(f"[{done_count}/{total_count}] ERR: {res['filename']} -> {res.get('error')}")
                
    # Sort results alphabetically
    results.sort(key=lambda x: x["filename"].lower())
    
    # Save manifest.json
    manifest_path = os.path.join(WORKSPACE_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_files": total_count,
            "success_count": success_count,
            "total_split_pages": total_split_pages,
            "total_download_bytes": total_download_bytes,
            "results": results
        }, f, indent=2)
        
    # Generate clean markdown index
    summary_md_path = os.path.join(WORKSPACE_DIR, "INDEX.md")
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write("# Apple Accessories Dimensional Drawings & Guidelines\n\n")
        f.write(f"- Total Downloaded: {success_count}/{total_count}\n")
        f.write(f"- Total Split Pages: {total_split_pages}\n")
        f.write(f"- Total Size: {total_download_bytes / (1024 * 1024):.2f} MB\n\n")
        f.write("| No. | Document / Device | Pages | Original File | Split Folder |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for i, item in enumerate(results, 1):
            if item["status"] == "success":
                orig_rel = f"[Download](original_pdfs/{item['filename']})"
                split_rel = f"[Browse Pages ({item['pages']})](split_pages/{item['stem']}/)"
                f.write(f"| {i} | {item['stem']} | {item['pages']} | {orig_rel} | {split_rel} |\n")
            else:
                f.write(f"| {i} | {item['filename']} | Error | Failed | {item.get('error')} |\n")

    elapsed = time.time() - start_time
    print(f"\n==========================================")
    print(f"COMPLETED in {elapsed:.1f}s")
    print(f"Success: {success_count}/{total_count}")
    print(f"Total split pages created: {total_split_pages}")
    print(f"Total size: {total_download_bytes / (1024*1024):.2f} MB")
    print(f"==========================================")

if __name__ == "__main__":
    main()
