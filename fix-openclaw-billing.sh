#!/usr/bin/env bash
# fix-openclaw-billing.sh
# Fixes the "Provider anthropic has billing issue (skipping all models)" error
# by migrating OpenClaw from the anthropic/ API backend to claude-cli/ backend.
#
# After Anthropic's April 4 2026 change, Claude subscriptions (Pro/Max) no
# longer cover API calls from third-party agents like OpenClaw. The claude-cli/
# backend routes through your local Claude Code CLI binary, which authenticates
# via your subscription -- so your existing credits work again.
#
# Usage: bash fix-openclaw-billing.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CONFIG="${OPENCLAW_CONFIG:-$HOME/.openclaw/openclaw.json}"
CRON_JOBS="$HOME/.openclaw/cron/jobs.json"

info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo "=========================================="
echo " OpenClaw Billing Fix - anthropic/ -> claude-cli/"
echo "=========================================="
echo ""

# ── Step 1: Check Claude CLI is installed and authenticated ──
echo "Step 1: Checking Claude CLI..."

CLAUDE_BIN=$(which claude 2>/dev/null || true)
if [ -z "$CLAUDE_BIN" ]; then
    fail "Claude CLI not found. Install it first:
    npm install -g @anthropic-ai/claude-code
  Then authenticate:
    claude auth login"
fi

CLAUDE_VER=$($CLAUDE_BIN --version 2>/dev/null || echo "unknown")
info "Found Claude CLI at $CLAUDE_BIN (version: $CLAUDE_VER)"

# Check auth status
AUTH_OUT=$($CLAUDE_BIN auth status 2>&1 || true)
if echo "$AUTH_OUT" | grep -qi "not.*logged\|no.*auth\|unauthenticated"; then
    fail "Claude CLI is not authenticated. Run:
    claude auth login"
fi
info "Claude CLI is authenticated"

# ── Step 2: Backup existing config ──
echo ""
echo "Step 2: Backing up configuration..."

if [ ! -f "$CONFIG" ]; then
    fail "OpenClaw config not found at $CONFIG
  Set OPENCLAW_CONFIG if your config is elsewhere."
fi

BACKUP="${CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG" "$BACKUP"
info "Backed up config to $BACKUP"

# ── Step 3: Check if already migrated ──
if grep -q '"claude-cli"' "$CONFIG" 2>/dev/null; then
    if ! grep -q '"anthropic/claude-' "$CONFIG" 2>/dev/null; then
        info "Already migrated to claude-cli/ backend. Nothing to do."
        exit 0
    fi
    warn "Partial migration detected -- continuing..."
fi

# ── Step 4: Inject claude-cli backend config ──
echo ""
echo "Step 3: Adding claude-cli backend configuration..."

# Use Python for reliable JSON manipulation
python3 << 'PYEOF'
import json
import sys
import os

config_path = os.environ.get("OPENCLAW_CONFIG", os.path.expanduser("~/.openclaw/openclaw.json"))
claude_bin = os.popen("which claude").read().strip()

with open(config_path) as f:
    config = json.load(f)

# Navigate to agents.defaults, creating keys if missing
agents = config.setdefault("agents", {})
defaults = agents.setdefault("defaults", {})
cli_backends = defaults.setdefault("cliBackends", {})

# Add claude-cli backend
cli_backends["claude-cli"] = {
    "command": claude_bin,
    "args": ["-p", "--output-format", "stream-json", "--verbose",
             "--permission-mode", "bypassPermissions"],
    "resumeArgs": ["-p", "--output-format", "stream-json", "--verbose",
                   "--permission-mode", "bypassPermissions", "--resume", "{sessionId}"],
    "output": "jsonl",
    "input": "arg",
    "modelArg": "--model",
    "modelAliases": {
        "opus": "opus",
        "claude-opus-4-6": "opus",
        "sonnet": "sonnet",
        "claude-sonnet-4-6": "sonnet",
        "haiku": "haiku",
        "claude-haiku-4-5": "haiku"
    },
    "sessionArg": "--session-id",
    "sessionMode": "always",
    "sessionIdFields": ["session_id", "sessionId", "conversation_id", "conversationId"],
    "systemPromptArg": "--append-system-prompt",
    "systemPromptMode": "append",
    "systemPromptWhen": "first",
    "clearEnv": ["ANTHROPIC_API_KEY"],
    "serialize": False
}

# Add claude-cli models to catalog
models = defaults.setdefault("models", {})
models["claude-cli/claude-opus-4-6"]   = {"alias": "opus"}
models["claude-cli/claude-sonnet-4-6"] = {"alias": "sonnet"}
models["claude-cli/claude-haiku-4-5"]  = {"alias": "haiku"}

# Update default model from anthropic/ to claude-cli/
model_cfg = defaults.get("model", {})
if isinstance(model_cfg, dict):
    primary = model_cfg.get("primary", "")
    if primary.startswith("anthropic/"):
        model_cfg["primary"] = primary.replace("anthropic/", "claude-cli/", 1)
        print(f"  Updated primary model: {primary} -> {model_cfg['primary']}")

    fallbacks = model_cfg.get("fallbacks", [])
    new_fallbacks = []
    for fb in fallbacks:
        if fb.startswith("anthropic/"):
            new_fb = fb.replace("anthropic/", "claude-cli/", 1)
            print(f"  Updated fallback: {fb} -> {new_fb}")
            new_fallbacks.append(new_fb)
        else:
            new_fallbacks.append(fb)
    model_cfg["fallbacks"] = new_fallbacks
    defaults["model"] = model_cfg
elif isinstance(model_cfg, str) and model_cfg.startswith("anthropic/"):
    new_model = model_cfg.replace("anthropic/", "claude-cli/", 1)
    print(f"  Updated default model: {model_cfg} -> {new_model}")
    defaults["model"] = new_model

# Replace any remaining anthropic/ model references in agent configs
def replace_anthropic_refs(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and v.startswith("anthropic/claude-"):
                new_v = v.replace("anthropic/", "claude-cli/", 1)
                obj[k] = new_v
                print(f"  Replaced {path}.{k}: {v} -> {new_v}")
            else:
                replace_anthropic_refs(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and v.startswith("anthropic/claude-"):
                new_v = v.replace("anthropic/", "claude-cli/", 1)
                obj[i] = new_v
                print(f"  Replaced {path}[{i}]: {v} -> {new_v}")
            else:
                replace_anthropic_refs(v, f"{path}[{i}]")

replace_anthropic_refs(config)

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

print("  Config updated successfully.")
PYEOF

info "claude-cli backend added and model references updated"

# ── Step 5: Update cron jobs if they exist ──
echo ""
echo "Step 4: Checking cron jobs..."

if [ -f "$CRON_JOBS" ]; then
    if grep -q "anthropic/" "$CRON_JOBS"; then
        cp "$CRON_JOBS" "${CRON_JOBS}.backup.$(date +%Y%m%d_%H%M%S)"
        sed -i 's|"anthropic/claude-opus-4-6"|"claude-cli/claude-opus-4-6"|g' "$CRON_JOBS"
        sed -i 's|"anthropic/claude-sonnet-4-6"|"claude-cli/claude-sonnet-4-6"|g' "$CRON_JOBS"
        sed -i 's|"anthropic/claude-sonnet-4-20250514"|"claude-cli/claude-sonnet-4-6"|g' "$CRON_JOBS"
        sed -i 's|"anthropic/claude-haiku-4-5"|"claude-cli/claude-haiku-4-5"|g' "$CRON_JOBS"
        sed -i 's|"anthropic/claude-haiku-4-0"|"claude-cli/claude-haiku-4-5"|g' "$CRON_JOBS"
        info "Cron jobs updated"
    else
        info "No anthropic/ references in cron jobs"
    fi
else
    info "No cron jobs file found (skipping)"
fi

# ── Step 6: Restart gateway ──
echo ""
echo "Step 5: Restarting OpenClaw gateway..."

if systemctl --user is-active openclaw-gateway &>/dev/null; then
    systemctl --user restart openclaw-gateway
    sleep 2
    if systemctl --user is-active openclaw-gateway &>/dev/null; then
        info "Gateway restarted successfully"
    else
        warn "Gateway may not have started cleanly. Check: journalctl --user -u openclaw-gateway -n 20"
    fi
elif command -v openclaw &>/dev/null; then
    warn "Gateway not running as systemd service. Restart it manually:
    openclaw gateway restart"
else
    warn "Could not detect running gateway. Restart OpenClaw manually."
fi

# ── Step 7: Verify ──
echo ""
echo "Step 6: Verifying..."

REMAINING=$(grep -c "anthropic/claude-" "$CONFIG" 2>/dev/null || echo "0")
if [ "$REMAINING" -gt 0 ]; then
    warn "$REMAINING anthropic/ model reference(s) still in config (may be inactive legacy entries)"
else
    info "No active anthropic/ references remain"
fi

echo ""
echo "=========================================="
echo -e " ${GREEN}Migration complete!${NC}"
echo "=========================================="
echo ""
echo "Your OpenClaw agents will now route through Claude CLI,"
echo "using your subscription credits (not API billing)."
echo ""
echo "If anything breaks, restore your backup:"
echo "  cp $BACKUP $CONFIG"
echo "  systemctl --user restart openclaw-gateway"
echo ""
