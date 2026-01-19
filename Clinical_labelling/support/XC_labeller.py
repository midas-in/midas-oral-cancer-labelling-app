#!/usr/bin/env python3
"""
Clinical Image Labelling Tool (Enhanced)

Features:
  ✔ Walk Case → Visit → XC → CLINICAL images
  ✔ Display each image in GUI
  ✔ Labels: Suspicious / Non-Suspicious / NA
  ✔ Save to properly formatted CSV (separate columns)
  ✔ Back/Relabel functionality
  ✔ Save progress anytime
  ✔ Case ID banner when switching cases
  ✔ Current case/label display at top
  ✔ Session summary with timing
"""

import os
import csv
import time
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, simpledialog
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

# -----------------------------
# SESSION TRACKING
# -----------------------------
SESSION = {
    "annotator": "",
    "start_time": None,
    "end_time": None,
    "times": [],
    "cases": set(),
    "total_images": 0,
    "last_case": None,  # Track case changes
}

# -----------------------------
# Find Clinical Images
# -----------------------------
def find_clinical_images(root):
    """
    Returns list of dicts:
      { "case": ..., "visit": ..., "path": Path(...) }
    Deduplicated and sorted.
    """
    root = Path(root)
    result = []
    seen = set()

    for case in sorted([p for p in root.iterdir() if p.is_dir()]):
        for visit in sorted([v for v in case.iterdir() if v.is_dir()]):
            for candidate in visit.rglob("*"):
                if not candidate.is_dir():
                    continue
                name = candidate.name.lower()
                if "xc" in name or "clinical" in name:
                    for img in sorted(candidate.rglob("*")):
                        if img.suffix.lower() in IMAGE_EXTS:
                            try:
                                resolved = str(img.resolve())
                            except Exception:
                                resolved = str(img)
                            if resolved in seen:
                                continue
                            seen.add(resolved)
                            result.append({
                                "case": case.name,
                                "visit": visit.name,
                                "path": img
                            })

    result.sort(key=lambda x: (x["case"], x["visit"], str(x["path"])))
    return result

# -----------------------------
# MAIN GUI LABELLER
# -----------------------------
class ClinicalLabelTool:
    def __init__(self, master, images, output_file):
        self.master = master
        self.images = images
        self.output_file = output_file
        self.index = 0
        self.labels = {}  # key = path_str, val = dict(case, visit, file, label, comment)
        self.history = []
        self.pointer = -1
        self.image_start_time = None

        # Ask annotator name
        if not SESSION["annotator"]:
            name = simpledialog.askstring("Annotator", "Enter Annotator Name:", 
                                         parent=master)
            SESSION["annotator"] = name if name else "Anonymous"
        
        SESSION["start_time"] = time.time()
        SESSION["total_images"] = len(images)

        self.master.title("Clinical Image Labeller")
        self.master.geometry("1100x850")

        # ===== TOP INFO BAR =====
        info_frame = tk.Frame(master, bg="#2c3e50", height=80)
        info_frame.pack(fill="x", pady=(0, 5))
        info_frame.pack_propagate(False)

        self.case_label = tk.Label(info_frame, text="", font=("Arial", 14, "bold"),
                                   bg="#2c3e50", fg="white")
        self.case_label.pack(side="left", padx=20, pady=10)

        self.label_count = tk.Label(info_frame, text="", font=("Arial", 12),
                                    bg="#2c3e50", fg="#ecf0f1")
        self.label_count.pack(side="right", padx=20, pady=10)

        # ===== CURRENT LABEL DISPLAY =====
        self.current_label_frame = tk.Frame(master, bg="#f39c12", height=40)
        # Don't pack initially - will show when viewing labeled image
        
        self.current_label_display = tk.Label(self.current_label_frame, 
                                             text="", font=("Arial", 12, "bold"),
                                             bg="#f39c12", fg="white", pady=8)
        self.current_label_display.pack(fill="x")

        # ===== CASE CHANGE BANNER (hidden by default) =====
        self.banner = tk.Label(master, text="", font=("Arial", 18, "bold"),
                              bg="#e74c3c", fg="white", pady=15)
        # Don't pack yet - will pack when case changes

        # ===== IMAGE DISPLAY =====
        self.img_label = tk.Label(master, bg="#34495e")
        self.img_label.pack(pady=10, fill="both", expand=True)

        # ===== LABEL BUTTONS =====
        btn_frame = tk.Frame(master)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="✓ Suspicious", width=18, height=2,
                 bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                 command=lambda: self.save_label("Suspicious")).grid(row=0, column=0, padx=8)

        tk.Button(btn_frame, text="✗ Non-Suspicious", width=18, height=2,
                 bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                 command=lambda: self.save_label("Non-Suspicious")).grid(row=0, column=1, padx=8)

        tk.Button(btn_frame, text="? NA / Comment", width=18, height=2,
                 bg="#95a5a6", fg="white", font=("Arial", 11, "bold"),
                 command=self.comment_window).grid(row=0, column=2, padx=8)

        # ===== NAVIGATION & ACTIONS =====
        nav_frame = tk.Frame(master)
        nav_frame.pack(pady=5)

        tk.Button(nav_frame, text="⬅ Back", width=15, bg="#34495e", fg="white",
                 command=self.go_back).grid(row=0, column=0, padx=5)

        tk.Button(nav_frame, text="🔄 Relabel", width=15, bg="#e67e22", fg="white",
                 command=self.relabel_current).grid(row=0, column=1, padx=5)

        tk.Button(nav_frame, text="💾 Save Progress", width=15, bg="#16a085", fg="white",
                 command=self.save_progress).grid(row=0, column=2, padx=5)

        # ===== STATUS BAR =====
        self.status = tk.Label(master, text="", font=("Arial", 10),
                              bg="#ecf0f1", relief="sunken", anchor="w", padx=10)
        self.status.pack(fill="x", side="bottom")

        self.update_info_display()
        self.show_image()

    def update_info_display(self):
        """Update top info bar with current case and label counts"""
        if self.index < len(self.images):
            current_case = self.images[self.index]["case"]
            self.case_label.config(text=f"Case: {current_case}")
        
        total = len(self.labels)
        suspicious = sum(1 for v in self.labels.values() if v["label"] == "Suspicious")
        non_suspicious = sum(1 for v in self.labels.values() if v["label"] == "Non-Suspicious")
        na = sum(1 for v in self.labels.values() if v["label"] == "NA")
        
        self.label_count.config(
            text=f"Labeled: {total}/{len(self.images)} | "
                 f"Suspicious: {suspicious} | Non-Suspicious: {non_suspicious} | NA: {na}"
        )

    def show_banner_if_new_case(self):
        """Show banner when moving to a new case"""
        if self.index >= len(self.images):
            return
        
        current_case = self.images[self.index]["case"]
        
        if SESSION["last_case"] and SESSION["last_case"] != current_case:
            # New case detected!
            self.banner.config(text=f"🔔 NEW CASE: {current_case}")
            self.banner.pack(after=self.case_label.master, fill="x")
            
            # Hide banner after 3 seconds
            self.master.after(3000, lambda: self.banner.pack_forget())
        
        SESSION["last_case"] = current_case

    def show_image(self):
        """Display current image"""
        if self.index >= len(self.images):
            self.finish()
            return

        img_info = self.images[self.index]
        img_path = img_info["path"]
        
        # Update history
        current_key = self.get_key(img_path)
        if self.pointer == -1 or (self.history and self.history[self.pointer] != current_key):
            self.history.append(current_key)
            self.pointer = len(self.history) - 1

        # Start timer
        self.image_start_time = time.time()

        # Check for case change
        self.show_banner_if_new_case()

        # Check if this image already has a label
        existing_label = self.labels.get(current_key)
        if existing_label:
            # Show existing label banner
            label_text = existing_label["label"]
            comment = existing_label.get("comment", "")
            
            if label_text == "Suspicious":
                self.current_label_frame.config(bg="#27ae60")
                self.current_label_display.config(bg="#27ae60", 
                    text=f"✓ Previously Labeled: SUSPICIOUS")
            elif label_text == "Non-Suspicious":
                self.current_label_frame.config(bg="#3498db")
                self.current_label_display.config(bg="#3498db",
                    text=f"✗ Previously Labeled: NON-SUSPICIOUS")
            else:  # NA
                self.current_label_frame.config(bg="#95a5a6")
                display_text = f"? Previously Labeled: NA"
                if comment:
                    display_text += f" | Comment: {comment[:50]}..."
                self.current_label_display.config(bg="#95a5a6", text=display_text)
            
            self.current_label_frame.pack(after=self.case_label.master, fill="x")
        else:
            # Hide label banner if no existing label
            self.current_label_frame.pack_forget()

        # Update status
        self.status.config(
            text=f"Image {self.index + 1}/{len(self.images)}: "
                 f"{img_info['case']} → {img_info['visit']} → {img_path.name}"
        )

        # Load and display image
        try:
            img = Image.open(img_path)
            max_w, max_h = 900, 600
            img.thumbnail((max_w, max_h), Image.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            self.img_label.config(image=self.tk_img, text="")
        except Exception as e:
            self.img_label.config(text=f"Error loading image:\n{e}", image="")
            self.tk_img = None

        self.update_info_display()

    def get_key(self, path):
        """Get unique key for image path"""
        try:
            return str(path.resolve())
        except:
            return str(path)

    def comment_window(self):
        """Open comment dialog for NA label"""
        win = tk.Toplevel(self.master)
        win.title("Add Comment - NA Label")
        win.geometry("500x250")

        tk.Label(win, text="Reason / Notes:", font=("Arial", 11)).pack(pady=5)

        txt = scrolledtext.ScrolledText(win, width=55, height=8, font=("Arial", 10))
        txt.pack(padx=10, pady=5)

        def save_na():
            comment = txt.get("1.0", tk.END).strip()
            self.save_label("NA", comment)
            win.destroy()

        tk.Button(win, text="💾 Save as NA", command=save_na,
                 bg="#95a5a6", fg="white", font=("Arial", 10, "bold"),
                 width=20, height=2).pack(pady=10)

    def save_label(self, label, comment=""):
        """Save label for current image"""
        img_info = self.images[self.index]
        key = self.get_key(img_info["path"])
        
        self.labels[key] = {
            "case": img_info["case"],
            "visit": img_info["visit"],
            "file": img_info["path"].name,
            "label": label,
            "comment": comment
        }

        # Track timing
        if self.image_start_time:
            elapsed = time.time() - self.image_start_time
            SESSION["times"].append(elapsed)
            self.image_start_time = None
        
        SESSION["cases"].add(img_info["case"])

        # Move to next
        self.index += 1
        self.show_image()

    def go_back(self):
        """Navigate to previous image"""
        if self.pointer > 0:
            self.pointer -= 1
            prev_key = self.history[self.pointer]
            
            # Find corresponding index
            for i, obj in enumerate(self.images):
                if self.get_key(obj["path"]) == prev_key:
                    self.index = i
                    break
            
            # Remove last timing
            if SESSION["times"]:
                SESSION["times"].pop()
            
            self.show_image()
        else:
            messagebox.showinfo("Info", "Already at the first image.")

    def relabel_current(self):
        """Clear label for current image"""
        if self.index < len(self.images):
            img_path = self.images[self.index]["path"]
            key = self.get_key(img_path)
            
            if key in self.labels:
                del self.labels[key]
                messagebox.showinfo("Relabel", 
                    "Label cleared. You can now assign a new label.")
                self.update_info_display()
            else:
                messagebox.showinfo("Info", "This image hasn't been labeled yet.")

    def save_progress(self):
        """Save progress to CSV without finishing"""
        if not self.labels:
            messagebox.showwarning("Warning", "No labels to save yet.")
            return
        
        try:
            self._write_csv(partial=True)
            messagebox.showinfo("Progress Saved", 
                f"Saved {len(self.labels)} labels to:\n{self.output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save progress:\n{e}")

    def finish(self):
        """Complete labeling and show review"""
        SESSION["end_time"] = time.time()
        self.master.destroy()
        ReviewWindow(self.labels, self.output_file)

    def _write_csv(self, partial=False):
        """Write labels to CSV with proper column formatting"""
        # Ensure output directory exists
        Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Sort labels
        rows = sorted(self.labels.values(), 
                     key=lambda r: (r["case"], r["visit"], r["file"]))
        
        # Write CSV with proper formatting
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["case", "visit", "file", "label", "comment"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, 
                                   quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for row in rows:
                # Clean comment (remove newlines)
                clean_comment = row.get("comment", "").replace("\n", " ").replace("\r", " ")
                writer.writerow({
                    "case": row.get("case", ""),
                    "visit": row.get("visit", ""),
                    "file": row.get("file", ""),
                    "label": row.get("label", ""),
                    "comment": clean_comment
                })
        
        # Save summary
        self._write_summary(partial)

    def _write_summary(self, partial=False):
        """Write detailed session summary with comprehensive statistics"""
        summary_path = Path(self.output_file).with_name(
            Path(self.output_file).stem + "_summary.txt"
        )
        
        end_time = SESSION.get("end_time") or time.time()
        duration = end_time - SESSION["start_time"]
        avg_time = sum(SESSION["times"]) / len(SESSION["times"]) if SESSION["times"] else 0
        
        # Calculate label statistics
        suspicious = sum(1 for v in self.labels.values() if v["label"] == "Suspicious")
        non_suspicious = sum(1 for v in self.labels.values() if v["label"] == "Non-Suspicious")
        na = sum(1 for v in self.labels.values() if v["label"] == "NA")
        
        # Per-case statistics
        case_stats = {}
        for key, label_data in self.labels.items():
            case = label_data["case"]
            if case not in case_stats:
                case_stats[case] = {"total": 0, "Suspicious": 0, "Non-Suspicious": 0, "NA": 0}
            case_stats[case]["total"] += 1
            case_stats[case][label_data["label"]] += 1
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(" " * 15 + "CLINICAL IMAGE LABELLING SESSION SUMMARY\n")
            f.write("=" * 70 + "\n\n")
            
            # Session Info
            f.write("SESSION INFORMATION\n")
            f.write("-" * 70 + "\n")
            f.write(f"Status: {'IN PROGRESS (Partial Save)' if partial else 'COMPLETED'}\n")
            f.write(f"Annotator: {SESSION['annotator']}\n")
            f.write(f"Session Started: {datetime.fromtimestamp(SESSION['start_time']).strftime('%Y-%m-%d %H:%M:%S')}\n")
            if not partial:
                f.write(f"Session Ended: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {int(duration // 60)}m {int(duration % 60)}s ({duration/60:.1f} minutes)\n")
            f.write(f"Output File: {self.output_file}\n\n")
            
            # Progress Statistics
            f.write("PROGRESS STATISTICS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total Images Available: {SESSION['total_images']}\n")
            f.write(f"Images Labeled: {len(self.labels)}\n")
            f.write(f"Images Remaining: {SESSION['total_images'] - len(self.labels)}\n")
            completion_pct = (len(self.labels) / SESSION['total_images'] * 100) if SESSION['total_images'] > 0 else 0
            f.write(f"Completion Rate: {completion_pct:.1f}%\n")
            f.write(f"Unique Cases Processed: {len(SESSION['cases'])}\n\n")
            
            # Timing Statistics
            if SESSION["times"]:
                f.write("TIMING ANALYSIS\n")
                f.write("-" * 70 + "\n")
                f.write(f"Average Time per Image: {avg_time:.2f} seconds\n")
                f.write(f"Fastest Image: {min(SESSION['times']):.2f} seconds\n")
                f.write(f"Slowest Image: {max(SESSION['times']):.2f} seconds\n")
                f.write(f"Median Time: {sorted(SESSION['times'])[len(SESSION['times'])//2]:.2f} seconds\n")
                total_label_time = sum(SESSION['times'])
                f.write(f"Total Active Labeling Time: {int(total_label_time // 60)}m {int(total_label_time % 60)}s\n")
                f.write(f"Estimated Time Remaining: {int((SESSION['total_images'] - len(self.labels)) * avg_time / 60)} minutes\n\n")
            
            # Label Distribution
            f.write("LABEL DISTRIBUTION\n")
            f.write("-" * 70 + "\n")
            f.write(f"Suspicious:     {suspicious:>5} ({suspicious/len(self.labels)*100:.1f}%)\n" if self.labels else "Suspicious:     0\n")
            f.write(f"Non-Suspicious: {non_suspicious:>5} ({non_suspicious/len(self.labels)*100:.1f}%)\n" if self.labels else "Non-Suspicious: 0\n")
            f.write(f"NA:             {na:>5} ({na/len(self.labels)*100:.1f}%)\n" if self.labels else "NA:             0\n")
            f.write(f"{'─' * 70}\n")
            f.write(f"Total:          {len(self.labels):>5}\n\n")
            
            # Per-Case Breakdown
            if case_stats:
                f.write("PER-CASE STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write(f"{'Case ID':<20} {'Total':>8} {'Suspicious':>12} {'Non-Susp':>12} {'NA':>8}\n")
                f.write("-" * 70 + "\n")
                for case in sorted(case_stats.keys()):
                    stats = case_stats[case]
                    f.write(f"{case:<20} {stats['total']:>8} {stats['Suspicious']:>12} "
                           f"{stats['Non-Suspicious']:>12} {stats['NA']:>8}\n")
                f.write("\n")
            
            # NA Comments Summary
            na_comments = [(v["case"], v["visit"], v["file"], v["comment"]) 
                          for v in self.labels.values() 
                          if v["label"] == "NA" and v.get("comment")]
            if na_comments:
                f.write("NA COMMENTS SUMMARY\n")
                f.write("-" * 70 + "\n")
                for case, visit, file, comment in na_comments:
                    f.write(f"Case: {case} | Visit: {visit}\n")
                    f.write(f"  File: {file}\n")
                    f.write(f"  Comment: {comment}\n")
                    f.write("-" * 70 + "\n")
                f.write("\n")
            
            # Productivity Metrics
            if SESSION["times"] and duration > 0:
                f.write("PRODUCTIVITY METRICS\n")
                f.write("-" * 70 + "\n")
                images_per_hour = len(self.labels) / (duration / 3600)
                f.write(f"Images per Hour: {images_per_hour:.1f}\n")
                f.write(f"Images per Minute: {images_per_hour/60:.2f}\n")
                if not partial:
                    f.write(f"Session Efficiency: {(sum(SESSION['times'])/duration)*100:.1f}% (active labeling time)\n")
                f.write("\n")
            
            # Footer
            f.write("=" * 70 + "\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n")

# -----------------------------
# REVIEW WINDOW
# -----------------------------
class ReviewWindow:
    def __init__(self, labels, output_file):
        self.labels = labels
        self.output_file = output_file

        self.win = tk.Tk()
        self.win.title("Review & Edit Labels")
        self.win.geometry("1000x600")

        # Title
        title = tk.Label(self.win, text="Review Your Labels", 
                        font=("Arial", 16, "bold"), bg="#2c3e50", fg="white", pady=10)
        title.pack(fill="x")

        # Treeview
        tree_frame = tk.Frame(self.win)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("Case", "Visit", "File", "Label", "Comment")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Configure columns
        for col in cols:
            self.tree.heading(col, text=col)
        
        self.tree.column("Case", width=150)
        self.tree.column("Visit", width=150)
        self.tree.column("File", width=250)
        self.tree.column("Label", width=150)
        self.tree.column("Comment", width=300)

        # Populate
        rows = sorted(labels.values(), key=lambda r: (r["case"], r["visit"], r["file"]))
        for row in rows:
            self.tree.insert("", tk.END, values=(
                row["case"], row["visit"], row["file"],
                row["label"], row["comment"]
            ))

        # Buttons
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="💾 Save Final CSV", command=self.save,
                 bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                 width=20, height=2).pack(side="left", padx=10)

        tk.Button(btn_frame, text="❌ Close", command=self.win.destroy,
                 bg="#c0392b", fg="white", font=("Arial", 11, "bold"),
                 width=20, height=2).pack(side="left", padx=10)

        self.win.mainloop()

    def save(self):
        """Save final CSV and summary"""
        try:
            # Write CSV
            Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
            
            rows = sorted(self.labels.values(), 
                         key=lambda r: (r["case"], r["visit"], r["file"]))
            
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ["case", "visit", "file", "label", "comment"]
                writer = csv.DictWriter(f, fieldnames=fieldnames,
                                       quoting=csv.QUOTE_MINIMAL)
                writer.writeheader()
                
                for row in rows:
                    clean_comment = row.get("comment", "").replace("\n", " ").replace("\r", " ")
                    writer.writerow({
                        "case": row.get("case", ""),
                        "visit": row.get("visit", ""),
                        "file": row.get("file", ""),
                        "label": row.get("label", ""),
                        "comment": clean_comment
                    })

            # Write summary (using same detailed format)
            summary_path = Path(self.output_file).with_name(
                Path(self.output_file).stem + "_summary.txt"
            )
            
            SESSION["end_time"] = time.time()
            duration = SESSION["end_time"] - SESSION["start_time"]
            avg_time = sum(SESSION["times"]) / len(SESSION["times"]) if SESSION["times"] else 0
            
            # Calculate statistics
            suspicious = sum(1 for v in self.labels.values() if v["label"] == "Suspicious")
            non_suspicious = sum(1 for v in self.labels.values() if v["label"] == "Non-Suspicious")
            na = sum(1 for v in self.labels.values() if v["label"] == "NA")
            
            # Per-case statistics
            case_stats = {}
            for key, label_data in self.labels.items():
                case = label_data["case"]
                if case not in case_stats:
                    case_stats[case] = {"total": 0, "Suspicious": 0, "Non-Suspicious": 0, "NA": 0}
                case_stats[case]["total"] += 1
                case_stats[case][label_data["label"]] += 1
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write(" " * 15 + "CLINICAL IMAGE LABELLING SESSION SUMMARY\n")
                f.write("=" * 70 + "\n\n")
                
                # Session Info
                f.write("SESSION INFORMATION\n")
                f.write("-" * 70 + "\n")
                f.write(f"Status: COMPLETED\n")
                f.write(f"Annotator: {SESSION['annotator']}\n")
                f.write(f"Session Started: {datetime.fromtimestamp(SESSION['start_time']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Session Ended: {datetime.fromtimestamp(SESSION['end_time']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Duration: {int(duration // 60)}m {int(duration % 60)}s ({duration/60:.1f} minutes)\n")
                f.write(f"Output File: {self.output_file}\n\n")
                
                # Progress Statistics
                f.write("PROGRESS STATISTICS\n")
                f.write("-" * 70 + "\n")
                f.write(f"Total Images Available: {SESSION['total_images']}\n")
                f.write(f"Images Labeled: {len(self.labels)}\n")
                completion_pct = (len(self.labels) / SESSION['total_images'] * 100) if SESSION['total_images'] > 0 else 0
                f.write(f"Completion Rate: {completion_pct:.1f}%\n")
                f.write(f"Unique Cases Processed: {len(SESSION['cases'])}\n\n")
                
                # Timing Statistics
                if SESSION["times"]:
                    f.write("TIMING ANALYSIS\n")
                    f.write("-" * 70 + "\n")
                    f.write(f"Average Time per Image: {avg_time:.2f} seconds\n")
                    f.write(f"Fastest Image: {min(SESSION['times']):.2f} seconds\n")
                    f.write(f"Slowest Image: {max(SESSION['times']):.2f} seconds\n")
                    f.write(f"Median Time: {sorted(SESSION['times'])[len(SESSION['times'])//2]:.2f} seconds\n")
                    total_label_time = sum(SESSION['times'])
                    f.write(f"Total Active Labeling Time: {int(total_label_time // 60)}m {int(total_label_time % 60)}s\n\n")
                
                # Label Distribution
                f.write("LABEL DISTRIBUTION\n")
                f.write("-" * 70 + "\n")
                f.write(f"Suspicious:     {suspicious:>5} ({suspicious/len(self.labels)*100:.1f}%)\n" if self.labels else "Suspicious:     0\n")
                f.write(f"Non-Suspicious: {non_suspicious:>5} ({non_suspicious/len(self.labels)*100:.1f}%)\n" if self.labels else "Non-Suspicious: 0\n")
                f.write(f"NA:             {na:>5} ({na/len(self.labels)*100:.1f}%)\n" if self.labels else "NA:             0\n")
                f.write(f"{'─' * 70}\n")
                f.write(f"Total:          {len(self.labels):>5}\n\n")
                
                # Per-Case Breakdown
                if case_stats:
                    f.write("PER-CASE STATISTICS\n")
                    f.write("-" * 70 + "\n")
                    f.write(f"{'Case ID':<20} {'Total':>8} {'Suspicious':>12} {'Non-Susp':>12} {'NA':>8}\n")
                    f.write("-" * 70 + "\n")
                    for case in sorted(case_stats.keys()):
                        stats = case_stats[case]
                        f.write(f"{case:<20} {stats['total']:>8} {stats['Suspicious']:>12} "
                               f"{stats['Non-Suspicious']:>12} {stats['NA']:>8}\n")
                    f.write("\n")
                
                # NA Comments Summary
                na_comments = [(v["case"], v["visit"], v["file"], v["comment"]) 
                              for v in self.labels.values() 
                              if v["label"] == "NA" and v.get("comment")]
                if na_comments:
                    f.write("NA COMMENTS SUMMARY\n")
                    f.write("-" * 70 + "\n")
                    for case, visit, file, comment in na_comments:
                        f.write(f"Case: {case} | Visit: {visit}\n")
                        f.write(f"  File: {file}\n")
                        f.write(f"  Comment: {comment}\n")
                        f.write("-" * 70 + "\n")
                    f.write("\n")
                
                # Productivity Metrics
                if SESSION["times"] and duration > 0:
                    f.write("PRODUCTIVITY METRICS\n")
                    f.write("-" * 70 + "\n")
                    images_per_hour = len(self.labels) / (duration / 3600)
                    f.write(f"Images per Hour: {images_per_hour:.1f}\n")
                    f.write(f"Images per Minute: {images_per_hour/60:.2f}\n")
                    f.write(f"Session Efficiency: {(sum(SESSION['times'])/duration)*100:.1f}% (active labeling time)\n")
                    f.write("\n")
                
                # Footer
                f.write("=" * 70 + "\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n")

            messagebox.showinfo("✓ Saved Successfully", 
                f"Labels saved to:\n{self.output_file}\n\nDetailed summary saved to:\n{summary_path}")
            self.win.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}")

# -----------------------------
# LAUNCHER
# -----------------------------
def select_root():
    root = filedialog.askdirectory(title="Select Batch Folder")
    if root:
        entry_root.delete(0, tk.END)
        entry_root.insert(0, root)

def select_output():
    out = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="clinical_labels.csv"
    )
    if out:
        entry_output.delete(0, tk.END)
        entry_output.insert(0, out)

def run():
    root_folder = entry_root.get().strip()
    out_file = entry_output.get().strip()

    if not root_folder or not out_file:
        messagebox.showerror("Error", "Please select both input folder and output file.")
        return

    images = find_clinical_images(root_folder)

    if not images:
        messagebox.showerror("Error", 
            "No Clinical images found.\n\nMake sure your folders contain 'XC' or 'CLINICAL' in their names.")
        return

    messagebox.showinfo("Ready", 
        f"Found {len(images)} clinical images across {len(set(img['case'] for img in images))} cases.\n\n"
        "Click OK to start labeling.")

    # Launch labeler
    main = tk.Toplevel(app)
    ClinicalLabelTool(main, images, out_file)

# Main window
app = tk.Tk()
app.title("Clinical Image Labelling Tool - Launcher")
app.geometry("700x200")

header = tk.Label(app, text="Clinical Image Labelling Tool", 
                 font=("Arial", 16, "bold"), bg="#2c3e50", fg="white", pady=15)
header.pack(fill="x")

form_frame = tk.Frame(app, padx=20, pady=20)
form_frame.pack(fill="both", expand=True)

tk.Label(form_frame, text="Batch Folder:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
entry_root = tk.Entry(form_frame, width=50, font=("Arial", 10))
entry_root.grid(row=0, column=1, padx=10, pady=5)
tk.Button(form_frame, text="Browse...", command=select_root, width=12).grid(row=0, column=2, pady=5)

tk.Label(form_frame, text="Output CSV:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
entry_output = tk.Entry(form_frame, width=50, font=("Arial", 10))
entry_output.grid(row=1, column=1, padx=10, pady=5)
tk.Button(form_frame, text="Browse...", command=select_output, width=12).grid(row=1, column=2, pady=5)

tk.Button(form_frame, text="🚀 Start Labelling", command=run, 
         bg="#27ae60", fg="white", font=("Arial", 12, "bold"),
         width=25, height=2).grid(row=2, column=1, pady=20)

app.mainloop()