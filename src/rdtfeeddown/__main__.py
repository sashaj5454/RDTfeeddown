import tkinter as tk
from .gui import RDTFeeddownGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = RDTFeeddownGUI(root)
    root.mainloop()
