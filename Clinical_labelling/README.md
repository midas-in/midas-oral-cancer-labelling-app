# Clinical Image Labelling Tool 🚀

> **Clinical-grade GUI application** for systematic annotation of clinical images across multi-case, multi-visit datasets. Designed for medical research, AI training workflows, and regulatory-compliant documentation with full audit trail and productivity analytics.

## ✨ Features

- **📁 Hierarchical Navigation**: `Case → Visit → XC/CLINICAL → Images`
- **🖼️ High-Res Viewer**: Tkinter + PIL (zoom, pan, fullscreen)
- **⚡ One-Click Labels**: **Suspicious** / **Non-Suspicious** / **NA** (mandatory comment)
- **🎯 Smart UX**: Case-change alerts, previous label display, back navigation
- **💾 Auto-Save**: Progress saved anytime (partial CSV + summary)
- **📋 Review Mode**: Final table view before export
- **📊 Analytics Dashboard**: Per-case stats, timing metrics, productivity reports

## 📂 Expected Folder Structure

```
Batch_Folder/
├── Case_001/
│   ├── Visit_1/
│   │   └── XC_CLINICAL/           # Must contain XC or CLINICAL
│   │       ├── img1.jpg
│   │       └── img2.png
│   └── Visit_2/
│       └── CLINICAL_IMAGES/
└── Case_002/
    └── Visit_1/
        └── XC/
```

> **Note**: Folder names must contain `XC` or `CLINICAL` (case-insensitive)

## 🛠️ Installation

### Prerequisites

```bash
# Python ≥ 3.8 required
python --version
```

### 1. Tkinter (GUI)

| Platform          | Command                           |
| :---------------- | :-------------------------------- |
| **Ubuntu/Debian** | `sudo apt-get install python3-tk` |
| **RHEL/CentOS**   | `sudo yum install tkinter`        |
| **Arch Linux**    | `sudo pacman -S tk`               |
| **macOS**         | `brew install python-tk`          |
| **Windows**       | ✅ Bundled with Python            |

**Verify**:

```bash
python -m tkinter
```

### 2. Pillow (Images)

```bash
pip install pillow
```

## 🚀 Quick Start

### Windows (Recommended)

```
double-click RUN_XC_labeller.exe
```

### Linux

```bash
# Via Wine
wine RUN_XC_labeller.exe

# Source
python3 clinical_label_tool.py
```

### macOS

```bash
python3 clinical_label_tool.py
```

## 🎯 Workflow

```
1. Select Batch Folder ✅
2. Choose Output CSV 📁
3. Enter Annotator Name ✍️
4. Start Labeling (Suspicious/Non-Suspicious/NA) ⚡
5. Review Table View 👀
6. Export CSV + Summary Report 🎉
```

## 📊 Output Files

### 1. **Labels CSV** `clinical_labels.csv`

```csv
case,visit,file,label,comment
Case_001,Visit_1,img1.jpg,Suspicious,
Case_001,Visit_1,img2.png,Non-Suspicious,
Case_002,Visit_1,img1.jpg,NA,"Needs second opinion"
```

**Ready for**:

- Model training
- Ground-truth benchmarking
- QC audits

### 2. **Audit Report** `clinical_labels_summary.txt`

```
📊 ANNOTATION SESSION REPORT
Annotator: Dr. Annotator1
Session: 2026-01-23 11:00 - 13:30 (2h 30m)
Images: 245 labeled / 755 total (32.5% complete)

⏱️ TIMING METRICS
Avg: 22s/image | Fastest: 8s | Slowest: 89s | Median: 19s
Productivity: 98 images/hour

🏷️ LABEL DISTRIBUTION
Suspicious: 23.7% (58) | Non-Suspicious: 67.3% (165) | NA: 9.0% (22)

📝 NA COMMENTS LOG
Case_002/Visit_1/img1.jpg: "Needs second opinion"
```

**Suitable for**:

- IRB / Ethics submissions
- Inter-institutional benchmarking
- Annotation quality assurance
- Clinical AI pipeline documentation

## 🎨 Designed For

| Use Case                                          | ✅ Supported |
| :------------------------------------------------ | :----------- |
| Clinical dataset curation                         | ✅           |
| Multi-center annotation pipelines                 | ✅           |
| AI training/validation datasets                   | ✅           |
| Medical audit/compliance (AIIMS/MIDAS)            | ✅           |
| Histopathology, fundus, WSI, clinical photography | ✅           |

## 🔒 Data Safety

| Feature                | Status                      |
| :--------------------- | :-------------------------- |
| Non-destructive        | ✅ Originals never modified |
| Local processing       | ✅ Fully offline            |
| User-controlled output | ✅ Custom save locations    |
| Unicode-safe           | ✅ CSV/TXT exports          |
| Full audit trail       | ✅ Timestamp + annotator    |

## 🔮 Future Extensions (v2.0)

- `🔒` Case-level diagnosis enforcement
- `⏭️` Locked progression (complete case before next)
- `📈` Inter-annotator agreement (Cohen's κ)
- `🩻` DICOM viewer integration
- `🔐` Encrypted audit trails for clinical trials

## 💾 Repository Structure

```
clinical_labeller/
├── clinical_label_tool.py
├── RUN_XC_labeller.exe
├── requirements.txt
└── README.md
```
