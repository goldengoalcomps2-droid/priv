#!/usr/bin/env python3
"""
Web UI for the Mac Agent.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 server.py

Then open http://127.0.0.1:5050 in your browser (it opens automatically).
"""

import json
import os
import sys
import time
import webbrowser
from threading import Lock

import anthropic
from flask import Flask, Response, request

from agent import Executor, run_bash, take_screenshot, MODEL, BETA, SYSTEM

app = Flask(__name__)

# ----- global agent state (single session) -----
_client = None
_executor = None
_messages = []
_lock = Lock()


def init():
    global _client, _executor
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.")
        print("  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)
    _client = anthropic.Anthropic()
    _executor = Executor()


# ----- HTML (single-page chat UI) -----
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mac Agent</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    background: #0d0d0d;
    color: #e4e4e4;
    display: flex;
    flex-direction: column;
  }
  header {
    padding: 14px 24px;
    border-bottom: 1px solid #1f1f1f;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }
  header h1 {
    font-size: 15px;
    font-weight: 600;
    letter-spacing: -0.01em;
  }
  .status {
    font-size: 12px;
    color: #666;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #4ade80;
  }
  .status.busy .dot { background: #fbbf24; animation: pulse 1.2s ease-in-out infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
  .clear-btn {
    background: transparent;
    border: 1px solid #333;
    color: #888;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
  }
  .clear-btn:hover { background: #1a1a1a; color: #e4e4e4; }
  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
  }
  .chat-inner {
    max-width: 860px;
    margin: 0 auto;
  }
  .msg {
    margin: 14px 0;
    padding: 12px 16px;
    border-radius: 14px;
    line-height: 1.55;
    word-wrap: break-word;
    white-space: pre-wrap;
    font-size: 14px;
  }
  .user {
    background: #2563eb;
    color: #fff;
    margin-left: auto;
    max-width: 72%;
    width: fit-content;
    border-bottom-right-radius: 4px;
  }
  .assistant {
    background: #1a1a1a;
    max-width: 82%;
    width: fit-content;
    border-bottom-left-radius: 4px;
  }
  .action {
    font-family: "SF Mono", Monaco, Consolas, monospace;
    font-size: 12px;
    color: #888;
    padding: 3px 16px;
    margin: 1px 0 1px 8px;
    border-left: 2px solid #2a2a2a;
  }
  .action .name { color: #fbbf24; margin-right: 6px; }
  .action .detail { color: #666; }
  .placeholder {
    text-align: center;
    color: #555;
    padding: 80px 20px;
    font-size: 14px;
  }
  .placeholder h2 { font-size: 20px; margin-bottom: 8px; color: #888; font-weight: 500; }
  .placeholder p { margin: 4px 0; }
  .placeholder .examples {
    margin-top: 24px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    align-items: center;
  }
  .placeholder .example {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    padding: 8px 14px;
    border-radius: 8px;
    cursor: pointer;
    color: #aaa;
    transition: all 0.15s;
    font-size: 13px;
  }
  .placeholder .example:hover { background: #222; border-color: #444; color: #e4e4e4; }
  footer {
    padding: 16px 24px 20px;
    border-top: 1px solid #1f1f1f;
    flex-shrink: 0;
  }
  .input-wrap {
    max-width: 860px;
    margin: 0 auto;
    position: relative;
  }
  #input {
    width: 100%;
    padding: 14px 48px 14px 18px;
    font-size: 14px;
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    color: #e4e4e4;
    border-radius: 14px;
    outline: none;
    font-family: inherit;
    resize: none;
    min-height: 48px;
    max-height: 200px;
  }
  #input:focus { border-color: #2563eb; }
  #input:disabled { opacity: 0.6; cursor: not-allowed; }
  .send-btn {
    position: absolute;
    right: 8px;
    bottom: 8px;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #2563eb;
    border: none;
    color: #fff;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
  }
  .send-btn:disabled { background: #333; cursor: not-allowed; }
  .send-btn:hover:not(:disabled) { background: #1d4ed8; }
  #chat::-webkit-scrollbar { width: 10px; }
  #chat::-webkit-scrollbar-track { background: #0d0d0d; }
  #chat::-webkit-scrollbar-thumb { background: #222; border-radius: 5px; }
</style>
</head>
<body>

<header>
  <h1>Mac Agent</h1>
  <div style="display: flex; gap: 12px; align-items: center;">
    <button class="clear-btn" onclick="clearChat()">New chat</button>
    <div class="status" id="status"><div class="dot"></div><span>Ready</span></div>
  </div>
</header>

<div id="chat">
  <div class="chat-inner" id="chatInner">
    <div class="placeholder" id="placeholder">
      <h2>What can I do for you?</h2>
      <p>I can see your screen, click, type, and run commands.</p>
      <div class="examples">
        <div class="example" onclick="useExample(this)">Open Safari and go to anthropic.com</div>
        <div class="example" onclick="useExample(this)">Take a screenshot and tell me what apps are open</div>
        <div class="example" onclick="useExample(this)">Open Blender and create a default cube</div>
        <div class="example" onclick="useExample(this)">Find all PDF files in my Downloads folder</div>
      </div>
    </div>
  </div>
</div>

<footer>
  <div class="input-wrap">
    <textarea id="input" rows="1" placeholder="Tell the agent what to do..." autofocus></textarea>
    <button class="send-btn" id="sendBtn" onclick="send()">↑</button>
  </div>
</footer>

<script>
const chatInner = document.getElementById('chatInner');
const input = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');
const status = document.getElementById('status');
const placeholder = document.getElementById('placeholder');

function removePlaceholder() {
  if (placeholder && placeholder.parentNode) placeholder.remove();
}

function useExample(el) {
  input.value = el.textContent;
  input.focus();
  autosize();
}

function add(cls, text) {
  removePlaceholder();
  const div = document.createElement('div');
  div.className = 'msg ' + cls;
  div.textContent = text;
  chatInner.appendChild(div);
  scrollBottom();
  return div;
}

function addAction(name, detail) {
  removePlaceholder();
  const div = document.createElement('div');
  div.className = 'action';
  const n = document.createElement('span');
  n.className = 'name';
  n.textContent = '→ ' + name;
  const d = document.createElement('span');
  d.className = 'detail';
  d.textContent = detail || '';
  div.appendChild(n);
  div.appendChild(d);
  chatInner.appendChild(div);
  scrollBottom();
}

function scrollBottom() {
  const chat = document.getElementById('chat');
  chat.scrollTop = chat.scrollHeight;
}

function setBusy(busy) {
  input.disabled = busy;
  sendBtn.disabled = busy;
  status.classList.toggle('busy', busy);
  status.querySelector('span').textContent = busy ? 'Working…' : 'Ready';
  if (!busy) input.focus();
}

function autosize() {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 200) + 'px';
}
input.addEventListener('input', autosize);

input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

function send() {
  const text = input.value.trim();
  if (!text) return;

  add('user', text);
  input.value = '';
  autosize();
  setBusy(true);

  const es = new EventSource('/stream?msg=' + encodeURIComponent(text));
  es.onmessage = (e) => {
    const d = JSON.parse(e.data);
    if (d.type === 'text') add('assistant', d.content);
    else if (d.type === 'action') addAction(d.name, d.detail);
    else if (d.type === 'error') add('assistant', '⚠️ ' + d.content);
    else if (d.type === 'done') {
      es.close();
      setBusy(false);
    }
  };
  es.onerror = () => {
    es.close();
    setBusy(false);
  };
}

function clearChat() {
  fetch('/reset', { method: 'POST' }).then(() => location.reload());
}
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return HTML


@app.route("/reset", methods=["POST"])
def reset():
    global _messages
    with _lock:
        _messages = []
    return {"ok": True}


@app.route("/stream")
def stream():
    msg = request.args.get("msg", "").strip()

    def evt(data):
        return f"data: {json.dumps(data)}\n\n"

    def generate():
        if not msg:
            yield evt({"type": "done"})
            return

        with _lock:
            _messages.append({"role": "user", "content": msg})

            tools = [
                {
                    "type": "computer_20250124",
                    "name": "computer",
                    "display_width_px": _executor.img_w,
                    "display_height_px": _executor.img_h,
                    "display_number": 1,
                },
                {"type": "bash_20250124", "name": "bash"},
            ]

            try:
                while True:
                    response = _client.messages.create(
                        model=MODEL,
                        max_tokens=4096,
                        system=SYSTEM,
                        tools=tools,
                        messages=_messages,
                        betas=[BETA],
                    )
                    _messages.append(
                        {"role": "assistant", "content": response.content}
                    )

                    tool_results = []
                    for block in response.content:
                        if block.type == "text":
                            yield evt({"type": "text", "content": block.text})

                        elif block.type == "tool_use":
                            if block.name == "computer":
                                action = block.input.get("action", "")
                                detail_parts = []
                                if "coordinate" in block.input:
                                    detail_parts.append(str(block.input["coordinate"]))
                                if "text" in block.input:
                                    t = block.input["text"]
                                    detail_parts.append(f'"{t[:50]}"')
                                if "key" in block.input:
                                    detail_parts.append(f"[{block.input['key']}]")
                                yield evt({
                                    "type": "action",
                                    "name": f"computer.{action}",
                                    "detail": " ".join(detail_parts),
                                })

                                result = _executor.run(**block.input)

                                if action == "screenshot" and result:
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": [{
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": "image/png",
                                                "data": result,
                                            },
                                        }],
                                    })
                                else:
                                    time.sleep(0.3)
                                    ss, _executor.img_w, _executor.img_h = take_screenshot()
                                    _executor.scale_x = _executor.logical_w / _executor.img_w
                                    _executor.scale_y = _executor.logical_h / _executor.img_h
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": [{
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": "image/png",
                                                "data": ss,
                                            },
                                        }],
                                    })

                            elif block.name == "bash":
                                cmd = block.input.get("command", "")
                                yield evt({
                                    "type": "action",
                                    "name": "bash",
                                    "detail": f"$ {cmd[:80]}",
                                })
                                output = run_bash(cmd)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": output,
                                })

                    if tool_results:
                        _messages.append({"role": "user", "content": tool_results})

                    if response.stop_reason == "end_turn" or not tool_results:
                        break

            except Exception as e:
                yield evt({"type": "error", "content": str(e)})

        yield evt({"type": "done"})

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    init()
    port = 5050
    url = f"http://127.0.0.1:{port}"
    print(f"\nMac Agent UI running at {url}")
    print("Opening in your browser…")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    app.run(host="127.0.0.1", port=port, threaded=True, debug=False)
