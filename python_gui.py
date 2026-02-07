import tkinter as tk
from tkinter import font
import datetime

class RetroTodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Retro To-Do List")
        self.configure(bg='#cccccc')
        # Pixel font (install or place Press Start 2P in working dir)
        self.pixel_font = font.Font(family='Press Start 2P', size=10)
        
        self.create_date_section()
        self.create_progress_section()
        self.create_input_section()
        self.create_tasks_section()

        # Seed tasks
        self.tasks = []
        for text, done in [
            ("grocery", True),
            ("laundry", True),
            ("makeup", False),
        ]:
            self.add_task(text, done)
        self.update_progress()

    def create_date_section(self):
        date_str = datetime.datetime.now().strftime("%A %d %B")
        frame = tk.Frame(self, bg='#00cc00')
        frame.pack(fill='x', padx=10, pady=5)
        tk.Label(
            frame,
            text=date_str,
            bg='#00cc00',
            fg='#000000',
            font=self.pixel_font
        ).pack(padx=5, pady=5)

    def create_progress_section(self):
        self.prog_frame = tk.Frame(self, bg=self['bg'])
        self.prog_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(
            self.prog_frame,
            text="Progress:",
            fg='#ff66cc',
            bg=self['bg'],
            font=self.pixel_font
        ).pack(side='left')

        self.prog_canvas = tk.Canvas(
            self.prog_frame,
            width=200,
            height=20,
            bg='#ffffff',
            highlightthickness=2,
            highlightbackground='#ff66cc'
        )
        self.prog_canvas.pack(side='left', padx=5)
        self.prog_text = self.prog_canvas.create_text(
            100, 10,
            text='',
            font=self.pixel_font
        )

    def update_progress(self):
        done = sum(1 for t in self.tasks if t['done'])
        total = len(self.tasks)
        self.prog_canvas.delete('bar')

        if total > 0:
            ratio = done / total
            fill_w = int(ratio * (200 - 2))
            self.prog_canvas.create_rectangle(
                1, 1, 1 + fill_w, 19,
                fill='#ff66cc', width=0, tags='bar'
            )

        self.prog_canvas.itemconfig(
            self.prog_text,
            text=f"{done} / {total} tasks done"
        )

    def create_input_section(self):
        frame = tk.Frame(self, bg=self['bg'])
        frame.pack(fill='x', padx=10, pady=5)

        self.entry = tk.Entry(
            frame,
            font=self.pixel_font,
            fg='#888888',
            bg='#ffffff',
            insertbackground='#000000',
            bd=2,
            relief='solid',
            highlightthickness=0
        )
        self.entry.insert(0, "Input your task!")
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._add_placeholder)
        self.entry.pack(side='left', fill='x', expand=True)

        tk.Button(
            frame,
            text="Add Task",
            bg='#ff66cc',
            fg='#ffffff',
            activebackground='#ff66cc',
            activeforeground='#ffffff',
            highlightthickness=0,
            font=self.pixel_font,
            bd=0,
            command=self.on_add_task
        ).pack(side='left', padx=5)

    def _clear_placeholder(self, event):
        if self.entry.get() == "Input your task!":
            self.entry.delete(0, 'end')
            self.entry.config(fg='#000000')

    def _add_placeholder(self, event):
        if not self.entry.get():
            self.entry.insert(0, "Input your task!")
            self.entry.config(fg='#888888')

    def on_add_task(self):
        text = self.entry.get().strip()
        if text and text != "Input your task!":
            self.add_task(text, done=False)
            self.entry.delete(0, 'end')
            self.update_progress()

    def create_tasks_section(self):
        frame = tk.Frame(self, bg=self['bg'])
        frame.pack(fill='both', padx=10, pady=5)
        tk.Label(
            frame,
            text="My Tasks:",
            fg='#ff66cc',
            bg=self['bg'],
            font=self.pixel_font
        ).pack(anchor='w')
        self.tasks_container = tk.Frame(frame, bg=self['bg'])
        self.tasks_container.pack(fill='both')

    def add_task(self, text, done=False):
        row = tk.Frame(
            self.tasks_container,
            bg='#ffffff',
            bd=1,
            relief='solid'
        )
        row.pack(fill='x', pady=2)

        box = tk.Canvas(
            row,
            width=20,
            height=20,
            bg='#ffffff',
            highlightthickness=1,
            highlightbackground='#000000'
        )
        box.pack(side='left', padx=5, pady=5)
        box.bind("<Button-1>", lambda e, b=box: self.toggle_task(b))

        tk.Label(
            row,
            text=text,
            bg='#ffffff',
            fg='#000000',
            font=self.pixel_font
        ).pack(side='left', padx=5)

        tk.Button(
            row,
            text="X",
            bg='#ff0000',
            fg='#ffffff',
            activebackground='#ff0000',
            activeforeground='#ffffff',
            highlightthickness=0,
            font=self.pixel_font,
            bd=0,
            command=lambda r=row: self.delete_task(r)
        ).pack(side='right', padx=5)

        self.tasks.append({
            'frame': row,
            'canvas': box,
            'done': done
        })
        self._draw_checkbox(box, done)

    def _draw_checkbox(self, canvas, done):
        canvas.delete('mark')
        if done:
            canvas.create_line(3, 10, 8, 15, fill='#000000', width=2, tags='mark')
            canvas.create_line(8, 15, 17, 5, fill='#000000', width=2, tags='mark')

    def toggle_task(self, canvas):
        for t in self.tasks:
            if t['canvas'] == canvas:
                t['done'] = not t['done']
                self._draw_checkbox(canvas, t['done'])
                break
        self.update_progress()

    def delete_task(self, row):
        for t in self.tasks:
            if t['frame'] == row:
                t['frame'].destroy()
                self.tasks.remove(t)
                break
        self.update_progress()


if __name__ == "__main__":
    app = RetroTodoApp()
    app.mainloop()
