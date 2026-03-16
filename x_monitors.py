#!/usr/bin/env python3
"""
X Monetization Assistant v1.2
- Monitors your X lists directly via X's API (no third-party services)
- Tracks daily reply count toward 300/day goal
- Enforces 60% For You feed rule to avoid suspension
- Logs all activity to CSV
- iMessage alerts on macOS
"""

import time
import json
import csv
import os
import sys
import threading
import webbrowser
from datetime import datetime, date
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

LISTS = {
    "Big Accounts (Impression)":  "1988709134276129138",
    "Engage & Farm":              "1971533164846997871",
    "Impression Farming":         "1832387796184809802",
    "Close Circle":               "2024050535511576668",
    "Crypto":                     "2029370665724461416",
}

DAILY_REPLY_GOAL     = 300
FOR_YOU_RATIO_TARGET = 0.60
POLL_INTERVAL_SECS   = 90
LOG_FILE             = "x_activity_log.csv"
STATE_FILE           = "x_daily_state.json"
COOKIE_FILE          = "x_cookies.json"

# iMessage — filled in at first run
IMESSAGE_RECIPIENT = ""   # 👈 fill your icloud id / phonenumber

# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"
    DIM    = "\033[2m"

def clr(text, *codes):
    return "".join(codes) + str(text) + C.RESET

# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────

def load_state():
    default = {"date": str(date.today()), "list_replies": 0, "foryou_replies": 0}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                s = json.load(f)
            if s.get("date") != str(date.today()):
                print(clr("📅  New day — resetting counters.", C.CYAN))
                return default
            return s
        except Exception:
            return default
    return default

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def log_reply(source, note=""):
    exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["timestamp", "source", "note"])
        w.writerow([datetime.now().isoformat(), source, note])

# ─────────────────────────────────────────────
# IMESSAGE
# ─────────────────────────────────────────────

def send_imessage(message):
    if not IMESSAGE_RECIPIENT or sys.platform != "darwin":
        return
    safe = message.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        'tell application "Messages"\n'
        f'  set b to buddy "{IMESSAGE_RECIPIENT}" of (1st account whose service type = iMessage)\n'
        f'  send "{safe}" to b\n'
        'end tell'
    )
    try:
        import subprocess
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
    except Exception:
        pass

def setup_imessage():
    global IMESSAGE_RECIPIENT
    if IMESSAGE_RECIPIENT or sys.platform != "darwin":
        return
    print(clr("  📱  iMessage alerts are OFF.", C.YELLOW))
    print(clr("  Enter your number or Apple ID (or Enter to skip):", C.YELLOW))
    val = input("  → ").strip()
    if val:
        IMESSAGE_RECIPIENT = val
        try:
            with open(__file__, "r") as f:
                src = f.read()
            src = src.replace(
                'IMESSAGE_RECIPIENT = "charvi.sethi@icloud.com"   # 👈 auto-filled at startup',
                f'IMESSAGE_RECIPIENT = "{val}"   # 👈 auto-filled at startup'
            )
            with open(__file__, "w") as f:
                f.write(src)
            print(clr(f"  ✅  Saved {val} — alerts active.", C.GREEN))
            send_imessage("✅ X Monitor connected. Alerts will appear here.")
        except Exception:
            print(clr("  ✅  Set for this session.", C.GREEN))
    else:
        print(clr("  Skipped.", C.DIM))
    print()

# ─────────────────────────────────────────────
# COOKIE SETUP — paste once, saved to file
# ─────────────────────────────────────────────

def load_cookies():
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE) as f:
                c = json.load(f)
            if c.get("auth_token") and c.get("ct0"):
                return c["auth_token"], c["ct0"]
        except Exception:
            pass
    return None, None

def save_cookies(auth_token, ct0):
    with open(COOKIE_FILE, "w") as f:
        json.dump({"auth_token": auth_token, "ct0": ct0}, f)

def setup_cookies():
    auth, ct0 = load_cookies()
    if auth and ct0:
        return auth, ct0

    print()
    print(clr("  ─────────────────────────────────────────────", C.DIM))
    print(clr("  🍪  ONE-TIME COOKIE SETUP (takes 60 seconds)", C.BOLD + C.CYAN))
    print(clr("  ─────────────────────────────────────────────", C.DIM))
    print()
    print("  1. Open Chrome → go to x.com (make sure you're logged in)")
    print("  2. Press  F12  to open DevTools")
    print("  3. Click the  Application  tab")
    print("  4. In the left sidebar: Storage → Cookies → https://x.com")
    print("  5. Find the cookie named  auth_token  → copy its Value")
    print("  6. Find the cookie named  ct0  → copy its Value")
    print()
    print(clr("  Paste auth_token value below:", C.YELLOW))
    auth = input("  → ").strip()
    print(clr("  Paste ct0 value below:", C.YELLOW))
    ct0 = input("  → ").strip()
    print()

    if auth and ct0:
        save_cookies(auth, ct0)
        print(clr("  ✅  Cookies saved to x_cookies.json", C.GREEN))
        print(clr("  You won't need to do this again unless you log out of X.", C.DIM))
    else:
        print(clr("  ⚠️  Skipped. List monitoring will be disabled.", C.YELLOW))
        auth, ct0 = None, None
    print()
    return auth, ct0

# ─────────────────────────────────────────────
# X API FETCH
# ─────────────────────────────────────────────

_auth_token = None
_ct0        = None

# X's public bearer token (same one used by the website)
BEARER = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
    "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)

def fetch_list_posts(list_id):
    if not _auth_token or not _ct0:
        return []

    url = (
        "https://api.twitter.com/2/timeline/list.json"
        f"?list_id={list_id}&count=20&tweet_mode=extended"
    )
    headers = {
        "User-Agent":    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Authorization": f"Bearer {BEARER}",
        "Cookie":        f"auth_token={_auth_token}; ct0={_ct0}",
        "X-Csrf-Token":  _ct0,
        "Referer":       "https://x.com/",
        "Accept":        "application/json",
    }
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        tweets = data.get("globalObjects", {}).get("tweets", {})
        users  = data.get("globalObjects", {}).get("users", {})
        posts  = []
        for tid, t in tweets.items():
            uid      = str(t.get("user_id_str", ""))
            username = users.get(uid, {}).get("screen_name", "unknown")
            text     = t.get("full_text") or t.get("text", "")
            posts.append({
                "id":    tid,
                "title": f"{username}: {text}",
                "link":  f"https://x.com/{username}/status/{tid}",
                "pub":   t.get("created_at", ""),
            })
        return posts
    except HTTPError as e:
        if e.code == 401:
            print(clr("\n  ⚠️  Cookies expired — run script again to re-enter them.", C.RED))
            if os.path.exists(COOKIE_FILE):
                os.remove(COOKIE_FILE)
        return []
    except Exception:
        return []

# ─────────────────────────────────────────────
# ALERT
# ─────────────────────────────────────────────

def alert(msg):
    print("\a", end="", flush=True)
    print(clr("┌" + "─" * 52 + "┐", C.GREEN))
    print(clr("│  🔔  NEW POST ALERT" + " " * 32 + "│", C.GREEN + C.BOLD))
    for line in msg.splitlines():
        padded = ("│  " + line)[:54].ljust(55) + "│"
        print(clr(padded, C.GREEN))
    print(clr("└" + "─" * 52 + "┘", C.GREEN))
    send_imessage("🔔 X Alert:\n" + msg)

# ─────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────

def print_stats(state):
    total     = state["list_replies"] + state["foryou_replies"]
    remaining = max(0, DAILY_REPLY_GOAL - total)
    filled    = int((total / DAILY_REPLY_GOAL) * 30)
    bar       = "█" * filled + "░" * (30 - filled)

    print()
    print(clr("━" * 54, C.DIM))
    print(clr("  📊  DAILY PROGRESS", C.BOLD))
    print(clr("━" * 54, C.DIM))
    print(f"  Replies today   : {clr(total, C.BOLD)} / {DAILY_REPLY_GOAL}  ({remaining} to go)")
    print(f"  [{clr(bar, C.GREEN)}]")
    print(f"  From Lists       : {clr(state['list_replies'], C.YELLOW)}")
    print(f"  From For You     : {clr(state['foryou_replies'], C.CYAN)}")

    if total == 0:
        print(f"  For You ratio    : {clr('— start replying to track', C.DIM)}")
    else:
        pct      = state["foryou_replies"] / total * 100
        ok       = pct >= FOR_YOU_RATIO_TARGET * 100
        icon     = clr("✅", C.GREEN) if ok else clr("⚠️ ", C.RED)
        color    = C.GREEN if ok else C.RED
        print(f"  For You ratio    : {icon}  {clr(f'{pct:.0f}%', color)}  (target ≥ 60%)")
        if not ok:
            needed = max(0, int(
                FOR_YOU_RATIO_TARGET * state["list_replies"] / (1 - FOR_YOU_RATIO_TARGET)
                - state["foryou_replies"]
            ))
            if needed > 0:
                print(clr(f"  ↳  Need {needed} more For You replies to balance.", C.RED))

    mon_status = clr("✅ active", C.GREEN) if (_auth_token and _ct0) else clr("⚠️  cookies needed", C.YELLOW)
    imsg       = clr("✅ " + IMESSAGE_RECIPIENT, C.GREEN) if IMESSAGE_RECIPIENT else clr("off", C.DIM)
    print(f"  List monitor     : {mon_status}")
    print(f"  iMessage         : {imsg}")
    print(clr("━" * 54, C.DIM))
    print()

# ─────────────────────────────────────────────
# MENU
# ─────────────────────────────────────────────

def menu(state):
    print_stats(state)
    print(clr("  What did you just do?", C.BOLD))
    print(f"  {clr('[1]', C.CYAN)} Replied from a LIST")
    print(f"  {clr('[2]', C.CYAN)} Replied from FOR YOU feed")
    print(f"  {clr('[3]', C.CYAN)} Show stats only")
    print(f"  {clr('[4]', C.CYAN)} Open all lists in browser")
    print(f"  {clr('[q]', C.RED)} Quit")
    print()
    choice = input("  → ").strip().lower()

    if choice == "1":
        note = input("  Optional note (e.g. '@handle topic'): ").strip()
        state["list_replies"] += 1
        log_reply("list", note)
        save_state(state)
        print(clr("  ✅  List reply logged.", C.GREEN))
        _milestones(state)

    elif choice == "2":
        note = input("  Optional note: ").strip()
        state["foryou_replies"] += 1
        log_reply("for_you", note)
        save_state(state)
        print(clr("  ✅  For You reply logged.", C.CYAN))
        _milestones(state)

    elif choice == "3":
        pass

    elif choice == "4":
        for name, lid in LISTS.items():
            print(clr(f"  Opening: {name}", C.DIM))
            webbrowser.open(f"https://x.com/i/lists/{lid}")
            time.sleep(0.5)

    elif choice == "q":
        print(clr("\n  👋  Session saved. See you tomorrow!\n", C.BOLD))
        sys.exit(0)

    else:
        print(clr(f"  ❌  '{choice}' is not valid. Use 1, 2, 3, 4, or q.", C.YELLOW))

    return state

def _milestones(state):
    total = state["list_replies"] + state["foryou_replies"]
    if total == 150:
        send_imessage("🏃 Halfway! 150/300 replies done today on X.")
    elif total == 300:
        send_imessage("🎉 Daily goal hit! 300 replies done. Great work!")

# ─────────────────────────────────────────────
# BACKGROUND MONITOR
# ─────────────────────────────────────────────

_seen_ids      = set()
_new_post_queue = []
_queue_lock    = threading.Lock()

def monitor_loop():
    global _seen_ids
    while True:
        for name, lid in LISTS.items():
            for p in fetch_list_posts(lid):
                if p["id"] not in _seen_ids:
                    _seen_ids.add(p["id"])
                    if len(_seen_ids) > 500:
                        _seen_ids = set(list(_seen_ids)[-400:])
                    with _queue_lock:
                        _new_post_queue.append({"list": name, **p})
        time.sleep(POLL_INTERVAL_SECS)

def check_alerts():
    with _queue_lock:
        if not _new_post_queue:
            return
        posts = _new_post_queue.copy()
        _new_post_queue.clear()
    for p in posts:
        author  = p["title"].split(":")[0] if ":" in p["title"] else "someone"
        preview = p["title"][:80] + ("…" if len(p["title"]) > 80 else "")
        alert(f"List : {p['list']}\nFrom : {author}\n{preview}\nLink : {p['link']}")

# ─────────────────────────────────────────────
# FOR YOU REMINDER
# ─────────────────────────────────────────────

def foryou_reminder(state):
    total = state["list_replies"] + state["foryou_replies"]
    if total < 5:
        return
    ratio = state["foryou_replies"] / total
    if (ratio < FOR_YOU_RATIO_TARGET
            and state["list_replies"] >= 5
            and state["list_replies"] % 5 == 0
            and state["foryou_replies"] < state["list_replies"]):
        needed = max(1, int(
            FOR_YOU_RATIO_TARGET * state["list_replies"] / (1 - FOR_YOU_RATIO_TARGET)
            - state["foryou_replies"]
        ))
        print()
        print(clr("  ⚠️   SUSPENSION RISK WARNING", C.RED + C.BOLD))
        print(clr(f"  Need ~{needed} more For You replies to hit 60%.", C.RED))
        print(clr("  Switch to your home feed and reply to a few posts!", C.YELLOW))
        print()
        send_imessage(
            f"⚠️ X Suspension Risk!\n"
            f"For You ratio too low.\n"
            f"Reply to {needed} more For You posts to stay safe."
        )

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    global _auth_token, _ct0

    os.system("clear" if os.name == "posix" else "cls")
    print()
    print(clr("  ██╗  ██╗  ███╗   ███╗ ██████╗ ███╗  ██╗", C.BLUE + C.BOLD))
    print(clr("   ╚██╗██╔╝  ████╗ ████║██╔═══██╗████╗ ██║", C.BLUE + C.BOLD))
    print(clr("    ╚███╔╝   ██╔████╔██║██║   ██║██╔██╗██║", C.BLUE + C.BOLD))
    print(clr("    ██╔██╗   ██║╚██╔╝██║██║   ██║██║╚████║", C.BLUE + C.BOLD))
    print(clr("   ██╔╝╚██╗  ██║ ╚═╝ ██║╚██████╔╝██║ ╚███║", C.BLUE + C.BOLD))
    print(clr("   ╚═╝  ╚═╝  ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚══╝", C.BLUE + C.BOLD))
    print(clr("        Monetization Assistant  v1.2", C.DIM))
    print()

    setup_imessage()

    _auth_token, _ct0 = setup_cookies()

    state = load_state()

    print(clr("  Seeding existing posts (so old posts won't alert)…", C.DIM))
    for name, lid in LISTS.items():
        for p in fetch_list_posts(lid):
            _seen_ids.add(p["id"])

    if _seen_ids:
        print(clr(f"  ✅  Seeded {len(_seen_ids)} existing posts. Only NEW posts will alert.", C.GREEN))
    elif _auth_token:
        print(clr("  ⚠️  No posts fetched. Will retry in background.", C.YELLOW))
    else:
        print(clr("  ⚠️  Monitoring disabled (no cookies). Tracker still works!", C.YELLOW))
    print()

    threading.Thread(target=monitor_loop, daemon=True).start()

    while True:
        check_alerts()
        foryou_reminder(state)
        state = menu(state)
        time.sleep(0.3)

if __name__ == "__main__":
    main()
