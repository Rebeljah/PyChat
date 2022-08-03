import tkinter as tk


class Room(tk.Frame):
    def __init__(self, master, id: str, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.id = id

        self.chat_panel = self.ChatPanel(self)

        self.arrange()
    
    def arrange(self):
        self.chat_panel.pack()

    class ChatPanel(tk.Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.text_frame = self.TextFrame(self)
            self.message_entry = self.MessageEntry(self)

            self.arrange()
        
        def arrange(self):
            self.text_frame.pack(side=tk.TOP)
            self.message_entry.pack(side=tk.TOP)

        class TextFrame(tk.Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

            class Message(tk.Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

        class MessageEntry(tk.Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                
                self.text = tk.StringVar()
                self.entry = tk.Entry(self, textvariable=self.text)
                self.button = tk.Button(self, text='Send')

                self.arrange()
            
            def arrange(self):
                self.entry.pack(side=tk.LEFT)
                self.button.pack(side=tk.LEFT)

    
    class UsersPanel(tk.Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)