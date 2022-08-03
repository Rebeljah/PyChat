import tkinter as tk
import asyncio

from .room import Room


class GUIRoot(tk.Tk):
    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_running_loop()
        self.closed = asyncio.Event()

        self.title('PyChat')
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.mainloop()
    
    def mainloop(self):
        self.update()
        self.loop.call_soon(self.mainloop)

    def close(self):
        self.closed.set()