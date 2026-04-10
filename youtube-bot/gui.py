"""YouTube Bot — Graphical User Interface.

A simple Tkinter GUI for the YouTube automation bot. Provides:
  - Quick action buttons (Visit YouTube, Search, Watch, Like, etc.)
  - A script editor where you can build a list of commands
  - A live log panel showing what the bot is doing
  - File loading and saving for instruction scripts

Run with:
    python3 gui.py
"""

import asyncio
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

from bot_controller import BotController
from instructions import parse_instruction, parse_instructions


# ── A queue-based stdout redirector so we can capture print() into the GUI ──
class QueueStream:
    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text:
            self.q.put(text)

    def flush(self):
        pass


class YouTubeBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Bot — Control Panel")
        self.root.geometry("960x720")
        self.root.minsize(800, 600)

        # State
        self.controller: BotController | None = None
        self.bot_thread: threading.Thread | None = None
        self.bot_loop: asyncio.AbstractEventLoop | None = None
        self.log_queue: queue.Queue = queue.Queue()
        self.is_running = False
        self.browser_choice = tk.StringVar(value="chromium")

        self._build_ui()
        self._start_log_pump()

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar — title and browser picker
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        title = ttk.Label(top, text="YouTube Automation Bot", font=("Helvetica", 18, "bold"))
        title.pack(side="left")

        browser_frame = ttk.Frame(top)
        browser_frame.pack(side="right")
        ttk.Label(browser_frame, text="Browser:").pack(side="left", padx=(0, 5))
        browser_combo = ttk.Combobox(
            browser_frame,
            textvariable=self.browser_choice,
            values=["chromium", "firefox", "webkit"],
            state="readonly",
            width=10,
        )
        browser_combo.pack(side="left")

        # Main split: left = controls, right = log
        main = ttk.PanedWindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # ── LEFT PANEL: Quick actions and script editor ───────────────────
        left = ttk.Frame(main, padding=5)
        main.add(left, weight=1)

        # Quick actions section
        actions_label = ttk.Label(left, text="Quick Actions", font=("Helvetica", 12, "bold"))
        actions_label.pack(anchor="w", pady=(0, 5))

        actions_frame = ttk.LabelFrame(left, text="Click to add to script", padding=8)
        actions_frame.pack(fill="x", pady=(0, 10))

        # Row 1: Navigation
        row1 = ttk.Frame(actions_frame)
        row1.pack(fill="x", pady=2)
        ttk.Button(row1, text="Visit YouTube", command=self._add_visit_youtube, width=18).pack(side="left", padx=2)
        ttk.Button(row1, text="Go to Videos Tab", command=self._add_go_to_videos, width=18).pack(side="left", padx=2)

        # Row 2: Search and channel
        row2 = ttk.Frame(actions_frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="Search:").pack(side="left", padx=2)
        self.search_entry = ttk.Entry(row2, width=25)
        self.search_entry.pack(side="left", padx=2)
        ttk.Button(row2, text="Add Search", command=self._add_search).pack(side="left", padx=2)

        row3 = ttk.Frame(actions_frame)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="Channel:").pack(side="left", padx=2)
        self.channel_entry = ttk.Entry(row3, width=25)
        self.channel_entry.pack(side="left", padx=2)
        ttk.Button(row3, text="Click Channel", command=self._add_click_channel).pack(side="left", padx=2)

        # Row 4: Watch settings
        watch_frame = ttk.LabelFrame(actions_frame, text="Watch Videos", padding=5)
        watch_frame.pack(fill="x", pady=5)

        wrow1 = ttk.Frame(watch_frame)
        wrow1.pack(fill="x", pady=2)
        ttk.Label(wrow1, text="How many:").pack(side="left", padx=2)
        self.video_count = tk.IntVar(value=20)
        ttk.Spinbox(wrow1, from_=1, to=20, textvariable=self.video_count, width=5).pack(side="left", padx=2)
        ttk.Label(wrow1, text="Duration:").pack(side="left", padx=(10, 2))
        self.duration_entry = ttk.Entry(wrow1, width=8)
        self.duration_entry.insert(0, "1m30s")
        self.duration_entry.pack(side="left", padx=2)

        wrow2 = ttk.Frame(watch_frame)
        wrow2.pack(fill="x", pady=2)
        self.like_var = tk.BooleanVar(value=False)
        self.comments_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(wrow2, text="Like each video", variable=self.like_var).pack(side="left", padx=5)
        ttk.Checkbutton(wrow2, text="Read comments", variable=self.comments_var).pack(side="left", padx=5)

        ttk.Button(watch_frame, text="Add Watch Command", command=self._add_watch).pack(pady=3)

        # Row 5: Single video actions
        single_frame = ttk.LabelFrame(actions_frame, text="Current Video Actions", padding=5)
        single_frame.pack(fill="x", pady=5)
        srow = ttk.Frame(single_frame)
        srow.pack(fill="x")
        ttk.Button(srow, text="Like Video", command=self._add_like, width=14).pack(side="left", padx=2)
        ttk.Button(srow, text="Read Comments", command=self._add_read_comments, width=14).pack(side="left", padx=2)
        ttk.Button(srow, text="Subscribe", command=self._add_subscribe, width=14).pack(side="left", padx=2)

        # Script editor section
        script_label = ttk.Label(left, text="Instruction Script", font=("Helvetica", 12, "bold"))
        script_label.pack(anchor="w", pady=(5, 5))

        self.script_text = scrolledtext.ScrolledText(left, height=12, font=("Menlo", 11), wrap="word")
        self.script_text.pack(fill="both", expand=True)

        # Pre-fill with example
        self.script_text.insert(
            "1.0",
            "# Example: search for a channel and watch 20 videos\n"
            "visit www.youtube.com\n"
            "search mind and motivation\n"
            "click_channel\n"
            "go_to_videos\n"
            "watch 20 duration=1m30s\n"
        )

        # Bottom button bar
        button_bar = ttk.Frame(left)
        button_bar.pack(fill="x", pady=8)

        self.run_btn = ttk.Button(
            button_bar, text="▶ Run Script", command=self._run_script, width=14
        )
        self.run_btn.pack(side="left", padx=2)

        self.stop_btn = ttk.Button(
            button_bar, text="■ Stop Bot", command=self._stop_bot, width=12, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=2)

        ttk.Button(button_bar, text="Clear Script", command=self._clear_script, width=12).pack(side="left", padx=2)
        ttk.Button(button_bar, text="Load File", command=self._load_file, width=10).pack(side="left", padx=2)
        ttk.Button(button_bar, text="Save File", command=self._save_file, width=10).pack(side="left", padx=2)

        # ── RIGHT PANEL: Activity log ─────────────────────────────────────
        right = ttk.Frame(main, padding=5)
        main.add(right, weight=1)

        log_label = ttk.Label(right, text="Activity Log", font=("Helvetica", 12, "bold"))
        log_label.pack(anchor="w", pady=(0, 5))

        self.log_text = scrolledtext.ScrolledText(
            right,
            font=("Menlo", 10),
            wrap="word",
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff",
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("info", foreground="#9cdcfe")
        self.log_text.tag_config("success", foreground="#6a9955")
        self.log_text.tag_config("error", foreground="#f44747")

        log_buttons = ttk.Frame(right)
        log_buttons.pack(fill="x", pady=5)
        ttk.Button(log_buttons, text="Clear Log", command=self._clear_log).pack(side="left", padx=2)

        # Status bar
        self.status = tk.StringVar(value="Ready — build a script and click Run")
        status_bar = ttk.Label(self.root, textvariable=self.status, relief="sunken", anchor="w", padding=5)
        status_bar.pack(side="bottom", fill="x")

    # ── Quick action handlers ──────────────────────────────────────────────

    def _append_command(self, command: str):
        """Add a command line to the script editor."""
        current = self.script_text.get("1.0", "end-1c")
        if current and not current.endswith("\n"):
            self.script_text.insert("end", "\n")
        self.script_text.insert("end", command + "\n")
        self.script_text.see("end")

    def _add_visit_youtube(self):
        self._append_command("visit www.youtube.com")

    def _add_search(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Missing input", "Please enter a search query.")
            return
        self._append_command(f"search {query}")

    def _add_click_channel(self):
        name = self.channel_entry.get().strip()
        if name:
            self._append_command(f"click_channel {name}")
        else:
            self._append_command("click_channel")

    def _add_go_to_videos(self):
        self._append_command("go_to_videos")

    def _add_watch(self):
        count = self.video_count.get()
        duration = self.duration_entry.get().strip() or "1m30s"
        cmd = f"watch {count} duration={duration}"
        if self.like_var.get():
            cmd += " like"
        if self.comments_var.get():
            cmd += " comments"
        self._append_command(cmd)

    def _add_like(self):
        self._append_command("like")

    def _add_read_comments(self):
        self._append_command("read_comments 10")

    def _add_subscribe(self):
        self._append_command("subscribe")

    def _clear_script(self):
        self.script_text.delete("1.0", "end")

    def _clear_log(self):
        self.log_text.delete("1.0", "end")

    def _load_file(self):
        path = filedialog.askopenfilename(
            title="Load Instruction Script",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            try:
                with open(path) as f:
                    content = f.read()
                self.script_text.delete("1.0", "end")
                self.script_text.insert("1.0", content)
                self.status.set(f"Loaded: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Load failed", str(e))

    def _save_file(self):
        path = filedialog.asksaveasfilename(
            title="Save Instruction Script",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            try:
                with open(path, "w") as f:
                    f.write(self.script_text.get("1.0", "end-1c"))
                self.status.set(f"Saved: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Save failed", str(e))

    # ── Bot execution (runs in background thread) ──────────────────────────

    def _run_script(self):
        if self.is_running:
            messagebox.showinfo("Already running", "The bot is already running. Stop it first.")
            return

        script = self.script_text.get("1.0", "end-1c").strip()
        if not script:
            messagebox.showwarning("Empty script", "Add some instructions first.")
            return

        instructions = parse_instructions(script)
        if not instructions:
            messagebox.showwarning("No valid instructions", "Couldn't parse any commands from the script.")
            return

        self.is_running = True
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.set(f"Running {len(instructions)} instructions...")

        # Run the bot in a background thread with its own asyncio loop
        self.bot_thread = threading.Thread(
            target=self._run_bot_thread,
            args=(instructions, self.browser_choice.get()),
            daemon=True,
        )
        self.bot_thread.start()

    def _run_bot_thread(self, instructions, browser):
        """Worker thread that owns its own asyncio loop."""
        # Redirect stdout into the GUI log
        old_stdout = sys.stdout
        sys.stdout = QueueStream(self.log_queue)

        try:
            self.bot_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.bot_loop)
            self.controller = BotController(browser_type=browser)
            self.bot_loop.run_until_complete(self._run_async(instructions))
        except Exception as e:
            self.log_queue.put(f"\n[ERROR] {e}\n")
        finally:
            sys.stdout = old_stdout
            self.is_running = False
            self.root.after(0, self._on_bot_finished)

    async def _run_async(self, instructions):
        try:
            await self.controller.start()
            await self.controller.run(instructions)
        finally:
            try:
                await self.controller.stop()
            except Exception:
                pass

    def _on_bot_finished(self):
        self.run_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.set("Done — ready for next run")

    def _stop_bot(self):
        if not self.is_running:
            return
        self.log_queue.put("\n[GUI] Stopping bot...\n")
        self.status.set("Stopping...")
        # Schedule shutdown on the bot's event loop
        if self.bot_loop and self.controller:
            try:
                asyncio.run_coroutine_threadsafe(self.controller.stop(), self.bot_loop)
            except Exception as e:
                self.log_queue.put(f"[GUI] Stop error: {e}\n")

    # ── Log pump (drains the queue into the GUI text widget) ───────────────

    def _start_log_pump(self):
        try:
            while True:
                text = self.log_queue.get_nowait()
                self._append_log(text)
        except queue.Empty:
            pass
        self.root.after(80, self._start_log_pump)

    def _append_log(self, text: str):
        # Color-code by content
        tag = ""
        if "ERROR" in text or "Could not" in text or "Failed" in text:
            tag = "error"
        elif "✓" in text or "complete" in text.lower() or "Finished" in text:
            tag = "success"
        elif "[" in text:
            tag = "info"

        self.log_text.insert("end", text, tag)
        self.log_text.see("end")


def main():
    root = tk.Tk()

    # Use a nicer theme on macOS/Linux
    style = ttk.Style()
    try:
        if sys.platform == "darwin":
            style.theme_use("aqua")
        else:
            style.theme_use("clam")
    except Exception:
        pass

    app = YouTubeBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
