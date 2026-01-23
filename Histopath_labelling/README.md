# Histopathology Image Labelling Tool 🩺

> **Clinical-grade GUI tool** for expert annotation of histopathology images with **pathology-correct multi-tier grading**. Designed for OSCC/OPMD precancer research pipelines with regulatory-ready audit trails.

## 🎯 Pathology-Correct Grading Logic

| Primary Diagnosis | Secondary Rules                                                    |
| :---------------- | :----------------------------------------------------------------- |
| **Normal**        | Tissue: **Stroma** / **Epithelium** / **Both**                     |
| **Dysplasia**     | **Low/High Risk** + **Mild/Moderate/Severe** **OR** **Ungradable** |
| **Cancer**        | **Well/Moderate/Poor** Differentiation **OR** **Ungradable**       |
| **Indeterminate** | **Mandatory free-text reason**                                     |

> **⚠️ Ungradable = Grading state** (not diagnosis)

## ✨ Key Features

- **🖼️ Full-Screen Viewer**: Adaptive zoom/pan (Tkinter + PIL)
- **⚡ Clickable Progress**: Jump to any image instantly
- **🎯 Case Alerts**: Visual banner on patient change
- **💾 Auto-Save**: Every 25 images + manual save
- **📊 Live Summary**: Case-wise statistics sidebar
- **⏱️ Time Tracking**: Per-image timing analytics
- **🔒 Smart Validation**: Comment enforcement for uncertainty
- **📋 Regulatory Audit**: Complete session report

## 📁 Expected Dataset Structure

```
Dataset_Root/
├── Case_001/
│   └── Visit_1/
│       └── Histopath/              # Must contain "histopath"
│           └── Tongue/
│               ├── 10x/            # 10x, 20x, 40x
│               │   └── img1.jpg
│               └── 40x/
│                   └── img2.tif
└── Case_002/
```

> **Rules**: `histopath` in folder name, magnification folders (10x/20x/40x), formats: `.jpg/.png/.tif`

## 🛠️ Installation

### Prerequisites

```bash
python --version  # ≥ 3.8 required
```

### 1. Tkinter (GUI)

| Platform          | Command                           |
| :---------------- | :-------------------------------- |
| **Ubuntu/Debian** | `sudo apt-get install python3-tk` |
| **RHEL/CentOS**   | `sudo yum install tkinter`        |
| **Arch**          | `sudo pacman -S tk`               |
| **macOS**         | `brew install python-tk`          |
| **Windows**       | ✅ Bundled                        |

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
double-click RUN_Histopath_labeller.exe
```

### Linux/macOS

```bash
# Executable via Wine (Linux)
wine RUN_Histopath_labeller.exe

# Source code
python3 histopath_label_tool.py
```

## 🎯 Workflow

```
1. Select Dataset Root 📁
2. Choose Output CSV 📊
3. Enter Annotator Name ✍️
4. Grade Images (Diagnosis → Subtype → Comment) 🎯
5. Auto-save + Progress Tracking ⏳
6. Export CSV + Audit Report 🎉
```

## 📊 Output Files

### 1. **Labels CSV** `histopath_labels.csv`

```csv
Case_ID,Visit_ID,Body_Site,Magnification,Image_File,Diagnosis,Subtype,Comment,Time_Spent_sec,Annotator,Timestamp
Case_001,Visit_1,Tongue,10x,img1.jpg,Dysplasia,Low Risk+Mild,,25,Dr.Suraj,2026-01-23T11:30:00
Case_001,Visit_1,Tongue,40x,img2.tif,Cancer,Well,,42,Dr.Suraj,2026-01-23T11:31:00
```

### 2. **Audit Report** `histopath_labels_summary.txt`

```
🏥 HISTOPATHOLOGY ANNOTATION AUDIT REPORT
Annotator: Dr. Annotator1
Session: 2026-01-23 11:00-14:30 (3h 30m)
Images: 189/567 (33.3%) | Cases: 12 unique

⏱️ TIMING ANALYTICS
Avg: 38s | Median: 32s | Fastest: 15s | Slowest: 127s
Productivity: 56 images/hour

🏷️ DIAGNOSIS BREAKDOWN
Normal: 12.2% | Dysplasia: 41.8% | Cancer: 28.0% | Indeterminate: 18.0%

✅ COMPLIANCE: All Indeterminate/Ungradable have comments
```

**Perfect for**: Ethics submissions, concordance studies, AI ground truth

## 🎨 Designed For

| Research Area                    | ✅ Supported |
| :------------------------------- | :----------- |
| **OSCC/OPMD annotation**         | ✅           |
| **Multi-magnification grading**  | ✅           |
| **Inter-institutional datasets** | ✅           |
| **AI model benchmarking**        | ✅           |
| **AIIMS/MIDAS compliance**       | ✅           |

## 🔒 Clinical Logic Compliance

| Feature                     | ✅ Enforced           |
| :-------------------------- | :-------------------- |
| Ungradable ≠ Diagnosis      | ✅ Grading state only |
| Indeterminate → Comment     | ✅ Mandatory          |
| Dysplasia: Binary + 3-Tier  | ✅ Structured         |
| Cancer: WHO Differentiation | ✅ Well/Moderate/Poor |
| Timing Quality Metrics      | ✅ Per-image tracking |

## 🔮 Data Safety

| Feature              | Status                   |
| :------------------- | :----------------------- |
| Non-destructive      | ✅ Images never modified |
| Fully offline        | ✅ Local processing      |
| Unicode-safe exports | ✅ CSV/TXT               |
| Full path uniqueness | ✅ No collisions         |
| Timestamped audit    | ✅ Regulatory-ready      |

## 💾 Repository Structure

```
histopath_labeller/
├── histopath_label_tool.py
├── RUN_Histopath_labeller.exe
├── requirements.txt
└── README.md
```
