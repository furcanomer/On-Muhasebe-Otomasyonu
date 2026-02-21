
import customtkinter as ctk
from tkinter import messagebox

class CalculatorView(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Hesap Makinesi")
        self.geometry("320x500")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        self.expression = ""
        self.history = ""

        # UI
        self.history_label = ctk.CTkLabel(self, text="", font=("Arial", 12), anchor="e", text_color="gray")
        self.history_label.pack(fill="x", padx=10, pady=(10, 0))

        self.display = ctk.CTkEntry(self, font=("Arial", 24, "bold"), justify="right", height=50)
        self.display.pack(fill="x", padx=10, pady=10)
        self.display.insert(0, "0")

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="both", expand=True, padx=10, pady=10)

        buttons = [
            'C', 'CE', '%', '/',
            '7', '8', '9', '*',
            '4', '5', '6', '-',
            '1', '2', '3', '+',
            '0', '.', '=', ''
        ]

        # Grid config
        for i in range(4):
            self.btn_frame.grid_columnconfigure(i, weight=1)
        for i in range(5):
            self.btn_frame.grid_rowconfigure(i, weight=1)

        row = 0
        col = 0
        for button in buttons:
            if not button: continue
            cmd = lambda x=button: self.on_button_click(x)
            btn = ctk.CTkButton(self.btn_frame, text=button, command=cmd, 
                               width=60, height=60, font=("Arial", 18))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            if button == '=':
                btn.configure(fg_color="#2ecc71", hover_color="#27ae60")
            elif button in ['C', 'CE']:
                btn.configure(fg_color="#e74c3c", hover_color="#c0392b")

            col += 1
            if col > 3:
                col = 0
                row += 1

        # Keyboard support
        self.bind("<Key>", self.on_key_press)

    def on_button_click(self, char):
        if char == '=':
            self.calculate()
        elif char == 'C':
            self.expression = ""
            self.history = ""
            self.update_display("0")
        elif char == 'CE':
            self.expression = ""
            self.update_display("0")
        else:
            if self.expression == "0" and char.isdigit():
                self.expression = char
            else:
                self.expression += str(char)
            self.update_display(self.expression)

    def on_key_press(self, event):
        key = event.char
        if key.isdigit() or key in ['+', '-', '*', '/', '.', '%']:
            self.on_button_click(key)
        elif event.keysym == 'Return':
            self.calculate()
        elif event.keysym == 'BackSpace':
            self.expression = self.expression[:-1]
            self.update_display(self.expression if self.expression else "0")
        elif event.keysym == 'Escape':
            self.destroy()

    def calculate(self):
        try:
            res = str(eval(self.expression.replace('%', '/100')))
            self.history = self.expression + " ="
            self.history_label.configure(text=self.history)
            self.expression = res
            self.update_display(res)
        except Exception:
            messagebox.showerror("Hata", "Geçersiz işlem")
            self.expression = ""
            self.update_display("0")

    def update_display(self, text):
        self.display.delete(0, "end")
        self.display.insert(0, text)
