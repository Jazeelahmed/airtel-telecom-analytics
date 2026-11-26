import base64
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------------ config
HERE = Path(__file__).parent
DB = HERE / "airtel.db"
RED, DARK, GREY = "#E40000", "#1F1F1F", "#6B6B6B"
REDS = ["#FFE3E3", "#FF9B9B", "#E40000", "#6E0000"]
IMG = (".png", ".jpg", ".jpeg", ".svg", ".webp")

st.set_page_config(page_title="Airtel Insights", page_icon="📶", layout="wide",
                   initial_sidebar_state="expanded")


def find_logo():
    """Any image with 'logo' or 'airtel' in its name, next to this file."""
    for folder in (HERE, HERE / "assets", HERE / "data", HERE / "images", HERE / "static"):
        if not folder.is_dir():
            continue
        for f in sorted(folder.iterdir()):
            n = f.name.lower()
            if f.is_file() and f.suffix.lower() in IMG and ("logo" in n or "airtel" in n):
                return f
    return None


# ------------------------------------------------------------------ styling
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
html, body, .stApp, [class*="css"] { font-family:'Plus Jakarta Sans',sans-serif; }
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {
  background:linear-gradient(160deg,#F20000 0%,#C40000 55%,#8F0000 100%) fixed !important; }
header[data-testid="stHeader"] { background:transparent !important; }
footer, #MainMenu { display:none; }
.block-container { padding:0.8rem 1.4rem 0.4rem !important; max-width:100% !important; }

[data-testid="stSidebar"] > div:first-child {
  background:linear-gradient(180deg,#5A0000 0%,#330000 100%) !important; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { color:#fff !important; }
[data-testid="stSidebar"] label p { font-size:.8rem; font-weight:600; }
[data-testid="stSidebar"] div[data-baseweb="select"] > div { background:#fff; border-radius:10px; }
[data-testid="stSidebar"] div[data-baseweb="select"] * { color:#1F1F1F !important; }
[data-testid="stSidebar"] button { background:#fff; color:%RED% !important; border-radius:999px;
  font-weight:700; border:0; width:100%; }
[data-testid="stSidebar"] button p { color:%RED% !important; }
.sbt { color:#fff; font-weight:800; font-size:1.05rem; margin:0 0 2px; }
.sbs { color:rgba(255,255,255,.75); font-size:.72rem; margin-bottom:10px; }
.sbh { color:#fff; font-weight:800; font-size:.82rem; margin:14px 0 2px;
  padding-bottom:4px; border-bottom:2px solid %RED%; }

.topbar { display:flex; align-items:center; justify-content:space-between; color:#fff;
  background:linear-gradient(110deg,#4A0000 0%,#7A0000 100%); border-radius:18px;
  padding:10px 22px; box-shadow:0 10px 26px rgba(0,0,0,.35);
  animation:drop .7s cubic-bezier(.2,.8,.2,1) both; }
.topbar h1 { font-size:1.2rem; font-weight:800; margin:0; color:#fff; }
.topbar span { color:rgba(255,255,255,.85); font-size:.78rem; }
.logo { background:#fff; border-radius:12px; padding:4px 14px; }
.logo svg, .logo img { height:34px; display:block; }

.kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:12px 0 8px; }
.kpi { display:flex; align-items:center; gap:12px; background:#fff; border-radius:14px;
  padding:9px 16px; box-shadow:0 6px 16px rgba(0,0,0,.25); animation:rise .6s ease both; }
.kpi:nth-child(2){animation-delay:.08s} .kpi:nth-child(3){animation-delay:.16s} .kpi:nth-child(4){animation-delay:.24s}
.kpi i { font-style:normal; width:40px; height:40px; border-radius:50%; flex:none; display:flex;
  align-items:center; justify-content:center; font-size:1.15rem;
  background:linear-gradient(135deg,#FFE3E3,#FFC9C9); }
.kpi b { display:block; font-size:1.4rem; font-weight:800; color:#1F1F1F; line-height:1.15; }
.kpi small { color:#6B6B6B; font-size:.72rem; }

div[data-baseweb="tab-list"] { gap:8px; }
button[data-baseweb="tab"] { background:#fff; border-radius:999px; padding:6px 20px;
  box-shadow:0 4px 12px rgba(0,0,0,.25); }
button[data-baseweb="tab"] p { color:%RED%; font-weight:700; }
button[aria-selected="true"] { background:#2B0000 !important; }
button[aria-selected="true"] p { color:#fff !important; }
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display:none; }
div[data-testid="stTabPanel"] { animation:fade .5s ease both; padding-top:10px; }

div[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border-radius:18px;
  border:0; padding:4px 10px 2px; box-shadow:0 8px 22px rgba(0,0,0,.28);
  transition:box-shadow .25s, transform .25s; }
div[data-testid="stVerticalBlockBorderWrapper"]:hover { box-shadow:0 14px 32px rgba(0,0,0,.4); transform:translateY(-2px); }
.ctitle { display:flex; align-items:center; justify-content:space-between; gap:8px;
  white-space:nowrap; font-weight:800; font-size:.95rem; margin:2px 0 0; color:#1F1F1F; }
.tt { overflow:hidden; text-overflow:ellipsis; min-width:0; }
.tt:before { content:""; display:inline-block; width:8px; height:8px; border-radius:50%;
  background:%RED%; margin-right:7px; }
.chip { flex:none; max-width:50%; overflow:hidden; text-overflow:ellipsis; background:#FFF0F0;
  color:#B00000; border-radius:999px; font-size:.66rem; font-weight:700; padding:1px 9px; }
.how { color:#6B6B6B; font-size:.72rem; line-height:1.25; height:2.5em; overflow:hidden; margin:2px 0; }
.ins { background:#FFF4F4; border-left:3px solid %RED%; border-radius:6px; color:#1F1F1F;
  font-size:.72rem; line-height:1.3; height:3.9em; overflow:hidden; padding:4px 8px; margin:2px 0 6px;
  display:flex; align-items:center; }

@keyframes drop { from {opacity:0; transform:translateY(-20px)} to {opacity:1; transform:none} }
@keyframes rise { from {opacity:0; transform:translateY(16px)} to {opacity:1; transform:none} }
@keyframes fade { from {opacity:0} to {opacity:1} }
@media (prefers-reduced-motion:reduce) { * { animation:none !important; transition:none !important; } }
</style>
""".replace("%RED%", RED)
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------------------ data
FEATURES_SQL = """
SELECT c.customer_id, ci.circle_name, ci.region, p.plan_name, p.plan_type,
  c.connection_type, c.acquisition_channel, c.age_band, c.is_churned,
  COALESCE(r.tot, 0) / 6.0 AS actual_arpu_6m,
  COALESCE(k.n, 0) AS complaint_count
FROM customers c
JOIN circles ci ON ci.circle_id = c.circle_id
LEFT JOIN plans p ON p.plan_id = c.current_plan_id
LEFT JOIN (SELECT customer_id, SUM(amount_inr) AS tot FROM recharges
           WHERE recharge_date >= '2025-01-01' GROUP BY customer_id) r
           ON r.customer_id = c.customer_id
LEFT JOIN (SELECT customer_id, COUNT(*) AS n FROM complaints GROUP BY customer_id) k
           ON k.customer_id = c.customer_id
"""


@st.cache_data(show_spinner="Loading Airtel data…")
def q(sql: str) -> pd.DataFrame:
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query(sql, con)


if not DB.exists() or DB.stat().st_size == 0:
    st.error(f"airtel.db is missing or empty. Copy the full database next to this file ({HERE}).")
    st.stop()

tables = set(q("SELECT name FROM sqlite_master WHERE type='table'")["name"])
base = {"customers", "plans", "circles", "recharges", "complaints"}
if not base <= tables:
    st.error(f"This airtel.db is missing tables: {', '.join(sorted(base - tables))}. "
             f"Tables found: {', '.join(sorted(tables)) or 'none'}. Use the full airtel.db.")
    st.stop()

cf = q(FEATURES_SQL)
complaints = q("SELECT category, is_resolved, resolution_days FROM complaints")
rev = q("""SELECT r.txn_type, p.plan_name, SUM(r.amount_inr) AS revenue
           FROM recharges r JOIN plans p ON p.plan_id = r.plan_id GROUP BY 1,2""")
act = q("SELECT substr(activation_date,1,7) AS m, COUNT(*) AS n FROM customers GROUP BY 1")
chn = q("""SELECT substr(churn_date,1,7) AS m, COUNT(*) AS n FROM customers
           WHERE churn_date IS NOT NULL GROUP BY 1""")

YEARS = sorted({m[:4] for m in pd.concat([act["m"], chn["m"]]).dropna()})
DEFAULT_YEAR = YEARS[-2] if len(YEARS) > 1 else YEARS[0]


def options(series):
    return ["All"] + sorted(series.dropna().astype(str).unique())


# ------------------------------------------------------------------ sidebar filters
KEYS = ["f1", "f2", "f3", "f4", "f5", "f6"]


def reset_filters():
    for k in KEYS:
        st.session_state[k] = DEFAULT_YEAR if k == "f6" else "All"


sb = st.sidebar
sb.markdown('<div class="sbt">Filters</div><div class="sbs">Each filter changes only the '
            'chart named next to it.</div>', unsafe_allow_html=True)
sb.markdown('<div class="sbh">Tab 1 · Customers & Churn</div>', unsafe_allow_html=True)
f1 = sb.selectbox("Chart 1 · Customer map: connection type", options(cf["connection_type"]), key="f1")
f2 = sb.selectbox("Chart 2 · Churn gap: region", options(cf["region"]), key="f2")
f3 = sb.selectbox("Chart 3 · Customer flow: age group", options(cf["age_band"]), key="f3")
sb.markdown('<div class="sbh">Tab 2 · Revenue & Service</div>', unsafe_allow_html=True)
f4 = sb.selectbox("Chart 4 · Plan revenue: payment type", options(rev["txn_type"]), key="f4")
f5 = sb.selectbox("Chart 5 · Complaints: category", options(complaints["category"]), key="f5")
f6 = sb.selectbox("Chart 6 · Growth: year", YEARS, index=YEARS.index(DEFAULT_YEAR), key="f6")
sb.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
sb.button("Reset all filters", on_click=reset_filters)


# ------------------------------------------------------------------ helpers
_n = {"i": 0}


def style(fig, h=285):
    fig.update_layout(
        height=h, margin=dict(l=6, r=6, t=6, b=6),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color=DARK),
        transition=dict(duration=500, easing="cubic-in-out"))
    return fig


def card(title, how, flt):
    box = st.container(border=True)
    box.markdown(f'<div class="ctitle"><span class="tt">{title}</span><span class="chip">{flt}</span></div>'
                 f'<div class="how">{how}</div>', unsafe_allow_html=True)
    return box


def show(box, fig, insight, empty=False):
    _n["i"] += 1
    if empty:
        box.info("No data for this filter. Pick another option in the left panel.")
        return
    cfg = {"displayModeBar": False}
    try:
        box.plotly_chart(fig, width="stretch", key=f"chart{_n['i']}", config=cfg)
    except TypeError:
        box.plotly_chart(fig, use_container_width=True, key=f"chart{_n['i']}", config=cfg)
    box.markdown(f'<div class="ins">💡 {insight}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ header
LOGO = find_logo()
if LOGO is not None:
    mime = {".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp"}.get(LOGO.suffix.lower(), "image/png")
    logo_html = f'<img src="data:{mime};base64,{base64.b64encode(LOGO.read_bytes()).decode()}">'
else:
    logo_html = (
        '<svg viewBox="0 0 190 50" xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="2" y="4" width="42" height="42" rx="12" fill="{RED}"/>'
        '<text x="23" y="38" text-anchor="middle" font-size="36" font-weight="800" '
        'font-family="Arial" fill="#fff">a</text>'
        f'<text x="54" y="37" font-size="34" font-weight="800" font-family="Arial" '
        f'fill="{RED}">airtel</text></svg>')

st.markdown(
    f'<div class="topbar"><div><h1>Customer, Churn &amp; Revenue Insights</h1>'
    f'<span>{len(cf):,} customers · pick filters in the left panel · version 4</span></div>'
    f'<div class="logo">{logo_html}</div></div>', unsafe_allow_html=True)

churn_rate = cf["is_churned"].mean() * 100
st.markdown(
    f"""<div class="kpis">
  <div class="kpi"><i>👥</i><div><b>{len(cf):,}</b><small>Total customers</small></div></div>
  <div class="kpi"><i>📉</i><div><b>{churn_rate:.1f}%</b><small>Customers who left (churn)</small></div></div>
  <div class="kpi"><i>💰</i><div><b>₹{cf['actual_arpu_6m'].mean():,.0f}</b><small>Avg monthly spend per customer</small></div></div>
  <div class="kpi"><i>🎧</i><div><b>{cf['complaint_count'].mean():.2f}</b><small>Complaints per customer</small></div></div>
</div>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Customers & Churn", "Revenue & Service"])

# ================================================================== TAB 1
with tab1:
    c1, c2, c3 = st.columns(3, gap="small")

    # 1 ── Treemap
    with c1:
        b = card("Where are our customers?",
                 "Bigger box = more customers. Darker red = more customers leaving.",
                 f"Connection: {f1}")
        d = cf if f1 == "All" else cf[cf["connection_type"] == f1]
        g = (d.groupby(["region", "circle_name"])
              .agg(customers=("customer_id", "count"), churn=("is_churned", "mean"))
              .reset_index())
        g["churn"] = (g["churn"] * 100).round(1)
        fig = go.Figure()
        ins = ""
        if len(g):
            fig = px.treemap(g, path=[px.Constant("India"), "region", "circle_name"],
                             values="customers", color="churn",
                             color_continuous_scale=REDS)
            fig.update_coloraxes(colorbar=dict(title="Churn %", thickness=8, len=0.8))
            fig.update_traces(textinfo="label", textfont=dict(size=10),
                              marker=dict(line=dict(color="#fff", width=1)))
            fig.update_layout(uniformtext=dict(minsize=8, mode="hide"))
            top = g.sort_values("churn").iloc[-1]
            big = g.sort_values("customers").iloc[-1]
            ins = (f"Largest circle: {big['circle_name']} ({int(big['customers']):,}). "
                   f"Highest churn: {top['circle_name']} ({top['churn']}%).")
        show(b, style(fig), ins, g.empty)

    # 2 ── Dumbbell
    with c2:
        b = card("Prepaid vs postpaid churn",
                 "Each row is a sign-up channel. Red dot = prepaid, black dot = postpaid. "
                 "Longer line = bigger difference.", f"Region: {f2}")
        d = cf if f2 == "All" else cf[cf["region"] == f2]
        p = (d.groupby(["acquisition_channel", "connection_type"])["is_churned"]
              .mean().mul(100).round(1).unstack()).dropna(how="all")
        fig = go.Figure()
        ins = ""
        if not p.empty:
            cols = [c for c in ("Prepaid", "Postpaid") if c in p.columns]
            colour = {"Prepaid": RED, "Postpaid": "#2B2B2B"}
            if len(cols) == 2:
                for ch, row in p.iterrows():
                    if row[cols].notna().all():
                        fig.add_trace(go.Scatter(
                            x=[row["Prepaid"], row["Postpaid"]], y=[ch, ch], mode="lines",
                            line=dict(color="#D9D9D9", width=5), showlegend=False,
                            hoverinfo="skip"))
            for c in cols:
                fig.add_trace(go.Scatter(
                    x=p[c], y=p.index, mode="markers", name=c,
                    marker=dict(size=13, color=colour[c]),
                    hovertemplate="%{y}: %{x}%<extra>" + c + "</extra>"))
            fig.update_xaxes(title="Customers who left (%)", gridcolor="#EEE")
            fig.update_yaxes(automargin=True, tickfont=dict(size=10))
            fig.update_layout(legend=dict(orientation="h", y=1.08, x=0))
            if len(cols) == 2:
                gap = (p["Postpaid"] - p["Prepaid"]).abs().dropna()
                if len(gap):
                    ch = gap.idxmax()
                    ins = (f"Biggest gap: {ch} — prepaid {p.loc[ch, 'Prepaid']}% vs "
                           f"postpaid {p.loc[ch, 'Postpaid']}%.")
        show(b, style(fig), ins or "Only one connection type in this view.", p.empty)

    # 3 ── Sankey
    with c3:
        b = card("How customers flow",
                 "Follow the bands left to right. Thicker band = more customers.",
                 f"Age: {f3}")
        d = cf if f3 == "All" else cf[cf["age_band"] == f3]
        fig = go.Figure()
        ins = ""
        if len(d):
            d = d.assign(outcome=np.where(d["is_churned"] == 1, "Left", "Stayed"))
            l1 = d.groupby(["acquisition_channel", "plan_type"]).size().reset_index()
            l2 = d.groupby(["plan_type", "outcome"]).size().reset_index()
            l1.columns = l2.columns = ["s", "t", "v"]
            links = pd.concat([l1, l2])
            nodes = list(pd.unique(links[["s", "t"]].values.ravel()))
            idx = {n: i for i, n in enumerate(nodes)}
            pal = ["#E40000", "#4A4A4A", "#FF8A8A", "#9A9A9A", "#A80000", "#D6D6D6"]
            ncol = ["#E40000" if n == "Left" else "#2B2B2B" if n == "Stayed"
                    else pal[i % len(pal)] for i, n in enumerate(nodes)]
            fig = go.Figure(go.Sankey(
                node=dict(label=nodes, color=ncol, pad=18, thickness=12),
                textfont=dict(size=10, color=DARK),
                link=dict(source=links["s"].map(idx), target=links["t"].map(idx),
                          value=links["v"], color="rgba(228,0,0,0.18)")))
            ins = (f"{d['is_churned'].mean() * 100:.1f}% of these {len(d):,} customers "
                   f"left.")
        show(b, style(fig), ins, d.empty)

# ================================================================== TAB 2
with tab2:
    c4, c5, c6 = st.columns(3, gap="small")

    # 4 ── Pareto
    with c4:
        b = card("Which plans earn the most?",
                 "Bars = money per plan (Pre = prepaid, Post = postpaid). Black line = running total %.",
                 f"Payment: {f4}")
        d = rev if f4 == "All" else rev[rev["txn_type"] == f4]
        d = (d.groupby("plan_name", as_index=False)["revenue"].sum()
              .sort_values("revenue", ascending=False))
        fig = go.Figure()
        ins = ""
        empty = d.empty or d["revenue"].sum() <= 0
        if not empty:
            d["cum"] = d["revenue"].cumsum() / d["revenue"].sum() * 100
            d["short"] = d["plan_name"].map(
                lambda n: f"{'Post' if n.startswith('Postpaid') else 'Pre'}<br>{n.split()[-1]}")
            fig.add_trace(go.Bar(x=d["short"], y=d["revenue"], name="Revenue (₹)",
                                 marker_color=RED, customdata=d["plan_name"],
                                 hovertemplate="%{customdata}<br>₹%{y:,.0f}<extra></extra>"))
            fig.add_trace(go.Scatter(x=d["short"], y=d["cum"], yaxis="y2",
                                     customdata=d["plan_name"],
                                     hovertemplate="%{customdata}<br>%{y:.0f}% so far<extra></extra>",
                                     mode="lines+markers", name="Running total %",
                                     line=dict(color="#2B2B2B")))
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", range=[0, 105],
                            ticksuffix="%", showgrid=False),
                legend=dict(orientation="h", y=1.1, x=0))
            fig.update_xaxes(tickangle=0, tickfont=dict(size=9), type="category")
            fig.update_yaxes(gridcolor="#EEE", tickformat="~s")
            n80 = int((d["cum"] < 80).sum() + 1)
            ins = (f"Top {min(n80, len(d))} of {len(d)} plans bring in 80% of the money. "
                   f"Best plan: {d.iloc[0]['plan_name']}.")
        fig = style(fig)
        fig.update_layout(margin=dict(l=6, r=6, t=6, b=30))
        show(b, fig, ins, empty)

    # 5 ── Funnel
    with c5:
        b = card("Are complaints getting fixed?",
                 "Each step shows how many complaints are left. A narrow bottom means slow fixes.",
                 f"Category: {f5}")
        d = complaints if f5 == "All" else complaints[complaints["category"] == f5]
        fig = go.Figure()
        ins = ""
        if len(d):
            rd = d["resolution_days"]
            vals = [len(d), int(d["is_resolved"].sum()), int((rd <= 7).sum()), int((rd <= 3).sum())]
            fig = go.Figure(go.Funnel(
                y=["Raised", "Resolved", "Fixed in 7 days", "Fixed in 3 days"], x=vals,
                textinfo="value+percent initial", textposition="inside",
                textfont=dict(color="#fff", size=11),
                marker=dict(color=["#6E0000", "#A80000", RED, "#D93636"]),
                connector=dict(line=dict(color="#E5E5E5"))))
            ins = (f"{vals[1] / vals[0] * 100:.0f}% resolved, but only "
                   f"{vals[3] / vals[0] * 100:.0f}% fixed within 3 days.")
        show(b, style(fig), ins, d.empty)

    # 6 ── Waterfall
    with c6:
        b = card("Are we growing each month?",
                 "Black bar = more new customers than leavers. Red bar = more leavers.",
                 f"Year: {f6}")
        mm = [f"{f6}-{i:02d}" for i in range(1, 13)]
        a = act.set_index("m")["n"].reindex(mm).fillna(0)
        c = chn.set_index("m")["n"].reindex(mm).fillna(0)
        net = (a - c).astype(int).tolist()
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        fig = go.Figure(go.Waterfall(
            x=labels, y=net, measure=["relative"] * 12,
            increasing=dict(marker=dict(color="#2B2B2B")),
            decreasing=dict(marker=dict(color=RED)),
            connector=dict(line=dict(color="#CFCFCF"))))
        fig.update_yaxes(gridcolor="#EEE", zeroline=True, zerolinecolor="#999")
        fig.update_xaxes(tickangle=0, tickfont=dict(size=9), type="category")
        ins = ""
        if any(net):
            best, worst = int(np.argmax(net)), int(np.argmin(net))
            ins = (f"Net change {sum(net):+,} customers in {f6}. "
                   f"Best: {labels[best]} ({net[best]:+,}). Weakest: {labels[worst]} ({net[worst]:+,}).")
        show(b, style(fig), ins, not any(net))