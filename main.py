import tkinter as tk
from ui.app_window import AgrosuperAppUI

def main():
    root = tk.Tk()
    app = AgrosuperAppUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()