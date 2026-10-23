# Apple Master Documentation & Developer Archive

Comprehensive repository containing Apple's complete master corporate, product, and legacy developer technical documentation, catalogs, and automation tools.

- **Total Documents & Assets**: 5,930 files (3.13 GB)
- **Developer Documentation Archive**: 5,198 files (1985–2018 historical documentation spanning macOS, iOS, watchOS, tvOS)
- **Master Corporate & Product PDFs**: 732 documents (Hardware drawings, Product Environmental Reports, ESG, AppleCare policies, Whitepapers)
- **Remote Cloud Storage Mirror**: [Google Drive Archive](https://drive.google.com/drive/folders/1tr0Emo4S2xsmU4dGNGdGRumQBo38uveP) (Folder ID: `1tr0Emo4S2xsmU4dGNGdGRumQBo38uveP`)

---

## Repository Structure

```
.
├── standard_library/                     # Standardized, categorized document hierarchy
│   ├── 01_Product_Environmental_Reports/ # Device PERs (iPhone, Mac, iPad, Watch, Audio, TV, iPod, Displays)
│   ├── 02_Environmental_Progress_and_ESG/# Annual progress reports (2008–2025), Green Bonds, Carbon neutrality
│   ├── 03_AppleCare_and_Warranty_Certificates/ # State-by-state warranty & AppleCare+ coverage terms
│   ├── 04_Swift_and_Education/           # Swift Playgrounds, Everyone Can Code, Teacher/Student guides
│   ├── 05_Privacy_Security_and_Whitepapers/ # Platform security, Private Relay, Data privacy whitepapers
│   ├── 06_Ethics_Compliance_and_Legal/   # Business conduct, Supplier Code of Conduct, Conflict Minerals, EEO-1
│   ├── 07_Health_and_Clinical_Research/  # Apple Heart Study, Hearing health, Mobility research
│   └── 08_Hardware_Accessories_Drawings/ # Accessory design guidelines & dimensional drawings
│
├── developer_archive/                    # Apple Developer Documentation Archive (1985–2018)
│   ├── 01_Sample_Code_Zips/              # 1,945 Xcode project source archives (.zip & docs)
│   ├── 02_Technical_QAs/                 # 1,519 Technical Q&A documents (.html)
│   ├── 03_Technical_Notes/               # 808 Technical Notes (.html)
│   ├── 04_Guides/                        # 681 Framework & architecture guides (.html)
│   ├── 05_Release_Notes/                 # 218 API diffs & SDK release notes (.html)
│   ├── 06_Getting_Started/               # 22 Getting started starter guides (.html)
│   ├── 07_Xcode_Tasks/                   # 3 Xcode task guides (.html)
│   └── 08_Articles/                      # 2 Technical articles (.html)
│
├── original_pdfs/                        # 732 master flat PDF files (mirrored on Google Drive)
├── INDEX.md                              # Master catalog and navigation table
├── manifest.json                         # Full machine-readable document metadata
│
├── download_developer_archive.py         # Multi-threaded crawler for Apple Developer Archive
├── organize_standard_library.py          # APFS zero-overhead library classification engine
└── upload_to_gdrive.py                   # Multi-threaded Google Drive synchronization engine
```

---

## Document Taxonomy & Classification

| Category | Subcategory | File Count | Primary Format | Storage Target |
| :--- | :--- | :--- | :--- | :--- |
| **Product Environmental Reports** | iPhone (75), Mac (111), iPad (63), Watch (53), Audio (17), TV/Vision (13), iPod (14), Displays (46) | 392 files | `.pdf` | Google Drive / Local |
| **Environmental Progress & ESG** | Annual Progress Reports (2008–2025), Green Bonds, Facilities, Packaging | 26 files | `.pdf` | Google Drive / Local |
| **AppleCare & Warranty Terms** | State-by-State Coverage Certificates, Service Terms, AIG Policies | 271 files | `.pdf` | Google Drive / Local |
| **Swift & Education Curriculum** | Everyone Can Code, Swift Playgrounds, App Development with Swift | 6 files | `.pdf` | Google Drive / Local |
| **Privacy, Security & Whitepapers** | Apple Platform Security, Private Relay, Trusted Ecosystem, Safari Privacy | 15 files | `.pdf` | Google Drive / Local |
| **Ethics, Compliance & Legal** | Business Conduct, Supplier Code of Conduct, Human Rights, Conflict Minerals | 13 files | `.pdf` | Google Drive / Local |
| **Health & Clinical Research** | Apple Heart Study, Hearing Health, Mobility Research Studies | 8 files | `.pdf` | Google Drive / Local |
| **Hardware Accessories Drawings** | Accessory Design Guidelines & Dimensional Specifications | 1 file | `.pdf` | Google Drive / Local |
| **Developer Documentation Archive** | Sample Code, Technical Notes, Q&As, Guides, Release Notes, Getting Started | 5,198 files | `.html` / `.zip` | GitHub + Google Drive |

---

## Heavy Binary Assets Storage Policy

Per GitHub repository size guidelines and the workspace policy, all heavy binary assets (`.pdf` and `.zip` archives, totaling 3.13 GB) are permanently stored and mirrored in the official **Google Drive Repository**:

- **Google Drive Folder**: `Apple_Developer_Accessories_and_Swift_PDFs`
- **Folder URL**: [https://drive.google.com/drive/folders/1tr0Emo4S2xsmU4dGNGdGRumQBo38uveP](https://drive.google.com/drive/folders/1tr0Emo4S2xsmU4dGNGdGRumQBo38uveP)
- **Local Mirror**: Kept intact on local storage in `original_pdfs/` and `standard_library/` using APFS zero-cost hard links.

---

## Automation Scripts

1. **`download_developer_archive.py`**:
   - Asynchronously parses `library.json` from Apple Developer Archive.
   - Concurrently downloads all 5,219 items with automatic fallback and checkpoint resumption.
2. **`organize_standard_library.py`**:
   - Categorizes all 732 master PDFs into standard topic and device folders.
   - Employs APFS hard links to ensure 0 bytes duplicate disk consumption.
3. **`upload_to_gdrive.py`**:
   - Multi-threaded uploader supporting resume tokens, automated directory creation, and rate-limit backoff.
