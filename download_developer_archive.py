#!/usr/bin/env python3
import os
import sys
import re
import json
import ssl
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

WORKSPACE_DIR = "/Users/Apple16/Documents/Social_Media/pple"
ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "developer_archive")
CHECKPOINT_PATH = os.path.join(ARCHIVE_DIR, ".download_checkpoint.json")

TYPE_SUBDIRS = {
    5: "01_Sample_Code_Zips",
    6: "02_Technical_QAs",
    2: "03_Technical_Notes",
    3: "04_Guides",
    7: "05_Release_Notes",
    9: "06_Getting_Started",
    15: "07_Xcode_Tasks",
    12: "08_Articles",
}

DEFAULT_SUBDIR = "09_Other_Docs"

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

checkpoint_lock = threading.Lock()
completed_items = set()

if os.path.exists(CHECKPOINT_PATH):
    try:
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            completed_items = set(json.load(f))
    except Exception:
        pass

def save_checkpoint(doc_key):
    with checkpoint_lock:
        completed_items.add(doc_key)
        if len(completed_items) % 50 == 0:
            with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
                json.dump(list(completed_items), f)

def flush_checkpoint():
    with checkpoint_lock:
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump(list(completed_items), f)

def sanitize_filename(name):
    # decode html entities
    name = re.sub(r"&quot;", '"', name)
    name = re.sub(r"&amp;", '&', name)
    name = re.sub(r"&lt;", '<', name)
    name = re.sub(r"&gt;", '>', name)
    # clean forbidden chars
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name).strip("_")
    return name[:120] if len(name) > 120 else name

def fetch_library_data():
    url = "https://developer.apple.com/library/archive/navigation/library.json"
    print(f">>> Fetching library metadata from {url}...")
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as r:
        raw = r.read().decode("utf-8", errors="ignore")
    cleaned = re.sub(r",\s*([\]\}])", r"\1", raw)
    data = json.loads(cleaned)
    return data

def process_item(doc, cols, counter_dict):
    name = doc[cols["name"]]
    doc_id = doc[cols["id"]]
    type_id = doc[cols["type"]]
    raw_url = doc[cols["url"]].split("#")[0]
    
    unique_key = f"{type_id}_{doc_id}"
    
    if unique_key in completed_items:
        with counter_dict["lock"]:
            counter_dict["done"] += 1
        return True, "skip"
        
    subdir_name = TYPE_SUBDIRS.get(type_id, DEFAULT_SUBDIR)
    target_dir = os.path.join(ARCHIVE_DIR, subdir_name)
    os.makedirs(target_dir, exist_ok=True)
    
    clean_name = sanitize_filename(name) or doc_id
    
    # Handle Sample Code
    if type_id == 5:
        parts = raw_url.split("/")
        proj = None
        if "samplecode" in parts:
            idx = parts.index("samplecode")
            if idx + 1 < len(parts):
                proj = parts[idx + 1]
        if not proj:
            proj = clean_name
            
        zip_url = f"https://developer.apple.com/library/archive/samplecode/{proj}/{proj}.zip"
        dest_file = os.path.join(target_dir, f"{proj}.zip")
        
        # Try downloading zip
        downloaded = False
        try:
            req = urllib.request.Request(zip_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=25) as resp:
                if resp.status == 200:
                    content = resp.read()
                    if len(content) > 100:
                        with open(dest_file, "wb") as f:
                            f.write(content)
                        downloaded = True
        except Exception:
            pass
            
        # Fallback to HTML introduction if zip is not directly available
        if not downloaded:
            base_nav = "https://developer.apple.com/library/archive/navigation/"
            full_html_url = urllib.parse.urljoin(base_nav, raw_url)
            html_dest = os.path.join(target_dir, f"{proj}_doc.html")
            try:
                req = urllib.request.Request(full_html_url, headers=HEADERS)
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as resp:
                    if resp.status == 200:
                        content = resp.read()
                        with open(html_dest, "wb") as f:
                            f.write(content)
                        downloaded = True
            except Exception:
                pass
                
        save_checkpoint(unique_key)
        with counter_dict["lock"]:
            counter_dict["done"] += 1
            if counter_dict["done"] % 100 == 0:
                print(f"[{counter_dict['done']}/{counter_dict['total']}] Processed (Current: {clean_name})")
        return downloaded, "sample_code"
        
    # Handle HTML documentation (Q&As, Technotes, Guides, Release Notes, etc.)
    base_nav = "https://developer.apple.com/library/archive/navigation/"
    full_url = urllib.parse.urljoin(base_nav, raw_url)
    
    # Decide filename
    dest_file = os.path.join(target_dir, f"{doc_id}_{clean_name}.html")
    
    downloaded = False
    try:
        req = urllib.request.Request(full_url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as resp:
            if resp.status == 200:
                content = resp.read()
                with open(dest_file, "wb") as f:
                    f.write(content)
                downloaded = True
    except Exception:
        pass
        
    save_checkpoint(unique_key)
    with counter_dict["lock"]:
        counter_dict["done"] += 1
        if counter_dict["done"] % 100 == 0:
            print(f"[{counter_dict['done']}/{counter_dict['total']}] Processed (Current: {clean_name})")
            
    return downloaded, "doc"

def main():
    start_t = time.time()
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    data = fetch_library_data()
    docs = data.get("documents", [])
    cols = data.get("columns", {})
    total = len(docs)
    print(f">>> Found {total} total archive items in library.json.")
    print(f">>> Already completed in checkpoint: {len(completed_items)} items.")
    
    counter_dict = {
        "done": len(completed_items),
        "total": total,
        "lock": threading.Lock()
    }
    
    pending_docs = [d for d in docs if f"{d[cols['type']]}_{d[cols['id']]}" not in completed_items]
    print(f">>> Pending to download: {len(pending_docs)} items using 24 concurrent workers...")
    
    success_count = 0
    with ThreadPoolExecutor(max_workers=24) as executor:
        futures = [executor.submit(process_item, d, cols, counter_dict) for d in pending_docs]
        for fut in as_completed(futures):
            ok, _ = fut.result()
            if ok:
                success_count += 1
                
    flush_checkpoint()
    elapsed = time.time() - start_t
    
    print("\n==========================================")
    print(f"ARCHIVE DOWNLOAD COMPLETE in {elapsed:.1f}s")
    print(f"Downloaded files saved to: {ARCHIVE_DIR}")
    
    # Calculate stats
    total_files = 0
    total_size = 0
    for root, _, files in os.walk(ARCHIVE_DIR):
        for f in files:
            if not f.startswith("."):
                total_files += 1
                total_size += os.path.getsize(os.path.join(root, f))
                
    print(f"Total Local Files: {total_files}")
    print(f"Total Local Size: {total_size / (1024*1024):.2f} MB ({total_size / (1024*1024*1024):.2f} GB)")
    print("==========================================")

if __name__ == "__main__":
    main()
