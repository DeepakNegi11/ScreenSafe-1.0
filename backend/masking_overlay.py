# backend/masking_overlay.py

import tkinter as tk
import threading
import time
import re
import pyautogui
from ocr_engine import extract_with_boxes

# ── Trigger words ─────────────────────────────────────────────────
TRIGGER_WORDS = {
    "otp", "password", "passwd", "pwd", "passphrase",
    "cvv", "cvc", "cvv2", "cvc2",
    "aadhaar", "aadhar", "ssn",
    "credential", "credentials",
    "pin", "mpin", "ipin",
    "secretkey", "privatekey",
    "token", "secret", "passcode",
    "ifsc", "iban",
    "expiry", "expiration", "expires",
    "dob", "dateofbirth",
}

CONTEXTUAL_TRIGGERS = {
    "card", "account", "acct", "key", "code",
    "pan", "verification", "auth", "no",
    "number", "num", "id",
}

# How many VALUE tokens to mask after finding the actual value
# (not filler words — see FILLER_WORDS below)
TRIGGER_MASK_COUNT = {
    "cvv":         1,
    "cvc":         1,
    "cvv2":        1,
    "cvc2":        1,
    "otp":         1,
    "pin":         1,
    "mpin":        1,
    "ipin":        1,
    "passcode":    1,
    "password":    1,
    "passwd":      1,
    "pwd":         1,
    "passphrase":  1,
    "secret":      1,
    "secretkey":   1,
    "privatekey":  1,
    "token":       1,
    "ssn":         1,
    "aadhaar":     1,
    "aadhar":      1,
    "ifsc":        1,
    "iban":        1,
    "expiry":      2,
    "expiration":  2,
    "expires":     2,
    "dob":         3,
    "dateofbirth": 3,
    "card":        4,
    "account":     1,
    "acct":        1,
    "pan":         1,
}

# Words that appear between trigger and value — skip these
# e.g. "otp IS 234322" — skip "is" and mask "234322"
# e.g. "your PASSWORD : dsa123" — skip ":" and mask "dsa123"
FILLER_WORDS = {
    "is", "are", "was", "were", "be", "been",
    "the", "a", "an",
    "your", "my", "our", "their", "its",
    ":", "-", "=", "|", "->", "=>",
    "no", "number", "num", "#",
    "for", "of", "to",
}

EXCLUDE_BOTTOM_PX = 80
CLEAR_THRESHOLD   = 3

# ── State ─────────────────────────────────────────────────────────
_lock              = threading.Lock()
_root              = None
_canvas            = None
_started           = False
_overlay_visible   = False
_clean_count       = 0
_verify_running    = False
_confirmed_regions = []


# ── Noise filter ──────────────────────────────────────────────────

def _is_noise(clean):
    patterns = [
        r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$',
        r'^\d{2,4}[-/]\d{1,2}[-/]\d{1,2}$',
        r'^\d{1,2}[-/]\d{1,2}$',
        r'^\d{1,2}:\d{2}$',
        r'^\d{1,2}:\d{2}\s*(am|pm)$',
        r'^\d+°[cCfF]$',
        r'^\d+%$',
        r'^20[2-3]\d$',
        r'^19\d{2}$',
        r'^\d{1,3}$',
        r'^\d{1,3}[.,]\d{1,3}$',
        r'^#\w+$',
        r'^v\d+\.\d+',
        r'^\d+px$',
        r'^\d+pt$',
        r'^\d+\s*(kb|mb|gb|tb)$',
        r'^rs\.?\s*\d+$',
        r'^\$\d+$',
        r'^₹\d+$',
    ]
    for p in patterns:
        if re.match(p, clean, re.IGNORECASE):
            return True
    return False


def _is_filler(word):
    """Returns True if this word is a connector/filler between trigger and value."""
    clean = word.strip().lower()
    # Pure punctuation
    if re.match(r'^[:\-=|#>]+$', clean):
        return True
    return clean in FILLER_WORDS


def _is_value_token(word):
    """
    Returns True if this word looks like an actual sensitive value.
    Used to skip filler words and find the real value after a trigger.
    """
    if not word:
        return False
    clean = word.strip()

    # Has letters and numbers mixed (password like dsa123@)
    if re.search(r'[A-Za-z]', clean) and re.search(r'[0-9@#$!%^&*]', clean):
        return True

    # Pure digits of any length > 3
    digits = re.sub(r'[\s\-]', '', clean)
    if digits.isdigit() and len(digits) > 3:
        return True

    # Looks like a password (has special chars)
    if re.search(r'[@#$!%^&*_\-+=]', clean) and len(clean) > 3:
        return True

    # All alphabetic but long enough to be a password
    if clean.isalpha() and len(clean) >= 6:
        return True

    # Alphanumeric token
    if re.match(r'^[A-Za-z0-9]{6,}$', clean):
        return True

    return False


# ── Standalone pattern detectors ─────────────────────────────────

def _looks_like_card_chunk(word):
    d = word.replace(" ", "").replace("-", "")
    return d.isdigit() and len(d) == 4


def _looks_like_full_card(word):
    d = word.replace(" ", "").replace("-", "")
    return d.isdigit() and len(d) == 16


def _looks_like_pan(word):
    return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', word.upper()))


def _looks_like_ifsc(word):
    return bool(re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', word.upper()))


def _looks_like_ssn(word):
    return bool(re.match(r'^\d{3}-\d{2}-\d{4}$', word))


def _looks_like_api_key(word):
    patterns = [
        r'^sk-[a-zA-Z0-9]{20,}$',
        r'^ghp_[a-zA-Z0-9]{36}$',
        r'^xox[baprs]-',
        r'^AIza[0-9A-Za-z\-_]{35}$',
        r'^[0-9a-f]{32}$',
        r'^[0-9a-f]{40}$',
    ]
    for p in patterns:
        if re.match(p, word):
            return True
    return False


def _looks_like_email(word):
    return bool(re.match(
        r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', word
    ))


def _looks_like_phone(word):
    d = re.sub(r'[\s\-\(\)\+]', '', word)
    return d.isdigit() and 10 <= len(d) <= 13


# ── Main masking logic ────────────────────────────────────────────

class _ScanState:
    """Tracks state across tokens during a single scan pass."""
    def __init__(self):
        self.active_trigger   = None  # current trigger word
        self.masks_remaining  = 0     # value tokens left to mask
        self.filler_budget    = 4     # max filler words to skip before giving up


def _process_token(word, state):
    """
    Process a single OCR token.
    Returns (should_mask, updated_state).

    Key improvements:
    1. Skips filler words between trigger and value
    2. Finds actual value token after fillers
    3. Handles "otp is 234322" correctly
    4. Handles "password: dsa123@" correctly
    5. Handles "your otp is: 482910" correctly
    """
    if not word:
        return False, state

    clean = word.strip()
    lower = clean.lower().rstrip(':= ')

    # ── Noise: never mask ──────────────────────────────────────
    if _is_noise(clean):
        # Reset trigger state if noise appears
        state.active_trigger  = None
        state.masks_remaining = 0
        state.filler_budget   = 0
        return False, state

    # ── Currently in mask window ───────────────────────────────
    if state.masks_remaining > 0:
        if _is_filler(clean):
            # Skip filler, spend budget
            state.filler_budget -= 1
            if state.filler_budget <= 0:
                # Too many fillers — abandon this trigger
                state.active_trigger  = None
                state.masks_remaining = 0
            return False, state

        if _is_value_token(clean):
            # This is the actual value — mask it
            state.masks_remaining -= 1
            if state.masks_remaining == 0:
                state.active_trigger = None
            return True, state
        else:
            # Not a value token and not filler — abandon trigger
            state.active_trigger  = None
            state.masks_remaining = 0
            return False, state

    # ── Waiting for value (trigger found, no value yet) ────────
    if state.active_trigger and state.filler_budget > 0:
        if _is_filler(clean):
            state.filler_budget -= 1
            return False, state

        if _is_value_token(clean):
            count = TRIGGER_MASK_COUNT.get(state.active_trigger, 1)
            state.masks_remaining = count - 1
            if state.masks_remaining == 0:
                state.active_trigger = None
            return True, state
        else:
            state.active_trigger  = None
            state.filler_budget   = 0
            return False, state

    # ── Check for new trigger word ─────────────────────────────
    is_trigger = lower in TRIGGER_WORDS

    # Contextual triggers need colon/equals immediately after
    # OR be followed by filler then value
    if not is_trigger and lower in CONTEXTUAL_TRIGGERS:
        is_trigger = True

    if is_trigger:
        state.active_trigger  = lower
        state.masks_remaining = 0
        state.filler_budget   = 4  # allow up to 4 filler tokens
        return False, state        # don't mask the trigger itself

    # ── Standalone patterns (no trigger needed) ────────────────
    if _looks_like_full_card(clean):
        return True, state

    if _looks_like_pan(clean):
        return True, state

    if _looks_like_ifsc(clean):
        return True, state

    if _looks_like_ssn(clean):
        return True, state

    if _looks_like_api_key(clean):
        return True, state

    if _looks_like_email(clean):
        return True, state

    if _looks_like_phone(clean):
        return True, state

    return False, state


def _is_inside_confirmed(region):
    rx, ry, rx2, ry2 = region
    for (cx, cy, cx2, cy2) in _confirmed_regions:
        if rx < cx2 and rx2 > cx and ry < cy2 and ry2 > cy:
            return True
    return False


def compute_regions(screenshot):
    regions  = []
    state    = _ScanState()
    screen_h = screenshot.size[1]
    safe_bottom = screen_h - EXCLUDE_BOTTOM_PX

    try:
        data = extract_with_boxes(screenshot)
        n    = len(data['text'])

        # ── Pass 1: token-level detection ─────────────────────
        for i in range(n):
            word = data['text'][i].strip()
            if not word:
                continue
            if data['top'][i] > safe_bottom:
                state = _ScanState()  # reset at taskbar
                continue

            should_mask, state = _process_token(word, state)

            if should_mask:
                pad = 8
                x   = max(0, data['left'][i]  - pad)
                y   = max(0, data['top'][i]   - pad)
                x2  = data['left'][i] + data['width'][i]  + pad
                y2  = data['top'][i]  + data['height'][i] + pad
                new = (x, y, x2, y2)
                if not _is_inside_confirmed(new):
                    regions.append(new)

        # ── Pass 2: card number block detection ───────────────
        # Detects "4111 1111 1111 1111" as 4 separate tokens
        card_seq = []
        for i in range(n):
            word = data['text'][i].strip()
            if data['top'][i] > safe_bottom:
                card_seq = []
                continue

            if _looks_like_card_chunk(word):
                if card_seq:
                    prev_i    = card_seq[-1]
                    same_line = abs(data['top'][i] - data['top'][prev_i]) < 15
                    if same_line:
                        card_seq.append(i)
                    else:
                        card_seq = [i]
                else:
                    card_seq.append(i)

                # 4 consecutive chunks = full card number
                if len(card_seq) >= 4:
                    for idx in card_seq:
                        pad = 8
                        x   = max(0, data['left'][idx]  - pad)
                        y   = max(0, data['top'][idx]   - pad)
                        x2  = data['left'][idx] + data['width'][idx]  + pad
                        y2  = data['top'][idx]  + data['height'][idx] + pad
                        new = (x, y, x2, y2)
                        if not _is_inside_confirmed(new):
                            regions.append(new)
                    card_seq = []
            else:
                card_seq = []

    except Exception as e:
        print(f"[Masking] compute error: {e}")

    return _merge(regions)


def _merge(regions, gap=20):
    if not regions:
        return []
    regions = sorted(regions, key=lambda r: (r[1], r[0]))
    merged  = [list(regions[0])]
    for c in regions[1:]:
        p = merged[-1]
        if abs(c[1] - p[1]) < gap and c[0] - p[2] < gap:
            p[0] = min(p[0], c[0])
            p[1] = min(p[1], c[1])
            p[2] = max(p[2], c[2])
            p[3] = max(p[3], c[3])
        else:
            merged.append(list(c))
    return [tuple(r) for r in merged]


# ── Tkinter helpers ───────────────────────────────────────────────

def _redraw_all():
    _canvas.delete("all")
    for (x, y, x2, y2) in _confirmed_regions:
        _canvas.create_rectangle(
            x, y, x2, y2,
            fill="black",
            outline="black"
        )
    print(f"[Masking] {len(_confirmed_regions)} box(es) on screen")


def _add_regions(new_regions):
    global _confirmed_regions, _overlay_visible, _clean_count
    added = 0
    for r in new_regions:
        if not _is_inside_confirmed(r):
            _confirmed_regions.append(r)
            added += 1
    if added > 0:
        print(f"[Masking] +{added} box(es) — total: {len(_confirmed_regions)}")
        _clean_count     = 0
        _overlay_visible = True
        _redraw_all()
        _root.deiconify()


def _clear_all():
    global _confirmed_regions, _overlay_visible, _clean_count
    _confirmed_regions = []
    _overlay_visible   = False
    _clean_count       = 0
    _canvas.delete("all")
    _root.withdraw()
    print("[Masking] Cleared — screen is clean")


# ── Verify loop ───────────────────────────────────────────────────

def _check_outside_confirmed(screenshot):
    state        = _ScanState()
    screen_h     = screenshot.size[1]
    safe_bottom  = screen_h - EXCLUDE_BOTTOM_PX
    found_outside = False
    try:
        data = extract_with_boxes(screenshot)
        n    = len(data['text'])
        for i in range(n):
            word = data['text'][i].strip()
            if not word:
                continue
            if data['top'][i] > safe_bottom:
                state = _ScanState()
                continue
            should_mask, state = _process_token(word, state)
            if should_mask:
                pad    = 8
                x      = max(0, data['left'][i]  - pad)
                y      = max(0, data['top'][i]   - pad)
                x2     = data['left'][i] + data['width'][i]  + pad
                y2     = data['top'][i]  + data['height'][i] + pad
                if not _is_inside_confirmed((x, y, x2, y2)):
                    found_outside = True
                    break
    except Exception as e:
        print(f"[Verify] outside check error: {e}")
    return not found_outside


def _verify_loop():
    global _clean_count, _verify_running
    _verify_running = True
    print("[Verify] Loop started")
    while _verify_running:
        try:
            screenshot  = pyautogui.screenshot()
            new_regions = compute_regions(screenshot)
            if new_regions:
                _clean_count = 0
                _root.after(0, lambda r=new_regions: _add_regions(r))
            elif _confirmed_regions:
                outside_clean = _check_outside_confirmed(screenshot)
                if outside_clean:
                    _clean_count += 1
                    print(f"[Verify] Clean {_clean_count}/{CLEAR_THRESHOLD}")
                    if _clean_count >= CLEAR_THRESHOLD:
                        _root.after(0, _clear_all)
                else:
                    _clean_count = 0
            else:
                _clean_count = 0
        except Exception as e:
            print(f"[Verify] Error: {e}")
        time.sleep(2)


# ── Window ────────────────────────────────────────────────────────

def _start_window():
    global _root, _canvas
    _root    = tk.Tk()
    screen_w = _root.winfo_screenwidth()
    screen_h = _root.winfo_screenheight()
    _root.geometry(f"{screen_w}x{screen_h}+0+0")
    _root.overrideredirect(True)
    _root.attributes("-topmost", True)
    _root.attributes("-transparentcolor", "#010101")
    _root.configure(bg="#010101")
    _root.attributes("-alpha", 1.0)
    _root.withdraw()
    _canvas = tk.Canvas(
        _root, width=screen_w, height=screen_h,
        bg="#010101", highlightthickness=0
    )
    _canvas.pack()
    threading.Thread(target=_verify_loop, daemon=True).start()
    _root.mainloop()


def _ensure_started():
    global _started
    with _lock:
        if _started:
            return
        _started = True
    threading.Thread(target=_start_window, daemon=True).start()
    time.sleep(0.8)


def apply_mask_overlay(is_sensitive, screenshot=None):
    _ensure_started()