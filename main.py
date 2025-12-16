import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2 # type: ignore
import numpy as np
from core.wafer_counter import WaferCounter
import os

class WaferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Silicon Wafer Counter - 硅片数片机")
        self.root.geometry("1000x800")
        
        self.counter = WaferCounter()
        self.current_image_path = None
        self.processed_image = None
        
        # UI Components
        self.setup_ui()
        
    def setup_ui(self):
        # Control Panel
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        btn_load = tk.Button(control_frame, text="Load Image (加载图像)", command=self.load_image, width=20)
        btn_load.pack(side=tk.LEFT, padx=20)
        
        btn_process = tk.Button(control_frame, text="Process (开始计数)", command=self.process_image, width=20)
        btn_process.pack(side=tk.LEFT, padx=20)
        
        self.lbl_count = tk.Label(control_frame, text="Count: N/A", font=("Arial", 16, "bold"))
        self.lbl_count.pack(side=tk.RIGHT, padx=50)
        
        # Image Display Area
        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.image_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
    def load_image(self):
        initial_dir = os.path.join(os.getcwd(), "input")
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            self.current_image_path = file_path
            self.show_image(file_path)
            self.lbl_count.config(text="Count: N/A")
            self.processed_image = None
            
    def show_image(self, img_path_or_array):
        # Clear canvas
        self.canvas.delete("all")
        
        if isinstance(img_path_or_array, str):
            # Load from path
            pil_image = Image.open(img_path_or_array)
        else:
            # Load from numpy array (BGR to RGB)
            img_rgb = cv2.cvtColor(img_path_or_array, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_rgb)
            
        # Resize to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            img_ratio = pil_image.width / pil_image.height
            canvas_ratio = canvas_width / canvas_height
            
            if img_ratio > canvas_ratio:
                new_width = canvas_width
                new_height = int(new_width / img_ratio)
            else:
                new_height = canvas_height
                new_width = int(new_height * img_ratio)
                
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        self.tk_image = ImageTk.PhotoImage(pil_image)
        
        # Center image
        x = canvas_width // 2
        y = canvas_height // 2
        self.canvas.create_image(x, y, image=self.tk_image, anchor=tk.CENTER)
        
    def process_image(self):
        if not self.current_image_path:
            messagebox.showwarning("Warning", "Please load an image first.")
            return
            
        try:
            count, result_img, _ = self.counter.process(self.current_image_path)
            self.processed_image = result_img
            self.show_image(result_img)
            self.lbl_count.config(text=f"Count: {count}")
            messagebox.showinfo("Success", f"Detection Complete!\nTotal Wafers: {count}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = WaferApp(root)
    root.mainloop()
