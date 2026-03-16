# X Monetization Assistant

A terminal-based tool that helps you hit X's monetization requirements without getting suspended.

Monitors your engagement lists, tracks your daily reply count, enforces the 60% For You feed rule, and sends iMessage alerts when new posts appear — so you can reply early and farm impressions efficiently.

---

## Requirements

- macOS (iMessage alerts require macOS)
- Python 3.9+
- A logged-in X account in Chrome or Safari
- X Premium (required for monetization anyway)

---

## Setup

**1. Download the script**

Save `x_monitors.py` to a folder on your Mac, e.g. `~/Downloads`.

**2. Run it**

```bash
python3 x_monitor.py
```

**3. First-run setup (two one-time steps)**

The script will walk you through both automatically:

**iMessage setup** — enter your phone number or Apple ID (e.g. `+919876543210` or `you@icloud.com`). You'll receive alerts here whenever a new post appears in your lists.

**Cookie setup** — the script needs your X session cookies to read your lists. Here's how to get them:

1. Open Chrome → go to `x.com` (make sure you're logged in)
2. Press `F12` → click the **Application** tab
3. Left sidebar → **Storage → Cookies → https://x.com**
4. Find `auth_token` → copy the Value
5. Find `ct0` → copy the Value
6. Paste each when prompted

Cookies are saved to `x_cookies.json` in the same folder. You won't need to do this again unless you log out of X.

---

## Daily Usage

Once running, the workflow is:

```
📱 iMessage arrives with a new post alert + link
  ↓
Open X on your phone → go reply early
  ↓
Come back to terminal → press 1 or 2 to log it
```

**Menu options:**

| Key | Action |
|-----|--------|
| `1` | Log a reply made from one of your lists |
| `2` | Log a reply made from your For You feed |
| `3` | Show today's stats |
| `4` | Open all 5 lists in your browser |
| `q` | Quit (progress is saved) |

---

## The Lists

The script monitors these 5 lists (from the original article):

| List | Purpose |
|------|---------|
| Big Accounts (Impression) | Large accounts — highest impression yield |
| Engage & Farm | Mid-tier engagement farming |
| Impression Farming | Impression volume |
| Close Circle | Tight engagement loop |
| Crypto | Niche-specific (high payout tier) |

---

## Suspension Safety Rules (Built In)

The script enforces the rules that keep your account safe:

**60% For You rule** — X flags accounts that only reply from lists. At least 60% of your replies must come from your For You feed. The script tracks this ratio and warns you (terminal + iMessage) when you're getting too list-heavy.

**Manual replies only** — the script never posts, replies, or interacts with X on your behalf. It only monitors and tracks. X cannot detect it.

**No API abuse** — uses your own session cookies, same as your browser. No third-party bots or automation tools.

---

## iMessage Alerts

You'll receive iMessages for:

| Alert | Trigger |
|-------|---------|
| 🔔 New post detected | Any new post in your 5 lists |
| ⚠️ Suspension risk | For You ratio drops below 60% |
| 🏃 Halfway milestone | 150 replies logged |
| 🎉 Daily goal hit | 300 replies logged |

---

## Files Created

| File | Contents |
|------|----------|
| `x_cookies.json` | Your X session cookies (keep private, don't share) |
| `x_daily_state.json` | Today's reply counts (auto-resets each day) |
| `x_activity_log.csv` | Full timestamped log of every reply |

---

## Realistic Expectations

The article author got monetized in 5 days — but was likely doing 6-8 hours of active engagement daily.

| Time available | Replies/day | Estimated timeline |
|----------------|-------------|-------------------|
| 6-8 hrs/day | 300 | 5-10 days |
| 1-2 hrs/day | 80-100 | 3-4 weeks |
| 30 min/day | 30-50 | 6-10 weeks |

Quality matters more than quantity. One early reply on a 500K-follower account can generate more impressions than 50 replies on small accounts. Focus on the **Big Accounts** list.

---

## Troubleshooting

**"No posts fetched" on startup**
Normal on first cold start. The background monitor picks up posts within 90 seconds.

**"Cookies expired" error**
X logged you out. Delete `x_cookies.json` and run the script again to re-enter fresh cookies.

**iMessage not sending**
Make sure Terminal has permission to control Messages: System Settings → Privacy & Security → Automation → Terminal → Messages ✅

**Script won't run**
Check your Python version: `python3 --version`. Needs 3.9 or higher.

---

## Monetization Requirements (for reference)

- ✅ X Premium (blue badge)
- ✅ 500 verified followers
- ✅ 5,000,000 impressions in the last 3 months
- ✅ 18+ years old

The bottleneck is always impressions. That's what this tool is for.
