import customtkinter as ctk
import tkinter as tk
import os
from tkinter import filedialog, messagebox, simpledialog, Toplevel, colorchooser
import pdf_utils
import image_utils
import video_utils
import audio_utils
import word_utils
import excel_utils
import ppt_utils
import system_utils
import qr_utils
import text_utils
import passport_utils
import file_utils
import threading
from datetime import datetime
from PIL import Image

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
        self.tab_text = self.tab_view.add("Text Studio")
        self.tab_file = self.tab_view.add("File Studio")
        self.tab_passport = self.tab_view.add("📷 Passport Studio")
        
        self.main_frame = None # Dynamic reference

        # Passport Studio state
        self._pp_original_img = None      # PIL Image – original upload
        self._pp_nobg_img = None           # PIL Image – after BG removal
        self._pp_colored_img = None        # PIL Image – with solid BG applied
        self._pp_passport_img = None       # PIL Image – cropped to passport size
        self._pp_a4_img = None             # PIL Image – A4 sheet
        self._pp_bg_color = "#FFFFFF"
        self._pp_dpi = 300

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
            ],
            "Batch & Creative": [
                ("Batch Process", self.tool_batch_img),
                ("Color Palette", self.tool_color_palette),
                ("Collage Maker", self.tool_collage),
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
            ],
            "Create & Cloud": [
                ("Social Media Downloader", self.tool_media_download),
                ("Video Transcription", self.tool_media_transcribe),
                ("Video to GIF", self.tool_video_to_gif),
                ("Extract Thumbnail", self.tool_video_thumbnail),
                ("Reverse Video", self.tool_reverse_video),
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
            ],
            "Processing": [
                ("Noise Reduction", self.tool_noise_reduction),
                ("Normalize Audio", self.tool_normalize_audio),
            ],
            "Cloud & AI": [
                ("Audio Transcription", self.tool_media_transcribe),
                ("Download Audio", self.tool_media_download),
            ]
        }
        
        self.word_tools = {
            "Create & Edit": [
                 ("📝 Create Word Doc", self.tool_create_word),
                 ("✏️ Edit Word Doc", self.tool_edit_word),
                 ("🖼️ Insert Image", self.tool_word_insert_image),
            ],
            "Convert": [
                 ("Word to PDF", self.tool_word_to_pdf),
                 ("Word to Images", self.tool_word_to_images),
            ]
        }

        self.excel_tools = {
            "Create & Edit": [
                 ("📊 Create Spreadsheet", self.tool_create_excel),
                 ("✏️ Edit Spreadsheet", self.tool_edit_excel),
            ],
            "Convert": [
                 ("Excel to PDF", self.tool_excel_to_pdf),
                 ("Excel to CSV", self.tool_excel_to_csv),
            ]
        }

        self.ppt_tools = {
            "Create & Edit": [
                 ("🎞️ Create Presentation", self.tool_create_ppt),
                 ("✏️ Edit Presentation", self.tool_edit_ppt),
            ],
            "Convert": [
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
            ],
            "Encoding & Analysis": [
                ("Base64 Encode", self.tool_base64_encode),
                ("Base64 Decode", self.tool_base64_decode),
                ("Disk Usage", self.tool_disk_usage),
                ("Color Picker", self.tool_color_picker),
            ]
        }
        
        self.qr_tools = {
            "QR Code Tools": [
                ("Generate QR Code", self.tool_generate_qr),
                ("Read QR Code", self.tool_read_qr),
            ]
        }

        self.text_tools = {
            "Text Analysis": [
                ("Word Counter", self.tool_word_counter),
                ("Word Frequency", self.tool_word_frequency),
            ],
            "Text Transform": [
                ("Case Converter", self.tool_case_converter),
                ("Find & Replace", self.tool_find_replace),
                ("Remove Extra Spaces", self.tool_remove_spaces),
            ],
            "Generators": [
                ("Lorem Ipsum", self.tool_lorem_ipsum),
            ]
        }

        self.file_tools = {
            "Splitters": [
                ("Split CSV", self.tool_split_csv),
                ("Split Excel", self.tool_split_excel),
            ],
            "Converters": [
                ("XML to Excel", self.tool_xml_to_excel),
                ("Excel to XML", self.tool_excel_to_xml),
                ("CSV to Excel", self.tool_csv_to_excel),
                ("XML to CSV", self.tool_xml_to_csv),
                ("XML to JSON", self.tool_xml_to_json),
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
        self.text_main_frame = self.setup_tab(self.tab_text, self.text_tools, "Text Tools")
        self.file_main_frame = self.setup_tab(self.tab_file, self.file_tools, "File & Data Tools")
        self.setup_passport_tab()
        
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
        self.show_welcome(self.text_main_frame)
        self.show_welcome(self.file_main_frame)
        # Passport tab has its own built-in welcome UI

        # Status Bar
        self.status_frame = ctk.CTkFrame(self, height=25, corner_radius=0)
        self.status_frame.pack(fill="x", side="bottom")
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", font=ctk.CTkFont(size=11), anchor="w")
        self.status_label.pack(side="left", padx=10)
        
        about_btn = ctk.CTkButton(self.status_frame, text="ℹ About", width=70, height=22,
                                   font=ctk.CTkFont(size=11), fg_color="transparent",
                                   border_width=1, command=self.show_about)
        about_btn.pack(side="right", padx=10)

        # Creator Branding Tag
        creator_lbl = ctk.CTkLabel(self.status_frame, text="Made by Sidhartha with Vibe Coding @ IOP", 
                                   font=ctk.CTkFont(size=12, slant="italic", weight="bold"), text_color="#00ffcc")
        creator_lbl.pack(side="right", padx=20)

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

    def update_status(self, message):
        """Update the status bar with a message and timestamp."""
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.configure(text=f"{message}  •  {now}")

    def show_about(self):
        """Show about dialog."""
        about_win = Toplevel(self)
        about_win.title("About")
        about_win.geometry("400x280")
        about_win.resizable(False, False)
        about_win.transient(self)
        about_win.grab_set()
        
        f = ctk.CTkFrame(about_win)
        f.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(f, text="Desktop Utility", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(f, text="All-in-One Tool v2.0", font=ctk.CTkFont(size=14)).pack()
        ctk.CTkLabel(f, text="PDF • Image • Video • Audio • Word • Excel\nPPT • System • QR • Text", font=ctk.CTkFont(size=12)).pack(pady=10)
        ctk.CTkLabel(f, text="Built with CustomTkinter", font=ctk.CTkFont(size=11)).pack(pady=5)
        ctk.CTkButton(f, text="Close", command=about_win.destroy, width=80).pack(pady=10)

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

    # ============================================================
    # WORD STUDIO – Full Rich Text Editor
    # ============================================================

    def tool_create_word(self):
        """Full MS Word-like document creator with rich-text toolbar."""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        # ── Title bar ─────────────────────────────────────────────
        title_bar = ctk.CTkFrame(frame, fg_color="transparent", height=42)
        title_bar.pack(fill="x", padx=8, pady=(6, 2))
        title_bar.pack_propagate(False)
        ctk.CTkLabel(title_bar, text="📄", font=ctk.CTkFont(size=18)).pack(side="left", padx=(4, 2))
        doc_title = ctk.CTkEntry(title_bar, placeholder_text="Untitled Document",
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 fg_color="transparent", border_width=0, height=36)
        doc_title.pack(side="left", fill="x", expand=True)

        # ── Toolbar helpers ────────────────────────────────────────
        def _btn(parent, text, cmd, width=34, color=None):
            b = ctk.CTkButton(parent, text=text, command=cmd, width=width, height=28,
                              font=ctk.CTkFont(size=11),
                              fg_color=color or "transparent", hover_color="#374151",
                              text_color=("gray10", "gray90"), corner_radius=4)
            b.pack(side="left", padx=1, pady=3)
            return b

        def _sep(parent):
            ctk.CTkFrame(parent, width=1, height=22, fg_color="gray40").pack(
                side="left", padx=4, pady=7)

        # ── Toolbar row 1 : Font / Size / Format / Color ───────────
        tb1 = ctk.CTkFrame(frame, height=36, corner_radius=6)
        tb1.pack(fill="x", padx=8, pady=2); tb1.pack_propagate(False)

        font_families = ["Calibri", "Arial", "Times New Roman", "Courier New",
                         "Georgia", "Verdana", "Trebuchet MS", "Helvetica"]
        font_var = tk.StringVar(value="Calibri")
        font_cmb = ctk.CTkComboBox(tb1, values=font_families, variable=font_var,
                                   width=150, height=28, command=lambda _: _apply_font())
        font_cmb.pack(side="left", padx=(6, 2), pady=4)

        size_var = tk.StringVar(value="12")
        size_ent = ctk.CTkEntry(tb1, textvariable=size_var, width=48, height=28)
        size_ent.pack(side="left", padx=2, pady=4)
        size_ent.bind("<Return>", lambda e: _refresh_tags())

        _sep(tb1)
        _btn(tb1, "B",  lambda: _toggle("bold"))
        _btn(tb1, "I",  lambda: _toggle("italic"))
        _btn(tb1, "U",  lambda: _toggle("underline"))
        _btn(tb1, "S̶", lambda: _toggle("strike"))
        _sep(tb1)

        _tc = {"v": "#ffffff"}
        tc_sw = ctk.CTkFrame(tb1, width=18, height=18, fg_color=_tc["v"], corner_radius=3)
        tc_sw.pack(side="left", padx=2, pady=9)
        def _pick_fg():
            c = colorchooser.askcolor(color=_tc["v"], title="Text Color")
            if c and c[1]:
                _tc["v"] = c[1]; tc_sw.configure(fg_color=c[1]); _apply_color(c[1], "fg_")
        _btn(tb1, "A🎨", _pick_fg, width=44)

        _hl = {"v": "#ffff00"}
        hl_sw = ctk.CTkFrame(tb1, width=18, height=18, fg_color=_hl["v"], corner_radius=3)
        hl_sw.pack(side="left", padx=2, pady=9)
        def _pick_hl():
            c = colorchooser.askcolor(color=_hl["v"], title="Highlight Color")
            if c and c[1]:
                _hl["v"] = c[1]; hl_sw.configure(fg_color=c[1]); _apply_color(c[1], "bg_")
        _btn(tb1, "🖊HL", _pick_hl, width=44)

        _sep(tb1)
        _btn(tb1, "↶", lambda: editor.edit_undo(), width=30)
        _btn(tb1, "↷", lambda: editor.edit_redo(), width=30)
        _btn(tb1, "✕", lambda: _clear_fmt(), width=30)

        # ── Toolbar row 2 : Headings / Align / Lists / Insert ─────
        tb2 = ctk.CTkFrame(frame, height=36, corner_radius=6)
        tb2.pack(fill="x", padx=8, pady=(0, 2)); tb2.pack_propagate(False)

        for label, tag in [("H1","h1"),("H2","h2"),("H3","h3"),("¶","clr_h")]:
            _btn(tb2, label, lambda t=tag: _heading(t), width=34)
        _sep(tb2)
        for label, jtag in [("≡L","left"),("≡C","center"),("≡R","right"),("≡J","justify")]:
            _btn(tb2, label, lambda j=jtag: _align(j), width=36)
        _sep(tb2)
        _btn(tb2, "•≡",  _insert_bullet, width=38)
        _btn(tb2, "1.≡", _insert_num,    width=38)
        _sep(tb2)
        _btn(tb2, "⊞ Table",  _insert_table_dlg, width=84)
        _btn(tb2, "🖼 Image",  _insert_img_inline, width=84)
        _btn(tb2, "🔍 Find",   _find_replace_dlg, width=80)

        # ── Editor area ────────────────────────────────────────────
        edit_wrap = tk.Frame(frame, bg="#1e1e2e")
        edit_wrap.pack(fill="both", expand=True, padx=8, pady=4)

        editor = tk.Text(
            edit_wrap, wrap="word", undo=True, maxundo=80,
            font=("Calibri", 12),
            bg="#1e1e2e", fg="#cdd6f4",
            insertbackground="#cba6f7",
            selectbackground="#313244", selectforeground="#cdd6f4",
            padx=60, pady=30, relief="flat", bd=0,
            spacing1=3, spacing2=2, spacing3=3,
        )
        vsb = tk.Scrollbar(edit_wrap, command=editor.yview, bg="#1e1e2e")
        editor.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        editor.pack(side="left", fill="both", expand=True)
        editor.focus_set()

        # Tags
        def _refresh_tags(*_):
            fn = font_var.get() or "Calibri"
            try: sz = int(size_var.get())
            except ValueError: sz = 12
            editor.tag_configure("bold",       font=(fn, sz, "bold"))
            editor.tag_configure("italic",     font=(fn, sz, "italic"))
            editor.tag_configure("underline",  font=(fn, sz), underline=True)
            editor.tag_configure("strike",     font=(fn, sz), overstrike=True)
            editor.tag_configure("normal_sz",  font=(fn, sz))
            editor.tag_configure("h1",  font=(fn, 28, "bold"))
            editor.tag_configure("h2",  font=(fn, 20, "bold"))
            editor.tag_configure("h3",  font=(fn, 15, "bold"))
            editor.tag_configure("bullet",  lmargin1=22, lmargin2=36)
            editor.tag_configure("numbered",lmargin1=22, lmargin2=40)
        _refresh_tags()

        def _apply_font(*_):
            _refresh_tags()

        def _sel():
            try:
                return editor.index("sel.first"), editor.index("sel.last")
            except tk.TclError:
                ln = editor.index("insert").split(".")[0]
                return f"{ln}.0", f"{ln}.end"

        def _toggle(tag):
            s, e = _sel()
            if tag in editor.tag_names(s):
                editor.tag_remove(tag, s, e)
            else:
                editor.tag_add(tag, s, e)

        def _heading(h_tag):
            s, e = _sel()
            for t in ("h1","h2","h3"): editor.tag_remove(t, s, e)
            if h_tag != "clr_h": editor.tag_add(h_tag, s, e)

        def _align(justify):
            s, e = _sel()
            # apply justify via paragraph tag
            tag = f"align_{justify}"
            for at in ("align_left","align_center","align_right","align_justify"):
                editor.tag_remove(at, s, e)
            editor.tag_configure(tag, justify=justify if justify != "justify" else "left")
            editor.tag_add(tag, s, e)

        def _apply_color(color, prefix):
            tname = f"{prefix}{color.replace('#','')}"
            editor.tag_configure(tname, **({
                "fg_": {"foreground": color},
                "bg_": {"background": color},
            }[prefix]))
            s, e = _sel()
            for t in editor.tag_names():
                if t.startswith(prefix): editor.tag_remove(t, s, e)
            editor.tag_add(tname, s, e)

        def _clear_fmt():
            s, e = _sel()
            for t in list(editor.tag_names()):
                if t not in ("sel",): editor.tag_remove(t, s, e)

        _num_ctr = [0]
        def _insert_bullet():
            ln = editor.index("insert").split(".")[0]
            editor.insert(f"{ln}.0", "• ")
            editor.tag_add("bullet", f"{ln}.0", f"{ln}.end")

        def _insert_num():
            _num_ctr[0] += 1
            ln = editor.index("insert").split(".")[0]
            editor.insert(f"{ln}.0", f"{_num_ctr[0]}. ")
            editor.tag_add("numbered", f"{ln}.0", f"{ln}.end")

        def _insert_table_dlg():
            win = Toplevel(self); win.title("Insert Table")
            win.geometry("260x160"); win.resizable(False, False)
            win.transient(self); win.grab_set()
            f = ctk.CTkFrame(win); f.pack(fill="both", expand=True, padx=14, pady=14)
            ctk.CTkLabel(f, text="Insert Table", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(0,8))
            rf = ctk.CTkFrame(f, fg_color="transparent"); rf.pack(fill="x")
            ctk.CTkLabel(rf, text="Rows:").pack(side="left")
            re_ = ctk.CTkEntry(rf, width=55); re_.insert(0,"3"); re_.pack(side="left", padx=4)
            ctk.CTkLabel(rf, text="Cols:").pack(side="left", padx=(8,0))
            ce_ = ctk.CTkEntry(rf, width=55); ce_.insert(0,"3"); ce_.pack(side="left", padx=4)
            def do():
                try: r,c = int(re_.get()), int(ce_.get())
                except: r,c = 3,3
                cw = 12
                t  = "┌" + ("─"*cw+"┬")*(c-1) + "─"*cw + "┐\n"
                mr = "│" + ("·"*cw+"│")*c + "\n"
                sr = "├" + ("─"*cw+"┼")*(c-1) + "─"*cw + "┤\n"
                bt = "└" + ("─"*cw+"┴")*(c-1) + "─"*cw + "┘\n"
                tbl = t
                for i in range(r):
                    tbl += mr
                    if i<r-1: tbl += sr
                tbl += bt
                editor.insert("insert", "\n"+tbl)
                win.destroy()
            ctk.CTkButton(f, text="Insert", command=do, fg_color="green").pack(pady=8)

        _word_images = {}
        def _insert_img_inline():
            f = filedialog.askopenfilename(
                filetypes=[("Images","*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
            if f:
                bn = os.path.basename(f)
                _word_images[bn] = f
                editor.insert("insert", f"\n[🖼 IMAGE: {bn}]\n")

        def _find_replace_dlg():
            win = Toplevel(self); win.title("Find & Replace")
            win.geometry("400x185"); win.transient(self); win.grab_set()
            f = ctk.CTkFrame(win); f.pack(fill="both", expand=True, padx=14, pady=14)
            ctk.CTkLabel(f, text="Find:").grid(row=0, column=0, sticky="w", pady=4)
            fe = ctk.CTkEntry(f, width=270); fe.grid(row=0, column=1, padx=6, pady=4)
            ctk.CTkLabel(f, text="Replace:").grid(row=1, column=0, sticky="w", pady=4)
            re_ = ctk.CTkEntry(f, width=270); re_.grid(row=1, column=1, padx=6, pady=4)
            rl = ctk.CTkLabel(f, text=""); rl.grid(row=2, column=0, columnspan=2)
            def find_all():
                q = fe.get()
                if not q: return
                editor.tag_remove("found","1.0","end")
                editor.tag_configure("found", background="#fbbf24", foreground="black")
                idx="1.0"; n=0
                while True:
                    idx = editor.search(q, idx, stopindex="end")
                    if not idx: break
                    end=f"{idx}+{len(q)}c"
                    editor.tag_add("found", idx, end); idx=end; n+=1
                rl.configure(text=f"Found {n} match(es)")
            def rep_all():
                q=fe.get(); r=re_.get()
                if not q: return
                txt=editor.get("1.0","end-1c").replace(q,r)
                editor.delete("1.0","end"); editor.insert("1.0",txt)
                rl.configure(text="Replaced all")
            bf = ctk.CTkFrame(f, fg_color="transparent"); bf.grid(row=3,column=0,columnspan=2,pady=8)
            ctk.CTkButton(bf, text="Find All",    command=find_all, width=100).pack(side="left", padx=3)
            ctk.CTkButton(bf, text="Replace All", command=rep_all, width=110, fg_color="#2563eb").pack(side="left", padx=3)
            ctk.CTkButton(bf, text="Close", command=win.destroy, width=80, fg_color="gray50").pack(side="left", padx=3)

        # ── Status bar ─────────────────────────────────────────────
        sb = ctk.CTkFrame(frame, height=22, corner_radius=0)
        sb.pack(fill="x", padx=8, pady=(0,4)); sb.pack_propagate(False)
        wc_lbl = ctk.CTkLabel(sb, text="Words: 0  |  Chars: 0",
                               font=ctk.CTkFont(size=11), text_color="gray")
        wc_lbl.pack(side="left", padx=10)
        pos_lbl = ctk.CTkLabel(sb, text="Ln 1  Col 1",
                                font=ctk.CTkFont(size=11), text_color="gray")
        pos_lbl.pack(side="right", padx=10)

        def _upd_sb(*_):
            c = editor.get("1.0","end-1c")
            wc_lbl.configure(text=f"Words: {len(c.split()) if c.strip() else 0}  |  Chars: {len(c)}")
            ln, col = editor.index("insert").split(".")
            pos_lbl.configure(text=f"Ln {ln}  Col {int(col)+1}")
        editor.bind("<KeyRelease>", _upd_sb)
        editor.bind("<ButtonRelease>", _upd_sb)

        # ── Save / Open helpers ────────────────────────────────────
        def _extract():
            lines = editor.get("1.0","end-1c").split("\n")
            out = []
            for li, line in enumerate(lines):
                lnum = li+1
                pos  = f"{lnum}.0"
                tags = set(editor.tag_names(pos))
                style = ("Heading 1" if "h1" in tags else
                         "Heading 2" if "h2" in tags else
                         "Heading 3" if "h3" in tags else "Normal")
                align = ("center" if "align_center" in tags else
                         "right"  if "align_right"  in tags else "left")
                color = next((("#"+t[3:]) for t in tags if t.startswith("fg_")), "")
                try: sz = int(size_var.get())
                except: sz = 12
                out.append({"text":line,"style":style,"align":align,"color":color,
                            "bold":"bold" in tags,"italic":"italic" in tags,
                            "underline":"underline" in tags,"size":sz})
            return out

        def _save_docx():
            out = filedialog.asksaveasfilename(
                defaultextension=".docx", filetypes=[("Word Document","*.docx")],
                initialfile=(doc_title.get() or "Untitled")+".docx")
            if not out: return
            try:
                word_utils.create_word_doc(out, title=doc_title.get(),
                    paragraphs=_extract(), font_name=font_var.get(),
                    font_size=int(size_var.get()) if size_var.get().isdigit() else 12)
                messagebox.showinfo("Saved", f"Saved:\n{out}")
                self.update_status("Word document saved.")
            except Exception as e: messagebox.showerror("Error", str(e))

        def _open_docx():
            f = filedialog.askopenfilename(filetypes=[("Word Documents","*.docx")])
            if not f: return
            try:
                paras = word_utils.read_word_doc(f)
                editor.delete("1.0","end")
                for p in paras: editor.insert("end", p["text"]+"\n")
                doc_title.delete(0,"end")
                doc_title.insert(0, os.path.splitext(os.path.basename(f))[0])
                self.update_status(f"Opened: {os.path.basename(f)}")
            except Exception as e: messagebox.showerror("Error", str(e))

        def _export_pdf():
            out = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
            if not out: return
            import tempfile
            tmp = tempfile.mktemp(suffix=".docx")
            try:
                word_utils.create_word_doc(tmp, title=doc_title.get(), paragraphs=_extract())
                word_utils.word_to_pdf(tmp, out)
                messagebox.showinfo("Exported", f"PDF saved:\n{out}")
            except Exception as e: messagebox.showerror("Error", str(e))
            finally:
                try: os.unlink(tmp)
                except: pass

        def _print_preview():
            txt = editor.get("1.0","end-1c")
            win = Toplevel(self); win.title("Print Preview")
            win.geometry("700x600"); win.transient(self)
            f = ctk.CTkFrame(win); f.pack(fill="both",expand=True, padx=10, pady=10)
            ctk.CTkLabel(f, text="Print Preview", font=ctk.CTkFont(size=14,weight="bold")).pack(pady=5)
            tb = tk.Text(f, wrap="word", font=("Calibri",12), padx=40, pady=40,
                         bg="white", fg="black", relief="flat")
            tb.insert("1.0", txt); tb.configure(state="disabled")
            tb.pack(fill="both", expand=True)
            ctk.CTkButton(f, text="Close", command=win.destroy).pack(pady=5)

        def _word_count_full():
            txt = editor.get("1.0","end-1c")
            words = len(txt.split()) if txt.strip() else 0
            chars = len(txt)
            chars_no_sp = len(txt.replace(" ",""))
            paras = len([l for l in txt.split("\n") if l.strip()])
            messagebox.showinfo("Word Count",
                f"Words: {words}\nCharacters: {chars}\n"
                f"Characters (no spaces): {chars_no_sp}\nParagraphs: {paras}")

        # ── Action bar ─────────────────────────────────────────────
        ab = ctk.CTkFrame(frame, fg_color="transparent")
        ab.pack(fill="x", padx=8, pady=(0,6))
        _btn(ab, "📂 Open",      _open_docx,     width=100)
        _btn(ab, "💾 Save .docx",_save_docx,     width=120, color="green")
        _btn(ab, "📄 Export PDF", _export_pdf,   width=120, color="#7c3aed")
        _btn(ab, "🖨 Preview",   _print_preview, width=100)
        _btn(ab, "📊 Word Count", _word_count_full, width=120)

    def tool_edit_word(self):
        """Open & edit an existing .docx using the same rich editor."""
        # Reuse create word with pre-loaded file
        self.tool_create_word()
        # Trigger open
        self.after(100, lambda: None)  # UI is ready; user clicks "Open" in the editor

    def tool_word_insert_image(self):
        """Insert an image into an existing Word document."""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self._wimg_doc = None; self._wimg_img = None
        dl = ctk.CTkLabel(frame, text="No document selected"); dl.pack(pady=8)
        def pd():
            f = filedialog.askopenfilename(filetypes=[("Word","*.docx")])
            if f: self._wimg_doc=f; dl.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="📄 Select Word Document", command=pd).pack(pady=4)
        il = ctk.CTkLabel(frame, text="No image selected"); il.pack(pady=8)
        def pi():
            f = filedialog.askopenfilename(filetypes=[("Images","*.png;*.jpg;*.jpeg;*.bmp")])
            if f: self._wimg_img=f; il.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="🖼 Select Image", command=pi).pack(pady=4)
        ctk.CTkLabel(frame, text="Image Width (cm):").pack(pady=(10,2))
        we = ctk.CTkEntry(frame); we.insert(0,"10"); we.pack(pady=4)
        def run():
            if not self._wimg_doc or not self._wimg_img:
                messagebox.showwarning("Missing","Select both files."); return
            out = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word","*.docx")])
            if not out: return
            try:
                word_utils.insert_image_word(self._wimg_doc, out, self._wimg_img,
                                             width_cm=float(we.get() or 10))
                messagebox.showinfo("Done", f"Saved:\n{out}")
            except Exception as e: messagebox.showerror("Error", str(e))
        ctk.CTkButton(frame, text="✅ Insert & Save", command=run, fg_color="green").pack(pady=20)

    def tool_word_to_images(self):
        frame = ctk.CTkFrame(self.main_frame); frame.pack(fill="both", expand=True)
        self.selected_file = None
        lbl = ctk.CTkLabel(frame, text="No file selected"); lbl.pack(pady=10)
        def sel():
            f = filedialog.askopenfilename(filetypes=[("Word","*.docx")])
            if f: self.selected_file=f; lbl.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="Select Word File", command=sel).pack(pady=10)
        def run():
            if not self.selected_file: return
            d = filedialog.askdirectory()
            if not d: return
            def task():
                try:
                    word_utils.word_to_images(self.selected_file, d)
                    self.after(0, lambda: messagebox.showinfo("Done","Images extracted!"))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error",str(e)))
            threading.Thread(target=task).start()
        ctk.CTkButton(frame, text="Convert to Images", command=run, fg_color="purple").pack(pady=20)


        """Rich Word document creator."""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        # ── Left panel: options ──
        left = ctk.CTkFrame(frame, width=280)
        left.pack(side="left", fill="y", padx=(0, 5), pady=5)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Document Settings", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5), padx=10, anchor="w")

        ctk.CTkLabel(left, text="Title:", anchor="w").pack(padx=10, anchor="w")
        title_ent = ctk.CTkEntry(left, placeholder_text="Document Title")
        title_ent.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(left, text="Font Name:", anchor="w").pack(padx=10, anchor="w")
        font_ent = ctk.CTkEntry(left, placeholder_text="Calibri")
        font_ent.insert(0, "Calibri")
        font_ent.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(left, text="Font Size (pt):", anchor="w").pack(padx=10, anchor="w")
        size_ent = ctk.CTkEntry(left, placeholder_text="12")
        size_ent.insert(0, "12")
        size_ent.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(left, text="Text Style:", anchor="w").pack(padx=10, anchor="w")
        self._word_bold = ctk.BooleanVar(value=False)
        self._word_italic = ctk.BooleanVar(value=False)
        self._word_underline = ctk.BooleanVar(value=False)
        chk_frame = ctk.CTkFrame(left, fg_color="transparent")
        chk_frame.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkCheckBox(chk_frame, text="Bold", variable=self._word_bold).pack(side="left", padx=(0, 5))
        ctk.CTkCheckBox(chk_frame, text="Italic", variable=self._word_italic).pack(side="left", padx=(0, 5))
        ctk.CTkCheckBox(chk_frame, text="Underline", variable=self._word_underline).pack(side="left")

        ctk.CTkLabel(left, text="Alignment:", anchor="w").pack(padx=10, anchor="w")
        align_cmb = ctk.CTkComboBox(left, values=["left", "center", "right", "justify"])
        align_cmb.set("left")
        align_cmb.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(left, text="Paragraph Style:", anchor="w").pack(padx=10, anchor="w")
        para_style_cmb = ctk.CTkComboBox(left, values=["Normal", "Heading 1", "Heading 2", "Heading 3"])
        para_style_cmb.set("Normal")
        para_style_cmb.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(left, text="Text Color (hex):", anchor="w").pack(padx=10, anchor="w")
        color_ent = ctk.CTkEntry(left, placeholder_text="#000000")
        color_ent.pack(fill="x", padx=10, pady=(0, 10))

        # ── Right panel: editor ──
        right = ctk.CTkFrame(frame)
        right.pack(side="left", fill="both", expand=True, pady=5)

        ctk.CTkLabel(right, text="Type your content below (each paragraph on a new line):", anchor="w").pack(padx=10, pady=(10, 3), anchor="w")
        txt_editor = ctk.CTkTextbox(right, font=ctk.CTkFont(family="Consolas", size=12))
        txt_editor.pack(fill="both", expand=True, padx=10, pady=5)

        # Paragraph list (internal state)
        self._word_paragraphs = []

        def add_paragraph():
            text = txt_editor.get("0.0", "end").strip()
            if not text:
                messagebox.showwarning("Empty", "Please enter some text first.")
                return
            para = {
                'text': text,
                'bold': self._word_bold.get(),
                'italic': self._word_italic.get(),
                'underline': self._word_underline.get(),
                'align': align_cmb.get(),
                'style': para_style_cmb.get(),
                'color': color_ent.get().strip(),
                'size': int(size_ent.get()) if size_ent.get().isdigit() else 12,
            }
            self._word_paragraphs.append(para)
            preview_box.configure(state="normal")
            preview_box.insert("end", f"[{para['style']}] {text[:80]}...\n" if len(text) > 80 else f"[{para['style']}] {text}\n")
            preview_box.configure(state="disabled")
            txt_editor.delete("0.0", "end")

        def clear_all():
            self._word_paragraphs.clear()
            preview_box.configure(state="normal")
            preview_box.delete("0.0", "end")
            preview_box.configure(state="disabled")

        def save_doc():
            if not self._word_paragraphs and not title_ent.get():
                messagebox.showwarning("Empty", "Add at least a title or a paragraph.")
                return
            out = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Document", "*.docx")])
            if not out:
                return
            try:
                fn = font_ent.get() or "Calibri"
                sz = int(size_ent.get()) if size_ent.get().isdigit() else 12
                word_utils.create_word_doc(out, title=title_ent.get(), paragraphs=self._word_paragraphs, font_name=fn, font_size=sz)
                messagebox.showinfo("Saved", f"Document saved:\n{out}")
                self.update_status("Word document saved.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_row, text="➕ Add Paragraph", command=add_paragraph, fg_color="#2563eb").pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_row, text="🗑️ Clear All", command=clear_all, fg_color="#dc2626").pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_row, text="💾 Save as .docx", command=save_doc, fg_color="green").pack(side="left")

        ctk.CTkLabel(right, text="Paragraphs added:", anchor="w").pack(padx=10, anchor="w")
        preview_box = ctk.CTkTextbox(right, height=110, font=ctk.CTkFont(family="Consolas", size=11))
        preview_box.pack(fill="x", padx=10, pady=(0, 5))
        preview_box.configure(state="disabled")

    def tool_edit_word(self):
        """Open and edit an existing .docx file."""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        self._edit_word_paras = []
        self._edit_word_path = None

        top_bar = ctk.CTkFrame(frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=8)

        file_lbl = ctk.CTkLabel(top_bar, text="No file selected", anchor="w")
        file_lbl.pack(side="left", padx=(0, 10))

        def open_file():
            f = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
            if not f:
                return
            try:
                paras = word_utils.read_word_doc(f)
                self._edit_word_paras = paras
                self._edit_word_path = f
                file_lbl.configure(text=os.path.basename(f))
                # Populate editor
                editor.configure(state="normal")
                editor.delete("0.0", "end")
                for p in paras:
                    editor.insert("end", p['text'] + "\n")
                self.update_status(f"Loaded: {os.path.basename(f)}")
                para_count_lbl.configure(text=f"{len(paras)} paragraphs loaded")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(top_bar, text="📂 Open .docx", command=open_file).pack(side="left", padx=(0, 8))

        para_count_lbl = ctk.CTkLabel(top_bar, text="", text_color="#64748b")
        para_count_lbl.pack(side="left")

        ctk.CTkLabel(frame, text="Edit content below. Each line = one paragraph. Bold/Italic from original file is preserved in metadata.", anchor="w",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(padx=10, anchor="w")

        editor = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=12))
        editor.pack(fill="both", expand=True, padx=10, pady=5)

        def save_edited():
            if self._edit_word_path is None:
                messagebox.showwarning("No File", "Open a .docx file first.")
                return
            out = filedialog.asksaveasfilename(
                defaultextension=".docx", filetypes=[("Word Document", "*.docx")],
                initialfile=os.path.basename(self._edit_word_path))
            if not out:
                return
            try:
                # Build paragraph list from edited text, preserving original style metadata
                lines = editor.get("0.0", "end").splitlines()
                new_paras = []
                for i, line in enumerate(lines):
                    orig = self._edit_word_paras[i] if i < len(self._edit_word_paras) else {}
                    new_paras.append({
                        'text': line,
                        'style': orig.get('style', 'Normal'),
                        'bold': orig.get('bold', False),
                        'italic': orig.get('italic', False),
                        'underline': orig.get('underline', False),
                    })
                word_utils.save_word_doc(self._edit_word_path, out, new_paras)
                messagebox.showinfo("Saved", f"Saved to:\n{out}")
                self.update_status("Word document updated.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(btn_row, text="💾 Save Changes", command=save_edited, fg_color="green").pack(side="left")

    def tool_word_insert_image(self):
        """Insert an image into an existing Word document."""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        self._wimg_doc = None
        self._wimg_img = None

        doc_lbl = ctk.CTkLabel(frame, text="No document selected")
        doc_lbl.pack(pady=8)
        def pick_doc():
            f = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
            if f:
                self._wimg_doc = f
                doc_lbl.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="📄 Select Word Document", command=pick_doc).pack(pady=4)

        img_lbl = ctk.CTkLabel(frame, text="No image selected")
        img_lbl.pack(pady=8)
        def pick_img():
            f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
            if f:
                self._wimg_img = f
                img_lbl.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="🖼️ Select Image", command=pick_img).pack(pady=4)

        ctk.CTkLabel(frame, text="Image Width (cm):").pack(pady=(10, 2))
        width_ent = ctk.CTkEntry(frame, placeholder_text="10")
        width_ent.insert(0, "10")
        width_ent.pack(pady=4)

        def run():
            if not self._wimg_doc or not self._wimg_img:
                messagebox.showwarning("Missing", "Select both a document and an image.")
                return
            out = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Document", "*.docx")])
            if not out:
                return
            try:
                w = float(width_ent.get()) if width_ent.get() else 10.0
                word_utils.insert_image_word(self._wimg_doc, out, self._wimg_img, width_cm=w)
                messagebox.showinfo("Done", f"Image inserted and saved:\n{out}")
                self.update_status("Image inserted into Word document.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(frame, text="✅ Insert Image & Save", command=run, fg_color="green").pack(pady=20)

    def tool_word_to_images(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self.selected_file = None
        lbl = ctk.CTkLabel(frame, text="No file selected"); lbl.pack(pady=10)
        def select():
            f = filedialog.askopenfilename(filetypes=[("Word", "*.docx")])
            if f: self.selected_file = f; lbl.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="Select Word File", command=select).pack(pady=10)
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
        ctk.CTkButton(frame, text="Convert to Images", command=run, fg_color="purple").pack(pady=20)

    # ============================================================
    # EXCEL STUDIO – Full Spreadsheet Editor
    # ============================================================

    def tool_create_excel(self):
        """Full MS Excel-like spreadsheet editor with formulas and formatting."""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        self._xl_file_path = None
        self._xl_sheets = {"Sheet1": {}}  # {"Sheet1": {(r,c): {"v":"val", "f":"formula", "b":False, "i":False, "fg":None, "bg":None}}}
        self._xl_curr_sheet = ctk.StringVar(value="Sheet1")
        self._xl_sel_r = ctk.IntVar(value=-1)
        self._xl_sel_c = ctk.IntVar(value=-1)
        
        self._rows = 100
        self._cols = 26
        self._col_widths = {c: 80 for c in range(self._cols)}
        
        # ── Toolbar ───────────────────────────────────────────────
        tb = ctk.CTkFrame(frame, height=42, corner_radius=0)
        tb.pack(fill="x"); tb.pack_propagate(False)

        def _btn(p, t, c, w=34):
            b=ctk.CTkButton(p, text=t, command=c, width=w, height=28,
                            fg_color="transparent", hover_color="#374151",
                            text_color=("gray10", "gray90"), corner_radius=4)
            b.pack(side="left", padx=1, pady=7)
            return b
            
        def _sep(p):
            ctk.CTkFrame(p, width=1, height=22, fg_color="gray40").pack(side="left", padx=4, pady=10)

        # File Ops
        _btn(tb, "📂 Open",  self._xl_open, w=60)
        _btn(tb, "💾 Save",  self._xl_save, w=60)
        _btn(tb, "💾 Save As", self._xl_save_as, w=70)
        _sep(tb)
        
        # Formatting
        self._xl_btn_b = _btn(tb, "B", lambda: self._xl_fmt_toggle('b'))
        self._xl_btn_i = _btn(tb, "I", lambda: self._xl_fmt_toggle('i'))
        
        _tc = {"v": "#ffffff"}
        tc_sw = ctk.CTkFrame(tb, width=16, height=16, fg_color=_tc["v"], corner_radius=2)
        tc_sw.pack(side="left", padx=2, pady=13)
        def _pick_fc():
            c = colorchooser.askcolor(color=_tc["v"], title="Font Color")
            if c and c[1]:
                _tc["v"] = c[1]; tc_sw.configure(fg_color=c[1]); self._xl_fmt_color('fg', c[1])
        _btn(tb, "A🎨", _pick_fc, w=40)
        
        _bgc = {"v": "#2b2b2b"}
        bgc_sw = ctk.CTkFrame(tb, width=16, height=16, fg_color=_bgc["v"], corner_radius=2)
        bgc_sw.pack(side="left", padx=2, pady=13)
        def _pick_bgc():
            c = colorchooser.askcolor(color=_bgc["v"], title="Fill Color")
            if c and c[1]:
                _bgc["v"] = c[1]; bgc_sw.configure(fg_color=c[1]); self._xl_fmt_color('bg', c[1])
        _btn(tb, "🪣", _pick_bgc, w=40)
        
        _sep(tb)
        _btn(tb, "Clear Fmt", self._xl_fmt_clear, w=75)

        # ── Formula Bar ───────────────────────────────────────────
        fb = ctk.CTkFrame(frame, height=36, corner_radius=0, fg_color="transparent")
        fb.pack(fill="x", pady=2); fb.pack_propagate(False)
        
        self._xl_sel_lbl = ctk.CTkLabel(fb, text="", width=40, font=ctk.CTkFont(weight="bold"))
        self._xl_sel_lbl.pack(side="left", padx=8)
        ctk.CTkLabel(fb, text="fx", font=ctk.CTkFont(family="Times New Roman", slant="italic", size=14)).pack(side="left", padx=(0,4))
        
        self._xl_fbar_var = tk.StringVar()
        fbar = ctk.CTkEntry(fb, textvariable=self._xl_fbar_var, font=ctk.CTkFont(family="Consolas", size=13))
        fbar.pack(side="left", fill="x", expand=True, padx=(0,8))
        fbar.bind("<Return>", lambda e: self._xl_fbar_submit())
        fbar.bind("<FocusOut>", lambda e: self._xl_fbar_submit())
        
        # ── Grid Area ──────────────────────────────────────────────
        gw = tk.Frame(frame, bg="#1e1e2e")
        gw.pack(fill="both", expand=True, padx=4, pady=(0,4))
        
        self._xl_canvas = tk.Canvas(gw, bg="#1e1e2e", highlightthickness=0)
        hsb = ctk.CTkScrollbar(gw, orientation="horizontal", command=self._xl_canvas.xview)
        vsb = ctk.CTkScrollbar(gw, orientation="vertical", command=self._xl_canvas.yview)
        self._xl_canvas.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._xl_canvas.pack(side="left", fill="both", expand=True)
        
        self._xl_grid_frame = tk.Frame(self._xl_canvas, bg="#313244")
        self._cw_win = self._xl_canvas.create_window((0,0), window=self._xl_grid_frame, anchor="nw")
        
        self._xl_entries = {}  # {(r,c): tk.Entry}
        self._xl_build_grid()
        
        self._xl_grid_frame.update_idletasks()
        self._xl_canvas.configure(scrollregion=self._xl_canvas.bbox("all"))

        # ── Bottom tabs ────────────────────────────────────────────
        bt = ctk.CTkFrame(frame, height=32, corner_radius=0, fg_color="transparent")
        bt.pack(fill="x"); bt.pack_propagate(False)
        
        self._xl_tab_frame = ctk.CTkFrame(bt, fg_color="transparent")
        self._xl_tab_frame.pack(side="left", fill="y")
        self._xl_refresh_tabs()
        
        _btn(bt, "➕", self._xl_add_sheet, w=30)
    
    # Grid Builders & Handlers
    def _xl_col_name(self, n):
        res = ""
        while n >= 0:
            res = chr(n % 26 + 65) + res
            n = n // 26 - 1
        return res

    def _xl_build_grid(self):
        for w in self._xl_grid_frame.winfo_children(): w.destroy()
        self._xl_entries.clear()
        
        # Corner
        tk.Label(self._xl_grid_frame, text="", bg="#45475a", relief="raised", bd=1).grid(row=0, column=0, sticky="nsew")
        
        # Headers
        for c in range(self._cols):
            l = tk.Label(self._xl_grid_frame, text=self._xl_col_name(c), bg="#45475a", fg="#cdd6f4", relief="raised", bd=1, width=int(self._col_widths[c]/8))
            l.grid(row=0, column=c+1, sticky="nsew")
        for r in range(self._rows):
            tk.Label(self._xl_grid_frame, text=str(r+1), bg="#45475a", fg="#cdd6f4", relief="raised", bd=1, width=4).grid(row=r+1, column=0, sticky="nsew")
            
        # Cells
        vcmd = (self.register(self._xl_validate), '%P', '%W')
        for r in range(self._rows):
            for c in range(self._cols):
                sv = tk.StringVar()
                e = tk.Entry(self._xl_grid_frame, textvariable=sv, bg="#1e1e2e", fg="#cdd6f4", 
                             insertbackground="#cdd6f4", relief="groove", bd=1,
                             font=("Calibri", 12), validate="focusout", validatecommand=vcmd)
                e.grid(row=r+1, column=c+1, sticky="nsew", padx=0, pady=0)
                e.bind("<Button-1>", lambda evt, rr=r, cc=c: self._xl_select(rr,cc))
                e.bind("<Return>", lambda evt, rr=r, cc=c: self._xl_enter_move(rr,cc))
                e.bind("<Up>", lambda evt, rr=r, cc=c: self._xl_arrow_move(rr-1,cc))
                e.bind("<Down>", lambda evt, rr=r, cc=c: self._xl_arrow_move(rr+1,cc))
                e.bind("<Left>", lambda evt, rr=r, cc=c: self._xl_arrow_move(rr,cc-1))
                e.bind("<Right>", lambda evt, rr=r, cc=c: self._xl_arrow_move(rr,cc+1))
                self._xl_entries[(r,c)] = {"w": e, "v": sv}
        
        self._xl_load_sheet_data()

    def _xl_select(self, r, c):
        # Deselect old
        old_r, old_c = self._xl_sel_r.get(), self._xl_sel_c.get()
        if old_r >= 0 and old_c >= 0:
            if (old_r, old_c) in self._xl_entries:
                self._xl_entries[(old_r, old_c)]["w"].configure(bg=self._xl_get_cell_bg(old_r, old_c))
        
        self._xl_sel_r.set(r); self._xl_sel_c.set(c)
        self._xl_sel_lbl.configure(text=f"{self._xl_col_name(c)}{r+1}")
        
        # Highlight new
        e = self._xl_entries[(r,c)]["w"]
        e.configure(bg="#313244") # highlight color
        
        # Load formula bar
        cd = self._xl_get_cell_data(r,c)
        self._xl_fbar_var.set(cd.get("f", cd.get("v", "")))

    def _xl_arrow_move(self, r, c):
        if 0 <= r < self._rows and 0 <= c < self._cols:
            self._xl_select(r,c)
            self._xl_entries[(r,c)]["w"].focus_set()

    def _xl_enter_move(self, r, c):
        self._xl_validate(self._xl_entries[(r,c)]["v"].get(), str(self._xl_entries[(r,c)]["w"]))
        self._xl_arrow_move(r+1, c)

    def _xl_validate(self, new_val, widget_name):
        r, c = self._xl_sel_r.get(), self._xl_sel_c.get()
        if r < 0 or c < 0: return True
        
        # Store data
        cd = self._xl_get_cell_data(r,c)
        if str(new_val).startswith("="):
            cd["f"] = new_val
            cd["v"] = self._xl_eval_formula(new_val)
        else:
            cd["f"] = ""
            cd["v"] = new_val
        
        sh = self._xl_curr_sheet.get()
        if cd["v"] or cd["f"] or cd["b"] or cd["i"] or cd["fg"] or cd["bg"]:
            self._xl_sheets[sh][(r,c)] = cd
        elif (r,c) in self._xl_sheets[sh]:
            del self._xl_sheets[sh][(r,c)]
            
        # Update display (don't update currently focused widget while it's typing)
        self._xl_refresh_display_values(exclude=(r,c))
        return True

    def _xl_fbar_submit(self):
        r, c = self._xl_sel_r.get(), self._xl_sel_c.get()
        if r < 0 or c < 0: return
        val = self._xl_fbar_var.get()
        cd = self._xl_get_cell_data(r,c)
        if val.startswith("="):
            cd["f"] = val
            cd["v"] = self._xl_eval_formula(val)
        else:
            cd["f"] = ""
            cd["v"] = val
            
        sh = self._xl_curr_sheet.get()
        self._xl_sheets[sh][(r,c)] = cd
        self._xl_refresh_display_values()

    def _xl_eval_formula(self, formula):
        # Basic parsing for SUM, AVG, math. Real Excel formulas need a proper parser.
        import re, math
        f = formula[1:].upper()
        try:
            # Replace cell refs like A1 with their values
            def rep(m):
                col_s, row_s = m.group(1), m.group(2)
                c = 0
                for char in col_s: c = c * 26 + (ord(char) - 64)
                c -= 1
                r = int(row_s) - 1
                return str(self._xl_get_display_val(r,c) or 0)
            
            # Simple handling of ranges A1:B2 -> A1,A2,B1,B2 for SUM()
            if "SUM(" in f:
                parts = re.split(r'SUM\((.*?)\)', f)
                new_f = ""
                for i, p in enumerate(parts):
                    if i % 2 == 1: # inside SUM
                        c_cells = p.split(":")
                        if len(c_cells)==2:
                            m1 = re.match(r'([A-Z]+)(\d+)', c_cells[0])
                            m2 = re.match(r'([A-Z]+)(\d+)', c_cells[1])
                            if m1 and m2:
                                c1, r1 = sum((ord(x)-64)*26**i for i,x in enumerate(m1.group(1)[::-1]))-1, int(m1.group(2))-1
                                c2, r2 = sum((ord(x)-64)*26**i for i,x in enumerate(m2.group(1)[::-1]))-1, int(m2.group(2))-1
                                vals = []
                                for rr in range(min(r1,r2), max(r1,r2)+1):
                                    for cc in range(min(c1,c2), max(c1,c2)+1):
                                        vals.append(str(self._xl_get_display_val(rr,cc) or 0))
                                new_f += "+".join(vals)
                        else: new_f += p.replace(',', '+')
                    else: new_f += p
                f = new_f
                
            f = re.sub(r'([A-Z]+)(\d+)', rep, f)
            # Evaluate safe math operations
            allowed = {**math.__dict__, "abs":abs, "min":min, "max":max, "sum":sum}
            val = eval(f, {"__builtins__": None}, allowed)
            return round(val, 4) if isinstance(val, float) else val
        except Exception as e:
            return "#ERROR!"
            
    def _xl_get_display_val(self, r, c):
        sh = self._xl_curr_sheet.get()
        if sh in self._xl_sheets and (r,c) in self._xl_sheets[sh]:
            v = self._xl_sheets[sh][(r,c)].get("v", "")
            try: return float(v) if '.' in str(v) else int(v)
            except: return v
        return ""

    def _xl_get_cell_data(self, r, c):
        sh = self._xl_curr_sheet.get()
        return self._xl_sheets[sh].get((r,c), {"v":"", "f":"", "b":False, "i":False, "fg":"#cdd6f4", "bg":"#1e1e2e"}).copy()
        
    def _xl_get_cell_bg(self, r, c):
        return self._xl_get_cell_data(r,c).get("bg", "#1e1e2e")

    def _xl_refresh_display_values(self, exclude=None):
        for (r,c), data in self._xl_entries.items():
            if exclude and exclude == (r,c): continue
            cd = self._xl_get_cell_data(r,c)
            val = str(cd.get("v", ""))
            
            # Re-evaluate formulas if needed (dependency cascade is missing, just a simple sweep)
            if cd.get("f", "").startswith("="):
                val = str(self._xl_eval_formula(cd["f"]))
                sh = self._xl_curr_sheet.get()
                if (r,c) not in self._xl_sheets[sh]: self._xl_sheets[sh][(r,c)] = cd
                self._xl_sheets[sh][(r,c)]["v"] = val
                
            if data["v"].get() != val:
                data["v"].set(val)
                
            # Apply formatting
            fn = "Calibri"; sz = 12; wt = "bold" if cd.get("b") else "normal"; sl = "italic" if cd.get("i") else "roman"
            data["w"].configure(
                font=(fn, sz, wt, sl),
                fg=cd.get("fg", "#cdd6f4"),
                bg=cd.get("bg", "#1e1e2e") if (self._xl_sel_r.get(), self._xl_sel_c.get()) != (r,c) else "#313244"
            )

    def _xl_load_sheet_data(self):
        self._xl_refresh_display_values()

    # Toolbar Formats
    def _xl_fmt_toggle(self, key):
        r, c = self._xl_sel_r.get(), self._xl_sel_c.get()
        if r < 0 or c < 0: return
        cd = self._xl_get_cell_data(r,c)
        cd[key] = not cd.get(key, False)
        self._xl_sheets[self._xl_curr_sheet.get()][(r,c)] = cd
        self._xl_refresh_display_values()
        
    def _xl_fmt_color(self, key, color):
        r, c = self._xl_sel_r.get(), self._xl_sel_c.get()
        if r < 0 or c < 0: return
        cd = self._xl_get_cell_data(r,c)
        cd[key] = color
        self._xl_sheets[self._xl_curr_sheet.get()][(r,c)] = cd
        self._xl_refresh_display_values()
        
    def _xl_fmt_clear(self):
        r, c = self._xl_sel_r.get(), self._xl_sel_c.get()
        if r < 0 or c < 0: return
        cd = self._xl_get_cell_data(r,c)
        cd.update({"b":False, "i":False, "fg":"#cdd6f4", "bg":"#1e1e2e"})
        self._xl_sheets[self._xl_curr_sheet.get()][(r,c)] = cd
        self._xl_refresh_display_values()

    # Tabs
    def _xl_refresh_tabs(self):
        for w in self._xl_tab_frame.winfo_children(): w.destroy()
        curr = self._xl_curr_sheet.get()
        for sh in self._xl_sheets.keys():
            b = ctk.CTkButton(self._xl_tab_frame, text=sh, width=80, height=24, corner_radius=0,
                              fg_color="#313244" if sh==curr else "transparent",
                              text_color="white" if sh==curr else "gray",
                              command=lambda s=sh: self._xl_switch_sheet(s))
            b.pack(side="left", padx=1)
            
    def _xl_switch_sheet(self, sh_name):
        self._xl_curr_sheet.set(sh_name)
        self._xl_sel_r.set(-1); self._xl_sel_c.set(-1)
        self._xl_refresh_tabs()
        self._xl_load_sheet_data()
        
    def _xl_add_sheet(self):
        name = simpledialog.askstring("New Sheet", "Enter sheet name:")
        if not name: return
        if name in self._xl_sheets: messagebox.showwarning("Exists", "Sheet exists."); return
        self._xl_sheets[name] = {}
        self._xl_switch_sheet(name)

    # I/O
    def _xl_get_active_data_rows(self, sh):
        data = self._xl_sheets[sh]
        if not data: return []
        max_r = max(r for r,c in data.keys())
        max_c = max(c for r,c in data.keys())
        rows = []
        for r in range(max_r + 1):
            row = []
            for c in range(max_c + 1):
                cd = data.get((r,c), {})
                # For openpyxl integration, we could pass formatting, but keeping it simple: just passing strings logic
                # To be true MS Office clone, we pass formulas if present.
                if cd.get("f"): val = cd["f"]
                else: val = cd.get("v", "")
                row.append(val)
            rows.append(row)
        return rows

    def _xl_open(self):
        f = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not f: return
        try:
            raw_data = excel_utils.read_excel(f)
            self._xl_file_path = f
            self._xl_sheets.clear()
            for sh_name, rows in raw_data.items():
                self._xl_sheets[sh_name] = {}
                for r, row in enumerate(rows):
                    for c, val in enumerate(row):
                        if val is not None and str(val).strip():
                            v_str = str(val)
                            self._xl_sheets[sh_name][(r,c)] = {"v": v_str, "f": v_str if v_str.startswith("=") else "", "b":False, "i":False}
            
            if not self._xl_sheets: self._xl_sheets = {"Sheet1":{}}
            self._xl_switch_sheet(list(self._xl_sheets.keys())[0])
            self.update_status(f"Opened: {os.path.basename(f)}")
        except Exception as e: messagebox.showerror("Error", str(e))

    def _xl_save(self):
        if not self._xl_file_path:
            self._xl_save_as()
            return
        self._save_core(self._xl_file_path)

    def _xl_save_as(self):
        out = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not out: return
        self._xl_file_path = out
        self._save_core(out)
        
    def _save_core(self, out_path):
        import openpyxl
        try:
            wb = openpyxl.Workbook()
            # Remove default sheet
            if "Sheet" in wb.sheetnames: wb.remove(wb["Sheet"])
            
            for sh_name in self._xl_sheets.keys():
                ws = wb.create_sheet(title=sh_name)
                rows = self._xl_get_active_data_rows(sh_name)
                for r_idx, row in enumerate(rows):
                    for c_idx, val in enumerate(row):
                        if val: ws.cell(row=r_idx+1, column=c_idx+1, value=val)
            
            wb.save(out_path)
            messagebox.showinfo("Saved", f"Spreadsheet saved to:\n{out_path}")
            self.update_status("Excel updated.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def tool_edit_excel(self):
        """Open and edit an existing .xlsx spreadsheet."""
        self.tool_create_excel()
        self.after(100, lambda: self._xl_open())
    def tool_excel_to_csv(self):
        self.create_single_file_processor("Excel", [("Excel", "*.xlsx;*.xls")],
            excel_utils.excel_to_csv, "Export to CSV", [("CSV", "*.csv")])

    # ============================================================
    # POWERPOINT STUDIO – Create / Edit
    # ============================================================

    def tool_create_ppt(self):
        """Full MS PowerPoint-like presentation editor with slides, properties, and preview."""
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        self._ppt_file_path = None
        self._ppt_slides = [{"id": 0, "title": "New Slide", "content": "• Point 1", "layout": "title", "bg": "#ffffff"}]
        self._ppt_sel_idx = 0
        self._ppt_next_id = 1

        # ── Toolbar ───────────────────────────────────────────────
        tb = ctk.CTkFrame(frame, height=42, corner_radius=0)
        tb.pack(fill="x"); tb.pack_propagate(False)

        def _btn(p, t, c, w=34):
            b=ctk.CTkButton(p, text=t, command=c, width=w, height=28,
                            fg_color="transparent", hover_color="#374151",
                            text_color=("gray10", "gray90"), corner_radius=4)
            b.pack(side="left", padx=1, pady=7)
            return b
            
        def _sep(p):
            ctk.CTkFrame(p, width=1, height=22, fg_color="gray40").pack(side="left", padx=4, pady=10)

        _btn(tb, "📂 Open",  self._ppt_open, w=60)
        _btn(tb, "💾 Save",  self._ppt_save, w=60)
        _btn(tb, "💾 Save As", self._ppt_save_as, w=70)
        _sep(tb)
        _btn(tb, "➕ New Slide", self._ppt_add_slide, w=90)
        _btn(tb, "🗑 Delete", self._ppt_del_slide, w=70)
        _btn(tb, "▲", lambda: self._ppt_move_slide(-1), w=30)
        _btn(tb, "▼", lambda: self._ppt_move_slide(1), w=30)

        # ── Body (Left: Thumbnails, Middle: Preview, Right: Props) ──
        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=4, pady=4)

        # Left: Thumbnails
        self._ppt_thumb_frame = ctk.CTkScrollableFrame(body, width=140, corner_radius=0)
        self._ppt_thumb_frame.pack(side="left", fill="y", padx=(0,4))
        
        # Right: Properties
        pnl = ctk.CTkFrame(body, width=280, corner_radius=0)
        pnl.pack(side="right", fill="y", padx=(4,0))
        pnl.pack_propagate(False)

        ctk.CTkLabel(pnl, text="Slide Properties", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(pnl, text="Layout:").pack(anchor="w", padx=10)
        self._ppt_layout_var = ctk.StringVar(value="title")
        l_cmb = ctk.CTkComboBox(pnl, values=["title", "content", "blank"], variable=self._ppt_layout_var, command=self._ppt_on_prop_change)
        l_cmb.pack(fill="x", padx=10, pady=(0,10))
        
        ctk.CTkLabel(pnl, text="Title:").pack(anchor="w", padx=10)
        self._ppt_title_var = ctk.StringVar()
        t_ent = ctk.CTkEntry(pnl, textvariable=self._ppt_title_var)
        t_ent.pack(fill="x", padx=10, pady=(0,10))
        t_ent.bind("<KeyRelease>", lambda e: self._ppt_on_prop_change())
        
        ctk.CTkLabel(pnl, text="Content:").pack(anchor="w", padx=10)
        self._ppt_content_txt = tk.Text(pnl, height=10, font=("Consolas",11), bg="#1e1e2e", fg="#cdd6f4")
        self._ppt_content_txt.pack(fill="x", padx=10, pady=(0,10))
        self._ppt_content_txt.bind("<KeyRelease>", lambda e: self._ppt_on_prop_change())

        # Middle: Live Preview
        mid = ctk.CTkFrame(body, fg_color="#181825", corner_radius=8)
        mid.pack(side="left", fill="both", expand=True)
        
        self._ppt_canvas = tk.Canvas(mid, bg="#ffffff", width=800, height=450, highlightthickness=1, highlightbackground="black")
        self._ppt_canvas.pack(expand=True)

        self._ppt_refresh_thumbs()
        self._ppt_refresh_canvas()

    def _ppt_add_slide(self):
        self._ppt_slides.append({
            "id": self._ppt_next_id, "title": "New Slide", "content": "• Point", "layout": "content", "bg": "#ffffff"
        })
        self._ppt_next_id += 1
        self._ppt_sel_idx = len(self._ppt_slides) - 1
        self._ppt_refresh_thumbs()
        self._ppt_load_props()

    def _ppt_del_slide(self):
        if len(self._ppt_slides) > 1:
            self._ppt_slides.pop(self._ppt_sel_idx)
            self._ppt_sel_idx = max(0, self._ppt_sel_idx - 1)
            self._ppt_refresh_thumbs()
            self._ppt_load_props()

    def _ppt_move_slide(self, d):
        idx = self._ppt_sel_idx
        nidx = idx + d
        if 0 <= nidx < len(self._ppt_slides):
            self._ppt_slides[idx], self._ppt_slides[nidx] = self._ppt_slides[nidx], self._ppt_slides[idx]
            self._ppt_sel_idx = nidx
            self._ppt_refresh_thumbs()

    def _ppt_refresh_thumbs(self):
        for w in self._ppt_thumb_frame.winfo_children(): w.destroy()
        for i, s in enumerate(self._ppt_slides):
            bg = "#313244" if i == self._ppt_sel_idx else "transparent"
            b = ctk.CTkButton(self._ppt_thumb_frame, text=f"{i+1}. {s['title'][:12]}...", width=120, height=40,
                              fg_color=bg, text_color="white", corner_radius=4,
                              command=lambda idx=i: self._ppt_select(idx))
            b.pack(pady=2, padx=2)

    def _ppt_select(self, idx):
        self._ppt_sel_idx = idx
        self._ppt_refresh_thumbs()
        self._ppt_load_props()

    def _ppt_load_props(self):
        s = self._ppt_slides[self._ppt_sel_idx]
        self._ppt_layout_var.set(s["layout"])
        self._ppt_title_var.set(s["title"])
        self._ppt_content_txt.delete("1.0", "end")
        self._ppt_content_txt.insert("1.0", s["content"])
        self._ppt_refresh_canvas()

    def _ppt_on_prop_change(self, *_):
        s = self._ppt_slides[self._ppt_sel_idx]
        s["layout"] = self._ppt_layout_var.get()
        s["title"] = self._ppt_title_var.get()
        s["content"] = self._ppt_content_txt.get("1.0", "end-1c")
        self._ppt_refresh_canvas()

    def _ppt_refresh_canvas(self):
        c = self._ppt_canvas
        c.delete("all")
        s = self._ppt_slides[self._ppt_sel_idx]
        
        # Draw slide background
        c.configure(bg=s["bg"])
        
        # Calculate scales (16:9 ratio, approx 800x450 max size)
        w, h = 800, 450
        
        t = s["title"]; cont = s["content"]
        if s["layout"] == "title":
            c.create_text(w/2, h/2 - 40, text=t, font=("Calibri", 48, "bold"), fill="black", anchor="center")
            c.create_text(w/2, h/2 + 40, text=cont.replace('\n', '  '), font=("Calibri", 24), fill="gray30", anchor="center")
        elif s["layout"] == "content":
            c.create_text(w/2, 40, text=t, font=("Calibri", 36, "bold"), fill="black", anchor="center")
            c.create_text(40, 100, text=cont, font=("Calibri", 20), fill="black", anchor="nw", width=w-80)

    def _ppt_open(self):
        f = filedialog.askopenfilename(filetypes=[("PowerPoint", "*.pptx")])
        if not f: return
        try:
            raw = ppt_utils.read_ppt_info(f)
            self._ppt_slides = []
            for i, sd in enumerate(raw):
                self._ppt_slides.append({
                    "id": i, "title": sd.get("title", f"Slide {i+1}"),
                    "content": sd.get("content", ""), "layout": "content", "bg": "#ffffff"
                })
            self._ppt_file_path = f
            if not self._ppt_slides: self._ppt_add_slide()
            self._ppt_select(0)
            self.update_status(f"Loaded: {os.path.basename(f)}")
        except Exception as e: messagebox.showerror("Error", str(e))

    def _ppt_save(self):
        if not self._ppt_file_path: self._ppt_save_as(); return
        self._save_ppt_core(self._ppt_file_path)

    def _ppt_save_as(self):
        out = filedialog.asksaveasfilename(defaultextension=".pptx", filetypes=[("PowerPoint", "*.pptx")])
        if out: self._ppt_file_path = out; self._save_ppt_core(out)

    def _save_ppt_core(self, out):
        try:
            ppt_utils.create_ppt(out, slides_data=self._ppt_slides)
            messagebox.showinfo("Saved", f"Saved to:\n{out}")
            self.update_status("Presentation updated.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def tool_edit_ppt(self):
        """Open and edit an existing PowerPoint file."""
        self.tool_create_ppt()
        self.after(100, lambda: self._ppt_open())

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

    # ============================================================
    # NEW IMAGE TOOLS
    # ============================================================
    def tool_batch_img(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self.selected_files = []
        
        txt_display = ctk.CTkTextbox(frame, height=150)
        txt_display.pack(fill="x", pady=5, padx=10)

        def update_display():
            txt_display.delete("0.0", "end")
            for f in self.selected_files:
                txt_display.insert("end", f + "\n")

        def add():
            files = filedialog.askopenfilenames(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
            if files: self.selected_files.extend(files); update_display()

        ctk.CTkButton(frame, text="Add Images", command=add).pack(pady=5)
        ctk.CTkButton(frame, text="Clear", command=lambda: [self.selected_files.clear(), update_display()], fg_color="red", width=80).pack(pady=2)

        op_cmb = ctk.CTkComboBox(frame, values=["resize", "grayscale", "compress", "rotate", "flip"])
        op_cmb.set("grayscale"); op_cmb.pack(pady=10)

        def run():
            if not self.selected_files: return
            out = filedialog.askdirectory(title="Output Folder")
            if out:
                self.update_status("Batch processing...")
                def task():
                    try:
                        c = image_utils.batch_process(self.selected_files, out, op_cmb.get())
                        self.after(0, lambda: [messagebox.showinfo("Done", f"Processed {c} images"), self.update_status(f"Batch: {c} images processed")])
                    except Exception as e:
                        self.after(0, lambda: messagebox.showerror("Error", str(e)))
                threading.Thread(target=task).start()

        ctk.CTkButton(frame, text="Process All", command=run, fg_color="green").pack(pady=15)

    def tool_color_palette(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        self.selected_file = None
        lbl = ctk.CTkLabel(frame, text="No image selected")
        lbl.pack(pady=10)

        def select():
            f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
            if f: self.selected_file = f; lbl.configure(text=os.path.basename(f))
        ctk.CTkButton(frame, text="Select Image", command=select).pack(pady=5)

        palette_frame = ctk.CTkFrame(frame, height=80)
        palette_frame.pack(fill="x", padx=20, pady=10)
        hex_box = ctk.CTkTextbox(frame, height=80)
        hex_box.pack(fill="x", padx=20, pady=5)

        def run():
            if not self.selected_file: return
            try:
                colors = image_utils.extract_color_palette(self.selected_file, 8)
                for w in palette_frame.winfo_children(): w.destroy()
                hex_box.delete("0.0", "end")
                for c in colors:
                    swatch = ctk.CTkFrame(palette_frame, width=50, height=50, fg_color=c)
                    swatch.pack(side="left", padx=3, pady=5)
                    hex_box.insert("end", f"{c}\n")
                self.update_status("Color palette extracted")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(frame, text="Extract Palette", command=run, fg_color="purple").pack(pady=10)

    def tool_collage(self):
        self.create_multi_file_processor("Image", [("Images", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")],
            image_utils.create_collage, "Create Collage", [("PNG", "*.png"), ("JPG", "*.jpg")])

    # ============================================================
    # NEW VIDEO TOOLS
    # ============================================================
    def tool_video_to_gif(self):
        frame = self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv")],
            lambda i, o: video_utils.video_to_gif(i, o, self.gif_start, self.gif_dur, self.gif_fps), "Make GIF",
            [("GIF", "*.gif")])
        self.gif_start, self.gif_dur, self.gif_fps = "00:00", 5, 10
        f2 = ctk.CTkFrame(frame, fg_color="transparent")
        f2.pack(before=frame.winfo_children()[-1], pady=5)
        ctk.CTkLabel(f2, text="Start:").pack(side="left"); e1 = ctk.CTkEntry(f2, width=70); e1.pack(side="left", padx=3); e1.insert(0, "00:00")
        ctk.CTkLabel(f2, text="Duration(s):").pack(side="left"); e2 = ctk.CTkEntry(f2, width=50); e2.pack(side="left", padx=3); e2.insert(0, "5")
        ctk.CTkLabel(f2, text="FPS:").pack(side="left"); e3 = ctk.CTkEntry(f2, width=40); e3.pack(side="left", padx=3); e3.insert(0, "10")
        def upd(): self.gif_start = e1.get(); self.gif_dur = float(e2.get()); self.gif_fps = int(e3.get())
        ctk.CTkButton(f2, text="Set", command=upd, width=50).pack(side="left", padx=5)

    def tool_video_thumbnail(self):
        frame = self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv")],
            lambda i, o: video_utils.extract_thumbnail(i, o, self.thumb_time), "Extract Thumbnail",
            [("PNG", "*.png"), ("JPG", "*.jpg")])
        self.thumb_time = "00:01"
        f2 = ctk.CTkFrame(frame, fg_color="transparent")
        f2.pack(before=frame.winfo_children()[-1], pady=5)
        ctk.CTkLabel(f2, text="Time (MM:SS):").pack(side="left")
        e = ctk.CTkEntry(f2, width=80); e.pack(side="left", padx=5); e.insert(0, "00:01")
        e.bind("<KeyRelease>", lambda ev: setattr(self, 'thumb_time', e.get()))

    def tool_reverse_video(self):
        self.create_single_file_processor("Video", [("Video", "*.mp4;*.avi;*.mov;*.mkv")],
            video_utils.reverse_video, "Reverse Video")

    # ============================================================
    # NEW AUDIO TOOLS
    # ============================================================
    def tool_noise_reduction(self):
        self.create_single_file_processor("Audio", [("Audio", "*.mp3;*.wav;*.ogg;*.m4a;*.flac")],
            audio_utils.reduce_noise, "Reduce Noise")

    def tool_normalize_audio(self):
        self.create_single_file_processor("Audio", [("Audio", "*.mp3;*.wav;*.ogg;*.m4a;*.flac")],
            audio_utils.normalize_audio, "Normalize")

    # ============================================================
    # NEW SYSTEM TOOLS
    # ============================================================
    def tool_base64_encode(self):
        self.create_single_file_processor("File", [("All Files", "*.*")],
            system_utils.base64_encode, "Encode to Base64", [("Text", "*.txt")])

    def tool_base64_decode(self):
        self.create_single_file_processor("File", [("Text", "*.txt")],
            system_utils.base64_decode, "Decode Base64", [("All Files", "*.*")])

    def tool_disk_usage(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Disk Usage Analyzer", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        res_box = ctk.CTkTextbox(frame, height=350)
        res_box.pack(fill="both", expand=True, padx=10, pady=10)

        def run():
            d = filedialog.askdirectory()
            if d:
                res_box.delete("0.0", "end")
                res_box.insert("end", "Scanning...\n")
                def task():
                    try:
                        info = system_utils.get_disk_usage(d)
                        fmt = system_utils.format_size
                        result = f"Disk: {fmt(info['total'])} total, {fmt(info['used'])} used, {fmt(info['free'])} free\n"
                        result += f"Files scanned: {info['file_count']}\n\n"
                        result += "--- Size by Extension ---\n"
                        for ext, size in info['extensions'][:25]:
                            result += f"  {ext:12s}  {fmt(size):>10s}\n"
                        self.after(0, lambda: [res_box.delete("0.0", "end"), res_box.insert("end", result)])
                    except Exception as e:
                        self.after(0, lambda: messagebox.showerror("Error", str(e)))
                threading.Thread(target=task).start()

        ctk.CTkButton(frame, text="Select Folder", command=run, fg_color="blue").pack(pady=10)

    def tool_color_picker(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Color Picker", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        preview = ctk.CTkFrame(frame, width=200, height=100, fg_color="#3498db")
        preview.pack(pady=10)

        inp_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inp_frame.pack(pady=10)
        ctk.CTkLabel(inp_frame, text="HEX:").grid(row=0, column=0, padx=5)
        hex_ent = ctk.CTkEntry(inp_frame, width=100); hex_ent.grid(row=0, column=1, padx=5); hex_ent.insert(0, "#3498db")
        ctk.CTkLabel(inp_frame, text="R:").grid(row=1, column=0)
        r_ent = ctk.CTkEntry(inp_frame, width=60); r_ent.grid(row=1, column=1, sticky="w")
        ctk.CTkLabel(inp_frame, text="G:").grid(row=1, column=2)
        g_ent = ctk.CTkEntry(inp_frame, width=60); g_ent.grid(row=1, column=3, sticky="w")
        ctk.CTkLabel(inp_frame, text="B:").grid(row=1, column=4)
        b_ent = ctk.CTkEntry(inp_frame, width=60); b_ent.grid(row=1, column=5, sticky="w")

        info_lbl = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(family="Consolas", size=12))
        info_lbl.pack(pady=10)

        def from_hex():
            h = hex_ent.get().strip()
            try:
                h = h.lstrip("#")
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                preview.configure(fg_color=f"#{h}")
                for e in [r_ent, g_ent, b_ent]: e.delete(0, "end")
                r_ent.insert(0, str(r)); g_ent.insert(0, str(g)); b_ent.insert(0, str(b))
                info_lbl.configure(text=f"HEX: #{h}  |  RGB({r}, {g}, {b})")
            except: messagebox.showerror("Error", "Invalid hex color")

        def from_rgb():
            try:
                r, g, b = int(r_ent.get()), int(g_ent.get()), int(b_ent.get())
                h = f"#{r:02x}{g:02x}{b:02x}"
                preview.configure(fg_color=h)
                hex_ent.delete(0, "end"); hex_ent.insert(0, h)
                info_lbl.configure(text=f"HEX: {h}  |  RGB({r}, {g}, {b})")
            except: messagebox.showerror("Error", "Invalid RGB values")

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=5)
        ctk.CTkButton(btn_frame, text="From HEX", command=from_hex, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="From RGB", command=from_rgb, width=100).pack(side="left", padx=5)

    # ============================================================
    # NEW TEXT TOOLS
    # ============================================================
    def tool_word_counter(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        txt = ctk.CTkTextbox(frame, height=200)
        txt.pack(fill="x", padx=10, pady=10)
        res_lbl = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(family="Consolas", size=13), justify="left")
        res_lbl.pack(pady=10)

        def run():
            data = txt.get("0.0", "end")
            stats = text_utils.count_words(data)
            res_lbl.configure(text=f"Characters: {stats['characters']}  (no spaces: {stats['characters_no_spaces']})\n"
                              f"Words: {stats['words']}  |  Sentences: {stats['sentences']}\n"
                              f"Paragraphs: {stats['paragraphs']}  |  Lines: {stats['lines']}")
            self.update_status("Word count complete")

        ctk.CTkButton(frame, text="Count", command=run, fg_color="blue").pack(pady=10)

    def tool_word_frequency(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        txt = ctk.CTkTextbox(frame, height=200)
        txt.pack(fill="x", padx=10, pady=10)
        res_box = ctk.CTkTextbox(frame, height=200)
        res_box.pack(fill="x", padx=10, pady=5)

        def run():
            data = txt.get("0.0", "end")
            freq = text_utils.count_frequency(data, 20)
            res_box.delete("0.0", "end")
            for word, count in freq:
                res_box.insert("end", f"{word:20s} {count}\n")

        ctk.CTkButton(frame, text="Analyze Frequency", command=run, fg_color="purple").pack(pady=10)

    def tool_case_converter(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        txt = ctk.CTkTextbox(frame, height=200)
        txt.pack(fill="x", padx=10, pady=10)
        mode_cmb = ctk.CTkComboBox(frame, values=["upper", "lower", "title", "sentence", "alternating", "inverse"])
        mode_cmb.set("upper"); mode_cmb.pack(pady=5)
        res_box = ctk.CTkTextbox(frame, height=200)
        res_box.pack(fill="x", padx=10, pady=5)

        def run():
            data = txt.get("0.0", "end").rstrip("\n")
            result = text_utils.convert_case(data, mode_cmb.get())
            res_box.delete("0.0", "end"); res_box.insert("end", result)

        ctk.CTkButton(frame, text="Convert", command=run, fg_color="green").pack(pady=10)

    def tool_find_replace(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        txt = ctk.CTkTextbox(frame, height=180)
        txt.pack(fill="x", padx=10, pady=5)
        
        fr = ctk.CTkFrame(frame, fg_color="transparent")
        fr.pack(pady=5)
        ctk.CTkLabel(fr, text="Find:").pack(side="left")
        find_ent = ctk.CTkEntry(fr, width=150); find_ent.pack(side="left", padx=5)
        ctk.CTkLabel(fr, text="Replace:").pack(side="left")
        rep_ent = ctk.CTkEntry(fr, width=150); rep_ent.pack(side="left", padx=5)

        res_box = ctk.CTkTextbox(frame, height=180)
        res_box.pack(fill="x", padx=10, pady=5)

        def run():
            data = txt.get("0.0", "end").rstrip("\n")
            result, count = text_utils.find_replace(data, find_ent.get(), rep_ent.get())
            res_box.delete("0.0", "end"); res_box.insert("end", result)
            self.update_status(f"Replaced {count} occurrences")

        ctk.CTkButton(frame, text="Find & Replace", command=run, fg_color="orange").pack(pady=10)

    def tool_remove_spaces(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        txt = ctk.CTkTextbox(frame, height=200)
        txt.pack(fill="x", padx=10, pady=10)
        res_box = ctk.CTkTextbox(frame, height=200)
        res_box.pack(fill="x", padx=10, pady=5)

        def run():
            data = txt.get("0.0", "end").rstrip("\n")
            result = text_utils.remove_extra_spaces(data)
            res_box.delete("0.0", "end"); res_box.insert("end", result)

        ctk.CTkButton(frame, text="Clean Text", command=run, fg_color="blue").pack(pady=10)

    def tool_lorem_ipsum(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)
        ctk.CTkLabel(frame, text="Number of paragraphs:").pack(pady=5)
        sl = ctk.CTkSlider(frame, from_=1, to=10, number_of_steps=9); sl.set(3); sl.pack(pady=5)
        lbl = ctk.CTkLabel(frame, text="3 paragraphs"); lbl.pack()
        sl.configure(command=lambda v: lbl.configure(text=f"{int(v)} paragraphs"))
        res_box = ctk.CTkTextbox(frame, height=300)
        res_box.pack(fill="both", expand=True, padx=10, pady=10)

        def run():
            result = text_utils.generate_lorem(int(sl.get()))
            res_box.delete("0.0", "end"); res_box.insert("end", result)

        ctk.CTkButton(frame, text="Generate", command=run, fg_color="green").pack(pady=10)

    # ═══════════════════════════════════════════════════════════════════════
    #  PASSPORT PHOTO STUDIO
    # ═══════════════════════════════════════════════════════════════════════
    def setup_passport_tab(self):
        """Build the full Passport Photo Studio UI inside self.tab_passport."""
        tab = self.tab_passport
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(0, weight=1)

        # ── Left panel ──────────────────────────────────────────────────────
        left = ctk.CTkScrollableFrame(tab, width=310, corner_radius=10,
                                       label_text="⚙ Controls")
        left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # Step 1 – Upload
        ctk.CTkLabel(left, text="Step 1 – Upload Photo",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(12, 4))
        ctk.CTkButton(left, text="📂  Upload Photo",
                       command=self._pp_upload, height=36).pack(fill="x", padx=10, pady=4)
        self._pp_file_lbl = ctk.CTkLabel(left, text="No file selected",
                                          font=ctk.CTkFont(size=11), text_color="gray")
        self._pp_file_lbl.pack(anchor="w", padx=14)

        ctk.CTkFrame(left, height=1, fg_color="gray30").pack(fill="x", padx=10, pady=8)

        # Step 2 – Background removal
        ctk.CTkLabel(left, text="Step 2 – Remove Background",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(4, 4))
        ctk.CTkButton(left, text="✂  Remove Background",
                       command=self._pp_remove_bg, fg_color="#7c3aed", height=36).pack(fill="x", padx=10, pady=4)

        ctk.CTkFrame(left, height=1, fg_color="gray30").pack(fill="x", padx=10, pady=8)

        # Step 3 – Background color
        ctk.CTkLabel(left, text="Step 3 – Background Color",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(4, 4))
        color_row = ctk.CTkFrame(left, fg_color="transparent")
        color_row.pack(fill="x", padx=10, pady=4)
        self._pp_color_swatch = ctk.CTkButton(color_row, text="", width=36, height=36,
                                               fg_color=self._pp_bg_color,
                                               command=self._pp_pick_color)
        self._pp_color_swatch.pack(side="left", padx=(0, 6))
        self._pp_color_entry = ctk.CTkEntry(color_row, placeholder_text="#FFFFFF", width=100)
        self._pp_color_entry.insert(0, self._pp_bg_color)
        self._pp_color_entry.pack(side="left", padx=4)
        ctk.CTkButton(color_row, text="Apply", width=60,
                       command=self._pp_apply_bg_color).pack(side="left", padx=4)

        # Common background presets
        preset_row = ctk.CTkFrame(left, fg_color="transparent")
        preset_row.pack(fill="x", padx=10, pady=(2, 8))
        presets = [("White", "#FFFFFF"), ("Light Blue", "#add8e6"),
                   ("Sky", "#87ceeb"), ("Gray", "#d3d3d3")]
        for name, col in presets:
            ctk.CTkButton(preset_row, text=name, width=66, height=26,
                           fg_color=col, text_color="#333333",
                           command=lambda c=col: self._pp_set_color(c)).pack(side="left", padx=2)

        ctk.CTkFrame(left, height=1, fg_color="gray30").pack(fill="x", padx=10, pady=8)

        # Step 4 – Passport size
        ctk.CTkLabel(left, text="Step 4 – Passport Size",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(4, 4))
        size_names = list(passport_utils.PASSPORT_SIZES.keys())
        self._pp_size_combo = ctk.CTkComboBox(left, values=size_names, width=280)
        self._pp_size_combo.set(size_names[0])
        self._pp_size_combo.pack(padx=10, pady=4)

        custom_row = ctk.CTkFrame(left, fg_color="transparent")
        custom_row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(custom_row, text="Custom W(mm):").pack(side="left")
        self._pp_custom_w = ctk.CTkEntry(custom_row, width=55, placeholder_text="35")
        self._pp_custom_w.pack(side="left", padx=4)
        ctk.CTkLabel(custom_row, text="H:").pack(side="left")
        self._pp_custom_h = ctk.CTkEntry(custom_row, width=55, placeholder_text="45")
        self._pp_custom_h.pack(side="left", padx=4)

        dpi_row = ctk.CTkFrame(left, fg_color="transparent")
        dpi_row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(dpi_row, text="Print DPI:").pack(side="left")
        self._pp_dpi_combo = ctk.CTkComboBox(dpi_row, values=["96", "150", "300", "600"], width=80)
        self._pp_dpi_combo.set("300")
        self._pp_dpi_combo.pack(side="left", padx=8)

        # Layout preset (margin/gap → controls how many photos on A4)
        layout_row = ctk.CTkFrame(left, fg_color="transparent")
        layout_row.pack(fill="x", padx=10, pady=(4, 2))
        ctk.CTkLabel(layout_row, text="A4 Layout:").pack(side="left")
        layout_names = list(passport_utils.LAYOUT_PRESETS.keys())
        self._pp_layout_combo = ctk.CTkComboBox(layout_row, values=layout_names, width=220)
        self._pp_layout_combo.set(layout_names[0])   # default = Compact 36 photos
        self._pp_layout_combo.pack(side="left", padx=8)

        ctk.CTkFrame(left, height=1, fg_color="gray30").pack(fill="x", padx=10, pady=8)

        # Step 5 – Generate A4 sheet
        ctk.CTkLabel(left, text="Step 5 – Generate A4 Sheet",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(4, 4))
        ctk.CTkButton(left, text="🖨  Generate A4 Sheet",
                       command=self._pp_generate_a4, fg_color="#0ea5e9", height=38).pack(fill="x", padx=10, pady=4)

        self._pp_info_lbl = ctk.CTkLabel(left, text="", font=ctk.CTkFont(size=11),
                                          text_color="#94a3b8", wraplength=270)
        self._pp_info_lbl.pack(anchor="w", padx=10)

        ctk.CTkFrame(left, height=1, fg_color="gray30").pack(fill="x", padx=10, pady=8)

        # Step 6 – Export
        ctk.CTkLabel(left, text="Step 6 – Export",
                      font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(4, 4))
        ctk.CTkButton(left, text="💾  Save as PDF",
                       command=self._pp_save_pdf, fg_color="#dc2626", height=34).pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(left, text="🖼  Save as JPEG",
                       command=self._pp_save_jpeg, fg_color="#d97706", height=34).pack(fill="x", padx=10, pady=3)
        ctk.CTkButton(left, text="📄  Save as DOCX",
                       command=self._pp_save_docx, fg_color="#2563eb", height=34).pack(fill="x", padx=10, pady=3)

        # Progress bar
        self._pp_progress = ctk.CTkProgressBar(left, mode="indeterminate")

        # ── Right panel – preview canvas ────────────────────────────────────
        right = ctk.CTkFrame(tab, corner_radius=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text="Preview",
                      font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, pady=(12, 4))

        self._pp_preview_lbl = ctk.CTkLabel(right, text="Upload a photo to get started.",
                                             font=ctk.CTkFont(size=14), text_color="gray")
        self._pp_preview_lbl.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Tab label row at bottom of preview
        self._pp_stage_lbl = ctk.CTkLabel(right, text="",
                                           font=ctk.CTkFont(size=11), text_color="#64748b")
        self._pp_stage_lbl.grid(row=2, column=0, pady=(0, 8))

    # ── Passport helpers ─────────────────────────────────────────────────────

    def _pp_show_preview(self, pil_img, stage_text=""):
        """Display a PIL image in the passport preview panel (fit to widget)."""
        if pil_img is None:
            return
        # Determine widget size
        self.update_idletasks()
        w = max(self._pp_preview_lbl.winfo_width(), 400)
        h = max(self._pp_preview_lbl.winfo_height(), 500)

        preview = pil_img.copy()
        preview.thumbnail((w - 20, h - 20), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=preview, dark_image=preview,
                                size=preview.size)
        self._pp_preview_lbl.configure(image=ctk_img, text="")
        self._pp_preview_lbl._image = ctk_img  # Keep reference to prevent GC
        self._pp_stage_lbl.configure(text=stage_text)

    def _pp_busy(self, is_busy: bool):
        if is_busy:
            self._pp_progress.pack(fill="x", padx=10, pady=2)
            self._pp_progress.start()
            self.is_busy = True
        else:
            self._pp_progress.stop()
            self._pp_progress.pack_forget()
            self.is_busy = False

    def _pp_get_size_mm(self):
        """Return (width_mm, height_mm) from current controls."""
        selected = self._pp_size_combo.get()
        dims = passport_utils.PASSPORT_SIZES.get(selected)
        if dims is None:  # Custom
            try:
                w = int(self._pp_custom_w.get())
                h = int(self._pp_custom_h.get())
                return w, h
            except ValueError:
                messagebox.showerror("Error", "Enter valid custom width & height in mm.")
                return None
        return dims

    def _pp_upload(self):
        f = filedialog.askopenfilename(
            title="Select Portrait Photo",
            filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.tiff")])
        if not f:
            return
        self._pp_original_img = Image.open(f).convert("RGB")
        self._pp_nobg_img = None
        self._pp_colored_img = None
        self._pp_passport_img = None
        self._pp_a4_img = None
        self._pp_file_lbl.configure(text=os.path.basename(f))
        self._pp_info_lbl.configure(text="")
        self._pp_show_preview(self._pp_original_img, "Original Photo")
        self.update_status("Photo uploaded.")
        print(f"Passport Studio: loaded {os.path.basename(f)}")

    def _pp_remove_bg(self):
        if self._pp_original_img is None:
            messagebox.showwarning("No Photo", "Please upload a photo first.")
            return
        if hasattr(self, 'is_busy') and self.is_busy:
            return

        # Save original to temp file for rembg
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_path = tmp.name
        tmp.close()
        self._pp_original_img.save(tmp_path, "PNG")

        self._pp_busy(True)
        self.update_status("Removing background (1st run downloads ~170MB model)...")
        self._pp_info_lbl.configure(
            text="⏳ Removing background...\nNote: first run downloads ~170 MB AI model. Please wait.")

        def task():
            try:
                nobg = passport_utils.remove_background(tmp_path)
                self._pp_nobg_img = nobg
                
                # Show checkerboard transparent preview
                preview_img = passport_utils.preview_transparency(nobg)
                # Auto apply current bg color for final sheet
                colored = passport_utils.apply_background_color(nobg, self._pp_bg_color)
                self._pp_colored_img = colored
                self.after(0, lambda: [
                    self._pp_show_preview(preview_img, "\u2713 Background Removed (Transparent)"),
                    self._pp_info_lbl.configure(text="\u2713 Background removed! Choose a color below to fill."),
                    self.update_status("Background removed."),
                    self._pp_busy(False)
                ])
            except Exception as e:
                err = str(e)
                self.after(0, lambda: [
                    messagebox.showerror("BG Removal Error", 
                        f"{err}\n\nTip: ensure rembg is installed:\n  pip install rembg onnxruntime"),
                    self._pp_info_lbl.configure(text=f"\u274c Error: {err[:80]}"),
                    self._pp_busy(False)
                ])
            finally:
                try: os.unlink(tmp_path)
                except: pass

        threading.Thread(target=task, daemon=True).start()

    def _pp_set_color(self, color: str):
        self._pp_bg_color = color
        self._pp_color_entry.delete(0, "end")
        self._pp_color_entry.insert(0, color)
        self._pp_color_swatch.configure(fg_color=color)
        self._pp_apply_bg_color()

    def _pp_pick_color(self):
        color = colorchooser.askcolor(title="Pick Background Color",
                                       color=self._pp_bg_color)
        if color and color[1]:
            self._pp_set_color(str(color[1]))

    def _pp_apply_bg_color(self):
        raw = self._pp_color_entry.get().strip()
        if raw:
            self._pp_bg_color = raw
        # Update swatch color safely
        try:
            self._pp_color_swatch.configure(fg_color=self._pp_bg_color)
        except Exception:
            pass

        if self._pp_nobg_img is not None:
            # Best path: nobg RGBA image → composite onto chosen color
            try:
                self._pp_colored_img = passport_utils.apply_background_color(
                    self._pp_nobg_img, self._pp_bg_color)
                self._pp_passport_img = None
                self._pp_a4_img = None
                self._pp_show_preview(self._pp_colored_img, "Background Color Applied")
            except Exception as e:
                messagebox.showerror("Color Error", str(e))
        elif self._pp_original_img is not None:
            # Fallback: paste original RGB onto solid-color canvas
            # (useful to preview sheet bg color even without BG removal)
            try:
                from PIL import Image as _Img
                ori = self._pp_original_img.convert("RGBA")
                colored = passport_utils.apply_background_color(ori, self._pp_bg_color)
                self._pp_colored_img = colored
                self._pp_passport_img = None
                self._pp_a4_img = None
                self._pp_show_preview(colored,
                    "Color Preview (remove BG for clean result)")
                self._pp_info_lbl.configure(
                    text="ℹ For best results: Remove Background first, then apply color.")
            except Exception as e:
                messagebox.showerror("Color Error", str(e))


    def _pp_generate_a4(self):
        # Require at least original image
        base = self._pp_colored_img or self._pp_original_img
        if base is None:
            messagebox.showwarning("No Photo", "Please upload a photo first.")
            return
        if hasattr(self, 'is_busy') and self.is_busy:
            return

        dims = self._pp_get_size_mm()
        if dims is None:
            return
        w_mm, h_mm = dims

        try:
            dpi = int(self._pp_dpi_combo.get())
        except ValueError:
            dpi = 300
        self._pp_dpi = dpi

        # Read layout preset → margin & gap
        layout_key = self._pp_layout_combo.get()
        margin_mm, gap_mm = passport_utils.LAYOUT_PRESETS.get(
            layout_key, (0, 0))   # default compact

        self._pp_busy(True)
        self.update_status("Generating A4 sheet...")

        def task():
            try:
                passport = passport_utils.crop_to_passport(base, w_mm, h_mm, dpi)
                self._pp_passport_img = passport
                a4 = passport_utils.create_a4_sheet(
                    passport, w_mm, h_mm, dpi,
                    bg_color=self._pp_bg_color,
                    margin_mm=margin_mm,
                    gap_mm=gap_mm
                )
                self._pp_a4_img = a4
                cols, rows = passport_utils.calculate_grid(w_mm, h_mm, margin_mm, gap_mm)
                info = (f"✓ A4 sheet ready: {cols}×{rows} = {cols*rows} photos  "
                        f"({w_mm}×{h_mm} mm @ {dpi} DPI)")
                self.after(0, lambda: [
                    self._pp_show_preview(a4, f"A4 Preview – {cols}×{rows} photos"),
                    self._pp_info_lbl.configure(text=info),
                    self.update_status("A4 sheet ready to export."),
                    self._pp_busy(False)
                ])
            except Exception as e:
                self.after(0, lambda: [
                    messagebox.showerror("Error", str(e)),
                    self._pp_busy(False)
                ])

        threading.Thread(target=task, daemon=True).start()

    def _pp_save_pdf(self):
        if self._pp_a4_img is None:
            messagebox.showwarning("Not Ready", "Generate the A4 sheet first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Save Passport Sheet as PDF")
        if not path:
            return
        try:
            passport_utils.export_as_pdf(self._pp_a4_img, path, self._pp_dpi)
            messagebox.showinfo("Saved", f"PDF saved:\n{path}")
            self.update_status("PDF exported.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _pp_save_jpeg(self):
        if self._pp_a4_img is None:
            messagebox.showwarning("Not Ready", "Generate the A4 sheet first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg;*.jpeg")],
            title="Save Passport Sheet as JPEG")
        if not path:
            return
        try:
            passport_utils.export_as_jpeg(self._pp_a4_img, path, self._pp_dpi)
            messagebox.showinfo("Saved", f"JPEG saved:\n{path}")
            self.update_status("JPEG exported.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def _pp_save_docx(self):
        if self._pp_a4_img is None:
            messagebox.showwarning("Not Ready", "Generate the A4 sheet first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            title="Save Passport Sheet as DOCX")
        if not path:
            return
        try:
            passport_utils.export_as_docx(self._pp_a4_img, path, self._pp_dpi)
            messagebox.showinfo("Saved", f"DOCX saved:\n{path}")
            self.update_status("DOCX exported.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ============================================================
    # FILE STUDIO
    # ============================================================

    def _create_splitter_ui(self, title, file_types, process_func):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Row count
        rc_frame = ctk.CTkFrame(frame, fg_color="transparent")
        rc_frame.pack(pady=10)
        ctk.CTkLabel(rc_frame, text="Rows per file:").pack(side="left")
        rows_ent = ctk.CTkEntry(rc_frame, width=80)
        rows_ent.insert(0, "1000")
        rows_ent.pack(side="left", padx=10)

        def run():
            f = filedialog.askopenfilename(filetypes=file_types)
            if not f: return
            try: rows = int(rows_ent.get())
            except: messagebox.showerror("Error", "Rows must be an integer."); return
            
            out_dir = filedialog.askdirectory(title="Select Output Folder")
            if not out_dir: return
            
            def task():
                try:
                    process_func(f, out_dir, rows)
                    self.after(0, lambda: messagebox.showinfo("Done", f"Files saved to:\n{out_dir}"))
                    self.update_status("Split operation complete.")
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))
            
            threading.Thread(target=task).start()

        ctk.CTkButton(frame, text="Select File & Split", command=run).pack(pady=20)

    def tool_split_csv(self):
        self._create_splitter_ui("Split CSV File", [("CSV", "*.csv")], file_utils.split_csv)

    def tool_split_excel(self):
        self._create_splitter_ui("Split Excel File", [("Excel", "*.xlsx;*.xls")], file_utils.split_excel)

    def tool_xml_to_excel(self):
        self.create_single_file_processor("XML", [("XML", "*.xml")], file_utils.xml_to_excel, "Convert XML to Excel", [("Excel", "*.xlsx")])

    def tool_excel_to_xml(self):
        self.create_single_file_processor("Excel", [("Excel", "*.xlsx;*.xls")], file_utils.excel_to_xml, "Convert Excel to XML", [("XML", "*.xml")])

    def tool_csv_to_excel(self):
        self.create_single_file_processor("CSV", [("CSV", "*.csv")], file_utils.csv_to_excel, "Convert CSV to Excel", [("Excel", "*.xlsx")])

    def tool_xml_to_csv(self):
        self.create_single_file_processor("XML", [("XML", "*.xml")], file_utils.xml_to_csv, "Convert XML to CSV", [("CSV", "*.csv")])

    def tool_xml_to_json(self):
        self.create_single_file_processor("XML", [("XML", "*.xml")], file_utils.xml_to_json, "Convert XML to JSON", [("JSON", "*.json")])


    # ============================================================
    # CLOUD & AI STUDIO (Video/Audio Ext)
    # ============================================================

    def tool_media_download(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(frame, text="Social Media Downloader (YT, IG, TikTok, Twitter)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        url_frame = ctk.CTkFrame(frame, fg_color="transparent")
        url_frame.pack(pady=10, fill="x", padx=50)
        ctk.CTkLabel(url_frame, text="Video URL:").pack(side="left")
        url_ent = ctk.CTkEntry(url_frame, width=400)
        url_ent.pack(side="left", padx=10, expand=True, fill="x")

        audio_only_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(frame, text="Extract Audio Only (MP3)", variable=audio_only_var).pack(pady=5)

        def run():
            url = url_ent.get().strip()
            if not url: return
            out_dir = filedialog.askdirectory(title="Select Download Folder")
            if not out_dir: return
            
            self.update_status("Downloading media... Please wait.")
            
            def task():
                success, msg = video_utils.download_media(url, out_dir, audio_only_var.get())
                if success:
                    self.after(0, lambda: messagebox.showinfo("Success", msg))
                    self.update_status("Download complete.")
                else:
                    self.after(0, lambda: messagebox.showerror("Download Error", msg))
                    self.update_status("Download failed.")
            
            threading.Thread(target=task, daemon=True).start()

        ctk.CTkButton(frame, text="Download", command=run).pack(pady=20)

    def tool_media_transcribe(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="both", expand=True)

        ctk.CTkLabel(frame, text="Audio/Video Transcription", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        text_box = ctk.CTkTextbox(frame, width=600, height=300)
        text_box.pack(pady=10, padx=20, fill="both", expand=True)

        def run():
            f = filedialog.askopenfilename(filetypes=[("Media Files", "*.mp4;*.mkv;*.avi;*.mp3;*.wav;*.m4a;*.ogg")])
            if not f: return
            
            self.update_status("Transcribing audio... This may take a while depending on file size.")
            text_box.delete("1.0", "end")
            text_box.insert("end", "Transcribing... Please wait.\n")
            
            def task():
                success, text = audio_utils.transcribe_audio(f)
                def update_ui():
                    text_box.delete("1.0", "end")
                    text_box.insert("end", text)
                    if success:
                        self.update_status("Transcription complete.")
                    else:
                        self.update_status("Transcription failed.")
                        messagebox.showerror("Transcription Error", text)
                self.after(0, update_ui)
            
            threading.Thread(target=task, daemon=True).start()

        ctk.CTkButton(frame, text="Select Media & Transcribe", command=run).pack(pady=10)
        
        def save_txt():
            content = text_box.get("1.0", "end-1c")
            if not content or "Transcribing..." in content: return
            path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
            if path:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(content)
                messagebox.showinfo("Saved", "Transcription saved!")
                
        ctk.CTkButton(frame, text="Save Transcript", command=save_txt, fg_color="green", hover_color="darkgreen").pack(pady=10)


if __name__ == "__main__":
    app = PDFStudioApp()
    app.mainloop()


