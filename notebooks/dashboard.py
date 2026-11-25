import base64
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------- config
HERE = Path(__file__).parent
DB = HERE / "airtel.db"
LOGO = HERE / "airtel_logo.png"   # optional: put the official logo here

RED, DARK, GREY = "#E40000", "#1F1F1F", "#6B6B6B"
REDS = ["#FDE8E8", "#F5A3A3", "#E40000", "#7A0000"]

st.set_page_config(page_title="Airtel Insights", page_icon="📶", layout="wide")


# ---------------------------------------------------------------- styling
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
html, body, [class*="css"], .stApp {{ font-family:'Plus Jakarta Sans',sans-serif; color:{DARK}; }}
.stApp {{ background:#F6F6F7; }}
header[data-testid="stHeader"], footer, #MainMenu {{ display:none; }}
.block-container {{ padding:0.6rem 1.6rem 0.4rem; max-width:100%; }}

.topbar {{ display:flex; align-items:center; justify-content:space-between;
  background:#fff; border-radius:14px; padding:8px 20px; border-bottom:3px solid {RED};
  animation:drop .7s cubic-bezier(.2,.8,.2,1) both; }}
.topbar h1 {{ font-size:1.15rem; font-weight:800; margin:0; }}
.topbar span {{ color:{GREY}; font-size:.8rem; }}
.logo svg, .logo img {{ height:38px; }}

.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:10px 0 6px; }}
.kpi {{ background:#fff; border-radius:12px; padding:8px 16px; border-left:4px solid {RED};
  animation:rise .6s ease both; }}
.kpi:nth-child(2) {{ animation-delay:.08s }} .kpi:nth-child(3) {{ animation-delay:.16s }}
.kpi:nth-child(4) {{ animation-delay:.24s }}
.kpi b {{ display:block; font-size:1.35rem; font-weight:800; color:{RED}; line-height:1.2; }}
.kpi small {{ color:{GREY}; font-size:.72rem; }}

div[data-baseweb="tab-list"] {{ gap:6px; }}
button[data-baseweb="tab"] {{ background:#fff; border-radius:10px 10px 0 0; padding:6px 18px; font-weight:600; }}
button[aria-selected="true"] {{ color:#fff !important; background:{RED} !important; }}
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {{ display:none; }}
div[data-testid="stTabPanel"] {{ animation:fade .5s ease both; padding-top:8px; }}

div[data-testid="stVerticalBlockBorderWrapper"] {{ background:#fff; border-radius:14px;
  border:1px solid #ECECEC; padding:2px 6px; transition:box-shadow .25s, transform .25s; }}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{ box-shadow:0 8px 22px rgba(228,0,0,.12); transform:translateY(-2px); }}
.ctitle {{ font-weight:800; font-size:.92rem; margin:2px 0 0; }}
.csub {{ color:{GREY}; font-size:.7rem; margin-bottom:2px; }}
div[data-baseweb="select"] > div {{ min-height:32px; border-radius:8px; }}
div[data-testid="stSelectbox"] {{ margin-bottom:-10px; }}

@keyframes drop {{ from {{opacity:0; transform:translateY(-20px)}} to {{opacity:1; transform:none}} }}
@keyframes rise {{ from {{opacity:0; transform:translateY(16px)}} to {{opacity:1; transform:none}} }}
@keyframes fade {{ from {{opacity:0}} to {{opacity:1}} }}
@media (prefers-reduced-motion:reduce) {{ * {{ animation:none !important; transition:none !important; }} }}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- data
@st.cache_data(show_spinner="Loading Airtel data…")
def q(sql: str) -> pd.DataFrame:
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query(sql, con)


if not DB.exists():
    st.error(f"airtel.db not found. Put it next to app.py ({HERE}).")
    st.stop()

cf = q("SELECT * FROM customer_features")
complaints = q("SELECT category, is_resolved, resolution_days FROM complaints")
rev = q("""SELECT r.txn_type, p.plan_type, p.plan_name, SUM(r.amount_inr) AS revenue
           FROM recharges r JOIN plans p ON p.plan_id = r.plan_id
           GROUP BY 1,2,3""")
act = q("""SELECT substr(activation_date,1,7) AS m, COUNT(*) AS n
           FROM customers GROUP BY 1""")
chn = q("""SELECT substr(churn_date,1,7) AS m, COUNT(*) AS n
           FROM customers WHERE churn_date IS NOT NULL GROUP BY 1""")


# ---------------------------------------------------------------- helpers
def style(fig, h=300):
    fig.update_layout(
        height=h, margin=dict(l=6, r=6, t=6, b=6),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color=DARK),
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    return fig


def card(title, sub):
    box = st.container(border=True)
    box.markdown(f'<div class="ctitle">{title}</div><div class="csub">{sub}</div>',
                 unsafe_allow_html=True)
    return box


def options(series):
    return ["All"] + sorted(series.dropna().astype(str).unique())


def sel(box, label, opts, key):
    return box.selectbox(label, opts, key=key, label_visibility="collapsed")


_n = {"i": 0}


def show(box, fig, empty=False):
    _n["i"] += 1
    if empty:
        box.info("No data for this filter. Pick another option.")
    else:
        box.plotly_chart(fig, use_container_width=True, key=f"chart{_n['i']}",
                         config={"displayModeBar": False})


# ---------------------------------------------------------------- header
if LOGO.exists():
    logo_html = f'<img src="data:image/png;base64,{base64.b64encode(LOGO.read_bytes()).decode()}">'
else:  # simple stand-in wordmark; replace by dropping airtel_logo.png next to app.py
    logo_html = (
        '<svg viewBox="0 0 190 50" xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="2" y="4" width="42" height="42" rx="12" fill="{RED}"/>'
        '<text x="23" y="38" text-anchor="middle" font-size="36" font-weight="800" '
        'font-family="Plus Jakarta Sans,Arial" fill="#fff">a</text>'
        f'<text x="54" y="37" font-size="34" font-weight="800" '
        f'font-family="Plus Jakarta Sans,Arial" fill="{RED}">airtel</text></svg>'
    )

st.markdown(
    f'<div class="topbar"><div><h1>Customer, Churn &amp; Revenue Insights</h1>'
    f'<span>22,000 customers · 14 plans · 22 circles</span></div>'
    f'<div class="logo">{logo_html}</div></div>',
    unsafe_allow_html=True,
)

churn_rate = cf["is_churned"].mean() * 100
st.markdown(
    f"""<div class="kpis">
  <div class="kpi"><b>{len(cf):,}</b><small>Total customers</small></div>
  <div class="kpi"><b>{churn_rate:.1f}%</b><small>Churn rate</small></div>
  <div class="kpi"><b>₹{cf['actual_arpu_6m'].mean():,.0f}</b><small>Avg monthly revenue per user (6 months)</small></div>
  <div class="kpi"><b>{cf['complaint_count'].mean():.2f}</b><small>Complaints per customer</small></div>
</div>""",
    unsafe_allow_html=True,
)

tab1, tab2 = st.tabs(["Customers & Churn", "Revenue & Service"])

# ================================================================= TAB 1
with tab1:
    c1, c2, c3 = st.columns(3, gap="small")

    # 1 ── Sunburst
    with c1:
        b = card("Where our customers are", "Region → circle. Colour shows churn rate")
        ct = sel(b, "Connection", options(cf["connection_type"]), "f1")
        d = cf if ct == "All" else cf[cf["connection_type"] == ct]
        g = (d.groupby(["region", "circle_name"])
              .agg(customers=("customer_id", "count"), churn=("is_churned", "mean"))
              .reset_index())
        g["churn"] = (g["churn"] * 100).round(1)
        fig = px.sunburst(g, path=["region", "circle_name"], values="customers",
                          color="churn", color_continuous_scale=REDS) if len(g) else go.Figure()
        fig.update_coloraxes(colorbar=dict(title="Churn %", thickness=8, len=0.7))
        show(b, style(fig), g.empty)

    # 2 ── Sankey
    with c2:
        b = card("Customer journey flow", "Acquisition channel → plan type → outcome")
        rg = sel(b, "Region", options(cf["region"]), "f2")
        d = cf if rg == "All" else cf[cf["region"] == rg]
        d = d.assign(outcome=np.where(d["is_churned"] == 1, "Churned", "Retained"))
        l1 = d.groupby(["acquisition_channel", "plan_type"]).size().reset_index(name="v")
        l1.columns = ["s", "t", "v"]
        l2 = d.groupby(["plan_type", "outcome"]).size().reset_index(name="v")
        l2.columns = ["s", "t", "v"]
        links = pd.concat([l1, l2])
        nodes = list(pd.unique(links[["s", "t"]].values.ravel()))
        idx = {n: i for i, n in enumerate(nodes)}
        pal = ["#E40000", "#2E2E2E", "#F28B82", "#8C8C8C", "#B30000", "#C9C9C9"]
        ncol = ["#E40000" if n == "Churned" else "#2E2E2E" if n == "Retained"
                else pal[i % len(pal)] for i, n in enumerate(nodes)]
        fig = go.Figure(go.Sankey(
            node=dict(label=nodes, color=ncol, pad=14, thickness=14),
            link=dict(source=links["s"].map(idx), target=links["t"].map(idx),
                      value=links["v"], color="rgba(228,0,0,0.18)")))
        show(b, style(fig), d.empty)

    # 3 ── Radar
    with c3:
        b = card("Churned vs retained profile", "Behaviour index (100 = average customer)")
        pt = sel(b, "Plan type", options(cf["plan_type"]), "f3")
        d = cf if pt == "All" else cf[cf["plan_type"] == pt]
        mets = {"complaint_count": "Complaints", "recency_days": "Days since last use",
                "actual_arpu_6m": "Revenue", "mb_per_active_day": "Data per day",
                "tenure_days": "Tenure", "usage_days": "Active days",
                "recharge_count": "Recharges"}
        m = d[list(mets)].fillna(0)
        base = m.mean().replace(0, np.nan)
        fig = go.Figure()
        for flag, name, col in [(0, "Retained", "#2E2E2E"), (1, "Churned", RED)]:
            sub = m[d["is_churned"] == flag]
            if len(sub):
                vals = (sub.mean() / base * 100).fillna(0).tolist()
                lab = list(mets.values())
                fig.add_trace(go.Scatterpolar(
                    r=vals + vals[:1], theta=lab + lab[:1], name=name, fill="toself",
                    line=dict(color=col), opacity=0.55))
        fig.update_layout(polar=dict(radialaxis=dict(showticklabels=False, gridcolor="#E5E5E5"),
                                     bgcolor="rgba(0,0,0,0)"),
                          legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"))
        show(b, style(fig), d.empty or not fig.data)

# ================================================================= TAB 2
with tab2:
    c4, c5, c6 = st.columns(3, gap="small")

    # 4 ── Treemap
    with c4:
        b = card("Revenue by plan", "Box size = total recharge value (₹)")
        tx = sel(b, "Transaction type", options(rev["txn_type"]), "f4")
        d = rev if tx == "All" else rev[rev["txn_type"] == tx]
        d = d.groupby(["plan_type", "plan_name"], as_index=False)["revenue"].sum()
        fig = px.treemap(d, path=[px.Constant("All plans"), "plan_type", "plan_name"],
                         values="revenue", color="revenue",
                         color_continuous_scale=REDS) if len(d) else go.Figure()
        fig.update_coloraxes(showscale=False)
        fig.update_traces(root_color="rgba(0,0,0,0)", textfont=dict(size=11))
        show(b, style(fig), d.empty)

    # 5 ── Funnel
    with c5:
        b = card("Complaint resolution funnel", "How many complaints get fixed, and how fast")
        cat = sel(b, "Category", options(complaints["category"]), "f5")
        d = complaints if cat == "All" else complaints[complaints["category"] == cat]
        rd = d["resolution_days"]
        stages = ["Raised", "Resolved", "Within 7 days", "Within 3 days"]
        vals = [len(d), int(d["is_resolved"].sum()),
                int((rd <= 7).sum()), int((rd <= 3).sum())]
        fig = go.Figure(go.Funnel(
            y=stages, x=vals, textinfo="value+percent initial",
            marker=dict(color=["#7A0000", "#B30000", RED, "#F28B82"]),
            connector=dict(line=dict(color="#E5E5E5"))))
        show(b, style(fig), d.empty)

    # 6 ── Waterfall
    with c6:
        b = card("Monthly net customer growth", "New activations minus churn, month by month")
        years = sorted({m[:4] for m in pd.concat([act["m"], chn["m"]]).dropna()})
        yr = sel(b, "Year", years, "f6")
        mm = [f"{yr}-{i:02d}" for i in range(1, 13)]
        a = act.set_index("m")["n"].reindex(mm).fillna(0)
        c = chn.set_index("m")["n"].reindex(mm).fillna(0)
        net = (a - c).astype(int).tolist()
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        fig = go.Figure(go.Waterfall(
            x=labels + ["Year net"], y=net + [0],
            measure=["relative"] * 12 + ["total"],
            increasing=dict(marker=dict(color="#2E2E2E")),
            decreasing=dict(marker=dict(color=RED)),
            totals=dict(marker=dict(color="#F28B82")),
            connector=dict(line=dict(color="#CFCFCF"))))
        fig.update_yaxes(gridcolor="#EEE")
        show(b, style(fig), not any(net))