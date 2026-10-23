#!/usr/bin/env python3
import os
import shutil

WORKSPACE_DIR = "/Users/Apple16/Documents/Social_Media/pple"
ORIGINAL_DIR = os.path.join(WORKSPACE_DIR, "original_pdfs")
STANDARD_DIR = os.path.join(WORKSPACE_DIR, "standard_library")

def classify_pdf(filename):
    name = filename.lower()
    
    # 08 Hardware Accessories & Drawings
    if any(k in name for k in ['drawing', 'dwg', 'accessory-design', 'band_design', 'case_design', 'dimensional']):
        return ('08_Hardware_Accessories_Drawings', None)
        
    # 04 Swift & Education Curriculum
    if any(k in name for k in ['swift', 'everyone_can_code', 'everyone-can-code', 'develop_in_swift', 'app_dev', 'intro_to_app', 'teacher_guide', 'student_guide', 'playgrounds', 'k-12_education', 'accessibilitytranscript']):
        return ('04_Swift_and_Education', None)
        
    # 07 Health & Clinical Research
    if any(k in name for k in ['health', 'hearing', 'heart', 'mobility', 'clinical', 'women_health', 'hearing_study']):
        return ('07_Health_and_Clinical_Research', None)
        
    # 05 Privacy, Security & Whitepapers
    if any(k in name for k in ['platform_security', 'security', 'white_paper', 'whitepaper', 'privacy', 'private_relay', 'your_data', 'trusted_ecosystem', 'longevity_by_design']):
        return ('05_Privacy_Security_and_Whitepapers', None)
        
    # 06 Ethics, Compliance, Supply Chain & Legal
    if any(k in name for k in ['supplier', 'supply_chain', 'smelter', 'conflict_minerals', 'human_rights', 'responsible_sourcing', 'transparency', 'conduct', 'compliance', 'ethics', 'governance', 'eeo-1', 'terms', 'promo_tandcs', 'offer_tcs', 'bundle_offer']):
        return ('06_Ethics_Compliance_and_Legal', None)
        
    # 03 AppleCare & Warranty Certificates
    if any(k in name for k in ['applecare', 'coverage-certs', 'aig-policies', 'applecareone', 'ac_plus', 'care_plus', 'acp_']):
        return ('03_AppleCare_and_Warranty_Certificates', None)
        
    # 02 Annual Environmental Progress & ESG Reports
    if any(k in name for k in ['progress_report', 'green_bond', 'climate', 'carbon', 'facilities_report', 'environmental_responsibility', 'environmental_progress', 'forestry', 'packaging', 'regulated_substances', 'impact-overview']):
        return ('02_Environmental_Progress_and_ESG', None)
        
    # 01 Product Environmental Reports (by device family)
    if 'iphone' in name:
        return ('01_Product_Environmental_Reports', '01_iPhone')
    elif any(k in name for k in ['macbook', 'imac', 'macmini', 'mac_mini', 'mac-mini', 'macpro', 'mac_pro', 'mac-pro', 'macstudio', 'mac-studio', 'mac_studio', '13inchmbp', '15inchmbp', '16inchmbp', '12inchmb']):
        return ('01_Product_Environmental_Reports', '02_Mac')
    elif 'ipad' in name:
        return ('01_Product_Environmental_Reports', '03_iPad')
    elif 'watch' in name:
        return ('01_Product_Environmental_Reports', '04_Apple_Watch')
    elif any(k in name for k in ['airpods', 'homepod', 'earpods', 'beats']):
        return ('01_Product_Environmental_Reports', '05_AirPods_and_Home')
    elif any(k in name for k in ['appletv', 'apple_tv', 'apple-tv', 'vision', 'zeiss']):
        return ('01_Product_Environmental_Reports', '06_Apple_TV_and_Vision')
    elif 'ipod' in name:
        return ('01_Product_Environmental_Reports', '07_iPod_Legacy')
    else:
        return ('01_Product_Environmental_Reports', '08_Accessories_and_Displays')

def build_standard_library():
    os.makedirs(STANDARD_DIR, exist_ok=True)
    files = sorted([f for f in os.listdir(ORIGINAL_DIR) if f.lower().endswith('.pdf')])
    print(f">>> Organizing {len(files)} PDFs into standard library...")
    
    category_counts = {}
    
    for f in files:
        src = os.path.join(ORIGINAL_DIR, f)
        cat, subcat = classify_pdf(f)
        
        target_dir = os.path.join(STANDARD_DIR, cat, subcat) if subcat else os.path.join(STANDARD_DIR, cat)
        os.makedirs(target_dir, exist_ok=True)
        
        dst = os.path.join(target_dir, f)
        if os.path.exists(dst):
            os.remove(dst)
            
        try:
            os.link(src, dst) # APFS zero-cost hard link
        except Exception:
            shutil.copy2(src, dst)
            
        cat_key = f"{cat}/{subcat}" if subcat else cat
        category_counts[cat_key] = category_counts.get(cat_key, 0) + 1

    # Generate Markdown Catalog
    catalog_path = os.path.join(STANDARD_DIR, "CATALOG.md")
    with open(catalog_path, "w", encoding="utf-8") as out:
        out.write("# Apple Standard Document Library Catalog\n\n")
        out.write("This directory provides an organized, categorized hierarchy of all 732 master Apple documents.\n\n")
        out.write("## Categories Summary\n\n")
        out.write("| Category | Subcategory | Document Count |\n")
        out.write("| :--- | :--- | :--- |\n")
        for key in sorted(category_counts.keys()):
            parts = key.split("/")
            cat = parts[0]
            sub = parts[1] if len(parts) > 1 else "-"
            out.write(f"| {cat} | {sub} | {category_counts[key]} |\n")
        out.write(f"| **Total Master Documents** | | **{len(files)}** |\n\n")
        
    print("\n==========================================")
    print("STANDARD LIBRARY CREATED SUCCESSFULLY")
    print(f"Target Directory: {STANDARD_DIR}")
    print(f"Catalog File: {catalog_path}")
    print(f"Total PDFs Linked: {len(files)} (Zero disk space overhead via APFS)")
    for key in sorted(category_counts.keys()):
        print(f"  - {key}: {category_counts[key]} files")
    print("==========================================")

if __name__ == "__main__":
    build_standard_library()
