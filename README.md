# Midas Oral Cancer Labelling Apps

A comprehensive repository containing two clinical-grade, executable GUI applications for systematic annotation of medical images. Designed for medical research, AI training workflows, and regulatory-compliant documentation at institutional scale (AIIMS / MIDAS).

---

## 📦 Applications Overview

| Application                             | Purpose                                      | Primary Use Case                      |
| :-------------------------------------- | :------------------------------------------- | :------------------------------------ |
| **Clinical Image Labelling Tool**       | Binary classification of clinical images     | Suspicious / Non-Suspicious screening |
| **Histopathology Image Labelling Tool** | Structured diagnosis with multi-tier grading | OSCC / OPMD pathology annotation      |

---

## 🔬 1. Clinical Image Labelling Tool

### Description

Executable application for systematic annotation of clinical images across multi-case, multi-visit datasets. Supports high-throughput screening with full audit trail and timing analytics.

### Features

- Walks directory hierarchy: `Case → Visit → XC / CLINICAL → Images`
- High-resolution image viewer (Tkinter + PIL)
- One-click labels: **Suspicious** / **Non-Suspicious** / **NA** (requires comment)
- Case-change alert banner
- Back navigation and relabeling
- Save progress anytime (partial CSV + summary)
- Final review table before export
- Automatic session summary with productivity metrics

### Expected Folder Structure

```
Batch_Folder/
├── Case_001/
│   ├── Visit_1/
│   │   └── XC_CLINICAL/
│   │       ├── img1.jpg
│   │       └── img2.png
│   └── Visit_2/
│       └── CLINICAL_IMAGES/
└── Case_002/
    └── Visit_1/
        └── XC/
```

> **Note**: Folder name must contain `XC` or `CLINICAL` (case-insensitive)

### How to Run

```bash
# Windows
RUN_XC_labeller.exe

# Linux (via Wine)
wine RUN_XC_labeller.exe

# Source
python3 clinical_label_tool.py
```

### Output Files

| File                          | Description                             |
| :---------------------------- | :-------------------------------------- |
| `clinical_labels.csv`         | Case, Visit, File, Label, Comment       |
| `clinical_labels_summary.txt` | Full audit report with timing analytics |

---

## 🔬 2. Histopathology Image Labelling Tool

### Description

Clinical-grade GUI for expert annotation of histopathology images with structured diagnosis and multi-tier grading for OSCC/precancer research.

### Pathology Grading Logic

| Primary Diagnosis | Secondary Rules                                                 |
| :---------------- | :-------------------------------------------------------------- |
| **Normal**        | Tissue type: Stroma / Epithelium / Both                         |
| **Dysplasia**     | Low/High Risk + Three-Tier (Mild/Moderate/Severe) OR Ungradable |
| **Cancer**        | Three-Tier Differentiation (Well/Moderate/Poor) OR Ungradable   |
| **Indeterminate** | Mandatory free-text reason                                      |

> **Note**: "Ungradable" is a grading state, not primary diagnosis

### Features

- Full-screen adaptive image viewer
- Clickable progress bar (jump to any image)
- Case-change alert banner
- Auto-save every 25 images
- Case-wise sidebar summary
- Time-tracking per image
- Comment enforcement for Indeterminate/Ungradable
- WHO-aligned differentiation grading

### Expected Folder Structure

```
Dataset_Root/
├── Case_001/
│   └── Visit_1/
│       └── Histopath/
│           └── Tongue/
│               ├── 10x/
│               │   └── img1.jpg
│               └── 40x/
│                   └── img2.tif
└── Case_002/
```

> **Rules**: Folder must contain "histopath"; Magnification folders: 10x/20x/40x; Formats: .jpg/.png/.tif

### How to Run

```bash
# Windows
RUN_Histopath_labeller.exe

# Linux (via Wine)
wine RUN_Histopath_labeller.exe

# Source
python3 histopath_label_tool.py
```

### Output Files

| File                           | Description                                                                                                                |
| :----------------------------- | :------------------------------------------------------------------------------------------------------------------------- |
| `histopath_labels.csv`         | Case_ID, Visit_ID, Body_Site, Magnification, Image_File, Diagnosis, Subtype, Comment, Time_Spent_sec, Annotator, Timestamp |
| `histopath_labels_summary.txt` | Regulatory-ready audit document                                                                                            |

---

## 🛠️ Installation

### Prerequisites

1. **Python ≥ 3.8**
2. **Tkinter** (GUI Library)
3. **Pillow** (Image Handling)

### Install Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk
pip install pillow

# macOS
brew install python-tk
pip install pillow

# Windows (Python bundled)
pip install pillow
```

**Verify Tkinter**:

```bash
python -m tkinter
```

**All dependencies**:

```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

**Clinical Images**:

```bash
cd clinical_labeller
python3 clinical_label_tool.py
```

**Histopathology**:

```bash
cd histopath_labeller
python3 histopath_label_tool.py
```

---

## 📊 Workflow Summary

### Clinical Tool

1. Select Batch Folder → Output CSV → Annotator Name
2. Label (Suspicious/Non-Suspicious/NA) → Review table → Export

### Histopathology Tool

1. Select Dataset Root → Output CSV → Annotator Name
2. Structured grading → Auto summary \& audit generated

---

## 📁 Repository Structure

```
medical-annotation-toolkit/
├── clinical_labeller/
│   ├── clinical_label_tool.py
│   ├── RUN_XC_labeller.exe
│   └── README.md
├── histopath_labeller/
│   ├── histopath_label_tool.py
│   ├── RUN_Histopath_labeller.exe
│   └── README.md
├── requirements.txt
└── README.md
```

---

## 🔮 Designed For

- Clinical dataset curation
- OSCC/OPMD histopathology annotation
- Multi-center annotation pipelines
- AI training/validation datasets
- Medical audit/compliance workflows

## 🔒 Data Safety

- ✅ Non-destructive (originals untouched)
- ✅ Fully offline processing
- ✅ User-controlled outputs
- ✅ Unicode-safe CSV exports
- ✅ Time-stamped audit trails

---

## 💡 Best Practices

1. **Before Starting**:

- Ensure your folder structure matches the expected format
- Test with a small dataset first
- Verify all dependencies are installed

2. **During Annotation**:

- Save progress regularly
- Use meaningful comments for NA/Indeterminate cases
- Take breaks to maintain annotation quality

3. **After Completion**:

- Review the summary report for consistency
- Back up both CSV and summary files
- Validate data before using in downstream analysis

---
