import tkinter as tk
from tkinter import ttk
import asyncio

from common.events import GuiSentMessage
from client import events

FRAME_RATE = 24


class MessagesBox(tk.Listbox):
    def __init__(self, master):
        super().__init__(master)


class MessageEntry(tk.Entry):
    def __init__(self, master):
        super().__init__(master)


class GUIContent(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.message_box = MessagesBox(self)
        self.message_box.pack()

        self.message_entry = MessageEntry(self)
        self.message_entry.pack()

        self.send_message_btn = tk.Button(
            self, text='Send',
            command=lambda: events.publish(
                GuiSentMessage(self.message_entry.get())
            ))
        self.send_message_btn.pack()


class GUIRoot(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('PyChat')

        self.content = GUIContent(self)
        self.content.pack()

    async def loop(self):
        while True:
            self.update()
            await asyncio.sleep(1 / FRAME_RATE)
