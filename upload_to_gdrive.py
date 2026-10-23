#!/usr/bin/env python3
import os
import sys
import time
import json
import threading
import mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

WORKSPACE_DIR = "/Users/Apple16/Documents/Social_Media/pple"
CREDENTIALS_PATH = "/Users/Apple16/.credentials/gdrive_user_token.json"
ROOT_FOLDER_NAME = "Apple_Developer_Accessories_and_Swift_PDFs"
ROOT_FOLDER_ID = "1tr0Emo4S2xsmU4dGNGdGRumQBo38uveP"

CHECKPOINT_PATH = os.path.join(WORKSPACE_DIR, ".gdrive_upload_checkpoint.json")
FOLDER_CACHE_PATH = os.path.join(WORKSPACE_DIR, ".gdrive_folder_cache.json")

folder_lock = threading.Lock()
folder_cache = {"": ROOT_FOLDER_ID}

checkpoint_lock = threading.Lock()
uploaded_files = set()

# Load checkpoint
if os.path.exists(CHECKPOINT_PATH):
    try:
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            uploaded_files = set(json.load(f))
    except Exception:
        pass

# Load folder cache
if os.path.exists(FOLDER_CACHE_PATH):
    try:
        with open(FOLDER_CACHE_PATH, "r", encoding="utf-8") as f:
            folder_cache.update(json.load(f))
    except Exception:
        pass

def save_checkpoint(rel_path):
    with checkpoint_lock:
        uploaded_files.add(rel_path)
        if len(uploaded_files) % 25 == 0:
            with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
                json.dump(list(uploaded_files), f)

def flush_checkpoint():
    with checkpoint_lock:
        with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
            json.dump(list(uploaded_files), f)

def save_folder_cache():
    with folder_lock:
        with open(FOLDER_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(folder_cache, f, indent=2)

def get_drive_service():
    with open(CREDENTIALS_PATH) as f:
        token_data = json.load(f)
    creds = Credentials.from_authorized_user_info(token_data)
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def get_or_create_folder(service, rel_dir_path):
    if not rel_dir_path:
        return ROOT_FOLDER_ID
        
    with folder_lock:
        if rel_dir_path in folder_cache:
            return folder_cache[rel_dir_path]
            
    # Resolve hierarchy step by step
    parts = rel_dir_path.strip("/").split("/")
    current_rel = ""
    current_parent_id = ROOT_FOLDER_ID
    
    for part in parts:
        current_rel = f"{current_rel}/{part}" if current_rel else part
        with folder_lock:
            if current_rel in folder_cache:
                current_parent_id = folder_cache[current_rel]
                continue
                
        # Check remote or create
        q = f"name = '{part}' and '{current_parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res = service.files().list(q=q, fields="files(id, name)").execute()
        files = res.get("files", [])
        if files:
            folder_id = files[0]["id"]
        else:
            meta = {
                "name": part,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [current_parent_id]
            }
            new_f = service.files().create(body=meta, fields="id").execute()
            folder_id = new_f.get("id")
            
        with folder_lock:
            folder_cache[current_rel] = folder_id
            current_parent_id = folder_id
            
    save_folder_cache()
    return current_parent_id

def upload_single_file(service, abs_path, rel_path, total_count, counter_dict):
    if rel_path in uploaded_files:
        with counter_dict["lock"]:
            counter_dict["done"] += 1
            idx = counter_dict["done"]
        print(f"[{idx}/{total_count}] SKIP (Already uploaded): {rel_path}")
        return True, rel_path
        
    rel_dir = os.path.dirname(rel_path)
    filename = os.path.basename(rel_path)
    
    folder_id = get_or_create_folder(service, rel_dir)
    
    mime_type, _ = mimetypes.guess_type(abs_path)
    if not mime_type:
        if filename.endswith(".md"):
            mime_type = "text/markdown"
        elif filename.endswith(".json"):
            mime_type = "application/json"
        elif filename.endswith(".pdf"):
            mime_type = "application/pdf"
        elif filename.endswith(".zip"):
            mime_type = "application/zip"
        elif filename.endswith(".html") or filename.endswith(".htm"):
            mime_type = "text/html"
        else:
            mime_type = "application/octet-stream"
            
    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }
    
    media = MediaFileUpload(abs_path, mimetype=mime_type, resumable=True)
    
    for attempt in range(1, 4):
        try:
            req = service.files().create(body=file_metadata, media_body=media, fields="id")
            response = None
            while response is None:
                status, response = req.next_chunk()
            save_checkpoint(rel_path)
            with counter_dict["lock"]:
                counter_dict["done"] += 1
                idx = counter_dict["done"]
            print(f"[{idx}/{total_count}] UPLOADED: {rel_path}")
            return True, rel_path
        except Exception as e:
            if attempt < 3:
                time.sleep(2 * attempt)
            else:
                with counter_dict["lock"]:
                    counter_dict["done"] += 1
                    idx = counter_dict["done"]
                print(f"[{idx}/{total_count}] FAILED: {rel_path} -> {e}")
                return False, rel_path

def collect_files_to_upload():
    items = []
    
    # Root manifest and index files
    for root_f in ["INDEX.md", "manifest.json"]:
        abs_p = os.path.join(WORKSPACE_DIR, root_f)
        if os.path.exists(abs_p):
            items.append((abs_p, root_f))
            
    # original_pdfs
    orig_dir = os.path.join(WORKSPACE_DIR, "original_pdfs")
    if os.path.exists(orig_dir):
        for f in sorted(os.listdir(orig_dir)):
            if f.endswith(".pdf"):
                items.append((os.path.join(orig_dir, f), f"original_pdfs/{f}"))
                
    # developer_archive (Sample Code ZIPs and HTML docs)
    archive_dir = os.path.join(WORKSPACE_DIR, "developer_archive")
    if os.path.exists(archive_dir):
        for root, dirs, files in os.walk(archive_dir):
            dirs.sort()
            for f in sorted(files):
                if not f.startswith("."):
                    abs_path = os.path.join(root, f)
                    rel_path = os.path.relpath(abs_path, WORKSPACE_DIR)
                    items.append((abs_path, rel_path))
                        
    return items

def main():
    start_time = time.time()
    files_to_upload = collect_files_to_upload()
    total_count = len(files_to_upload)
    pending_files = [item for item in files_to_upload if item[1] not in uploaded_files]
    pending_count = len(pending_files)
    print(f">>> Found {total_count} total files. Already uploaded: {len(uploaded_files)}. Pending to upload: {pending_count}.")

    counter_dict = {"done": 0, "lock": threading.Lock()}

    thread_local = threading.local()
    def get_thread_service():
        if not hasattr(thread_local, "service"):
            thread_local.service = get_drive_service()
        return thread_local.service

    def worker(item):
        abs_p, rel_p = item
        srv = get_thread_service()
        return upload_single_file(srv, abs_p, rel_p, pending_count, counter_dict)

    print(f">>> Starting multi-threaded upload for {pending_count} files (16 workers)...")
    success_count = 0
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(worker, item) for item in pending_files]
        for fut in as_completed(futures):
            ok, _ = fut.result()
            if ok:
                success_count += 1
                
    flush_checkpoint()
    elapsed = time.time() - start_time
    print("\n==========================================")
    print(f"GOOGLE DRIVE UPLOAD COMPLETE in {elapsed:.1f}s")
    print(f"Uploaded: {success_count}/{total_count} files")
    print(f"Target Google Drive Folder: {ROOT_FOLDER_NAME}")
    print(f"Folder URL: https://drive.google.com/drive/folders/{ROOT_FOLDER_ID}")
    print("==========================================")

if __name__ == "__main__":
    main()
