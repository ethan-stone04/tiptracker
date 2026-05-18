import streamlit as st
import json
import os
import re
import requests
import secrets
from datetime import date, datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Chicago")  # CST/CDT — auto-handles DST

# ── Config ────────────────────────────────────────────────────────────────────
DATA_FILE = "shifts.json"
PROFILE_FILE = "profile.json"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.set_page_config(page_title="Shift Tracker", page_icon="🍸", layout="centered")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&family=Cormorant+Garamond:wght@500;600;700&display=swap');

/* ── Force speakeasy palette regardless of Light/Dark/System toggle ─────── */
.stApp, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse at top, rgba(201,169,97,0.10) 0%, transparent 55%),
        radial-gradient(ellipse at bottom right, rgba(122,46,46,0.14) 0%, transparent 60%),
        linear-gradient(180deg, #14100c 0%, #0f0b07 100%) !important;
    background-attachment: fixed !important;
    color: #f0e2c4 !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMain"], [data-testid="stMainBlockContainer"] { color: #f0e2c4 !important; }

html, body, [class*="css"], .stMarkdown, .stMarkdown p, .stMarkdown li,
[data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] {
    font-family: 'DM Sans', sans-serif !important;
    color: #f0e2c4 !important;
}
[data-testid="stCaptionContainer"], .stCaption,
[data-testid="stCaptionContainer"] p { color: #a89070 !important; }

h1 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 600 !important; color: #e8c878 !important;
    letter-spacing: 0.01em;
    text-shadow: 0 2px 16px rgba(201,169,97,0.25);
}
h2, h3 { font-family: 'DM Mono', monospace !important; color: #f0e2c4 !important; }

/* ── Metric boxes ──────────────────────────────────────────────────────── */
.metric-row { display: flex; gap: 14px; margin-bottom: 1.75rem; }
.metric-box {
    flex: 1; position: relative; overflow: hidden;
    background: linear-gradient(145deg, #241a10 0%, #1a130b 100%);
    border: 1px solid #3a2f1f;
    border-radius: 8px; padding: 1.2rem 1rem; text-align: center;
    box-shadow:
        0 4px 16px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(201,169,97,0.12),
        inset 0 0 30px rgba(201,169,97,0.03);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.metric-box::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201,169,97,0.55), transparent);
}
.metric-box:hover {
    transform: translateY(-2px); border-color: #5a4630;
    box-shadow: 0 8px 24px rgba(0,0,0,0.55), inset 0 1px 0 rgba(201,169,97,0.18);
}
.metric-box .label {
    font-size: 10px; color: #a89070; text-transform: uppercase;
    letter-spacing: 0.15em; margin-bottom: 8px; font-weight: 500;
}
.metric-box .value {
    font-family: 'DM Mono', monospace; font-size: 26px; font-weight: 500;
    background: linear-gradient(135deg, #c9a961 0%, #e8c878 50%, #c9a961 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ── Shift cards ───────────────────────────────────────────────────────── */
.shift-card {
    background: linear-gradient(180deg, #1f1810 0%, #1a130b 100%);
    border: 1px solid #3a2f1f; border-radius: 8px;
    padding: 0.95rem 1.2rem; margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.35);
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}
.shift-card:hover {
    transform: translateX(3px); border-color: #c9a961;
    box-shadow: 0 4px 16px rgba(0,0,0,0.45);
}
.shift-row-inner { display: flex; justify-content: space-between; align-items: center; }
.shift-left .day { font-weight: 600; font-size: 15px; color: #f0e2c4; }
.shift-left .detail { font-size: 12px; color: #a89070; margin-top: 3px; }
.shift-right .total {
    font-family: 'DM Mono', monospace; font-size: 18px; font-weight: 500;
    background: linear-gradient(135deg, #c9a961 0%, #e8c878 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ── Section headers — art-deco gold divider ───────────────────────────── */
.section-header {
    font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 0.2em;
    text-transform: uppercase; color: #a89070; margin: 2rem 0 1rem;
    padding-bottom: 10px; position: relative;
}
.section-header::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, #c9a961 0%, #5a4630 35%, transparent 100%);
}

/* ── Widgets: inputs, selects ──────────────────────────────────────────── */
.stTextInput input, .stNumberInput input,
[data-baseweb="input"] input, [data-baseweb="base-input"] input {
    background-color: #1a130b !important;
    border: 1px solid #3a2f1f !important;
    color: #f0e2c4 !important;
    font-family: 'DM Mono', monospace !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #c9a961 !important;
    box-shadow: 0 0 0 1px rgba(201,169,97,0.3) !important;
}
.stSelectbox div[data-baseweb="select"] > div,
.stSelectbox [role="combobox"] {
    background-color: #1a130b !important;
    border-color: #3a2f1f !important;
    color: #f0e2c4 !important;
}
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"] {
    background-color: #1f1810 !important;
    border: 1px solid #3a2f1f !important;
}
[data-baseweb="menu"] li:hover { background-color: #2a1f15 !important; color: #e8c878 !important; }

/* Ensure dropdown popovers stack above everything and accept outside-click-to-close */
[data-baseweb="popover"], [data-baseweb="layer"] {
    z-index: 9999 !important;
}

.stNumberInput button {
    background-color: #2a1f15 !important; color: #c9a961 !important;
    border-color: #3a2f1f !important;
}

[data-testid="stWidgetLabel"] p, label p {
    color: #a89070 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.08em;
}

/* ── Buttons ───────────────────────────────────────────────────────────── */
.stButton button, .stFormSubmitButton button {
    background: linear-gradient(180deg, #2a1f15 0%, #1f1810 100%) !important;
    color: #f0e2c4 !important;
    border: 1px solid #3a2f1f !important;
    font-family: 'DM Mono', monospace !important;
    text-transform: uppercase; letter-spacing: 0.12em;
    font-size: 12px !important; font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
.stButton button:hover, .stFormSubmitButton button:hover {
    border-color: #c9a961 !important; color: #e8c878 !important;
    box-shadow: 0 0 16px rgba(201,169,97,0.25) !important;
}
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"],
.stButton button[kind="primaryFormSubmit"], .stFormSubmitButton button[kind="primaryFormSubmit"] {
    background: linear-gradient(180deg, #d4af6a 0%, #a8893f 100%) !important;
    color: #14100c !important; border-color: #c9a961 !important;
}
.stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover,
.stButton button[kind="primaryFormSubmit"]:hover, .stFormSubmitButton button[kind="primaryFormSubmit"]:hover {
    background: linear-gradient(180deg, #e8c878 0%, #c9a961 100%) !important;
    box-shadow: 0 0 20px rgba(201,169,97,0.4) !important;
}

/* ── Tabs ──────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid #3a2f1f !important;
    background: transparent !important; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #a89070 !important;
    font-family: 'DM Mono', monospace !important;
    text-transform: uppercase; letter-spacing: 0.08em;
    font-size: 12px !important; background: transparent !important;
}
.stTabs [aria-selected="true"] { color: #e8c878 !important; }
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { background-color: #c9a961 !important; }

/* ── Form container ────────────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: linear-gradient(180deg, #1a130b 0%, #14100c 100%) !important;
    border: 1px solid #3a2f1f !important;
    border-radius: 10px; padding: 1.2rem !important;
}

/* ── Alerts (info / success / warning / error) ─────────────────────────── */
[data-testid="stAlert"], [data-testid="stNotification"] {
    background-color: #1f1810 !important;
    border: 1px solid #3a2f1f !important;
    border-left: 3px solid #c9a961 !important;
    color: #f0e2c4 !important;
}
[data-testid="stAlert"] *, [data-testid="stNotification"] * { color: #f0e2c4 !important; }

/* ── Expander (past weeks) ─────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #1a130b !important;
    border: 1px solid #3a2f1f !important;
    border-radius: 8px;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] details > summary {
    color: #f0e2c4 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 13px !important;
}
[data-testid="stExpander"] summary p { color: #f0e2c4 !important; }
[data-testid="stExpander"] summary:hover { background: #241a10 !important; }
[data-testid="stExpander"] svg { fill: #c9a961 !important; color: #c9a961 !important; }

/* ── Mobile responsive ────────────────────────────────────────────────── */
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"], [data-testid="stAppViewContainer"] .main .block-container {
        padding: 1rem 0.85rem !important; max-width: 100% !important;
    }
    h1 { font-size: 1.85rem !important; }

    .metric-row { gap: 8px; margin-bottom: 1.25rem; }
    .metric-box {
        padding: 0.85rem 0.5rem; border-radius: 6px;
        min-width: 0; /* let flex items shrink instead of overflowing */
    }
    .metric-box .label { font-size: 9px; letter-spacing: 0.1em; margin-bottom: 5px; }
    .metric-box .value { font-size: 19px; }

    .shift-card { padding: 0.8rem 0.95rem; border-radius: 6px; margin-bottom: 8px; }
    .shift-left .day { font-size: 14px; }
    .shift-left .detail { font-size: 11px; }
    .shift-right .total { font-size: 16px; }

    .section-header { font-size: 10px; margin: 1.5rem 0 0.75rem; letter-spacing: 0.15em; }

    /* Stack form input columns on small screens */
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.5rem !important; }
    [data-testid="stHorizontalBlock"] > div { min-width: 100% !important; }

    /* Compact tab labels */
    .stTabs [data-baseweb="tab"] { font-size: 11px !important; padding: 0.5rem 0.75rem !important; }

    /* Form padding tighter */
    [data-testid="stForm"] { padding: 0.9rem !important; }

    /* Dialog (Sunday summary popup) fills the screen comfortably */
    [data-testid="stDialog"] > div, [role="dialog"] {
        width: 95vw !important; max-width: 95vw !important;
    }
}
</style>
""", unsafe_allow_html=True)


# ── Storage backend: GitHub Gist (deployed) or local JSON (dev) ──────────────
def _read_secret(key: str):
    try:
        return st.secrets.get(key)
    except Exception:
        return None

GITHUB_TOKEN = _read_secret("github_token") or os.environ.get("GITHUB_TOKEN")
GIST_ID      = _read_secret("gist_id")      or os.environ.get("GIST_ID")
USE_GIST     = bool(GITHUB_TOKEN and GIST_ID)

@st.cache_data(ttl=300, show_spinner=False)
def _gist_files() -> dict:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    r = requests.get(
        f"https://api.github.com/gists/{GIST_ID}", headers=headers, timeout=10
    )
    r.raise_for_status()
    return r.json().get("files", {})


def _gist_write(filename: str, content_str: str):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    body = {"files": {filename: {"content": content_str}}}
    r = requests.patch(
        f"https://api.github.com/gists/{GIST_ID}",
        headers=headers, json=body, timeout=10,
    )
    r.raise_for_status()
    _gist_files.clear()


def _read_json(filename: str) -> dict:
    if USE_GIST:
        try:
            content = _gist_files().get(filename, {}).get("content", "")
            return json.loads(content) if content.strip() else {}
        except Exception as e:
            st.error(f"Couldn't read {filename} from Gist: {e}")
            return {}
    if os.path.exists(filename):
        with open(filename) as f:
            return json.load(f)
    return {}


def _write_json(filename: str, payload: dict):
    content_str = json.dumps(payload, indent=2)
    if USE_GIST:
        _gist_write(filename, content_str)
    else:
        with open(filename, "w") as f:
            f.write(content_str)


def _all_data() -> dict:
    return _read_json(DATA_FILE)


def _all_profiles() -> dict:
    return _read_json(PROFILE_FILE)


def load_data(token: str) -> dict:
    return _all_data().get(token, {})


def save_data(token: str, data: dict):
    payload = _all_data()
    payload[token] = data
    _write_json(DATA_FILE, payload)


def load_profile(token: str) -> dict:
    return _all_profiles().get(token, {})


def save_profile(token: str, profile: dict):
    payload = _all_profiles()
    payload[token] = profile
    _write_json(PROFILE_FILE, payload)


def is_known_user(token: str) -> bool:
    return bool(token) and token in _all_profiles()


def generate_token() -> str:
    return secrets.token_urlsafe(24)


def current_week_key() -> str:
    today = datetime.now(LOCAL_TZ).date()
    iso = today.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def week_label(week_key: str) -> str:
    year, week = int(week_key[:4]), int(week_key[6:])
    monday = datetime.strptime(f"{year}-W{week:02d}-1", "%G-W%V-%u").date()
    sunday = datetime.strptime(f"{year}-W{week:02d}-7", "%G-W%V-%u").date()
    return f"{monday.strftime('%b %#d')} – {sunday.strftime('%b %#d, %Y')}"


def week_totals(week: dict) -> tuple:
    hours  = sum(s.get("hours", 0) for s in week.values())
    tips   = sum(s.get("tips",  0) for s in week.values())
    shifts = len(week)
    return hours, tips, shifts


def position_breakdown(week_data: dict) -> dict:
    """{position: {"shifts": int, "hours": float, "tips": float}}"""
    out: dict = {}
    for s in week_data.values():
        pos = s.get("position") or "Unspecified"
        bucket = out.setdefault(pos, {"shifts": 0, "hours": 0.0, "tips": 0.0})
        bucket["shifts"] += 1
        bucket["hours"]  += s.get("hours", 0)
        bucket["tips"]   += s.get("tips",  0)
    return out


_WEEK_KEY_RE = re.compile(r"^\d{4}-W\d{2}$")


def _migrate_legacy_if_needed():
    """If gist data is in single-tenant format, wrap it under app_token."""
    owner_token = _read_secret("app_token") or os.environ.get("APP_TOKEN")
    if not owner_token:
        return

    shifts_raw = _read_json(DATA_FILE)
    if shifts_raw and any(_WEEK_KEY_RE.match(str(k)) for k in shifts_raw.keys()):
        _write_json(DATA_FILE, {owner_token: shifts_raw})

    prof_raw = _read_json(PROFILE_FILE)
    if prof_raw and "name" in prof_raw and owner_token not in prof_raw:
        _write_json(PROFILE_FILE, {owner_token: prof_raw})


# ── One-time migration from single-tenant to multi-tenant ─────────────────────
_migrate_legacy_if_needed()

# ── Determine current user from the ?k= URL token ─────────────────────────────
visitor_token = str(st.query_params.get("k", ""))

# ── Signup flow for new visitors (no token, or token not in profiles) ─────────
if not is_known_user(visitor_token):
    st.markdown("# 🍸 Shift Tracker")

    if "_signup_token" in st.session_state:
        new_token = st.session_state["_signup_token"]
        personal_url = f"https://shift-tracker.streamlit.app/?k={new_token}"
        st.markdown(
            "<p style='color:#e8c878; font-family: \"Cormorant Garamond\", serif; "
            "font-size:22px; font-style:italic; margin:-0.5rem 0 1rem;'>"
            "Your tracker is ready.</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#f0e2c4; font-size:14px;'>"
            "Bookmark this URL — it's the only way back into your data.</p>",
            unsafe_allow_html=True,
        )
        st.code(personal_url, language=None)
        st.markdown(
            "<p style='color:#a89070; font-size:12px; margin-top:0.5rem;'>"
            "Anyone with this URL has full access to your tips. Keep it private.</p>",
            unsafe_allow_html=True,
        )
        st.link_button(
            "Open my tracker", personal_url,
            use_container_width=True, type="primary",
        )
        st.stop()

    st.markdown(
        "<p style='color:#a89070; font-family: \"Cormorant Garamond\", serif; "
        "font-size:20px; font-style:italic; margin:-0.5rem 0 1rem;'>"
        "Welcome — set up your tracker.</p>",
        unsafe_allow_html=True,
    )
    with st.form("signup"):
        name_input = st.text_input("What should we call you?", placeholder="e.g. Ethan")
        restaurant_input = st.text_input(
            "Where do you work?", placeholder="e.g. The Velvet Room"
        )
        submitted = st.form_submit_button(
            "Create my tracker", type="primary", use_container_width=True
        )
        if submitted:
            if name_input.strip() and restaurant_input.strip():
                new_token = generate_token()
                save_profile(new_token, {
                    "name": name_input.strip(),
                    "restaurant": restaurant_input.strip(),
                })
                st.session_state["_signup_token"] = new_token
                st.rerun()
            else:
                st.warning("Please fill out both fields to continue.")
    st.stop()

# ── Load current user's state ─────────────────────────────────────────────────
token       = visitor_token
profile     = load_profile(token)
data        = load_data(token)
week_key    = current_week_key()
if week_key not in data:
    data[week_key] = {}
week        = data[week_key]
name        = profile.get("name", "")
restaurant  = profile.get("restaurant", "")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🍸 Shift Tracker")
st.markdown(
    f"""<div style='display:flex; justify-content:space-between; align-items:baseline;
              flex-wrap:wrap; gap:0.5rem; margin:-0.5rem 0 0.25rem;'>
      <p style='color:#e8c878; font-family: "Cormorant Garamond", serif;
                font-size:22px; font-style:italic; margin:0;'>
        Welcome back, {name}.
      </p>
      <p style='color:#a89070; font-family: "DM Mono", monospace;
                font-size:12px; text-transform:uppercase; letter-spacing:0.18em; margin:0;'>
        {restaurant}
      </p>
    </div>""",
    unsafe_allow_html=True,
)
try:
    st.caption(f"Week of {week_label(week_key)}")
except Exception:
    st.caption(week_key)

# ── Sunday-night weekly summary popup ─────────────────────────────────────────
_now = datetime.now(LOCAL_TZ)
_today = _now.date()
_last_shown = profile.get("last_summary_shown", "")
if (_today.weekday() == 6 and _now.hour >= 18
        and _last_shown != _today.isoformat() and week):
    profile["last_summary_shown"] = _today.isoformat()
    save_profile(token, profile)

    @st.dialog(f"{name}'s Weekly Summary")
    def _weekly_summary_dialog():
        wk_hours, wk_tips, wk_shifts = week_totals(week)
        try:
            st.markdown(f"*{week_label(week_key)}*")
        except Exception:
            st.markdown(f"*{week_key}*")
        if restaurant:
            st.caption(restaurant)

        # ── By position ──
        st.markdown(
            '<div class="section-header" style="margin-top:1rem;">By position</div>',
            unsafe_allow_html=True,
        )
        for pos, totals in position_breakdown(week).items():
            s_word = "shift" if totals["shifts"] == 1 else "shifts"
            st.markdown(
                f"**{pos}** &nbsp;·&nbsp; {totals['shifts']} {s_word} · "
                f"{totals['hours']:.1f} hrs &nbsp;·&nbsp; "
                f"<span style='color:#e8c878; font-weight:600; "
                f"font-family:\"DM Mono\", monospace;'>"
                f"${totals['tips']:,.2f}</span>",
                unsafe_allow_html=True,
            )

        # ── By day ──
        st.markdown(
            '<div class="section-header">By day</div>',
            unsafe_allow_html=True,
        )
        for day in DAYS:
            if day in week:
                s = week[day]
                pos_str  = f" · {s['position']}" if s.get("position") else ""
                note_str = f" · {s['note']}"     if s.get("note")     else ""
                st.markdown(
                    f"**{day}** — ${s.get('tips', 0):,.2f} &nbsp;·&nbsp; "
                    f"{s.get('hours', 0):.1f} hrs{pos_str}{note_str}"
                )

        # ── Grand total ──
        st.markdown(f"""
        <div style="margin-top:1.5rem; padding:1.1rem;
                    border-radius:10px; text-align:center;
                    background: linear-gradient(180deg, #241a10 0%, #1a130b 100%);
                    border:1px solid #c9a961;
                    box-shadow: 0 4px 18px rgba(201,169,97,0.18),
                                inset 0 1px 0 rgba(201,169,97,0.18);">
          <div style="font-family:'DM Mono', monospace; font-size:11px;
                      color:#a89070; letter-spacing:0.22em;
                      text-transform:uppercase; margin-bottom:8px;">
            Total Earned
          </div>
          <div style="font-family:'DM Mono', monospace; font-size:30px;
                      font-weight:500;
                      background: linear-gradient(135deg, #c9a961 0%, #e8c878 50%, #c9a961 100%);
                      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                      background-clip: text;">
            ${wk_tips:,.2f}
          </div>
          <div style="font-family:'DM Sans', sans-serif; font-size:12px;
                      color:#a89070; margin-top:4px;">
            {wk_shifts} {"shift" if wk_shifts == 1 else "shifts"} · {wk_hours:.1f} hrs
          </div>
        </div>
        """, unsafe_allow_html=True)
    _weekly_summary_dialog()

# ── Summary metrics ───────────────────────────────────────────────────────────
hours, tips_total, shift_count = week_totals(week)

st.markdown(f"""
<div class="metric-row">
  <div class="metric-box">
    <div class="label">Shifts</div>
    <div class="value">{shift_count}</div>
  </div>
  <div class="metric-box">
    <div class="label">Hours</div>
    <div class="value">{hours:.1f}</div>
  </div>
  <div class="metric-box">
    <div class="label">Tips This Week</div>
    <div class="value">${tips_total:,.2f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Logged shifts ─────────────────────────────────────────────────────────────
if week:
    st.markdown("<div class=\"section-header\">This week's shifts</div>", unsafe_allow_html=True)
    for day in DAYS:
        if day not in week:
            continue
        s    = week[day]
        hrs  = s.get("hours", 0)
        tips = s.get("tips",  0)
        note = s.get("note",  "")
        pos  = s.get("position", "")
        detail_parts = [f"{hrs:.1f} hrs"]
        if pos:
            detail_parts.append(pos)
        if note:
            detail_parts.append(note)
        detail = " · ".join(detail_parts)

        st.markdown(f"""
        <div class="shift-card">
          <div class="shift-row-inner">
            <div class="shift-left">
              <div class="day">{day}</div>
              <div class="detail">{detail}</div>
            </div>
            <div class="shift-right">
              <div class="total">${tips:,.2f}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No shifts logged yet this week. Add one below.")

# ── Log / Edit a shift ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Log or edit a shift</div>', unsafe_allow_html=True)

logged_days   = [d for d in DAYS if d in week]
unlogged_days = [d for d in DAYS if d not in week]

tab_log, tab_edit = st.tabs(["➕  New shift", "✏️  Edit existing"])

# ── Tab 1: Log new shift ──────────────────────────────────────────────────────
with tab_log:
    if not unlogged_days:
        st.success("Every day this week has been logged!")
    else:
        with st.form("log_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                day_new   = st.selectbox("Day", unlogged_days)
                hours_new = st.number_input(
                    "Hours worked", min_value=0.0, max_value=24.0,
                    step=0.5, value=6.0, format="%.1f"
                )
                position_new = st.selectbox(
                    "Position", ["Serving", "Bartending", "Other"]
                )
            with col2:
                tips_new = st.number_input(
                    "Tips earned ($)", min_value=0.0,
                    step=0.50, value=0.0, format="%.2f"
                )
                note_new = st.text_input(
                    "Note (optional)", placeholder="e.g. double shift, slow night"
                )
                position_other_new = st.text_input(
                    "If 'Other', specify", placeholder="e.g. Hosting, Barback"
                )

            submitted = st.form_submit_button(
                "Save shift", use_container_width=True, type="primary"
            )
            if submitted:
                position_to_save = (
                    position_other_new.strip()
                    if position_new == "Other" and position_other_new.strip()
                    else position_new
                )
                week[day_new] = {
                    "hours": hours_new, "tips": tips_new,
                    "note": note_new, "position": position_to_save,
                }
                data[week_key] = week
                save_data(token, data)
                st.success(f"{day_new} logged — ${tips_new:,.2f} in tips!")
                st.rerun()

# ── Tab 2: Edit existing shift ────────────────────────────────────────────────
with tab_edit:
    if not logged_days:
        st.info("No shifts logged yet to edit.")
    else:
        with st.form("edit_form", clear_on_submit=False):
            # Default the selector to the most recently logged day
            default_idx = DAYS.index(logged_days[-1])
            day_edit = st.selectbox("Select day to edit", DAYS, index=default_idx)

            existing = week.get(day_edit, {})
            existing_pos = existing.get("position", "")
            known_positions = ["Serving", "Bartending", "Other"]
            if existing_pos in ("Serving", "Bartending"):
                initial_pos_idx, initial_pos_other = known_positions.index(existing_pos), ""
            elif existing_pos:
                initial_pos_idx, initial_pos_other = 2, existing_pos
            else:
                initial_pos_idx, initial_pos_other = 0, ""

            col1, col2 = st.columns(2)
            with col1:
                hours_edit = st.number_input(
                    "Hours worked", min_value=0.0, max_value=24.0,
                    step=0.5, value=float(existing.get("hours", 6.0)), format="%.1f"
                )
                position_edit = st.selectbox(
                    "Position", known_positions, index=initial_pos_idx
                )
            with col2:
                tips_edit = st.number_input(
                    "Tips earned ($)", min_value=0.0, step=0.50,
                    value=float(existing.get("tips", 0.0)), format="%.2f"
                )
                note_edit = st.text_input("Note (optional)", value=existing.get("note", ""))
                position_other_edit = st.text_input(
                    "If 'Other', specify", value=initial_pos_other,
                    placeholder="e.g. Hosting, Barback"
                )

            col_save, col_delete = st.columns([3, 1])
            with col_save:
                save_edit = st.form_submit_button(
                    "Update shift", use_container_width=True, type="primary"
                )
            with col_delete:
                delete_shift = st.form_submit_button(
                    "Delete", use_container_width=True
                )

            if save_edit:
                position_to_save = (
                    position_other_edit.strip()
                    if position_edit == "Other" and position_other_edit.strip()
                    else position_edit
                )
                week[day_edit] = {
                    "hours": hours_edit, "tips": tips_edit, "note": note_edit,
                    "position": position_to_save,
                }
                data[week_key] = week
                save_data(token, data)
                st.success(f"{day_edit} updated!")
                st.rerun()

            if delete_shift and day_edit in week:
                del week[day_edit]
                data[week_key] = week
                save_data(token, data)
                st.warning(f"{day_edit} removed.")
                st.rerun()

# ── Past weeks ────────────────────────────────────────────────────────────────
past_weeks = sorted([k for k in data if k != week_key], reverse=True)
if past_weeks:
    st.markdown('<div class="section-header">Past weeks</div>', unsafe_allow_html=True)

    show_all = False
    if len(past_weeks) > 4:
        show_all = st.toggle(f"Show all ({len(past_weeks)} weeks)", value=False)

    visible_weeks = past_weeks if show_all else past_weeks[:4]
    for wk in visible_weeks:
        wk_hours, wk_tips, wk_shifts = week_totals(data[wk])
        try:
            label = week_label(wk)
        except Exception:
            label = wk
        with st.expander(f"{label}  —  ${wk_tips:,.2f}"):
            for day in DAYS:
                if day not in data[wk]:
                    continue
                s = data[wk][day]
                pos_str  = f" · {s['position']}" if s.get("position") else ""
                note_str = f" · {s['note']}"     if s.get("note")     else ""
                st.markdown(
                    f"**{day}** — ${s.get('tips', 0):,.2f} &nbsp;·&nbsp; "
                    f"{s.get('hours', 0):.1f} hrs{pos_str}{note_str}"
                )
            st.caption(f"{wk_shifts} shifts · {wk_hours:.1f} hrs total")
