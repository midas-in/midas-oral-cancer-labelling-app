#!/usr/bin/env python3
"""
Histopathology Image Labelling Tool - Refactored Grading Interface
Key Changes:
- Ungradable is now a GRADING state, not a primary diagnosis
- Indeterminate remains a primary diagnosis with mandatory comment
- Dysplasia: Binary + Three-Tier OR Ungradable
- Cancer: Three-Tier OR Ungradable
"""

import os
import csv
import time
import re
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

SESSION = {
    "annotator": "",
    "start_time": None,
    "end_time": None,
    "times": [],
    "cases": set(),
    "last_case": None,
}

# ═══════════════════════════════════════════════════════════════════════════
# IMAGE DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════

def extract_magnification(folder_name):
    """Extract magnification value from folder name"""
    match = re.search(r'(\d+)x', folder_name.lower())
    return int(match.group(1)) if match else 0

def find_histopath_images(root):
    """Find all histopathology images in directory structure"""
    root = Path(root)
    result = []
    seen = set()

    for case_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        case_id = case_dir.name
        
        for visit_dir in sorted([v for v in case_dir.iterdir() if v.is_dir()]):
            visit_id = visit_dir.name
            
            histopath_base = None
            for candidate in visit_dir.rglob("*"):
                if candidate.is_dir() and "histopath" in candidate.name.lower():
                    histopath_base = candidate
                    break
            
            if not histopath_base:
                continue
            
            for body_site_dir in sorted([b for b in histopath_base.iterdir() if b.is_dir()]):
                body_site = body_site_dir.name
                
                for mag_dir in sorted([m for m in body_site_dir.iterdir() if m.is_dir()]):
                    magnification = mag_dir.name
                    mag_value = extract_magnification(magnification)
                    
                    for img_path in sorted(mag_dir.iterdir()):
                        if img_path.suffix.lower() in IMAGE_EXTS:
                            try:
                                resolved = str(img_path.resolve())
                            except Exception:
                                resolved = str(img_path)
                            
                            if resolved in seen:
                                continue
                            seen.add(resolved)
                            
                            result.append({
                                "case_id": case_id,
                                "visit_id": visit_id,
                                "body_site": body_site,
                                "magnification": magnification,
                                "mag_value": mag_value,
                                "filename": img_path.name,
                                "path": img_path
                            })

    result.sort(key=lambda x: (x["case_id"], x["visit_id"], x["body_site"], x["mag_value"], x["filename"]))
    return result

# ═══════════════════════════════════════════════════════════════════════════
# MAIN LABELLING GUI
# ═══════════════════════════════════════════════════════════════════════════

class HistopathLabelTool:
    def __init__(self, master, images, output_file):
        self.master = master
        self.images = images
        self.output_file = output_file
        self.index = 0
        self.labels = {}
        self.image_start_time = None
        self.current_primary = None
        
        # Multi-tier grading state
        self.current_grading = {}
        
        # Visibility flags for banner and previous label
        self.banner_visible = False
        self.prev_label_visible = False

        if not SESSION["annotator"]:
            name = simpledialog.askstring("Annotator", "Enter Annotator Name:", parent=master)
            SESSION["annotator"] = name if name else "Anonymous"
        
        SESSION["start_time"] = time.time()

        self.master.title("Histopathology Image Labelling Tool - Refactored Grading v3.0")
        
        # Auto-detect screen size and set appropriate window size
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        # Use 90% of screen size or maximum reasonable size
        window_width = min(int(screen_width * 0.9), 1450)
        window_height = min(int(screen_height * 0.9), 950)
        
        # Center the window
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        
        self.master.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Make window resizable
        self.master.resizable(True, True)
        
        # Set minimum size
        self.master.minsize(1000, 700)
        
        self.setup_gui()
        self.show_image()

    def setup_gui(self):
        """Setup complete GUI with refactored grading interface"""
        
        # Create main container with scrollbar for small screens
        main_container = tk.Frame(self.master)
        main_container.pack(fill="both", expand=True)
        
        # Create canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_container)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.container = scrollable_frame
        
        # TOP INFO BAR
        info_frame = tk.Frame(self.container, bg="#2c3e50", height=60)
        info_frame.pack(fill="x")
        info_frame.pack_propagate(False)

        self.info_label = tk.Label(info_frame, text="", font=("Arial", 10, "bold"),
                                   bg="#2c3e50", fg="white", anchor="w", padx=15)
        self.info_label.pack(side="left", fill="both", expand=True, pady=8)

        self.progress_label = tk.Label(info_frame, text="", font=("Arial", 9),
                                      bg="#2c3e50", fg="#ecf0f1", anchor="e", padx=15)
        self.progress_label.pack(side="right", pady=8)

        # CLICKABLE PROGRESS BAR
        progress_container = tk.Frame(self.container, bg="#34495e", height=50)
        progress_container.pack(fill="x", pady=(0, 3))
        progress_container.pack_propagate(False)

        tk.Label(progress_container, text="Quick Jump (click any image):", 
                font=("Arial", 8, "bold"), bg="#34495e", fg="white").pack(anchor="w", padx=8, pady=(3, 0))

        self.progress_canvas = tk.Canvas(progress_container, bg="#34495e", height=25, highlightthickness=0)
        self.progress_canvas.pack(fill="x", padx=8, pady=(0, 3))
        self.progress_canvas.bind("<Button-1>", self.on_progress_click)

        # CASE CHANGE BANNER
        self.banner = tk.Label(self.container, text="", font=("Arial", 12, "bold"),
                              bg="#e74c3c", fg="white", pady=8)

        # PREVIOUS LABEL DISPLAY
        self.prev_label_frame = tk.Frame(self.container, bg="#f39c12")
        self.prev_label_display = tk.Label(self.prev_label_frame, text="", 
                                           font=("Arial", 9, "bold"),
                                           bg="#f39c12", fg="white", pady=6)
        self.prev_label_display.pack(fill="x")

        # MAIN CONTENT AREA
        main_content = tk.Frame(self.container)
        main_content.pack(fill="both", expand=True, padx=3, pady=3)

        # LEFT: Case history sidebar
        sidebar = tk.Frame(main_content, width=250, bg="#ecf0f1")
        sidebar.pack(side="left", fill="y", padx=(0, 3))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="📋 Current Case", font=("Arial", 9, "bold"),
                bg="#7f8c8d", fg="white", pady=8).pack(fill="x")

        scroll_frame = tk.Frame(sidebar)
        scroll_frame.pack(fill="both", expand=True, padx=3, pady=3)

        scrollbar_case = tk.Scrollbar(scroll_frame)
        scrollbar_case.pack(side="right", fill="y")

        self.case_listbox = tk.Listbox(scroll_frame, font=("Arial", 8), 
                                       yscrollcommand=scrollbar_case.set, bg="#ecf0f1")
        self.case_listbox.pack(side="left", fill="both", expand=True)
        scrollbar_case.config(command=self.case_listbox.yview)

        # CENTER: Image display
        img_frame = tk.Frame(main_content, bg="#2c3e50")
        img_frame.pack(side="left", fill="both", expand=True)

        self.img_label = tk.Label(img_frame, bg="#2c3e50")
        self.img_label.pack(pady=5, fill="both", expand=True)

        # LABELLING PANEL
        label_panel = tk.Frame(self.container, bg="#ecf0f1", relief="raised", bd=2)
        label_panel.pack(fill="x", padx=8, pady=3)

        # Primary diagnosis buttons (ONLY 4 NOW)
        tk.Label(label_panel, text="PRIMARY DIAGNOSIS (Click one):", 
                font=("Arial", 9, "bold"), bg="#ecf0f1").pack(pady=(8, 3))

        primary_frame = tk.Frame(label_panel, bg="#ecf0f1")
        primary_frame.pack(pady=3)

        btn_width = 13
        btn_height = 1

        tk.Button(primary_frame, text="Normal", width=btn_width, height=btn_height,
                 bg="#27ae60", fg="white", font=("Arial", 9, "bold"),
                 command=lambda: self.select_primary("Normal")).grid(row=0, column=0, padx=3)

        tk.Button(primary_frame, text="Dysplasia", width=btn_width, height=btn_height,
                 bg="#e67e22", fg="white", font=("Arial", 9, "bold"),
                 command=lambda: self.select_primary("Dysplasia")).grid(row=0, column=1, padx=3)

        tk.Button(primary_frame, text="Cancer", width=btn_width, height=btn_height,
                 bg="#c0392b", fg="white", font=("Arial", 9, "bold"),
                 command=lambda: self.select_primary("Cancer")).grid(row=0, column=2, padx=3)

        tk.Button(primary_frame, text="Indeterminate", width=btn_width, height=btn_height,
                 bg="#95a5a6", fg="white", font=("Arial", 9, "bold"),
                 command=lambda: self.select_primary("Indeterminate")).grid(row=0, column=3, padx=3)

        # Secondary options frame
        self.secondary_frame = tk.Frame(label_panel, bg="#ecf0f1")
        self.secondary_frame.pack(pady=6, fill="x")

        # Current selection display
        self.selection_frame = tk.Frame(label_panel, bg="#d5dbdb", relief="solid", bd=1)
        self.selection_label = tk.Label(self.selection_frame, text="", 
                                        font=("Arial", 8, "bold"), bg="#d5dbdb", fg="#2c3e50")
        self.selection_label.pack(pady=5, padx=15)

        # Comment section
        comment_container = tk.Frame(label_panel, bg="#ecf0f1")
        comment_container.pack(fill="x", padx=15, pady=(3, 8))

        self.comment_label = tk.Label(comment_container, text="Comment (optional):", 
                font=("Arial", 8), bg="#ecf0f1")
        self.comment_label.pack(side="left", padx=(0, 8))

        self.comment_text = scrolledtext.ScrolledText(comment_container, height=2, width=80,
                                                      font=("Arial", 8))
        self.comment_text.pack(side="left", fill="x", expand=True)

        # NAVIGATION BUTTONS
        nav_frame = tk.Frame(self.container, bg="#ecf0f1")
        nav_frame.pack(pady=8)

        tk.Button(nav_frame, text="⬅ Previous", width=12, height=1,
                 bg="#34495e", fg="white", font=("Arial", 9, "bold"),
                 command=self.go_back).grid(row=0, column=0, padx=4)

        tk.Button(nav_frame, text="➡ Next", width=12, height=1,
                 bg="#3498db", fg="white", font=("Arial", 9, "bold"),
                 command=self.next_image).grid(row=0, column=1, padx=4)

        tk.Button(nav_frame, text="🔄 Relabel", width=12, height=1,
                 bg="#e67e22", fg="white", font=("Arial", 9, "bold"),
                 command=self.relabel_current).grid(row=0, column=2, padx=4)

        tk.Button(nav_frame, text="💾 Save Progress", width=15, height=1,
                 bg="#16a085", fg="white", font=("Arial", 9, "bold"),
                 command=self.save_progress).grid(row=0, column=3, padx=4)

        # STATUS BAR
        self.status = tk.Label(self.container, text="", font=("Arial", 8),
                              bg="#bdc3c7", relief="sunken", anchor="w", padx=8)
        self.status.pack(fill="x", side="bottom")

    def select_primary(self, diagnosis):
        """Handle primary diagnosis selection"""
        self.current_primary = diagnosis
        self.current_grading = {"diagnosis": diagnosis}
        
        for widget in self.secondary_frame.winfo_children():
            widget.destroy()

        # Update comment requirement (ONLY for Indeterminate)
        if diagnosis == "Indeterminate":
            self.comment_label.config(text="Comment (REQUIRED ⚠):", fg="red", font=("Arial", 8, "bold"))
        else:
            self.comment_label.config(text="Comment (optional):", fg="black", font=("Arial", 8))

        if diagnosis == "Normal":
            tk.Label(self.secondary_frame, text="Tissue Type:", 
                    font=("Arial", 8, "bold"), bg="#ecf0f1").pack(side="left", padx=15)
            
            for tissue in ["Stroma", "Epithelium", "Both"]:
                tk.Button(self.secondary_frame, text=tissue, width=12, height=1,
                         bg="#2ecc71", fg="white", font=("Arial", 8, "bold"),
                         command=lambda t=tissue: self.save_label_simple(t)).pack(side="left", padx=3)

        elif diagnosis == "Dysplasia":
            self.setup_dysplasia_grading()

        elif diagnosis == "Cancer":
            self.setup_cancer_grading()

        elif diagnosis == "Indeterminate":
            tk.Label(self.secondary_frame, text="⚠ Provide reason in comment (required)  →", 
                    font=("Arial", 8, "bold"), bg="#ecf0f1", fg="red").pack(side="left", padx=15)
            
            tk.Button(self.secondary_frame, text="✓ Save as Indeterminate", width=20, height=1,
                     bg="#95a5a6", fg="white", font=("Arial", 8, "bold"),
                     command=lambda: self.save_label_simple("")).pack(side="left", padx=8)

    def setup_dysplasia_grading(self):
        """Setup Dysplasia grading: Binary + Three-Tier OR Ungradable"""
        
        # Title
        tk.Label(self.secondary_frame, text="GRADING OPTIONS:", 
                font=("Arial", 9, "bold"), bg="#ecf0f1", fg="#d35400").pack(pady=(5, 8))
        
        grading_container = tk.Frame(self.secondary_frame, bg="#ecf0f1")
        grading_container.pack()
        
        # Binary grading section
        binary_frame = tk.Frame(grading_container, bg="#ecf0f1")
        binary_frame.pack(side="left", padx=10)
        
        tk.Label(binary_frame, text="Binary:", 
                font=("Arial", 8, "bold"), bg="#ecf0f1").pack()
        
        binary_buttons = tk.Frame(binary_frame, bg="#ecf0f1")
        binary_buttons.pack(pady=3)
        
        tk.Button(binary_buttons, text="Low Risk", width=10, height=1,
                 bg="#f39c12", fg="white", font=("Arial", 8, "bold"),
                 command=lambda: self.select_grading("binary", "Low_Risk")).pack(side="left", padx=2)
        
        tk.Button(binary_buttons, text="High Risk", width=10, height=1,
                 bg="#d35400", fg="white", font=("Arial", 8, "bold"),
                 command=lambda: self.select_grading("binary", "High_Risk")).pack(side="left", padx=2)
        
        # Separator
        tk.Label(grading_container, text="|", font=("Arial", 14), 
                bg="#ecf0f1", fg="#7f8c8d").pack(side="left", padx=6)
        
        # Three-tier grading section
        three_frame = tk.Frame(grading_container, bg="#ecf0f1")
        three_frame.pack(side="left", padx=10)
        
        tk.Label(three_frame, text="Three-Tier:", 
                font=("Arial", 8, "bold"), bg="#ecf0f1").pack()
        
        three_buttons = tk.Frame(three_frame, bg="#ecf0f1")
        three_buttons.pack(pady=3)
        
        for grade, color in [("Mild", "#f39c12"), ("Moderate", "#e67e22"), ("Severe", "#d35400")]:
            tk.Button(three_buttons, text=grade, width=9, height=1,
                     bg=color, fg="white", font=("Arial", 8, "bold"),
                     command=lambda g=grade: self.select_grading("three_tier", g)).pack(side="left", padx=2)
        
        # Separator
        tk.Label(grading_container, text="|", font=("Arial", 14), 
                bg="#ecf0f1", fg="#7f8c8d").pack(side="left", padx=6)
        
        # Ungradable option
        ungradable_frame = tk.Frame(grading_container, bg="#ecf0f1")
        ungradable_frame.pack(side="left", padx=10)
        
        tk.Label(ungradable_frame, text="Quality:", 
                font=("Arial", 8, "bold"), bg="#ecf0f1").pack()
        
        tk.Button(ungradable_frame, text="Ungradable", width=12, height=1,
                 bg="#7f8c8d", fg="white", font=("Arial", 8, "bold"),
                 command=lambda: self.select_ungradable()).pack(pady=3)
        
        # Show current selection and save button
        self.update_grading_display()

    def setup_cancer_grading(self):
        """Setup Cancer grading: Three-Tier OR Ungradable"""
        
        # Title
        tk.Label(self.secondary_frame, text="GRADING OPTIONS:", 
                font=("Arial", 9, "bold"), bg="#ecf0f1", fg="#922b21").pack(pady=(5, 8))
        
        grading_container = tk.Frame(self.secondary_frame, bg="#ecf0f1")
        grading_container.pack()
        
        # Three-tier grading section
        three_frame = tk.Frame(grading_container, bg="#ecf0f1")
        three_frame.pack(side="left", padx=10)
        
        tk.Label(three_frame, text="Three-Tier Differentiation:", 
                font=("Arial", 8, "bold"), bg="#ecf0f1").pack()
        
        three_buttons = tk.Frame(three_frame, bg="#ecf0f1")
        three_buttons.pack(pady=3)
        
        grades = [
            ("Well", "#c0392b", "Well_Differentiated"),
            ("Moderate", "#922b21", "Moderately_Differentiated"),
            ("Poor", "#641e16", "Poorly_Differentiated")
        ]
        
        for label, color, value in grades:
            tk.Button(three_buttons, text=label, width=8, height=1,
                     bg=color, fg="white", font=("Arial", 7, "bold"),
                     command=lambda v=value: self.select_grading("three_tier_diff", v)).pack(side="left", padx=2)
        
        # Separator
        tk.Label(grading_container, text="|", font=("Arial", 14), 
                bg="#ecf0f1", fg="#7f8c8d").pack(side="left", padx=6)
        
        # Ungradable option
        ungradable_frame = tk.Frame(grading_container, bg="#ecf0f1")
        ungradable_frame.pack(side="left", padx=10)
        
        tk.Label(ungradable_frame, text="Quality:", 
                font=("Arial", 8, "bold"), bg="#ecf0f1").pack()
        
        tk.Button(ungradable_frame, text="Ungradable", width=12, height=1,
                 bg="#7f8c8d", fg="white", font=("Arial", 8, "bold"),
                 command=lambda: self.select_ungradable()).pack(pady=3)
        
        # Show current selection and save button
        self.update_grading_display()

    def select_grading(self, tier, value):
        """Record grading selection"""
        # Clear ungradable if grading is selected
        if "ungradable" in self.current_grading:
            del self.current_grading["ungradable"]
            # Reset comment requirement when switching away from ungradable
            self.comment_label.config(text="Comment (optional):", fg="black", font=("Arial", 8))
        
        self.current_grading[tier] = value
        self.update_grading_display()

    def select_ungradable(self):
        """Mark as ungradable - clears other grading selections"""
        diagnosis = self.current_grading.get("diagnosis")
        
        # Clear other grading fields
        keys_to_remove = [k for k in self.current_grading.keys() if k not in ["diagnosis"]]
        for key in keys_to_remove:
            del self.current_grading[key]
        
        self.current_grading["ungradable"] = True
        
        # Make comment mandatory for ungradable
        self.comment_label.config(text="Comment (REQUIRED ⚠):", fg="red", font=("Arial", 8, "bold"))
        
        self.update_grading_display()

    def update_grading_display(self):
        """Update display showing current selections and save button"""
        diagnosis = self.current_grading.get("diagnosis")
        
        # Check if ungradable
        if self.current_grading.get("ungradable"):
            display_text = "Selected: Ungradable (quality issue)"
            self.selection_label.config(text=display_text, fg="#7f8c8d")
            self.selection_frame.pack(before=self.comment_text.master, fill="x", padx=20, pady=5)
            self.show_save_button()
            return
        
        if diagnosis == "Dysplasia":
            binary = self.current_grading.get("binary", "⚠ Not selected")
            three = self.current_grading.get("three_tier", "⚠ Not selected")
            
            display_text = f"Selected: Binary={binary} | Three-Tier={three}"
            
            # Show selection status
            self.selection_label.config(text=display_text, fg="#2c3e50")
            self.selection_frame.pack(before=self.comment_text.master, fill="x", padx=20, pady=5)
            
            # Enable save button only if both are selected
            if "binary" in self.current_grading and "three_tier" in self.current_grading:
                self.show_save_button()
            
        elif diagnosis == "Cancer":
            three = self.current_grading.get("three_tier_diff", "⚠ Not selected")
            
            display_text = f"Selected: Three-Tier={three}"
            
            self.selection_label.config(text=display_text, fg="#2c3e50")
            self.selection_frame.pack(before=self.comment_text.master, fill="x", padx=20, pady=5)
            
            if "three_tier_diff" in self.current_grading:
                self.show_save_button()

    def show_save_button(self):
        """Show final save button after all gradings selected"""
        # Remove existing save button if any
        for widget in self.secondary_frame.winfo_children():
            if isinstance(widget, tk.Button) and "SAVE" in widget.cget("text"):
                widget.destroy()
        
        tk.Label(self.secondary_frame, text=" → ", font=("Arial", 12, "bold"),
                bg="#ecf0f1", fg="#27ae60").pack(side="left", padx=6)
        
        tk.Button(self.secondary_frame, text="✓ SAVE", width=15, height=1,
                 bg="#27ae60", fg="white", font=("Arial", 9, "bold"),
                 command=self.save_multi_tier_label).pack(side="left", padx=6)

    def save_label_simple(self, subtype):
        """Save simple label (Normal, Indeterminate)"""
        comment = self.comment_text.get("1.0", tk.END).strip()
        diagnosis = self.current_grading.get("diagnosis")
        
        # Validate mandatory comment for Indeterminate
        if diagnosis == "Indeterminate" and not comment:
            messagebox.showwarning(
                "Comment Required", 
                "⚠ You must provide a reason/comment for 'Indeterminate' diagnosis."
            )
            self.comment_text.focus_set()
            return
        
        self.save_label_to_storage(diagnosis, subtype, comment)

    def save_multi_tier_label(self):
        """Save multi-tier grading label (Dysplasia, Cancer)"""
        diagnosis = self.current_grading.get("diagnosis")
        comment = self.comment_text.get("1.0", tk.END).strip()
        
        # Check if ungradable - requires comment
        if self.current_grading.get("ungradable"):
            if not comment:
                messagebox.showwarning(
                    "Comment Required", 
                    "⚠ You must provide a reason/comment when marking as 'Ungradable'."
                )
                self.comment_text.focus_set()
                return
            subtype = "Ungradable"
            self.save_label_to_storage(diagnosis, subtype, comment)
            return
        
        if diagnosis == "Dysplasia":
            if "binary" not in self.current_grading or "three_tier" not in self.current_grading:
                messagebox.showwarning("Incomplete", "Please select both Binary and Three-Tier grading, or mark as Ungradable.")
                return
            
            subtype = f"Binary:{self.current_grading['binary']}|ThreeTier:{self.current_grading['three_tier']}"
            
        elif diagnosis == "Cancer":
            if "three_tier_diff" not in self.current_grading:
                messagebox.showwarning("Incomplete", "Please select Three-Tier grading, or mark as Ungradable.")
                return
            
            subtype = f"ThreeTier:{self.current_grading['three_tier_diff']}"
        
        else:
            return
        
        self.save_label_to_storage(diagnosis, subtype, comment)

    def save_label_to_storage(self, diagnosis, subtype, comment):
        """Common save function"""
        img_info = self.images[self.index]
        key = self.get_key(img_info["path"])
        
        self.labels[key] = {
            "case_id": img_info["case_id"],
            "visit_id": img_info["visit_id"],
            "body_site": img_info["body_site"],
            "magnification": img_info["magnification"],
            "mag_value": img_info["mag_value"],
            "filename": img_info["filename"],
            "diagnosis": diagnosis,
            "subtype": subtype,
            "comment": comment
        }

        if self.image_start_time:
            SESSION["times"].append(time.time() - self.image_start_time)
        
        SESSION["cases"].add(img_info["case_id"])

        self.index += 1
        self.current_primary = None
        self.current_grading = {}
        self.show_image()

    def next_image(self):
        """Move to next image without saving"""
        if self.index < len(self.images) - 1:
            self.index += 1
            self.current_primary = None
            self.current_grading = {}
            self.show_image()
        else:
            messagebox.showinfo("End", "This is the last image.")

    def go_back(self):
        """Navigate to previous image"""
        if self.index > 0:
            self.index -= 1
            self.current_primary = None
            self.current_grading = {}
            if SESSION["times"]:
                SESSION["times"].pop()
            self.show_image()
        else:
            messagebox.showinfo("Start", "This is the first image.")

    def show_image(self):
        """Display current image with metadata"""
        if self.index >= len(self.images):
            self.finish()
            return

        img_info = self.images[self.index]
        self.image_start_time = time.time()
        self.show_banner_if_new_case()

        self.info_label.config(
            text=f"Case: {img_info['case_id']} | Site: {img_info['body_site']} | "
                 f"Mag: {img_info['magnification']} | Image: {self.index + 1}/{len(self.images)}"
        )
        self.progress_label.config(text=f"Labeled: {len(self.labels)}/{len(self.images)}")
        self.draw_progress_bar()

        # Check existing label
        key = self.get_key(img_info["path"])
        existing = self.labels.get(key)
        
        if existing:
            text = f"⚠ Previously: {existing['diagnosis']}"
            if existing.get("subtype"):
                text += f" → {existing['subtype']}"
            if existing.get("comment"):
                text += f" | {existing['comment'][:50]}..."
            self.prev_label_display.config(text=text)
            
            if not self.prev_label_visible:
                try:
                    children = self.container.winfo_children()
                    if len(children) >= 3:
                        self.prev_label_frame.pack(after=children[1], fill="x")
                    else:
                        self.prev_label_frame.pack(fill="x")
                    self.prev_label_visible = True
                except Exception as e:
                    print(f"Previous label pack error: {e}")
        else:
            if self.prev_label_visible:
                try:
                    self.prev_label_frame.pack_forget()
                    self.prev_label_visible = False
                except:
                    pass

        self.update_case_sidebar()
        self.status.config(text=f"Visit: {img_info['visit_id']} | File: {img_info['filename']}")

        # Load image with proper error handling
        try:
            img = Image.open(img_info["path"])
            max_w, max_h = 700, 400
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            self.img_label.config(image=self.tk_img, text="")
        except Exception as e:
            self.img_label.config(text=f"Error loading image:\n{str(e)}", image="")
            self.tk_img = None
            print(f"Error loading image {img_info['path']}: {e}")

        # Reset form
        self.current_primary = None
        self.current_grading = {}
        for widget in self.secondary_frame.winfo_children():
            widget.destroy()
        self.selection_frame.pack_forget()
        self.comment_text.delete("1.0", tk.END)
        self.comment_label.config(text="Comment (optional):", fg="black", font=("Arial", 8))
        
        if existing and existing.get("comment"):
            self.comment_text.insert("1.0", existing["comment"])

    def draw_progress_bar(self):
        """Draw clickable progress visualization"""
        self.progress_canvas.delete("all")
        w = self.progress_canvas.winfo_width() or 1300
        total = len(self.images)
        if not total:
            return
        
        box_w = max(2, w // total)
        
        for i in range(total):
            x1, x2 = i * box_w, (i + 1) * box_w - 1
            key = self.get_key(self.images[i]["path"])
            
            color = "#3498db" if i == self.index else ("#27ae60" if key in self.labels else "#95a5a6")
            self.progress_canvas.create_rectangle(x1, 0, x2, 30, fill=color, outline="white")

    def on_progress_click(self, event):
        """Jump to clicked image"""
        w = self.progress_canvas.winfo_width()
        idx = event.x // max(2, w // len(self.images))
        if 0 <= idx < len(self.images):
            self.index = idx
            self.current_primary = None
            self.current_grading = {}
            self.show_image()

    def show_banner_if_new_case(self):
        """Show new case notification"""
        if self.index >= len(self.images):
            return
        
        current_case = self.images[self.index]["case_id"]
        
        if SESSION["last_case"] and SESSION["last_case"] != current_case:
            self.banner.config(text=f"🔔 NEW CASE: {current_case}")
            
            if not self.banner_visible:
                try:
                    children = self.container.winfo_children()
                    if len(children) >= 3:
                        self.banner.pack(after=children[1], fill="x")
                    else:
                        self.banner.pack(fill="x")
                    self.banner_visible = True
                except Exception as e:
                    print(f"Banner pack error: {e}")
            
            def hide_banner():
                if self.banner_visible:
                    try:
                        self.banner.pack_forget()
                        self.banner_visible = False
                    except:
                        pass
            
            self.master.after(3000, hide_banner)
        
        SESSION["last_case"] = current_case

    def update_case_sidebar(self):
        """Update sidebar with current case labels"""
        self.case_listbox.delete(0, tk.END)
        if self.index >= len(self.images):
            return
        
        case = self.images[self.index]["case_id"]
        case_labels = [l for l in self.labels.values() if l["case_id"] == case]
        case_labels.sort(key=lambda x: (x["body_site"], x.get("mag_value", 0)))
        
        if not case_labels:
            self.case_listbox.insert(tk.END, "")
            self.case_listbox.insert(tk.END, "  No labels yet for this case")
        else:
            for lbl in case_labels:
                self.case_listbox.insert(tk.END, f"  {lbl['body_site']} | {lbl['magnification']}")
                text = f"    ✓ {lbl['diagnosis']}"
                if lbl.get("subtype"):
                    text += f" → {lbl['subtype']}"
                self.case_listbox.insert(tk.END, text)
                self.case_listbox.insert(tk.END, "")

    def relabel_current(self):
        """Clear current label"""
        if self.index < len(self.images):
            key = self.get_key(self.images[self.index]["path"])
            if key in self.labels:
                del self.labels[key]
                messagebox.showinfo("Relabel", "Label cleared. Select new diagnosis.")
                self.show_image()
            else:
                messagebox.showinfo("Info", "This image hasn't been labeled yet.")

    def save_progress(self):
        """Save progress without finishing"""
        if not self.labels:
            messagebox.showwarning("Warning", "No labels to save yet.")
            return
        try:
            self._write_csv(partial=True)
            messagebox.showinfo("Saved", f"✓ Saved {len(self.labels)} labels\n\n{self.output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")

    def finish(self):
        """Complete session"""
        SESSION["end_time"] = time.time()
        if not self.labels:
            messagebox.showinfo("Complete", "No labels were saved.")
            self.master.destroy()
            return
        try:
            self._write_csv(partial=False)
            messagebox.showinfo("Complete!", 
                f"✓ {len(self.labels)} images labeled\n\nSaved to:\n{self.output_file}")
            self.master.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Save failed:\n{e}")

    def get_key(self, path):
        """Get unique key for path"""
        try:
            return str(path.resolve())
        except:
            return str(path)

    def get_summary_path(self):
        """Get summary file path"""
        p = Path(self.output_file)
        return p.with_name(p.stem + "_summary.txt")

    def _write_csv(self, partial=False):
        """Write labels to CSV"""
        Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
        
        rows = sorted(self.labels.values(), 
                     key=lambda r: (r["case_id"], r["visit_id"], r["body_site"], 
                                   r["mag_value"], r["filename"]))
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            fields = ["Case_ID", "Visit_ID", "Body_Site", "Magnification", 
                     "Image_File", "Diagnosis", "Subtype", "Comment", 
                     "Time_Spent_sec", "Annotator", "Timestamp"]
            writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for i, row in enumerate(rows):
                writer.writerow({
                    "Case_ID": row["case_id"],
                    "Visit_ID": row["visit_id"],
                    "Body_Site": row["body_site"],
                    "Magnification": row["magnification"],
                    "Image_File": row["filename"],
                    "Diagnosis": row["diagnosis"],
                    "Subtype": row.get("subtype", ""),
                    "Comment": row.get("comment", "").replace("\n", " ").replace("\r", " "),
                    "Time_Spent_sec": f"{SESSION['times'][i]:.2f}" if i < len(SESSION["times"]) else "0",
                    "Annotator": SESSION["annotator"],
                    "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        self._write_summary(partial)

    def _write_summary(self, partial=False):
        """Write session summary"""
        end = SESSION.get("end_time") or time.time()
        duration = end - SESSION["start_time"]
        times = SESSION["times"]
        
        counts = {}
        for lbl in self.labels.values():
            d = lbl["diagnosis"]
            counts[d] = counts.get(d, 0) + 1
        
        with open(self.get_summary_path(), 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n HISTOPATHOLOGY LABELLING SESSION - REFACTORED GRADING v3.0\n" + "="*80 + "\n\n")
            f.write(f"Status: {'IN PROGRESS' if partial else 'COMPLETED'}\n")
            f.write(f"Annotator: {SESSION['annotator']}\n")
            f.write(f"Started: {datetime.fromtimestamp(SESSION['start_time']).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {int(duration//60)}m {int(duration%60)}s\n\n")
            f.write(f"Total Images: {len(self.images)}\n")
            f.write(f"Images Labeled: {len(self.labels)} ({len(self.labels)/len(self.images)*100:.1f}%)\n")
            f.write(f"Unique Cases: {len(SESSION['cases'])}\n\n")
            if times:
                f.write(f"Avg Time: {sum(times)/len(times):.2f}s | Median: {sorted(times)[len(times)//2]:.2f}s\n\n")
            f.write("LABEL DISTRIBUTION:\n" + "-"*80 + "\n")
            for diag, count in sorted(counts.items()):
                f.write(f"{diag:<20} {count:>6} ({count/len(self.labels)*100:>5.1f}%)\n")

# ═══════════════════════════════════════════════════════════════════════════
# LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════

def select_root():
    root = filedialog.askdirectory(title="Select Dataset Root Folder")
    if root:
        entry_root.delete(0, tk.END)
        entry_root.insert(0, root)

def select_output():
    out = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="histopath_labels.csv"
    )
    if out:
        entry_output.delete(0, tk.END)
        entry_output.insert(0, out)

def run():
    root_folder = entry_root.get().strip()
    out_file = entry_output.get().strip()

    if not root_folder or not out_file:
        messagebox.showerror("Error", "Please select input folder and output file.")
        return

    messagebox.showinfo("Scanning", "Scanning for images...")
    images = find_histopath_images(root_folder)

    if not images:
        messagebox.showerror("Error", 
            "No histopathology images found.\n\n"
            "Expected structure:\nCase_ID/VISIT_*/.../*histopath*/BODY_SITE/MAG/*.{jpg,png,tif}")
        return

    cases = len(set(img['case_id'] for img in images))
    sites = len(set(img['body_site'] for img in images))
    
    if messagebox.askyesno("Ready", 
        f"Found {len(images)} images\nCases: {cases} | Body Sites: {sites}\n\nStart labelling?"):
        main = tk.Toplevel(app)
        HistopathLabelTool(main, images, out_file)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = tk.Tk()
    app.title("Histopathology Labelling Tool - Refactored Grading v3.0")
    app.geometry("850x350")

    tk.Label(app, text="🔬 Histopathology Image Labelling Tool", 
             font=("Arial", 18, "bold"), bg="#2c3e50", fg="white", pady=20).pack(fill="x")

    form_frame = tk.Frame(app, padx=30, pady=20)
    form_frame.pack(fill="both", expand=True)

    tk.Label(form_frame, text="Dataset Root:", font=("Arial", 11, "bold")).grid(
        row=0, column=0, sticky="w", pady=10)
    entry_root = tk.Entry(form_frame, width=55, font=("Arial", 10))
    entry_root.grid(row=0, column=1, padx=10)
    tk.Button(form_frame, text="Browse", command=select_root, width=12,
             bg="#3498db", fg="white", font=("Arial", 9, "bold")).grid(row=0, column=2)

    tk.Label(form_frame, text="Output CSV:", font=("Arial", 11, "bold")).grid(
        row=1, column=0, sticky="w", pady=10)
    entry_output = tk.Entry(form_frame, width=55, font=("Arial", 10))
    entry_output.grid(row=1, column=1, padx=10)
    tk.Button(form_frame, text="Browse", command=select_output, width=12,
             bg="#3498db", fg="white", font=("Arial", 9, "bold")).grid(row=1, column=2)

    tk.Button(form_frame, text="🚀 Start Labelling", command=run, 
             bg="#27ae60", fg="white", font=("Arial", 13, "bold"),
             width=35, height=2).grid(row=2, column=1, pady=25)

    app.mainloop()