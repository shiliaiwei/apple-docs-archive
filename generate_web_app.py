#!/usr/bin/env python3
import os
import json
import re

WORKSPACE_DIR = "/Users/Apple16/Documents/Social_Media/pple"
WEB_DIR = os.path.join(WORKSPACE_DIR, "web")
STANDARD_DIR = os.path.join(WORKSPACE_DIR, "standard_library")
DEV_ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "developer_archive")
GDRIVE_ROOT_URL = "https://drive.google.com/drive/folders/1tr0Emo4S2xsmU4dGNGdGRumQBo38uveP"
GITHUB_REPO_URL = "https://github.com/shiliaiwei/apple-docs-archive"

os.makedirs(WEB_DIR, exist_ok=True)

# 1. Collect PDFs from standard_library
docs = []

for root, dirs, files in os.walk(STANDARD_DIR):
    rel_dir = os.path.relpath(root, STANDARD_DIR)
    if rel_dir == ".":
        continue
    parts = rel_dir.split(os.sep)
    category = parts[0].replace("_", " ")
    subcategory = parts[1].replace("_", " ") if len(parts) > 1 else "-"
    
    for f in sorted(files):
        if f.lower().endswith(".pdf"):
            full_path = os.path.join(root, f)
            size = os.path.getsize(full_path)
            clean_title = os.path.splitext(f)[0].replace("_", " ").replace("-", " ")
            docs.append({
                "id": f"pdf_{len(docs)+1}",
                "title": clean_title,
                "filename": f,
                "category": category,
                "subcategory": subcategory,
                "type": "PDF Document",
                "format": "PDF",
                "size_kb": round(size / 1024, 1),
                "url": f"https://developer.apple.com/accessories/", # fallback / gdrive link
                "source": "Apple Corporate & Product",
                "gdrive_url": GDRIVE_ROOT_URL
            })

print(f"Collected {len(docs)} PDFs from standard_library.")

# 2. Collect developer_archive docs from library.json
lib_path = os.path.join(WORKSPACE_DIR, "download_developer_archive.py")
# We can read library.json from cached download script or web
import urllib.request, ssl
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://developer.apple.com/library/archive/navigation/library.json", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, context=ssl_ctx) as r:
    raw = r.read().decode("utf-8", errors="ignore")
cleaned = re.sub(r",\s*([\]\}])", r"\1", raw)
data = json.loads(cleaned)

type_map = {}
for g in data.get("topics", []):
    if g.get("name") == "Resource Types":
        for c in g.get("contents", []):
            type_map[int(c["key"])] = c["name"].replace("&amp;", "&")

cols = data.get("columns", {})
dev_docs = data.get("documents", [])

for d in dev_docs:
    raw_name = d[cols["name"]]
    clean_name = re.sub(r"&quot;", '"', raw_name)
    clean_name = re.sub(r"&amp;", '&', clean_name)
    clean_name = re.sub(r"&lt;", '<', clean_name)
    clean_name = re.sub(r"&gt;", '>', clean_name)
    
    doc_id = d[cols["id"]]
    type_id = d[cols["type"]]
    type_name = type_map.get(type_id, "Documentation")
    date_str = d[cols["date"]]
    raw_url = d[cols["url"]].split("#")[0]
    platform = d[cols["platform"]] or "All Platforms"
    
    is_sample = (type_id == 5)
    fmt = "ZIP" if is_sample else "HTML"
    
    if is_sample:
        parts = raw_url.split("/")
        proj = parts[parts.index("samplecode")+1] if "samplecode" in parts and parts.index("samplecode")+1 < len(parts) else doc_id
        download_url = f"https://developer.apple.com/library/archive/samplecode/{proj}/{proj}.zip"
    else:
        download_url = f"https://developer.apple.com/library/archive/{raw_url.replace('../', '')}"
        
    docs.append({
        "id": f"dev_{doc_id}",
        "title": clean_name,
        "filename": f"{doc_id}_{fmt.lower()}",
        "category": "Developer Documentation Archive",
        "subcategory": type_name,
        "type": type_name,
        "format": fmt,
        "date": date_str,
        "platform": platform,
        "size_kb": 0,
        "url": download_url,
        "source": "Apple Developer (1985–2018)",
        "gdrive_url": GDRIVE_ROOT_URL
    })

print(f"Total documents indexed for web app: {len(docs)}")

# Write data.json
data_file = os.path.join(WEB_DIR, "data.json")
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(docs, f)

print(f"Wrote {data_file} ({os.path.getsize(data_file) / (1024*1024):.2f} MB)")
