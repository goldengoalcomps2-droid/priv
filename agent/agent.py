#!/usr/bin/env python3
"""
Mac Agent — gives Claude eyes and hands on your Mac.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    pip install -r requirements.txt
    python agent.py
"""

import anthropic
import base64
import io
import os
import subprocess
import sys
import time

from PIL import Image

# ---------- config ----------
MODEL = "claude-sonnet-4-20250514"
BETA = "computer-use-2025-01-24"
MAX_SCREENSHOT_W = 1280
MAX_SCREENSHOT_H = 800
SYSTEM = (
    "You are a helpful assistant controlling a macOS computer. "
    "You can see the screen, move the mouse, click, type, press keys, "
    "and run terminal commands. Be direct and efficient."
)


# ---------- screen helpers ----------
def get_retina_scale():
    """Return the Retina scale factor (2 on Retina, 1 otherwise)."""
    try:
        out = subprocess.run(
            ["osascript", "-e",
             'tell application "Finder" to get bounds of window of desktop'],
            capture_output=True, text=True,
        )
        # Fallback: check with system_profiler
        import pyautogui
        logical_w, _ = pyautogui.size()
        # Take a tiny screenshot to measure native resolution
        tmp = "/tmp/_agent_probe.png"
        subprocess.run(["screencapture", "-x", tmp], check=True,
                       capture_output=True)
        img = Image.open(tmp)
        native_w = img.width
        os.remove(tmp)
        return native_w / logical_w
    except Exception:
        return 2.0  # safe default for modern Macs


def take_screenshot():
    """Capture screen, resize for the API, return (b64, w, h)."""
    tmp = "/tmp/_agent_ss.png"
    subprocess.run(["screencapture", "-x", tmp], check=True,
                   capture_output=True)
    img = Image.open(tmp)

    # resize to fit within budget
    ratio = min(MAX_SCREENSHOT_W / img.width, MAX_SCREENSHOT_H / img.height, 1)
    if ratio < 1:
        img = img.resize(
            (int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS
        )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.standard_b64encode(buf.getvalue()).decode(), img.width, img.height


# ---------- action executor ----------
class Executor:
    def __init__(self):
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05
        self.pag = pyautogui

        self.retina = get_retina_scale()
        # Take initial screenshot to learn dimensions
        _, self.img_w, self.img_h = take_screenshot()
        self.logical_w, self.logical_h = self.pag.size()
        self.scale_x = self.logical_w / self.img_w
        self.scale_y = self.logical_h / self.img_h

    def _map(self, coord):
        """Map API coordinates to pyautogui logical coordinates."""
        x, y = coord
        return int(x * self.scale_x), int(y * self.scale_y)

    def run(self, action, **kw):
        if action == "screenshot":
            b64, self.img_w, self.img_h = take_screenshot()
            self.scale_x = self.logical_w / self.img_w
            self.scale_y = self.logical_h / self.img_h
            return b64

        if action == "mouse_move":
            x, y = self._map(kw["coordinate"])
            self.pag.moveTo(x, y)

        elif action == "left_click":
            x, y = self._map(kw["coordinate"])
            self.pag.click(x, y)

        elif action == "right_click":
            x, y = self._map(kw["coordinate"])
            self.pag.rightClick(x, y)

        elif action == "double_click":
            x, y = self._map(kw["coordinate"])
            self.pag.doubleClick(x, y)

        elif action == "triple_click":
            x, y = self._map(kw["coordinate"])
            self.pag.tripleClick(x, y)

        elif action == "middle_click":
            x, y = self._map(kw["coordinate"])
            self.pag.middleClick(x, y)

        elif action == "left_click_drag":
            sx, sy = self._map(kw["start_coordinate"])
            ex, ey = self._map(kw["coordinate"])
            self.pag.moveTo(sx, sy)
            self.pag.mouseDown()
            self.pag.moveTo(ex, ey, duration=0.4)
            self.pag.mouseUp()

        elif action == "type":
            self.pag.write(kw["text"], interval=0.02)

        elif action == "key":
            key_str = kw["key"]
            # Map common names to pyautogui names
            km = {
                "Return": "enter", "Tab": "tab", "Escape": "escape",
                "BackSpace": "backspace", "Delete": "delete", "space": "space",
                "Up": "up", "Down": "down", "Left": "left", "Right": "right",
                "Home": "home", "End": "end", "Page_Up": "pageup",
                "Page_Down": "pagedown", "super": "command",
            }
            parts = key_str.split("+")
            mapped = [km.get(p, p.lower()) for p in parts]
            if len(mapped) == 1:
                self.pag.press(mapped[0])
            else:
                self.pag.hotkey(*mapped)

        elif action == "scroll":
            if "coordinate" in kw:
                x, y = self._map(kw["coordinate"])
                self.pag.moveTo(x, y)
            dx = kw.get("delta_x", 0)
            dy = kw.get("delta_y", 0)
            if dy:
                self.pag.scroll(int(dy))
            if dx:
                self.pag.hscroll(int(dx))

        elif action == "wait":
            time.sleep(kw.get("duration", 1))

        elif action == "cursor_position":
            pos = self.pag.position()
            return f"{int(pos[0] / self.scale_x)},{int(pos[1] / self.scale_y)}"

        return None


def run_bash(command, restart=False):
    """Execute a shell command and return output."""
    try:
        r = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=120
        )
        out = r.stdout + ("\n" + r.stderr if r.stderr else "")
        return out.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out (120s)"
    except Exception as e:
        return f"Error: {e}"


# ---------- agent loop ----------
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first:")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    client = anthropic.Anthropic()
    executor = Executor()

    print(f"Screen: {executor.img_w}x{executor.img_h} "
          f"(logical {executor.logical_w}x{executor.logical_h}, "
          f"retina {executor.retina}x)")
    print("Agent ready. Type your request or 'q' to quit.\n")

    tools = [
        {
            "type": "computer_20250124",
            "name": "computer",
            "display_width_px": executor.img_w,
            "display_height_px": executor.img_h,
            "display_number": 1,
        },
        {
            "type": "bash_20250124",
            "name": "bash",
        },
        {
            "type": "text_editor_20250124",
            "name": "text_editor",
        },
    ]

    messages = []

    while True:
        try:
            user_input = input("\033[1mYou:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not user_input or user_input.lower() in ("q", "quit", "exit"):
            print("Bye!")
            break

        messages.append({"role": "user", "content": user_input})

        # agentic loop — keep going until Claude stops using tools
        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM,
                tools=tools,
                messages=messages,
                betas=[BETA],
            )

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "text":
                    print(f"\n\033[36mAgent:\033[0m {block.text}")

                elif block.type == "tool_use":
                    if block.name == "computer":
                        action = block.input.get("action", "")
                        label = f"  >> computer.{action}"
                        if "coordinate" in block.input:
                            label += f" {block.input['coordinate']}"
                        if "text" in block.input:
                            label += f" \"{block.input['text'][:60]}\""
                        if "key" in block.input:
                            label += f" [{block.input['key']}]"
                        print(label)

                        result = executor.run(**block.input)

                        if action == "screenshot" and result:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": [{"type": "image", "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": result,
                                }}],
                            })
                        elif action == "cursor_position" and result:
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            })
                        else:
                            # after any action, give Claude a fresh screenshot
                            time.sleep(0.3)
                            ss, executor.img_w, executor.img_h = take_screenshot()
                            executor.scale_x = executor.logical_w / executor.img_w
                            executor.scale_y = executor.logical_h / executor.img_h
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": [{"type": "image", "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": ss,
                                }}],
                            })

                    elif block.name == "bash":
                        cmd = block.input.get("command", "")
                        print(f"  >> $ {cmd}")
                        output = run_bash(cmd, block.input.get("restart", False))
                        print(f"     {output[:200]}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output,
                        })

                    elif block.name == "text_editor":
                        # text_editor tool — handle file operations
                        te_cmd = block.input.get("command")
                        path = block.input.get("path", "")
                        print(f"  >> editor.{te_cmd} {path}")

                        if te_cmd == "view":
                            try:
                                with open(path) as f:
                                    lines = f.readlines()
                                vr = block.input.get("view_range")
                                if vr:
                                    start, end = vr
                                    lines = lines[start - 1:end]
                                    start_n = start
                                else:
                                    start_n = 1
                                numbered = "".join(
                                    f"{i}: {l}"
                                    for i, l in enumerate(lines, start_n)
                                )
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": numbered or "(empty file)",
                                })
                            except Exception as e:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Error: {e}",
                                    "is_error": True,
                                })

                        elif te_cmd == "create":
                            try:
                                os.makedirs(os.path.dirname(path), exist_ok=True)
                                with open(path, "w") as f:
                                    f.write(block.input.get("file_text", ""))
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Created {path}",
                                })
                            except Exception as e:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Error: {e}",
                                    "is_error": True,
                                })

                        elif te_cmd == "str_replace":
                            try:
                                with open(path) as f:
                                    content = f.read()
                                old = block.input["old_str"]
                                new = block.input.get("new_str", "")
                                if old not in content:
                                    raise ValueError("old_str not found in file")
                                content = content.replace(old, new, 1)
                                with open(path, "w") as f:
                                    f.write(content)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Replaced in {path}",
                                })
                            except Exception as e:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Error: {e}",
                                    "is_error": True,
                                })

                        elif te_cmd == "insert":
                            try:
                                with open(path) as f:
                                    lines = f.readlines()
                                line_n = block.input["insert_line"]
                                new_text = block.input["new_str"]
                                lines.insert(line_n, new_text + "\n")
                                with open(path, "w") as f:
                                    f.writelines(lines)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Inserted at line {line_n} in {path}",
                                })
                            except Exception as e:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": f"Error: {e}",
                                    "is_error": True,
                                })

                        elif te_cmd == "undo_edit":
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": "Undo not supported — use str_replace to revert.",
                                "is_error": True,
                            })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            if response.stop_reason == "end_turn" or not tool_results:
                break

        print()


if __name__ == "__main__":
    main()
