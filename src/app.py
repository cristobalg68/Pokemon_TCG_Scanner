import tkinter as tk
from tkinter import filedialog, messagebox

from scanner import ImageScanner, VideoScanner, LiveScanner

path_weights = "weights/best_1.pt"
path_df = "D:/Proyectos/Pokemon_TCG_Scanner/datasets/cards_of_pokemon.xlsx"
hash_size = 16
size = 640
confidence = 0.9
iou = 0.8

FONT = ("Arial", 12)

ext_file = {
    "1":("Image File", r"*.png *.jpg *.jpge"),
    "2":("Video File", r"*.mp4 *.avi *.mov")
            }

default_file_ext = {
    "1": ".png",
    "2": ".avi",
    "3": ".avi"
}

class GUI:
    def __init__(self, root):
        self.root = root
        root.title("Select the mode of use")
        root.geometry("500x400")

        self.mode = tk.StringVar(value="1")
        self.input_file_ext = ext_file[self.mode.get()]
        self.file = None
        self.save = tk.BooleanVar()
        self.path_save = tk.StringVar()

        self.live_source = tk.StringVar(value="pc")
        self.ip_entry_var = tk.StringVar()

        self.elements = []
        self.video_label = None
        self.video_running = False

        self.result_frame = tk.Frame(self.root)

        self.build_ui()

    def create_element(self, widget, **pack_args):
        widget.pack(**pack_args)
        self.elements.append(widget)

    def build_ui(self):
        self.create_element(tk.Label(self.root, text="Select the mode of use:", font=FONT))

        modes_name = ['Image', 'Video', 'Live']
        for i in range(3):
            rb = tk.Radiobutton(self.root, text=modes_name[i], variable=self.mode, value=str(i+1), command=self.update_ui, font=FONT)
            self.create_element(rb)

        self.button_file = tk.Button(self.root, text="Select file", command=self.select_file, font=FONT)
        self.create_element(self.button_file)

        self.check_save = tk.Checkbutton(self.root, text="Save result", variable=self.save, command=self.toggle_save, font=FONT)
        self.create_element(self.check_save)

        self.button_save = tk.Button(self.root, text="Select folder", command=self.select_save, font=FONT)
        self.create_element(self.button_save)
        self.button_save.config(state=tk.DISABLED)

        self.label_save = tk.Label(self.root, textvariable=self.path_save, font=FONT)
        self.create_element(self.label_save)

        self.label_mode3 = tk.Label(self.root, text="Options for Mode Live:", font=FONT)
        self.rb_pc = tk.Radiobutton(self.root, text="Use PC camera", variable=self.live_source, value="pc", command=self.update_ui, font=FONT)
        self.rb_ip = tk.Radiobutton(self.root, text="Use IP camera", variable=self.live_source, value="ip", command=self.update_ui, font=FONT)
        self.entry_ip = tk.Entry(self.root, textvariable=self.ip_entry_var, font=FONT)

        self.button_execute = tk.Button(self.root, text="Execute", command=self.execute, font=FONT)
        self.create_element(self.button_execute)

        self.update_ui()

    def update_ui(self):
        mode = self.mode.get()
        if mode in ["1", "2"]:
            self.input_file_ext = ext_file[mode]
            self.button_file.config(state=tk.NORMAL)
            self.hide_mode3_options()
        else:
            self.button_file.config(state=tk.DISABLED)
            self.show_mode3_options()

        if self.live_source.get() == "ip":
            self.entry_ip.config(state=tk.NORMAL)
        else:
            self.entry_ip.config(state=tk.DISABLED)

    def show_mode3_options(self):
        self.label_mode3.pack(before=self.button_execute)
        self.rb_pc.pack(before=self.button_execute)
        self.rb_ip.pack(before=self.button_execute)
        self.entry_ip.pack(before=self.button_execute)

    def hide_mode3_options(self):
        self.label_mode3.pack_forget()
        self.rb_pc.pack_forget()
        self.rb_ip.pack_forget()
        self.entry_ip.pack_forget()

    def select_file(self):
        file = filedialog.askopenfilename(title="Select file", filetypes=[self.input_file_ext])
        if file:
            self.file = file

    def toggle_save(self):
        if not self.save.get():
            self.path_save.set("")
            self.button_save.config(state=tk.DISABLED)
        else:
            self.button_save.config(state=tk.NORMAL)

    def select_save(self):
        if self.save.get():
            folder = filedialog.askdirectory(title="Select folder")
            if folder:
                name = folder + "/result" + default_file_ext[self.mode.get()]
                self.path_save.set(name)

    def clear_window(self):
        for element in self.elements:
            element.destroy()
        self.elements = []
        for widget in self.result_frame.winfo_children():
            widget.destroy()

    def execute(self):
        mode = self.mode.get()
        save = self.save.get()
        path = self.path_save.get()

        if mode in ["1", "2"] and not self.file:
            messagebox.showerror("Error", "You must select a file for this mode.")
            return
        if save and not path:
            messagebox.showerror("Error", "You must select a path to save the result.")
            return

        if mode == "1":
            scanner = ImageScanner(path_weights, size, confidence, iou, hash_size, path_df, save, path)
            source = self.file
        elif mode == "2":
            scanner = VideoScanner(path_weights, size, confidence, iou, hash_size, path_df, save, path)
            source = self.file
        else:
            source = self.live_source.get()
            ip = self.ip_entry_var.get()

            if source not in ["ip", "pc"]:
                messagebox.showerror("Error", "You must select one video source for Mode 3.")
                return
            if source == "ip" and not ip:
                messagebox.showerror("Error", "You must enter the IP address of the camera.")
                return

            scanner = LiveScanner(path_weights, size, confidence, iou, hash_size, path_df, save, path)
            source = ip if source == "ip" else '0'

        self.clear_window()
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        scanner.run(source, self.result_frame)

if __name__ == "__main__":
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()


# 'C:/Users/Cristobal/Desktop/test.jpg' / '' / 'http://192.168.1.11:4747/video'