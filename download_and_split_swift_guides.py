#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # PyMuPDF

WORKSPACE_DIR = "/Users/Apple16/Documents/Social_Media/pple"
ORIGINALS_DIR = os.path.join(WORKSPACE_DIR, "original_pdfs")
SPLIT_DIR = os.path.join(WORKSPACE_DIR, "split_pages")

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

SWIFT_URLS = [
    "https://www.apple.com/education/docs/everyone-can-code-curriculum-guide.pdf",
    "https://www.apple.com/education/docs/develop-in-swift-curriculum-guide.pdf",
    "https://www.apple.com/education/docs/everyone-can-code-early-learners.pdf",
    "https://www.apple.com/education/docs/app-showcase-guide.pdf",
    "https://education-static.apple.com/teaching-code/student-survey.pdf"
]

def download_file(url, target_path, retries=3):
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as resp:
                content = resp.read()
                
            if len(content) == 0:
                raise ValueError("Empty file received")
            
            if not content.startswith(b"%PDF"):
                raise ValueError(f"Not a valid PDF header: {content[:30]}")
                
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
    
    print(f"Downloading {filename}...")
    ok, size, err = download_file(url, orig_path)
    if not ok:
        print(f"Failed to download {filename}: {err}")
        return {"url": url, "filename": filename, "status": "failed_download", "error": err}
        
    print(f"Splitting {filename} ({size/(1024*1024):.2f} MB)...")
    pages, split_err = split_pdf(orig_path, target_split_dir, pdf_stem)
    if split_err:
        print(f"Failed to split {filename}: {split_err}")
        return {"url": url, "filename": filename, "status": "failed_split", "error": split_err}
        
    print(f"Completed {filename}: {pages} pages split.")
    return {
        "url": url,
        "filename": filename,
        "stem": pdf_stem,
        "status": "success",
        "size_bytes": size,
        "pages": pages,
        "category": "Swift & Coding Curriculum"
    }

def update_manifest_and_index(new_results):
    manifest_path = os.path.join(WORKSPACE_DIR, "manifest.json")
    existing_data = {"results": []}
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    # merge results
    existing_filenames = {r["filename"] for r in existing_data.get("results", [])}
    for r in new_results:
        if r["filename"] not in existing_filenames:
            existing_data["results"].append(r)
        else:
            for i, ex in enumerate(existing_data["results"]):
                if ex["filename"] == r["filename"]:
                    existing_data["results"][i] = r
                    
    results = sorted(existing_data["results"], key=lambda x: x["filename"].lower())
    
    total_files = len(results)
    success_count = sum(1 for r in results if r.get("status") == "success")
    total_split_pages = sum(r.get("pages", 0) for r in results if r.get("status") == "success")
    total_download_bytes = sum(r.get("size_bytes", 0) for r in results if r.get("status") == "success")
    
    existing_data["total_files"] = total_files
    existing_data["success_count"] = success_count
    existing_data["total_split_pages"] = total_split_pages
    existing_data["total_download_bytes"] = total_download_bytes
    existing_data["results"] = results
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2)
        
    # Write updated INDEX.md
    summary_md_path = os.path.join(WORKSPACE_DIR, "INDEX.md")
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write("# Apple Developer & Education Official PDF Library\n\n")
        f.write(f"- Total Downloaded: {success_count}/{total_files}\n")
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

def main():
    print(">>> Starting download and splitting of official Apple Swift & coding curriculum guides...")
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_single_pdf, url): url for url in SWIFT_URLS}
        for fut in as_completed(futures):
            results.append(fut.result())
            
    update_manifest_and_index(results)
    print(">>> Done! Manifest and INDEX.md updated.")

if __name__ == "__main__":
    main()
