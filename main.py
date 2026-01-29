import customtkinter as ctk
import os
from tkinter import filedialog, messagebox, simpledialog, Toplevel
import pdf_utils
import image_utils
import video_utils
import audio_utils
import word_utils
import excel_utils
import ppt_utils
import system_utils
import qr_utils
import threading

import sys

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LogRedirector:
    def __init__(self, textbox):
        self.textbox = textbox
        self.buffer = ""
        
    def write(self, text):
        # We need to schedule the update on the main thread
        # But 'write' is called from any thread (e.g. video processing)
        # However, tkinter methods should be main-thread mostly, but 'insert' is often thread-safe-ish in some implementations,
        # or we might need a queue. Simple way: direct insert.
        # If it crashes, we use after()
        try:
             self.textbox.after(0, self._append, text)
        except: pass

    def _append(self, text):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def flush(self):
        pass

class PDFStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Desktop Utility - All in One Tool")
        self.geometry("1300x850")
        
        # Tabs
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_pdf = self.tab_view.add("PDF Studio")
        self.tab_img = self.tab_view.add("Image Studio")
        self.tab_vid = self.tab_view.add("Video Studio")
        self.tab_audio = self.tab_view.add("Audio Studio")
        self.tab_word = self.tab_view.add("Word Studio")
        self.tab_excel = self.tab_view.add("Excel Studio")
        self.tab_ppt = self.tab_view.add("PowerPoint Studio")
        self.tab_sys = self.tab_view.add("System Studio")
        self.tab_qr = self.tab_view.add("QR Studio")
        
        self.main_frame = None # Dynamic reference

        # Tools Configuration
        self.pdf_tools = {
            "Organize": [
                ("Merge PDF", self.tool_merge),
                ("Split PDF", self.tool_split),
                ("Compress PDF", self.tool_compress),
                ("Delete Pages", self.tool_delete_pages),
                ("Rotate PDF", self.tool_rotate),
                ("Crop PDF", self.tool_crop),
                ("Rearrange PDF", self.tool_rearrange),
            ],
            "Convert FROM PDF": [
                ("PDF to Word", self.tool_pdf_to_word),
                ("PDF to Excel", self.tool_pdf_to_excel),
                ("PDF to PPT", self.tool_pdf_to_ppt),
                ("PDF to CSV", self.tool_pdf_to_csv),
                ("PDF to Images", self.tool_pdf_to_images),
                ("PDF to TIFF", self.tool_pdf_to_tiff),
                ("PDF to Text", self.tool_pdf_to_text),
            ],
            "Convert TO PDF": [
                ("Images to PDF", self.tool_images_to_pdf),
                ("Word to PDF", self.tool_word_to_pdf),
                ("PPT to PDF", self.tool_ppt_to_pdf),
                ("EPUB to PDF", self.tool_epub_to_pdf),
                ("URL to PDF", self.tool_url_to_pdf),
                ("Create PDF (Text)", self.tool_create_pdf),
                ("Outlook MSG to PDF", self.tool_msg_to_pdf),
            ],
            "Edit & Security": [
                ("Protect PDF", self.tool_protect),
                ("Unlock PDF", self.tool_unlock),
                ("Add Watermark", self.tool_watermark),
                ("Add Text", self.tool_add_text),
                ("Translate PDF", self.tool_translate_pdf),
                ("Add Page Numbers", self.tool_page_numbers),
                ("Sign PDF", self.tool_sign_pdf),
                ("Flatten PDF", self.tool_flatten_pdf),
            ]
        }
        
        self.img_tools = {
            "Enhancement": [
                ("Remove Background", self.tool_remove_bg),
                ("Upscale Image", self.tool_upscale),
                ("Unblur Image", self.tool_unblur),
                ("Grayscale", self.tool_grayscale),
                ("Pixelate", self.tool_pixelate),
                ("Change BG Color", self.tool_change_bg),
                ("Compress Image", self.tool_compress_img),
                ("Brightness/Contrast", self.tool_brightness_contrast),
                ("Face Blur", self.tool_face_blur),
            ],
            "Manipulation": [
                ("Resize Image", self.tool_resize_img),
                ("Crop Image", self.tool_crop_img),
                ("Flip Image", self.tool_flip_img),
                ("Rotate Image", self.tool_rotate_img),
                ("Add Border", self.tool_add_border),
                ("Round Image", self.tool_round_img),
                ("Add Text", self.tool_add_img_text),
            ],
            "Conversion": [
                ("Convert Format", self.tool_convert_img),
                ("Image OCR (Text)", self.tool_ocr_img),
            ]
        }

        self.video_tools = {
            "Editing": [
                ("Join/Merge Videos", self.tool_video_join),
                ("Cut/Trim Video", self.tool_video_cut),
            ],
            "Processing": [
                ("Convert Format", self.tool_video_convert),
                ("Compress Video", self.tool_video_compress),
                ("Extract Audio", self.tool_extract_audio),
            ],
            "Effects": [
                ("Add Watermark", self.tool_video_watermark),
                ("Change Speed", self.tool_video_speed),
                ("Mute Video", self.tool_mute_video),
                ("Add Music", self.tool_add_music),
            ]
        }

        self.audio_tools = {
            "Audio Tools": [
                ("Convert Format", self.tool_audio_convert),
                ("Cut/Trim Audio", self.tool_audio_cut),
                ("Join Audio", self.tool_audio_join),
            ],
            "Effects": [
                ("Adjust Volume", self.tool_audio_volume),
                ("Fade In/Out", self.tool_audio_fade),
            ]
        }
        
        self.word_tools = {
            "Word Tools": [
                 ("Word to PDF", self.tool_word_to_pdf),
                 ("Word to Images", self.tool_word_to_images),
            ]
        }

        self.excel_tools = {
            "Excel Tools": [
                 ("Excel to PDF", self.tool_excel_to_pdf),
                 ("Excel to CSV", self.tool_excel_to_csv),
            ]
        }

        self.ppt_tools = {
            "PowerPoint Tools": [
                 ("PPT to PDF", self.tool_ppt_to_pdf),
                 ("PPT to Images", self.tool_ppt_to_images),
            ]
        }
        
        self.sys_tools = {
            "File Management": [
                ("Bulk Rename", self.tool_bulk_rename),
                ("Organize Folder", self.tool_organize_folder),
            ],
            "Utils": [
                ("Identify File Hash", self.tool_file_hash),
                ("Find Duplicates", self.tool_find_duplicates),
                ("Clean Empty Folders", self.tool_clean_empty),
            ]
        }
        
        self.qr_tools = {
            "QR Code Tools": [
                ("Generate QR Code", self.tool_generate_qr),
                ("Read QR Code", self.tool_read_qr),
            ]
        }

        self.pdf_main_frame = self.setup_tab(self.tab_pdf, self.pdf_tools, "PDF Tools Menu")
        self.img_main_frame = self.setup_tab(self.tab_img, self.img_tools, "Image Tools Menu")
        self.vid_main_frame = self.setup_tab(self.tab_vid, self.video_tools, "Video Tools Menu")
        self.aud_main_frame = self.setup_tab(self.tab_audio, self.audio_tools, "Audio Tools")
        self.word_main_frame = self.setup_tab(self.tab_word, self.word_tools, "Word Tools")
        self.excel_main_frame = self.setup_tab(self.tab_excel, self.excel_tools, "Excel Tools")
        self.ppt_main_frame = self.setup_tab(self.tab_ppt, self.ppt_tools, "PowerPoint Tools")
        self.sys_main_frame = self.setup_tab(self.tab_sys, self.sys_tools, "System Tools")
        self.qr_main_frame = self.setup_tab(self.tab_qr, self.qr_tools, "QR Code Tools")
        
        # Default
        self.main_frame = self.pdf_main_frame
        self.show_welcome(self.pdf_main_frame)
        self.show_welcome(self.img_main_frame)
        self.show_welcome(self.vid_main_frame)
        self.show_welcome(self.aud_main_frame)
        self.show_welcome(self.word_main_frame)
        self.show_welcome(self.excel_main_frame)
        self.show_welcome(self.ppt_main_frame)
        self.show_welcome(self.sys_main_frame)
        self.show_welcome(self.qr_main_frame)

        # Log Console
        self.log_frame = ctk.CTkFrame(self, height=150, corner_radius=0)
        self.log_frame.pack(fill="x", side="bottom")
        
        self.log_lbl = ctk.CTkLabel(self.log_frame, text="Log Console", font=ctk.CTkFont(size=12, weight="bold"))
        self.log_lbl.pack(anchor="w", padx=10, pady=(5,0))
        
        self.log_box = ctk.CTkTextbox(self.log_frame, height=120, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_box.configure(state="disabled")

        # Redirect Output
        sys.stdout = LogRedirector(self.log_box)
        sys.stderr = LogRedirector(self.log_box)
        
        print("Application Started...")
        print("Ready.")

    def setup_tab(self, tab, tools_dict, title):
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        sidebar = ctk.CTkScrollableFrame(tab, width=250, corner_radius=0, label_text=title)
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Main Content
        main_frame = ctk.CTkFrame(tab, corner_radius=0, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Populate
        row = 0
        for category, items in tools_dict.items():
            lbl = ctk.CTkLabel(sidebar, text=category, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
            lbl.grid(row=row, column=0, padx=10, pady=(15, 5), sticky="ew")
            row += 1
            for name, func in items:
                # Capture frame in binding
                btn = ctk.CTkButton(sidebar, text=name, command=lambda f=func, n=name, mf=main_frame: self.load_tool(n, f, mf), 
                                    fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), anchor="w")
                btn.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
                row += 1
        return main_frame

    def clear_main(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def show_welcome(self, frame):
        self.clear_main(frame)
        ctk.CTkLabel(frame, text="Select a tool from the sidebar.", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=40)

    def load_tool(self, name, func, frame):
        if hasattr(self, 'is_busy') and self.is_busy:
            messagebox.showwarning("Busy", "A task is currently running. Please wait.")
            return

        self.main_frame = frame # Set active frame for helpers
        self.clear_main(frame)
        ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20))
        func()

    # --- Generic UI Helpers ---
    def create_single_file_processor(self, file_type, file_filter, process_callback, btn_text="Process", output_filter=None):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        self.selected_file = None
        
        lbl_file = ctk.CTkLabel(frame, text="No file selected")
        lbl_file.pack(pady=10)

        def select():
            f = filedialog.askopenfilename(filetypes=file_filter)
            if f:
                self.selected_file = f
                lbl_file.configure(text=os.path.basename(f))
                _update_preview(f) # Call _update_preview here

        ctk.CTkButton(frame, text=f"Select {file_type}", command=select).pack(pady=10)
        
        # Preview
        self.preview_label = ctk.CTkLabel(frame, text="")
        self.preview_label.pack(pady=5)
        
        # Original select logic wrapper needed to update preview
        def _update_preview(f):
            if not f: return
            try:
                thumb = image_utils.get_thumbnail(f)
                if thumb:
                    ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
                    self.preview_label.configure(image=ctk_img, text="")
                else:
                    self.preview_label.configure(image=None, text="")
            except: pass
        
        # Progress Bar
        self.progress = ctk.CTkProgressBar(frame, mode="indeterminate", width=300)
        
        def run():
            if not self.selected_file:
                messagebox.showerror("Error", "Please select a file first.")
                return
            
            target_filter = output_filter or file_filter
            def_ext = None
            if target_filter and len(target_filter) > 0:
                 try:
                    first_ext = target_filter[0][1].split(';')[0]
                    if "*" in first_ext: def_ext = first_ext.replace("*", "")
                 except: pass

            output = filedialog.asksaveasfilename(filetypes=target_filter, defaultextension=def_ext)
            if output:
                self.is_busy = True # Lock UI
                self.progress.pack(pady=10)
                self.progress.start()
                def task():
                    try:
                        process_callback(self.selected_file, output)
                        self.after(0, lambda: [messagebox.showinfo("Success", "Operation Completed!"), self.progress.stop(), self.progress.pack_forget(), setattr(self, 'is_busy', False)])
                    except Exception as e:
                        msg = str(e) or repr(e)
                        self.after(0, lambda: [messagebox.showerror("Error", msg), self.progress.stop(), self.progress.pack_forget(), setattr(self, 'is_busy', False)])
                threading.Thread(target=task).start()

        ctk.CTkButton(frame, text=btn_text, command=run, fg_color="green").pack(pady=20)
        return frame

    def create_multi_file_processor(self, file_type, file_filter, process_callback, btn_text="Process", output_filter=None):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        self.selected_files = []
        
        txt_display = ctk.CTkTextbox(frame, height=200)
        txt_display.pack(fill="x", pady=10)

        def update_display():
            txt_display.delete("0.0", "end")
            for f in self.selected_files:
                txt_display.insert("end", f + "\n")

        def add():
            files = filedialog.askopenfilenames(filetypes=file_filter)
            if files:
                self.selected_files.extend(files)
                update_display()

        ctk.CTkButton(frame, text=f"Add {file_type}s", command=add).pack(pady=10)
        ctk.CTkButton(frame, text="Clear List", command=lambda: [self.selected_files.clear(), update_display()], fg_color="red").pack(pady=5)
        
        self.progress_multi = ctk.CTkProgressBar(frame, mode="indeterminate", width=300)

        def run():
            if not self.selected_files:
                messagebox.showerror("Error", "Please select files first.")
                return
            
            out_filter = output_filter if output_filter else file_filter
            
            # Determine default extension
            def_ext = None
            if out_filter and len(out_filter) > 0:
                try:
                    # e.g. [("MP4", "*.mp4")] -> take first ext
                    first_ext = out_filter[0][1].split(';')[0]
                    if "*" in first_ext:
                        def_ext = first_ext.replace("*", "")
                except: pass

            output = filedialog.asksaveasfilename(filetypes=out_filter, defaultextension=def_ext)
            if output:
                self.is_busy = True # Lock
                self.progress_multi.pack(pady=10)
                self.progress_multi.start()
                def task():
                    try:
                        process_callback(self.selected_files, output)
                        self.after(0, lambda: [messagebox.showinfo("Success", "Operation Completed!"), self.selected_files.clear(), update_display(), self.progress_multi.stop(), self.progress_multi.pack_forget(), setattr(self, 'is_busy', False)])
                    except Exception as e:
                        print(f"Task Failed: {repr(e)}")
                        msg = str(e) or repr(e)
                        self.after(0, lambda: [messagebox.showerror("Error", msg), self.progress_multi.stop(), self.progress_multi.pack_forget(), setattr(self, 'is_busy', False)])
                threading.Thread(target=task).start()

        ctk.CTkButton(frame, text=btn_text, command=run, fg_color="green").pack(pady=20)
        return frame

    # --- Organizers ---
    def tool_merge(self): self.create_multi_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.merge_pdfs, "Merge PDFs")
    
    def tool_split(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self.selected_file = None
        lbl = ctk.CTkLabel(frame, text="No file selected")
        lbl.pack(pady=10)
        
        def select():
            f = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
            if f:
                self.selected_file = f
                lbl.configure(text=os.path.basename(f))
                
        ctk.CTkButton(frame, text="Select PDF", command=select).pack(pady=10)
        
        def run():
            if not self.selected_file: return
            out_dir = filedialog.askdirectory()
            if not out_dir: return
            
            def task():
                try:
                    pdf_utils.split_pdf(self.selected_file, out_dir)
                    self.after(0, lambda: messagebox.showinfo("Done", "Split complete!"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))
            threading.Thread(target=task).start()

        ctk.CTkButton(frame, text="Split All Pages", command=run, fg_color="orange").pack(pady=20)

    def tool_compress(self): self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.compress_pdf, "Compress Now")

    def tool_delete_pages(self):
        frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.delete_pages(i, o, self.del_pages), "Delete Pages")
        lbl = ctk.CTkLabel(frame, text="Pages to delete (comma sep):")
        lbl.pack(before=frame.winfo_children()[-1])
        ent = ctk.CTkEntry(frame)
        ent.pack(before=frame.winfo_children()[-1], pady=5)
        self.del_pages = []
        ent.bind("<KeyRelease>", lambda e: setattr(self, 'del_pages', [int(x) for x in ent.get().split(',') if x.strip().isdigit()]))

    def tool_rotate(self):
        frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.rotate_pdf(i, o, self.rot_deg), "Rotate")
        self.rot_deg = 90
        seg = ctk.CTkSegmentedButton(frame, values=["90", "180", "270"], command=lambda v: setattr(self, 'rot_deg', int(v)))
        seg.pack(before=frame.winfo_children()[-1], pady=10)
        seg.set("90")

    def tool_crop(self):
        frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.crop_pdf(i, o, self.crop_margins), "Crop")
        self.crop_margins = [0,0,0,0]
        entries_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entries_frame.pack(before=frame.winfo_children()[-1], pady=10)
        entries = []
        for i, txt in enumerate(["Left", "Top", "Right", "Bottom"]):
            ctk.CTkLabel(entries_frame, text=txt).grid(row=0, column=i, padx=5)
            e = ctk.CTkEntry(entries_frame, width=50)
            e.grid(row=1, column=i, padx=5)
            entries.append(e)
            e.insert(0, "0")
        def upd(): self.crop_margins = [float(e.get()) for e in entries]
        ctk.CTkButton(entries_frame, text="Update", command=upd).grid(row=2, column=0, columnspan=4, pady=5)

    def tool_rearrange(self):
        frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.rearrange_pdf(i, o, self.page_order), "Rearrange")
        ctk.CTkLabel(frame, text="Page Order (e.g. 2,1,3):").pack(before=frame.winfo_children()[-1])
        ent = ctk.CTkEntry(frame)
        ent.pack(before=frame.winfo_children()[-1], pady=5)
        self.page_order = []
        ent.bind("<KeyRelease>", lambda e: setattr(self, 'page_order', [int(x) for x in ent.get().split(',') if x.strip().isdigit()]))

    # --- Convert From PDF ---
    def tool_pdf_to_word(self): self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.pdf_to_word, "To Word", [("Word", "*.docx")])
    def tool_pdf_to_excel(self): self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.pdf_to_excel, "To Excel", [("Excel", "*.xlsx")])
    def tool_pdf_to_csv(self): self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.pdf_to_csv, "To CSV", [("CSV", "*.csv")]) 
    def tool_pdf_to_ppt(self): self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.pdf_to_ppt, "To PPT", [("PPT", "*.pptx")])
    def tool_pdf_to_tiff(self): self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.pdf_to_tiff, "To TIFF", [("TIFF", "*.tiff")])
    def tool_pdf_to_text(self): self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.pdf_to_text, "To Text", [("Text", "*.txt")])
    def tool_pdf_to_images(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self.selected_file = None
        lbl = ctk.CTkLabel(frame, text="No file selected")
        lbl.pack(pady=10)
        
        def select():
            f = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
            if f:
                self.selected_file = f
                lbl.configure(text=os.path.basename(f))
        
        ctk.CTkButton(frame, text="Select PDF", command=select).pack(pady=10)
        
        def run():
            if not self.selected_file: return
            out_dir = filedialog.askdirectory()
            if not out_dir: return
            
            def task():
                try:
                    pdf_utils.pdf_to_images(self.selected_file, out_dir)
                    self.after(0, lambda: messagebox.showinfo("Done", "Images extracted!"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))
            threading.Thread(target=task).start()

        ctk.CTkButton(frame, text="Extract Images", command=run, fg_color="purple").pack(pady=20)

    # --- Convert To PDF ---
    def tool_images_to_pdf(self): self.create_multi_file_processor("Image", [("Images", "*.jpg;*.png;*.jpeg;*.tiff;*.bmp;*.gif;*.webp;*.heic")], pdf_utils.images_to_pdf, "Create PDF", [("PDF", "*.pdf")])
    def tool_word_to_pdf(self): self.create_single_file_processor("Word", [("Word", "*.docx")], word_utils.word_to_pdf, "To PDF", [("PDF", "*.pdf")])
    def tool_ppt_to_pdf(self): self.create_single_file_processor("PPT", [("PPT", "*.ppt;*.pptx")], ppt_utils.ppt_to_pdf, "To PDF", [("PDF", "*.pdf")])
    def tool_epub_to_pdf(self): self.create_single_file_processor("EPUB", [("EPUB", "*.epub")], pdf_utils.epub_to_pdf, "To PDF", [("PDF", "*.pdf")])
    def tool_msg_to_pdf(self): self.create_single_file_processor("MSG", [("MSG", "*.msg")], pdf_utils.msg_to_pdf, "To PDF", [("PDF", "*.pdf")])

    def tool_url_to_pdf(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Enter Webpage URL:").pack(pady=10)
        ent = ctk.CTkEntry(frame, width=400)
        ent.pack(pady=10)
        def run():
            url = ent.get()
            if not url: return
            out = filedialog.asksaveasfilename(defaultextension=".pdf")
            if out: 
                threading.Thread(target=lambda: [pdf_utils.url_to_pdf(url, out), messagebox.showinfo("Success", "PDF Created!")]).start()
        ctk.CTkButton(frame, text="Convert URL", command=run, fg_color="blue").pack(pady=20)

    def tool_create_pdf(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Enter Text Content:").pack(pady=10)
        txt = ctk.CTkTextbox(frame, height=300)
        txt.pack(fill="x", padx=10, pady=10)
        def run():
            content = txt.get("0.0", "end")
            out = filedialog.asksaveasfilename(defaultextension=".pdf")
            if out:
                pdf_utils.create_pdf(content, out)
                messagebox.showinfo("Success", "Created!")
        ctk.CTkButton(frame, text="Save as PDF", command=run, fg_color="green").pack(pady=20)

    # --- Edit ---
    def tool_protect(self):
        frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.add_password(i, o, self.pwd), "Encrypt")
        ent = ctk.CTkEntry(frame, show="*")
        ent.pack(before=frame.winfo_children()[-1], pady=5)
        self.pwd = ""
        ent.bind("<KeyRelease>", lambda e: setattr(self, 'pwd', ent.get()))

    def tool_unlock(self):
        frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.unlock_pdf(i, o, self.pwd), "Decrypt")
        ent = ctk.CTkEntry(frame, show="*")
        ent.pack(before=frame.winfo_children()[-1], pady=5)
        self.pwd = ""
        ent.bind("<KeyRelease>", lambda e: setattr(self, 'pwd', ent.get()))

    def tool_watermark(self):
        frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.add_watermark(i, o, self.wm), "Add Watermark")
        ent = ctk.CTkEntry(frame, placeholder_text="Watermark Text")
        ent.pack(before=frame.winfo_children()[-1], pady=5)
        self.wm = "CONFIDENTIAL"
        ent.bind("<KeyRelease>", lambda e: setattr(self, 'wm', ent.get()))

    def tool_add_text(self):
        frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.add_text_annotation(i, o, self.txt_val, self.txt_x, self.txt_y), "Add Text")
        f2 = ctk.CTkFrame(frame, fg_color="transparent")
        f2.pack(before=frame.winfo_children()[-1], pady=10)
        ctk.CTkLabel(f2, text="Text:").grid(row=0, column=0); e1=ctk.CTkEntry(f2); e1.grid(row=0, column=1)
        ctk.CTkLabel(f2, text="X:").grid(row=0, column=2); e2=ctk.CTkEntry(f2, width=50); e2.grid(row=0, column=3)
        ctk.CTkLabel(f2, text="Y:").grid(row=0, column=4); e3=ctk.CTkEntry(f2, width=50); e3.grid(row=0, column=5)
        self.txt_val, self.txt_x, self.txt_y = "", 100, 100
        def upd(*a): 
            try: self.txt_val, self.txt_x, self.txt_y = e1.get(), float(e2.get()), float(e3.get())
            except: pass
        ctk.CTkButton(f2, text="Update", command=upd, width=60).grid(row=0, column=6, padx=5)

    def tool_translate_pdf(self):
         frame = self.create_single_file_processor("PDF", [("PDF", "*.pdf")], lambda i, o: pdf_utils.translate_pdf(i, o, self.lang), "Translate & Convert")
         ent = ctk.CTkEntry(frame, placeholder_text="Target Lang (e.g. 'fr', 'es')")
         ent.pack(before=frame.winfo_children()[-1], pady=5)
         self.lang = "en"
         ent.bind("<KeyRelease>", lambda e: setattr(self, 'lang', ent.get()))

    def tool_page_numbers(self): self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.add_page_numbers, "Add Page Numbers")
    
    def tool_change_bg(self):
        self.bg_col = "#FFFFFF"  # Default white background
        frame = self.create_single_file_processor("Image", [("PNG", "*.png")],  lambda i, o: image_utils.change_image_background(i, o, self.bg_col), "Process Image", [("PNG", "*.png")])
        # Color input
        color_frame = ctk.CTkFrame(frame, fg_color="transparent")
        color_frame.pack(before=frame.winfo_children()[-1], pady=10)
        ctk.CTkLabel(color_frame, text="Background Color (hex):").pack(side="left", padx=5)
        ent = ctk.CTkEntry(color_frame, width=100)
        ent.pack(side="left", padx=5)
        ent.insert(0, "#FFFFFF")
        ent.bind("<KeyRelease>", lambda e: setattr(self, 'bg_col', ent.get()))
        
    def tool_compress_img(self):
         # Quality slider
         frame = self.create_single_file_processor("Image", [("Images", "*.jpg;*.jpeg;*.png")], lambda i, o: image_utils.compress_image(i, o, self.img_qual), "Compress")
         self.img_qual = 50
         sl = ctk.CTkSlider(frame, from_=10, to=95, number_of_steps=85)
         sl.set(50)
         sl.pack(before=frame.winfo_children()[-1], pady=5)
         lbl = ctk.CTkLabel(frame, text="Quality: 50")
         lbl.pack(before=frame.winfo_children()[-1])
         sl.configure(command=lambda v: [setattr(self, 'img_qual', int(v)), lbl.configure(text=f"Quality: {int(v)}")])
    # --- Image Tools ---
    def tool_remove_bg(self): self.create_single_file_processor("Image", [("Images", "*.png;*.jpg;*.jpeg;*.webp")], image_utils.remove_background, "Remove BG", [("PNG", "*.png")])
    def tool_upscale(self): self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], image_utils.upscale_image, "Upscale 2x")
    def tool_unblur(self): self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], image_utils.unblur_image, "Unblur/Sharpen")
    def tool_grayscale(self): self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], image_utils.grayscale_image, "Convert to B/W")
    def tool_pixelate(self): self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], image_utils.pixelate_image, "Pixelate")
    def tool_add_border(self): self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], image_utils.add_border, "Add Border")
    def tool_round_img(self): self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], image_utils.make_round_image, "Make Round", [("PNG", "*.png")])
    def tool_ocr_img(self): self.create_single_file_processor("Image", [("Images", "*.png;*.jpg;*.jpeg;*.tiff;*.bmp")], image_utils.extract_text_ocr, "Extract Text", [("Text", "*.txt")])
    
    def tool_resize_img(self):
        frame = self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], lambda i, o: image_utils.resize_image(i, o, self.w, self.h), "Resize")
        f2 = ctk.CTkFrame(frame, fg_color="transparent")
        f2.pack(before=frame.winfo_children()[-1], pady=5)
        ctk.CTkLabel(f2, text="W:").pack(side="left"); e1=ctk.CTkEntry(f2, width=60); e1.pack(side="left", padx=5)
        ctk.CTkLabel(f2, text="H:").pack(side="left"); e2=ctk.CTkEntry(f2, width=60); e2.pack(side="left", padx=5)
        self.w, self.h = 800, 600
        def upd(*a): 
            try: self.w, self.h = int(e1.get()), int(e2.get())
            except: pass
        ctk.CTkButton(f2, text="Set", command=upd, width=50).pack(side="left")

    def tool_crop_img(self):
        frame = self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], lambda i, o: image_utils.crop_image_rel(i, o, self.cl, self.ct, self.cr, self.cb), "Crop")
        f2 = ctk.CTkFrame(frame, fg_color="transparent")
        f2.pack(before=frame.winfo_children()[-1], pady=5)
        entries=[]
        for t in ["L","T","R","B"]:
            ctk.CTkLabel(f2, text=t).pack(side="left")
            e = ctk.CTkEntry(f2, width=40); e.pack(side="left", padx=2); entries.append(e); e.insert(0,"0")
        self.cl, self.ct, self.cr, self.cb = 0,0,0,0
        ctk.CTkButton(f2, text="Update", command=lambda: setattr(self, 'cl', int(entries[0].get())) or setattr(self, 'ct', int(entries[1].get())) or setattr(self, 'cr', int(entries[2].get())) or setattr(self, 'cb', int(entries[3].get())), width=50).pack(side="left")

    def tool_flip_img(self):
        frame = self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], lambda i, o: image_utils.flip_image(i, o, self.flip_dir), "Flip")
        self.flip_dir="horizontal"
        seg = ctk.CTkSegmentedButton(frame, values=["Horizontal", "Vertical"], command=lambda v: setattr(self, 'flip_dir', v))
        seg.pack(before=frame.winfo_children()[-1], pady=10)
        seg.set("Horizontal")

    def tool_rotate_img(self):
        frame = self.create_single_file_processor("Image", [("Images", "*.png;*.jpg")], lambda i, o: image_utils.rotate_image(i, o, self.rot_ang), "Rotate")
        self.rot_ang=90
        seg = ctk.CTkSegmentedButton(frame, values=["90", "180", "270"], command=lambda v: setattr(self, 'rot_ang', int(v)))
        seg.pack(before=frame.winfo_children()[-1], pady=10)
        seg.set("90")

    def tool_convert_img(self):
        # Massive format converter
        formats = [("Images", "*.png;*.jpg;*.jpeg;*.webp;*.heic;*.tiff;*.bmp;*.gif;*.svg;*.psd;*.eps")]
        frame = self.create_single_file_processor("Image", formats, image_utils.convert_image_format, "Convert")
        
        # We need flexible output extension. For now, let user pick format in save dialog.
        # But `create_single_file_processor` uses `filetypes` arg for saves.
        # We can add a dropdown to select TARGET format if we want more control,
        # but defaulting to standard save dialog extensions is easier.
        # Just override the save types.
        
        # Hack to access the save button logic or just re-implement
        # Re-implementing simplified logic just for this tool
        self.clear_main(self.main_frame)
        ctk.CTkLabel(self.main_frame, text="Convert Image Format", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20))
        
        ctk.CTkLabel(self.main_frame, text="Supports: JPG, PNG, WEBP, HEIC, TIFF, SVG, PSD, EPS, GIF -> MP4/AVIF").pack(pady=5)
        
        self.sel_img_conv = None
        lbl = ctk.CTkLabel(self.main_frame, text="No file selected")
        lbl.pack(pady=10)
        
        def pick():
            f = filedialog.askopenfilename(filetypes=formats)
            if f:
                self.sel_img_conv = f
                lbl.configure(text=os.path.basename(f))
        
        ctk.CTkButton(self.main_frame, text="Select File", command=pick).pack(pady=10)
        
        # Target format selection
        target_formats = [
            "JPG", "PNG", "WEBP", "TIFF", "ICO", "PDF", "BMP", "SVG", "GIF", "MP4" 
        ]
        
        cmb = ctk.CTkComboBox(self.main_frame, values=target_formats)
        cmb.pack(pady=10)
        cmb.set("PNG")
        
        def run():
            if not self.sel_img_conv: return
            fmt = cmb.get().lower()
            ext = f".{fmt}"
            out = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(fmt.upper(), f"*{ext}")])
            if out:
                threading.Thread(target=lambda: [image_utils.convert_image_format(self.sel_img_conv, out), messagebox.showinfo("Done", "Converted!")]).start()
                
        ctk.CTkButton(self.main_frame, text="Convert Now", command=run, fg_color="green").pack(pady=20)


    # --- Video Tools ---
    def tool_video_join(self):
        self.create_multi_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv")], video_utils.join_videos, "Join Videos", [("MP4", "*.mp4")])

    def tool_video_cut(self):
        frame = self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv")], lambda i, o: video_utils.cut_video(i, o, self.v_start, self.v_end), "Cut Video")
        f2 = ctk.CTkFrame(frame, fg_color="transparent")
        f2.pack(before=frame.winfo_children()[-1], pady=5)
        
        ctk.CTkLabel(f2, text="Start (MM:SS):").pack(side="left", padx=5)
        e1 = ctk.CTkEntry(f2, width=80)
        e1.pack(side="left", padx=5)
        e1.insert(0, "00:00")
        
        ctk.CTkLabel(f2, text="End (MM:SS):").pack(side="left", padx=5)
        e2 = ctk.CTkEntry(f2, width=80)
        e2.pack(side="left", padx=5)
        
        self.v_start, self.v_end = "00:00", "00:10"
        
        def upd(*a):
            self.v_start = e1.get()
            self.v_end = e2.get()
            
        ctk.CTkButton(f2, text="Update", command=upd, width=60).pack(side="left", padx=10)

    def tool_video_convert(self):
        # Allow saving as different formats
        formats = [("MP4", "*.mp4"), ("AVI", "*.avi"), ("MOV", "*.mov"), ("MKV", "*.mkv"), ("GIF", "*.gif")]
        self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv;*.gif")], video_utils.convert_video, "Convert", formats)

    def tool_video_compress(self):
        self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv")], video_utils.compress_video, "Compress (Auto)")

    def tool_extract_audio(self):
        self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi")], video_utils.extract_audio, "Extract Audio", [("MP3", "*.mp3")])

    # --- Audio Tools ---
    def tool_audio_convert(self):
        # Supports MP3, WAV, AAC, etc.
        formats = [("MP3", "*.mp3"), ("WAV", "*.wav"), ("AAC", "*.aac"), ("FLAC", "*.flac"), ("M4A", "*.m4a")]
        self.create_single_file_processor("Audio", [("Audio", "*.mp3;*.wav;*.ogg;*.m4a;*.flac")], audio_utils.convert_audio, "Convert", formats)

    def tool_audio_cut(self):
        frame = self.create_single_file_processor("Audio", [("Audio", "*.mp3;*.wav;*.ogg;*.m4a")], lambda i, o: audio_utils.cut_audio(i, o, self.a_start, self.a_end), "Cut Audio")
        f2 = ctk.CTkFrame(frame, fg_color="transparent")
        f2.pack(before=frame.winfo_children()[-1], pady=5)
        
        ctk.CTkLabel(f2, text="Start:").pack(side="left", padx=5)
        e1 = ctk.CTkEntry(f2, width=80); e1.pack(side="left", padx=5); e1.insert(0, "00:00")
        
        ctk.CTkLabel(f2, text="End:").pack(side="left", padx=5)
        e2 = ctk.CTkEntry(f2, width=80); e2.pack(side="left", padx=5)
        
        self.a_start, self.a_end = "00:00", "00:10"
        def upd(*a): self.a_start, self.a_end = e1.get(), e2.get()
        ctk.CTkButton(f2, text="Set Times", command=upd, width=60).pack(side="left", padx=10)

    def tool_audio_join(self):
        self.create_multi_file_processor("Audio", [("Audio", "*.mp3;*.wav;*.ogg")], audio_utils.join_audio, "Merge Audio", [("MP3", "*.mp3")])

    # --- Office Tools ---
    def tool_word_to_images(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self.selected_file = None
        lbl = ctk.CTkLabel(frame, text="No file selected")
        lbl.pack(pady=10)
        
        def select():
            f = filedialog.askopenfilename(filetypes=[("Word", "*.docx;*.doc")])
            if f:
                self.selected_file = f
                lbl.configure(text=os.path.basename(f))
        
        ctk.CTkButton(frame, text="Select Word Document", command=select).pack(pady=10)
        
        def run():
            if not self.selected_file: return
            out_dir = filedialog.askdirectory()
            if not out_dir: return
            def task():
                try:
                    word_utils.word_to_images(self.selected_file, out_dir)
                    self.after(0, lambda: messagebox.showinfo("Done", "Images extracted!"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))
            threading.Thread(target=task).start()

        ctk.CTkButton(frame, text="Convert to Images", command=run, fg_color="blue").pack(pady=20)

    def tool_excel_to_pdf(self):
        self.create_single_file_processor("Excel", [("Excel", "*.xlsx;*.xls")], excel_utils.excel_to_pdf, "To PDF", [("PDF", "*.pdf")])

    def tool_excel_to_csv(self):
         # We need a dedicated pandas bridge here because utils.pdf_to_csv is for PDF
         # Let's add a small lambda or update utils?
         # I'll create an inline wrapper since it's simple pandas
         def ex_to_csv(i, o):
             import pandas as pd
             df = pd.read_excel(i)
             df.to_csv(o, index=False)
         self.create_single_file_processor("Excel", [("Excel", "*.xlsx;*.xls")], ex_to_csv, "To CSV", [("CSV", "*.csv")])

    def tool_ppt_to_images(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self.selected_file = None
        lbl = ctk.CTkLabel(frame, text="No file selected")
        lbl.pack(pady=10)
        
        def select():
            f = filedialog.askopenfilename(filetypes=[("PPT", "*.pptx;*.ppt")])
            if f:
                self.selected_file = f
                lbl.configure(text=os.path.basename(f))
        
        ctk.CTkButton(frame, text="Select Presentation", command=select).pack(pady=10)
        
        def run():
            if not self.selected_file: return
            out_dir = filedialog.askdirectory()
            if not out_dir: return
            def task():
                try:
                    ppt_utils.ppt_to_images(self.selected_file, out_dir)
                    self.after(0, lambda: messagebox.showinfo("Done", "Slides exported!"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))
            threading.Thread(target=task).start()

        ctk.CTkButton(frame, text="Export Slides", command=run, fg_color="purple").pack(pady=20)

    # --- System Tools ---
    def tool_bulk_rename(self):
        # We need a custom UI for folder selection + prefix/suffix inputs
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(frame, text="Bulk Rename Files in Folder", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.ren_folder = ""
        lbl_f = ctk.CTkLabel(frame, text="No folder selected") # Define lbl_f before use in lambda
        
        def pick_folder():
             self.ren_folder = filedialog.askdirectory()
             if self.ren_folder:
                 lbl_f.configure(text=self.ren_folder)
        
        btn = ctk.CTkButton(frame, text="Select Folder", command=pick_folder)
        btn.pack(pady=5); lbl_f.pack()

        e1 = ctk.CTkEntry(frame, placeholder_text="Prefix"); e1.pack(pady=5)
        e2 = ctk.CTkEntry(frame, placeholder_text="Suffix"); e2.pack(pady=5)
        e3 = ctk.CTkEntry(frame, placeholder_text="Replace 'This'"); e3.pack(pady=5)
        e4 = ctk.CTkEntry(frame, placeholder_text="With 'That'"); e4.pack(pady=5)

        def run():
            if not self.ren_folder: return
            files = [os.path.join(self.ren_folder, f) for f in os.listdir(self.ren_folder) if os.path.isfile(os.path.join(self.ren_folder, f))]
            count = system_utils.bulk_rename(files, e1.get(), e2.get(), e3.get() if e3.get() else None, e4.get())
            messagebox.showinfo("Done", f"Renamed {count} files.")

        ctk.CTkButton(frame, text="Rename All", command=run, fg_color="orange").pack(pady=20)

    def tool_organize_folder(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Organize Folder by Extension", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        def run():
            d = filedialog.askdirectory()
            if d:
                c = system_utils.organize_folder(d)
                messagebox.showinfo("Done", f"Organized {c} files.")
        
        ctk.CTkButton(frame, text="Select Folder to Organize", command=run, fg_color="blue").pack(pady=20)

    def tool_file_hash(self):
        # Manual UI
        self.clear_main(self.main_frame)
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Calculate File Hash", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.hash_file = ""
        lbl = ctk.CTkLabel(frame, text="No file")
        def sel():
            f = filedialog.askopenfilename()
            if f:
                self.hash_file = f
                lbl.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="Select File", command=sel).pack(pady=5); lbl.pack()

        res_box = ctk.CTkTextbox(frame, height=100); res_box.pack(fill="x", pady=10)

        def run():
            if not self.hash_file: return
            md5 = system_utils.calculate_hash(self.hash_file, "md5")
            sha = system_utils.calculate_hash(self.hash_file, "sha256")
            res_box.delete("0.0", "end")
            res_box.insert("end", f"MD5:    {md5}\nSHA256: {sha}")

        ctk.CTkButton(frame, text="Calculate", command=run, fg_color="green").pack(pady=10)

    # --- NEW: PDF Sign & Flatten Tools ---
    def tool_sign_pdf(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        
        self.selected_file = None
        self.sig_img = None
        
        lbl_pdf = ctk.CTkLabel(frame, text="No PDF selected")
        lbl_pdf.pack(pady=5)
        
        def sel_pdf():
            f = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
            if f:
                self.selected_file = f
                lbl_pdf.configure(text=os.path.basename(f))
        
        ctk.CTkButton(frame, text="Select PDF", command=sel_pdf).pack(pady=5)
        
        lbl_sig = ctk.CTkLabel(frame, text="No signature image selected")
        lbl_sig.pack(pady=5)
        
        def sel_sig():
            f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
            if f:
                self.sig_img = f
                lbl_sig.configure(text=os.path.basename(f))
        
        ctk.CTkButton(frame, text="Select Signature Image", command=sel_sig).pack(pady=5)
        
        # Position inputs
        pos_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pos_frame.pack(pady=10)
        ctk.CTkLabel(pos_frame, text="X:").pack(side="left"); ex = ctk.CTkEntry(pos_frame, width=60); ex.pack(side="left", padx=5); ex.insert(0, "100")
        ctk.CTkLabel(pos_frame, text="Y:").pack(side="left"); ey = ctk.CTkEntry(pos_frame, width=60); ey.pack(side="left", padx=5); ey.insert(0, "100")
        ctk.CTkLabel(pos_frame, text="W:").pack(side="left"); ew = ctk.CTkEntry(pos_frame, width=60); ew.pack(side="left", padx=5); ew.insert(0, "150")
        ctk.CTkLabel(pos_frame, text="H:").pack(side="left"); eh = ctk.CTkEntry(pos_frame, width=60); eh.pack(side="left", padx=5); eh.insert(0, "50")
        
        def run():
            if not self.selected_file or not self.sig_img: 
                messagebox.showerror("Error", "Select both PDF and signature image")
                return
            out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if out:
                try:
                    pdf_utils.sign_pdf(self.selected_file, out, self.sig_img, 
                                       float(ex.get()), float(ey.get()), float(ew.get()), float(eh.get()))
                    messagebox.showinfo("Done", "PDF signed!")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(frame, text="Sign PDF", command=run, fg_color="green").pack(pady=20)

    def tool_flatten_pdf(self):
        self.create_single_file_processor("PDF", [("PDF", "*.pdf")], pdf_utils.flatten_pdf, "Flatten PDF")

    # --- NEW: Image Tools ---
    def tool_brightness_contrast(self):
        frame = self.create_single_file_processor("Image", [("Images", "*.png;*.jpg;*.jpeg")], 
            lambda i, o: image_utils.adjust_brightness_contrast(i, o, self.brightness, self.contrast), "Apply")
        
        self.brightness, self.contrast = 1.0, 1.0
        
        sl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        sl_frame.pack(before=frame.winfo_children()[-1], pady=10)
        
        ctk.CTkLabel(sl_frame, text="Brightness:").grid(row=0, column=0, padx=5)
        sb = ctk.CTkSlider(sl_frame, from_=0.2, to=2.0, number_of_steps=36)
        sb.set(1.0); sb.grid(row=0, column=1)
        lbl_b = ctk.CTkLabel(sl_frame, text="1.0"); lbl_b.grid(row=0, column=2, padx=5)
        sb.configure(command=lambda v: [setattr(self, 'brightness', v), lbl_b.configure(text=f"{v:.1f}")])
        
        ctk.CTkLabel(sl_frame, text="Contrast:").grid(row=1, column=0, padx=5)
        sc = ctk.CTkSlider(sl_frame, from_=0.2, to=2.0, number_of_steps=36)
        sc.set(1.0); sc.grid(row=1, column=1)
        lbl_c = ctk.CTkLabel(sl_frame, text="1.0"); lbl_c.grid(row=1, column=2, padx=5)
        sc.configure(command=lambda v: [setattr(self, 'contrast', v), lbl_c.configure(text=f"{v:.1f}")])

    def tool_face_blur(self):
        self.create_single_file_processor("Image", [("Images", "*.png;*.jpg;*.jpeg")], image_utils.blur_faces, "Blur Faces")

    def tool_add_img_text(self):
        frame = self.create_single_file_processor("Image", [("Images", "*.png;*.jpg;*.jpeg")], 
            lambda i, o: image_utils.add_text_to_image(i, o, self.img_text, self.txt_x, self.txt_y, self.font_sz, self.txt_col), "Add Text")
        
        self.img_text, self.txt_x, self.txt_y, self.font_sz, self.txt_col = "Sample Text", 10, 10, 24, "white"
        
        inp_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inp_frame.pack(before=frame.winfo_children()[-1], pady=10)
        
        ctk.CTkLabel(inp_frame, text="Text:").grid(row=0, column=0); et = ctk.CTkEntry(inp_frame, width=200); et.grid(row=0, column=1); et.insert(0, "Sample Text")
        ctk.CTkLabel(inp_frame, text="X:").grid(row=1, column=0); ex = ctk.CTkEntry(inp_frame, width=60); ex.grid(row=1, column=1, sticky="w"); ex.insert(0, "10")
        ctk.CTkLabel(inp_frame, text="Y:").grid(row=2, column=0); ey = ctk.CTkEntry(inp_frame, width=60); ey.grid(row=2, column=1, sticky="w"); ey.insert(0, "10")
        ctk.CTkLabel(inp_frame, text="Size:").grid(row=3, column=0); esz = ctk.CTkEntry(inp_frame, width=60); esz.grid(row=3, column=1, sticky="w"); esz.insert(0, "24")
        ctk.CTkLabel(inp_frame, text="Color:").grid(row=4, column=0); ecol = ctk.CTkEntry(inp_frame, width=100); ecol.grid(row=4, column=1, sticky="w"); ecol.insert(0, "white")
        
        def upd():
            self.img_text = et.get()
            self.txt_x, self.txt_y = int(ex.get()), int(ey.get())
            self.font_sz = int(esz.get())
            self.txt_col = ecol.get()
        
        ctk.CTkButton(inp_frame, text="Update", command=upd, width=60).grid(row=5, column=0, columnspan=2, pady=5)

    # --- NEW: Video Tools ---
    def tool_video_watermark(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        
        self.selected_file = None
        self.wm_img = None
        
        lbl_vid = ctk.CTkLabel(frame, text="No video selected")
        lbl_vid.pack(pady=5)
        
        def sel_vid():
            f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4;*.avi;*.mov;*.mkv")])
            if f: self.selected_file = f; lbl_vid.configure(text=os.path.basename(f))
        
        ctk.CTkButton(frame, text="Select Video", command=sel_vid).pack(pady=5)
        
        lbl_wm = ctk.CTkLabel(frame, text="No watermark image selected")
        lbl_wm.pack(pady=5)
        
        def sel_wm():
            f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
            if f: self.wm_img = f; lbl_wm.configure(text=os.path.basename(f))
        
        ctk.CTkButton(frame, text="Select Watermark Image", command=sel_wm).pack(pady=5)
        
        pos_cmb = ctk.CTkComboBox(frame, values=["bottom-right", "bottom-left", "top-right", "top-left"])
        pos_cmb.set("bottom-right"); pos_cmb.pack(pady=5)
        
        self.progress_wm = ctk.CTkProgressBar(frame, mode="indeterminate", width=300)
        
        def run():
            if not self.selected_file or not self.wm_img: return
            out = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
            if out:
                self.is_busy = True
                self.progress_wm.pack(pady=10); self.progress_wm.start()
                def task():
                    try:
                        video_utils.add_watermark(self.selected_file, out, self.wm_img, pos_cmb.get())
                        self.after(0, lambda: [messagebox.showinfo("Done", "Watermark added!"), self.progress_wm.stop(), self.progress_wm.pack_forget(), setattr(self, 'is_busy', False)])
                    except Exception as e:
                        self.after(0, lambda: [messagebox.showerror("Error", str(e)), self.progress_wm.stop(), self.progress_wm.pack_forget(), setattr(self, 'is_busy', False)])
                threading.Thread(target=task).start()
        
        ctk.CTkButton(frame, text="Add Watermark", command=run, fg_color="green").pack(pady=20)

    def tool_video_speed(self):
        frame = self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv")], 
            lambda i, o: video_utils.change_speed(i, o, self.speed_factor), "Change Speed")
        
        self.speed_factor = 1.0
        sl = ctk.CTkSlider(frame, from_=0.25, to=4.0, number_of_steps=75)
        sl.set(1.0); sl.pack(before=frame.winfo_children()[-1], pady=5)
        lbl = ctk.CTkLabel(frame, text="Speed: 1.0x"); lbl.pack(before=frame.winfo_children()[-1])
        sl.configure(command=lambda v: [setattr(self, 'speed_factor', v), lbl.configure(text=f"Speed: {v:.2f}x")])

    def tool_mute_video(self):
        self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv")], video_utils.mute_video, "Mute Video")

    def tool_add_music(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        
        self.selected_file = None
        self.music_file = None
        
        lbl_vid = ctk.CTkLabel(frame, text="No video selected"); lbl_vid.pack(pady=5)
        def sel_vid():
            f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4;*.avi;*.mov")])
            if f: self.selected_file = f; lbl_vid.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="Select Video", command=sel_vid).pack(pady=5)
        
        lbl_aud = ctk.CTkLabel(frame, text="No audio selected"); lbl_aud.pack(pady=5)
        def sel_aud():
            f = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3;*.wav;*.m4a")])
            if f: self.music_file = f; lbl_aud.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="Select Music", command=sel_aud).pack(pady=5)
        
        self.music_vol = 0.5
        sl = ctk.CTkSlider(frame, from_=0.0, to=1.0, number_of_steps=20); sl.set(0.5); sl.pack(pady=5)
        lbl_vol = ctk.CTkLabel(frame, text="Music Volume: 50%"); lbl_vol.pack()
        sl.configure(command=lambda v: [setattr(self, 'music_vol', v), lbl_vol.configure(text=f"Music Volume: {int(v*100)}%")])
        
        self.progress_music = ctk.CTkProgressBar(frame, mode="indeterminate", width=300)
        
        def run():
            if not self.selected_file or not self.music_file: return
            out = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
            if out:
                self.is_busy = True
                self.progress_music.pack(pady=10); self.progress_music.start()
                def task():
                    try:
                        video_utils.add_background_music(self.selected_file, out, self.music_file, self.music_vol)
                        self.after(0, lambda: [messagebox.showinfo("Done", "Music added!"), self.progress_music.stop(), self.progress_music.pack_forget(), setattr(self, 'is_busy', False)])
                    except Exception as e:
                        self.after(0, lambda: [messagebox.showerror("Error", str(e)), self.progress_music.stop(), self.progress_music.pack_forget(), setattr(self, 'is_busy', False)])
                threading.Thread(target=task).start()
        
        ctk.CTkButton(frame, text="Add Background Music", command=run, fg_color="green").pack(pady=20)

    # --- NEW: Audio Tools ---
    def tool_audio_volume(self):
        frame = self.create_single_file_processor("Audio", [("Audio", "*.mp3;*.wav;*.ogg;*.m4a")], 
            lambda i, o: audio_utils.adjust_volume(i, o, self.vol_factor), "Adjust Volume")
        
        self.vol_factor = 1.5
        sl = ctk.CTkSlider(frame, from_=0.1, to=3.0, number_of_steps=29); sl.set(1.5); sl.pack(before=frame.winfo_children()[-1], pady=5)
        lbl = ctk.CTkLabel(frame, text="Volume: 1.5x"); lbl.pack(before=frame.winfo_children()[-1])
        sl.configure(command=lambda v: [setattr(self, 'vol_factor', v), lbl.configure(text=f"Volume: {v:.1f}x")])

    def tool_audio_fade(self):
        frame = self.create_single_file_processor("Audio", [("Audio", "*.mp3;*.wav;*.ogg;*.m4a")], 
            lambda i, o: audio_utils.add_fade(i, o, self.fade_in, self.fade_out), "Apply Fade")
        
        self.fade_in, self.fade_out = 2.0, 2.0
        
        fade_frame = ctk.CTkFrame(frame, fg_color="transparent")
        fade_frame.pack(before=frame.winfo_children()[-1], pady=10)
        
        ctk.CTkLabel(fade_frame, text="Fade In (sec):").grid(row=0, column=0)
        e1 = ctk.CTkEntry(fade_frame, width=60); e1.grid(row=0, column=1, padx=5); e1.insert(0, "2")
        ctk.CTkLabel(fade_frame, text="Fade Out (sec):").grid(row=0, column=2)
        e2 = ctk.CTkEntry(fade_frame, width=60); e2.grid(row=0, column=3, padx=5); e2.insert(0, "2")
        
        def upd():
            self.fade_in = float(e1.get())
            self.fade_out = float(e2.get())
        ctk.CTkButton(fade_frame, text="Set", command=upd, width=50).grid(row=0, column=4, padx=5)

    # --- NEW: System Tools ---
    def tool_find_duplicates(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Find Duplicate Files", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        res_box = ctk.CTkTextbox(frame, height=300); res_box.pack(fill="both", expand=True, padx=10, pady=10)
        
        def run():
            d = filedialog.askdirectory()
            if d:
                res_box.delete("0.0", "end")
                res_box.insert("end", "Scanning...\n")
                def task():
                    dups = system_utils.find_duplicates(d)
                    result = ""
                    total = 0
                    for hash_val, files in dups.items():
                        total += len(files) - 1
                        result += f"\n--- Duplicate Group ---\n"
                        for f in files:
                            result += f"  {f}\n"
                    if not dups:
                        result = "No duplicates found!"
                    else:
                        result = f"Found {total} duplicate files:\n" + result
                    self.after(0, lambda: [res_box.delete("0.0", "end"), res_box.insert("end", result)])
                threading.Thread(target=task).start()
        
        ctk.CTkButton(frame, text="Select Folder to Scan", command=run, fg_color="orange").pack(pady=10)

    def tool_clean_empty(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Clean Empty Folders", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(frame, text="This will remove all empty subdirectories in the selected folder.").pack(pady=5)
        
        def run():
            d = filedialog.askdirectory()
            if d:
                count = system_utils.clean_empty_folders(d)
                messagebox.showinfo("Done", f"Removed {count} empty folders.")
        
        ctk.CTkButton(frame, text="Select Folder", command=run, fg_color="red").pack(pady=20)

    # --- NEW: QR Code Tools ---
    def tool_generate_qr(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Generate QR Code", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(frame, text="Enter text or URL:").pack(pady=5)
        txt = ctk.CTkEntry(frame, width=400); txt.pack(pady=10)
        
        def run():
            data = txt.get()
            if not data:
                messagebox.showerror("Error", "Enter text or URL")
                return
            out = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if out:
                try:
                    qr_utils.generate_qr(data, out)
                    messagebox.showinfo("Done", f"QR Code saved to {out}")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(frame, text="Generate QR Code", command=run, fg_color="green").pack(pady=20)

    def tool_read_qr(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Read QR Code", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.selected_file = None
        lbl = ctk.CTkLabel(frame, text="No image selected"); lbl.pack(pady=5)
        
        def sel():
            f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
            if f: self.selected_file = f; lbl.configure(text=os.path.basename(f))
        
        ctk.CTkButton(frame, text="Select QR Image", command=sel).pack(pady=5)
        
        res_box = ctk.CTkTextbox(frame, height=150); res_box.pack(fill="x", padx=10, pady=10)
        
        def run():
            if not self.selected_file: return
            try:
                results = qr_utils.read_qr(self.selected_file)
                res_box.delete("0.0", "end")
                if results:
                    for r in results:
                        res_box.insert("end", f"Type: {r['type']}\nData: {r['data']}\n\n")
                else:
                    res_box.insert("end", "No QR code found in image.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ctk.CTkButton(frame, text="Read QR Code", command=run, fg_color="blue").pack(pady=10)


if __name__ == "__main__":
    app = PDFStudioApp()
    app.mainloop()

