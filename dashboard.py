"""
dashboard.py — Streamlit dashboard for Spectatr lead outreach review.

Reads from the PersonalisedLeads Google Sheet tab and displays contacts
grouped by company with a Top Leads sidebar and date filtering.

Run: streamlit run dashboard.py
"""

import os
from datetime import date as date_type

import gspread
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

st.set_page_config(
    page_title="Spectatr — Lead Intelligence",
    page_icon="🎯",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

st.markdown("""<style>
/* ── Page background ── */
[data-testid="stAppViewContainer"] { background: #f4f6f9; }
[data-testid="stHeader"] { background: transparent; }
.main .block-container { padding-top: 3rem !important; }

/* ── Force light textarea regardless of Streamlit theme ── */
div[data-testid="stTextArea"] textarea {
    background-color: #ffffff !important;
    color: #111827 !important;
}

/* ── Stat boxes ── */
.stat-box {
    background: #ffffff;
    border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    padding: 14px 18px;
    text-align: center;
    margin-bottom: 8px;
}
.stat-number { font-size: 1.8rem; font-weight: 800; color: #1a1a2e; line-height: 1; }
.stat-label  { font-size: 0.72rem; color: #999; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.04em; }

/* ── Company block ── */
.company-block {
    border-left: 3px solid #d1d5db;
    padding-left: 14px;
    margin: 24px 0 10px 0;
}
.company-header {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0 0 3px 0;
}
.company-sub {
    font-size: 0.80rem;
    color: #9ca3af;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 95%;
    margin-bottom: 5px;
}
.company-article-link a {
    font-size: 0.78rem;
    color: #6b7280;
    text-decoration: none;
}
.company-article-link a:hover { text-decoration: underline; }

/* ── Lead cards ── */
.lead-card {
    background: #ffffff;
    border-radius: 10px 10px 0 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    padding: 14px 18px 10px 18px;
    margin-top: 8px;
    margin-bottom: 0;
}
.lead-name {
    font-size: 0.93rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 2px;
}
.lead-name a {
    color: #6366f1;
    text-decoration: none;
    font-size: 0.80rem;
    font-weight: 500;
    margin-left: 6px;
}
.lead-title {
    font-size: 0.80rem;
    color: #6b7280;
    margin-bottom: 8px;
}
.lead-badges { margin-bottom: 2px; }

/* ── Badges ── */
.badge {
    display: inline-block;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-right: 5px;
    vertical-align: middle;
}
.badge-funding    { background: #d1fae5; color: #065f46; }
.badge-broadcast  { background: #dbeafe; color: #1e40af; }
.badge-sponsor    { background: #ede9fe; color: #5b21b6; }
.badge-launch     { background: #ccfbf1; color: #0f766e; }
.badge-general    { background: #f3f4f6; color: #6b7280; }
.badge-score-high { background: #d1fae5; color: #065f46; }
.badge-score-mid  { background: #fef3c7; color: #92400e; }
.badge-score-low  { background: #f3f4f6; color: #9ca3af; }

/* ── Message code block styled as message box ── */
div[data-testid="stCodeBlock"] {
    margin-bottom: 16px !important;
}
div[data-testid="stCodeBlock"] pre {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: 0.82rem !important;
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 0 0 10px 10px !important;
    border-top: 1px solid #e5e7eb !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07) !important;
    color: #111827 !important;
    line-height: 1.5 !important;
}

/* ── Pipeline overview card ── */
.pipeline-card {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    padding: 16px 18px;
    margin-bottom: 4px;
}
.pipeline-card-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 14px;
}
.pipeline-row {
    display: flex;
    align-items: center;
    justify-content: space-around;
}
.pipe-step { text-align: center; flex: 1; }
.pipe-num  { font-size: 1.6rem; font-weight: 800; color: #1a1a2e; line-height: 1; }
.pipe-label {
    font-size: 0.68rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 5px;
}
.pipe-arrow { color: #d1d5db; font-size: 1.1rem; padding-bottom: 12px; flex: 0; }

/* ── Sidebar panel ── */
.sidebar-panel {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    padding: 18px 16px;
}
.sidebar-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #1a1a2e;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid #f3f4f6;
}
.top-lead-row {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 10px 0;
    border-bottom: 1px solid #f3f4f6;
}
.top-lead-row:last-child { border-bottom: none; }
.rank-num {
    font-size: 1.1rem;
    font-weight: 800;
    color: #d1d5db;
    min-width: 26px;
    padding-top: 2px;
}
.rank-num.top3 { color: #f59e0b; }
.top-lead-name {
    font-weight: 700;
    font-size: 0.86rem;
    color: #111827;
}
.top-lead-name a {
    color: #6366f1;
    font-size: 0.76rem;
    font-weight: 500;
    text-decoration: none;
    margin-left: 5px;
}
.top-lead-co {
    font-size: 0.76rem;
    color: #9ca3af;
    margin-bottom: 4px;
}
.top-lead-article a {
    font-size: 0.72rem;
    color: #6b7280;
    text-decoration: none;
    display: block;
    margin: 3px 0 2px 0;
}
.top-lead-article a:hover { text-decoration: underline; }
.top-lead-msg {
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 5px;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* ── Divider spacing ── */
hr { margin: 10px 0 !important; }
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Badge helpers
# ---------------------------------------------------------------------------

_SIGNAL_MAP: dict[str, tuple[str, str]] = {
    "funding/investment":  ("badge-funding",   "Funding"),
    "broadcast deal":      ("badge-broadcast", "Broadcast"),
    "sponsorship deal":    ("badge-sponsor",   "Sponsorship"),
    "platform launch":     ("badge-launch",    "Platform Launch"),
    "new season/expansion":("badge-general",   "New Season"),
    "general coverage":    ("badge-general",   "Coverage"),
}


def _signal_badge(signal: str) -> tuple[str, str]:
    return _SIGNAL_MAP.get(signal.strip().lower(), ("badge-general", signal or "Signal"))


def _score_badge(score_raw: str) -> tuple[str, str]:
    try:
        s = int(float(score_raw))
    except (ValueError, TypeError):
        return ("badge-score-low", "—")
    if s >= 70:
        return ("badge-score-high", str(s))
    if s >= 50:
        return ("badge-score-mid", str(s))
    return ("badge-score-low", str(s))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_resource
def _get_gs_client() -> gspread.Client:
    import json as _json
    gcp_json = st.secrets.get("GCP_CREDENTIALS_JSON", "") or os.getenv("GCP_CREDENTIALS_JSON", "")
    if gcp_json:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            _json.loads(gcp_json), _SCOPES
        )
    else:
        default_creds = os.path.join(os.path.dirname(__file__), "credentials.json")
        creds_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", default_creds)
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, _SCOPES)
    return gspread.authorize(creds)


@st.cache_data(ttl=300)
def load_pipeline_counts() -> dict[str, int]:
    spreadsheet_id = os.getenv("OUTPUT_SPREADSHEET_ID") or st.secrets.get("OUTPUT_SPREADSHEET_ID", "")
    if not spreadsheet_id:
        return {}
    ss = _get_gs_client().open_by_key(spreadsheet_id)
    counts: dict[str, int] = {}
    for tab, key in [
        ("MarketingLeads",    "Articles"),
        ("ApolloLeads",       "Contacts"),
        ("PersonalisedLeads", "Messages"),
    ]:
        try:
            rows = ss.worksheet(tab).get_all_values()
            counts[key] = max(0, len(rows) - 1)
        except Exception:
            counts[key] = 0
    return counts


@st.cache_data(ttl=300)
def load_leads() -> pd.DataFrame:
    spreadsheet_id = os.getenv("OUTPUT_SPREADSHEET_ID") or st.secrets.get("OUTPUT_SPREADSHEET_ID", "")
    if not spreadsheet_id:
        st.error("OUTPUT_SPREADSHEET_ID is not set in .env or Streamlit secrets")
        return pd.DataFrame()

    sheet_name = os.getenv("COLD_AGENT_OUTPUT_SHEET") or st.secrets.get("COLD_AGENT_OUTPUT_SHEET", "PersonalisedLeads")
    try:
        ws = _get_gs_client().open_by_key(spreadsheet_id).worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        st.error(f"Sheet tab '{sheet_name}' not found. Run the pipeline first.")
        return pd.DataFrame()

    rows = ws.get_all_values()
    if len(rows) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df[df.get("linkedin_profile", pd.Series(dtype=str)).str.strip() != ""]
    df = df.reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Header zone
# ---------------------------------------------------------------------------

st.title("Spectatr — Lead Intelligence")

df = load_leads()

if df.empty:
    st.info("No leads found. Run the pipeline with COLD_AGENT_ENABLED=true first.")
    st.stop()

has_dates = "date_processed" in df.columns and df["date_processed"].str.strip().any()

# Build sorted available dates (proper date sort, not string sort)
if has_dates:
    _date_str_to_obj: dict[str, date_type] = {}
    for _d in df["date_processed"].str.strip().unique():
        try:
            _date_str_to_obj[_d] = pd.to_datetime(_d).date()
        except Exception:
            pass
    _sorted_date_strs = sorted(_date_str_to_obj, key=lambda d: _date_str_to_obj[d], reverse=True)
    _available_dates = [_date_str_to_obj[d] for d in _sorted_date_strs]
else:
    _sorted_date_strs = []
    _available_dates = []

ctrl_l, ctrl_spacer, ctrl_r = st.columns([2, 6, 1])
with ctrl_l:
    if has_dates:
        selected_date_obj = st.date_input(
            "Date",
            value=_available_dates[0],
            min_value=_available_dates[-1],
            max_value=_available_dates[0],
            label_visibility="collapsed",
        )
        # Match back to sheet string
        selected_date = next(
            (s for s, d in _date_str_to_obj.items() if d == selected_date_obj), None
        )
        filtered = df[df["date_processed"] == selected_date].copy() if selected_date else pd.DataFrame()
    else:
        st.caption("No date data — showing all leads.")
        filtered = df.copy()
        selected_date = "all time"

with ctrl_r:
    if st.button("Refresh", use_container_width=True):
        load_leads.clear()
        load_pipeline_counts.clear()
        st.rerun()

if filtered.empty:
    st.info("No leads for this date.")
    st.stop()

# Stats row
scores_all = pd.to_numeric(filtered["score"], errors="coerce").fillna(0)
n_companies = filtered["company_name"].nunique()
n_leads = len(filtered)
n_high = int((scores_all >= 70).sum())
avg_score = f"{scores_all.mean():.0f}" if len(scores_all) else "—"

s1, s2, s3, s4 = st.columns(4)
for col, number, label in [
    (s1, n_companies, "Companies"),
    (s2, n_leads,     "Leads"),
    (s3, n_high,      "High Intent"),
    (s4, avg_score,   "Avg Score"),
]:
    with col:
        st.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-number">{number}</div>'
            f'<div class="stat-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.divider()

# ---------------------------------------------------------------------------
# Chart constants
# ---------------------------------------------------------------------------

_SIGNAL_COLORS: dict[str, str] = {
    "Funding/Investment":  "#10b981",
    "Broadcast Deal":      "#3b82f6",
    "Sponsorship Deal":    "#8b5cf6",
    "Platform Launch":     "#14b8a6",
    "New Season/Expansion":"#f59e0b",
    "General Coverage":    "#9ca3af",
}

_CHART_CONFIG = {"displayModeBar": False}

_CHART_LAYOUT = dict(
    margin=dict(l=10, r=10, t=36, b=10),
    paper_bgcolor="white",
    plot_bgcolor="white",
    font_family="sans-serif",
    title_font_size=13,
    title_font_color="#1a1a2e",
)

# ---------------------------------------------------------------------------
# Two-column body
# ---------------------------------------------------------------------------

main_col, side_col = st.columns([11, 9])

# ── Left: company-grouped lead feed ────────────────────────────────────────

with main_col:
    for company_name, group in filtered.groupby("company_name", sort=False):
        first = group.iloc[0]
        desc = str(first.get("company_description", "") or "").strip()
        article_url = str(first.get("article_url", "") or "").strip()
        article_title = str(first.get("article_title", "") or "").strip()
        n_leads_co = len(group)

        label = f"{company_name}  ·  {n_leads_co} lead{'s' if n_leads_co != 1 else ''}"
        with st.expander(label, expanded=False):
            if desc:
                st.caption(desc)
            if article_url:
                link_label = article_title if article_title else "Source Article"
                st.markdown(
                    f'<div class="company-article-link">'
                    f'<a href="{article_url}" target="_blank">↗ {link_label}</a>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            if desc or article_url:
                st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

            for i, row in group.iterrows():
                full_name = (str(row.get("full_name", "") or "")).strip() or \
                            f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                job_title = str(row.get("job_title", "") or "").strip()
                linkedin  = str(row.get("linkedin_profile", "") or "").strip()
                message   = str(row.get("personalised_message", "") or "")
                signal    = str(row.get("lead_signal", "") or "").strip()
                score_raw = str(row.get("score", "") or "").strip()

                sig_cls, sig_lbl = _signal_badge(signal)
                sc_cls,  sc_lbl  = _score_badge(score_raw)

                li_html = (
                    f'<a href="{linkedin}" target="_blank">↗ LinkedIn</a>'
                    if linkedin else ""
                )

                st.markdown(
                    f'<div class="lead-card">'
                    f'<div class="lead-name">{full_name} {li_html}</div>'
                    f'<div class="lead-title">{job_title}</div>'
                    f'<div class="lead-badges">'
                    f'<span class="badge {sig_cls}">{sig_lbl}</span>'
                    f'<span class="badge {sc_cls}">Score {sc_lbl}</span>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.code(message, language=None)

# ── Right column ────────────────────────────────────────────────────────────

def _render_side_panel(data: pd.DataFrame, top_leads_title: str, show_pipeline: bool = False) -> None:
    """Render charts + top leads for a given dataframe slice."""
    data_scores = pd.to_numeric(data["score"], errors="coerce").fillna(0)

    # Pipeline overview (all-time only)
    if show_pipeline:
        pipeline = load_pipeline_counts()
        if pipeline:
            articles = pipeline.get("Articles", 0)
            contacts = pipeline.get("Contacts", 0)
            messages = pipeline.get("Messages", 0)
            st.markdown(
                f'<div class="pipeline-card">'
                f'<div class="pipeline-card-title">Pipeline Overview (All Time)</div>'
                f'<div class="pipeline-row">'
                f'  <div class="pipe-step"><div class="pipe-num">{articles}</div><div class="pipe-label">Articles</div></div>'
                f'  <div class="pipe-arrow">→</div>'
                f'  <div class="pipe-step"><div class="pipe-num">{contacts}</div><div class="pipe-label">Contacts</div></div>'
                f'  <div class="pipe-arrow">→</div>'
                f'  <div class="pipe-step"><div class="pipe-num">{messages}</div><div class="pipe-label">Messages</div></div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Leads by Signal (donut)
    sig_counts = data["lead_signal"].value_counts().reset_index()
    sig_counts.columns = ["Signal", "Count"]
    sig_counts["Signal"] = sig_counts["Signal"].str.title()
    fig1 = px.pie(
        sig_counts, names="Signal", values="Count", hole=0.55,
        color="Signal", color_discrete_map=_SIGNAL_COLORS, title="Leads by Signal",
    )
    fig1.update_traces(textposition="inside", textinfo="percent")
    fig1.update_layout(
        **_CHART_LAYOUT, height=240, showlegend=True,
        legend=dict(orientation="v", x=1.0, y=0.5, font=dict(size=10)),
    )
    st.plotly_chart(fig1, use_container_width=True, config=_CHART_CONFIG)

    # Avg Score by Company
    co_scores = (
        data.assign(_s=data_scores)
        .groupby("company_name")["_s"].mean()
        .nlargest(6).sort_values(ascending=True).reset_index()
        .rename(columns={"company_name": "Company", "_s": "Avg Score"})
    )
    co_scores["Company"] = co_scores["Company"].apply(
        lambda n: (n[:18] + "…") if len(n) > 18 else n
    )
    fig2 = px.bar(
        co_scores, x="Avg Score", y="Company", orientation="h",
        title="Avg Score by Company",
        text=co_scores["Avg Score"].round(0).astype(int),
    )
    fig2.update_traces(marker_color="#6366f1", textposition="inside", insidetextanchor="end")
    fig2.update_layout(
        **_CHART_LAYOUT, height=240, showlegend=False, bargap=0.35,
        xaxis=dict(title="", range=[0, 105], showgrid=True, gridcolor="#f3f4f6"),
        yaxis=dict(title=""),
    )
    st.plotly_chart(fig2, use_container_width=True, config=_CHART_CONFIG)

    # Avg Score by Signal
    sig_scores = (
        data.assign(_s=data_scores)
        .groupby("lead_signal")["_s"].mean()
        .reset_index()
        .rename(columns={"lead_signal": "Signal", "_s": "Avg Score"})
    )
    sig_scores["Signal"] = sig_scores["Signal"].str.title()
    sig_scores = sig_scores.sort_values("Avg Score", ascending=True)
    fig3 = px.bar(
        sig_scores, x="Avg Score", y="Signal", orientation="h",
        title="Avg Score by Signal",
        text=sig_scores["Avg Score"].round(0).astype(int),
        color="Signal", color_discrete_map=_SIGNAL_COLORS,
    )
    fig3.update_traces(textposition="inside", insidetextanchor="end")
    fig3.update_layout(
        **_CHART_LAYOUT, height=240, showlegend=False, bargap=0.35,
        xaxis=dict(title="", range=[0, 105], showgrid=True, gridcolor="#f3f4f6"),
        yaxis=dict(title=""),
    )
    st.plotly_chart(fig3, use_container_width=True, config=_CHART_CONFIG)

    # Top Leads
    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)
    top5 = data.assign(_s=data_scores).nlargest(5, "_s")
    parts: list[str] = [
        f'<div class="sidebar-panel"><div class="sidebar-title">{top_leads_title}</div>'
    ]
    for rank, (_, row) in enumerate(top5.iterrows(), start=1):
        full_name = (str(row.get("full_name", "") or "")).strip() or \
                    f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
        company       = str(row.get("company_name", "") or "").strip()
        job_title     = str(row.get("job_title", "") or "").strip()
        linkedin      = str(row.get("linkedin_profile", "") or "").strip()
        message       = str(row.get("personalised_message", "") or "")
        signal        = str(row.get("lead_signal", "") or "").strip()
        score_raw     = str(row.get("score", "") or "").strip()
        article_url   = str(row.get("article_url", "") or "").strip()
        article_title = str(row.get("article_title", "") or "").strip()
        sig_cls, sig_lbl = _signal_badge(signal)
        sc_cls,  sc_lbl  = _score_badge(score_raw)
        rank_class = "top3" if rank <= 3 else ""
        li_html    = f'<a href="{linkedin}" target="_blank">↗</a>' if linkedin else ""
        preview    = message[:160].replace("<", "&lt;").replace(">", "&gt;")
        ellipsis   = "…" if len(message) > 160 else ""
        art_label  = (article_title[:45] + "…") if len(article_title) > 45 else article_title
        art_html   = (
            f'<div class="top-lead-article">'
            f'<a href="{article_url}" target="_blank">↗ {art_label or "Source Article"}</a>'
            f'</div>'
        ) if article_url else ""
        parts.append(
            f'<div class="top-lead-row">'
            f'<div class="rank-num {rank_class}">#{rank}</div>'
            f'<div style="flex:1;min-width:0">'
            f'<div class="top-lead-name">{full_name} {li_html}</div>'
            f'<div class="top-lead-co">{company} · {job_title}</div>'
            f'<span class="badge {sig_cls}">{sig_lbl}</span>'
            f'<span class="badge {sc_cls}">{sc_lbl}</span>'
            f'{art_html}'
            f'<div class="top-lead-msg">{preview}{ellipsis}</div>'
            f'</div></div>'
        )
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


with side_col:
    tab_day, tab_all = st.tabs(["Selected Date", "All Time"])

    with tab_day:
        _render_side_panel(filtered, top_leads_title="Top Leads", show_pipeline=False)

    with tab_all:
        _render_side_panel(df, top_leads_title="Top Leads (All Time)", show_pipeline=True)
