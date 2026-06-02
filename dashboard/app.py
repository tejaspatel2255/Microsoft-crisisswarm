"""Streamlit dashboard for CrisisSwarm."""
import os
import sys
import streamlit as st
import json
from typing import List, Dict, Any, Optional

import pandas as pd
import pydeck as pdk

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.scenario import (
    SCENARIOS,
    load_demo_scenario,
    zone_coords_for_scenario,
    is_approximate_map,
    zoom_for_scenario,
    detect_scenario_name,
)
from core.swarm import run_swarm, run_swarm_partial, run_swarm_complete
from core import groq_client

st.set_page_config(page_title="CrisisSwarm Dashboard", layout="wide")

st.title("CrisisSwarm — Multi-Agent Disaster Response")
st.caption("Microsoft Build AI Hackathon 2026 · Theme 05 — Agent Swarms")

if groq_client.is_configured():
    blocked, block_reason = groq_client.is_temporarily_unavailable()
    if blocked:
        st.warning(
            "**Groq quota reached** during the last swarm run on this server. "
            "Further agents will use offline heuristics until you start a new run "
            "after limits reset.\n\n"
            f"{block_reason}"
        )
    else:
        ok, msg = groq_client.verify_connection(use_cache=True)
        key_info = groq_client.get_active_key_info()
        if ok:
            if key_info["keys_available"] >= 2:
                st.success(
                    f"Groq live — dual key rotation enabled "
                    f"(Key {key_info['active_key']} active). {msg}"
                )
            else:
                st.success(f"Groq live — {msg}")
            st.caption(
                "Tip: two keys on the **same** Groq account share one daily token limit. "
                "Use a second account for `GROQ_API_KEY_2`, or `GROQ_MODEL=llama-3.1-8b-instant`."
            )
        else:
            st.error(
                "**Groq key is in `.env` but the API is NOT working.** "
                "The app runs on offline heuristics until fixed.\n\n"
                f"Error: {msg}"
            )
else:
    st.warning("No Groq API key. Set `GROQ_API_KEY` in `.env` for live AI agents.")

AGENT_COLORS = {
    "Situation": "#636efa",
    "Commander": "#1f77b4",
    "Triage": "#ff7f0e",
    "Resource": "#2ca02c",
    "Routing": "#d62728",
    "Comms": "#9467bd",
    "Verifier": "#e377c2",
    "Reporter": "#8c564b",
    "Analysis": "#17becf",
}

SCENARIO_BUTTON_LABELS = {
    "Mumbai Earthquake": "🌏 Mumbai Earthquake",
    "Florida Hurricane": "🌀 Florida Hurricane",
    "Tokyo Flood": "🌊 Tokyo Flood",
    "Turkey Earthquake": "🏔️ Turkey Earthquake",
    "Chennai Cyclone": "🌪️ Chennai Cyclone",
}

# ---------------------------------------------------------------------------
# PDF Export Support
# ---------------------------------------------------------------------------
import io
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def generate_report_bytes(out: Dict[str, Any]) -> tuple[bytes, str, str]:
    situation = out.get("situation", {})
    plan = out.get("plan", {})
    allocations = out.get("allocations", {}).get("allocations", [])
    routes = out.get("routes", {}).get("routes", [])
    verifier = out.get("verifier", {})
    analysis = out.get("analysis", {})
    report = out.get("report", {})
    
    if REPORTLAB_AVAILABLE:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        from datetime import datetime
        elements.append(Paragraph("<b>CrisisSwarm Situation Report</b>", styles['Heading1']))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Scenario Summary</b>", styles['Heading2']))
        elements.append(Paragraph(situation.get("summary", "N/A"), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Disaster Details</b>", styles['Heading2']))
        data = [["Type", "Location", "Severity"]]
        data.append([str(situation.get("disaster_type", "")), str(situation.get("location", "")), str(situation.get("severity", ""))])
        t = Table(data, colWidths=[150, 150, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Triage Summary</b>", styles['Heading2']))
        data = [["Zone", "Total", "Critical", "Serious", "Minor"]]
        for zone, info in plan.get("triage", {}).get("zones", {}).items():
            br = info.get("breakdown", {})
            data.append([
                str(zone), str(info.get("estimated_total", 0)),
                str(br.get("Critical", 0)), str(br.get("Serious", 0)), str(br.get("Minor", 0))
            ])
        t = Table(data, colWidths=[100, 75, 75, 75, 75])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Resource Allocations</b>", styles['Heading2']))
        data = [["Zone", "Ambulances", "Medical Teams"]]
        for a in allocations:
            data.append([str(a.get("zone", "")), str(a.get("ambulances", 0)), str(a.get("medical_teams", 0))])
        t = Table(data, colWidths=[200, 100, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Routing</b>", styles['Heading2']))
        data = [["Zone", "Distance km", "ETA minutes", "Status"]]
        for r in routes:
            data.append([str(r.get("zone", "")), str(r.get("distance_km", "")), str(r.get("eta_minutes", "")), str(r.get("status", ""))])
        t = Table(data, colWidths=[150, 80, 80, 90])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Verifier Result</b>", styles['Heading2']))
        approved = "Yes" if verifier.get("approved") else "No"
        elements.append(Paragraph(f"Approved: {approved}", styles['Normal']))
        elements.append(Paragraph(f"Confidence: {verifier.get('confidence_score', 0)}%", styles['Normal']))
        issues = verifier.get("issues_found", [])
        if issues:
            elements.append(Paragraph("Issues:", styles['Normal']))
            for issue in issues:
                elements.append(Paragraph(f"• {issue}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Recommended Actions</b>", styles['Heading2']))
        for action in analysis.get("recommended_actions", []):
            elements.append(Paragraph(f"• {action}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Reporter Summary</b>", styles['Heading2']))
        for p in report.get("text_summary", "").split('\n'):
            if p.strip():
                elements.append(Paragraph(p.strip(), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("<i>Generated by CrisisSwarm · Microsoft Build AI Hackathon 2026</i>", styles['Normal']))
        
        doc.build(elements)
        return buffer.getvalue(), "application/pdf", "sitrep.pdf"
        
    else:
        from datetime import datetime
        html = f"""<html><head><title>Situation Report</title>
        <style>
            body {{ font-family: Helvetica, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; max-width: 800px; margin-bottom: 20px; }}
            th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            h2 {{ margin-top: 20px; }}
        </style></head><body>"""
        html += f"<h1>CrisisSwarm Situation Report</h1><p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        
        html += "<h2>Scenario Summary</h2>"
        html += f"<p>{situation.get('summary', 'N/A')}</p>"
        
        html += "<h2>Disaster Details</h2>"
        html += f"<table><tr><th>Type</th><th>Location</th><th>Severity</th></tr>"
        html += f"<tr><td>{situation.get('disaster_type', '')}</td><td>{situation.get('location', '')}</td><td>{situation.get('severity', '')}</td></tr></table>"
        
        html += "<h2>Triage Summary</h2>"
        html += "<table><tr><th>Zone</th><th>Total</th><th>Critical</th><th>Serious</th><th>Minor</th></tr>"
        for zone, info in plan.get("triage", {}).get("zones", {}).items():
            br = info.get("breakdown", {})
            html += f"<tr><td>{zone}</td><td>{info.get('estimated_total', 0)}</td><td>{br.get('Critical', 0)}</td><td>{br.get('Serious', 0)}</td><td>{br.get('Minor', 0)}</td></tr>"
        html += "</table>"
        
        html += "<h2>Resource Allocations</h2>"
        html += "<table><tr><th>Zone</th><th>Ambulances</th><th>Medical Teams</th></tr>"
        for a in allocations:
            html += f"<tr><td>{a.get('zone', '')}</td><td>{a.get('ambulances', 0)}</td><td>{a.get('medical_teams', 0)}</td></tr>"
        html += "</table>"
        
        html += "<h2>Routing</h2>"
        html += "<table><tr><th>Zone</th><th>Distance km</th><th>ETA minutes</th><th>Status</th></tr>"
        for r in routes:
            html += f"<tr><td>{r.get('zone', '')}</td><td>{r.get('distance_km', '')}</td><td>{r.get('eta_minutes', '')}</td><td>{r.get('status', '')}</td></tr>"
        html += "</table>"
        
        html += "<h2>Verifier Result</h2>"
        approved = "Yes" if verifier.get("approved") else "No"
        html += f"<p>Approved: {approved}<br/>Confidence: {verifier.get('confidence_score', 0)}%</p>"
        issues = verifier.get("issues_found", [])
        if issues:
            html += "<p>Issues:</p><ul>"
            for issue in issues:
                html += f"<li>{issue}</li>"
            html += "</ul>"
            
        html += "<h2>Recommended Actions</h2><ul>"
        for action in analysis.get("recommended_actions", []):
            html += f"<li>{action}</li>"
        html += "</ul>"
        
        html += "<h2>Reporter Summary</h2>"
        for p in report.get("text_summary", "").split('\n'):
            if p.strip():
                html += f"<p>{p.strip()}</p>"
                
        html += "<br/><br/><p><i>Generated by CrisisSwarm &middot; Microsoft Build AI Hackathon 2026</i></p>"
        html += "</body></html>"
        
        return html.encode("utf-8"), "text/html", "sitrep.html"


def _zone_rgb(breakdown: Dict[str, Any]) -> List[int]:
    critical = breakdown.get("Critical", 0)
    serious = breakdown.get("Serious", 0)
    if critical >= serious and critical > 0:
        return [220, 50, 50]
    if serious > 0:
        return [255, 140, 0]
    return [50, 200, 80]


def render_message(msg: Dict[str, str]) -> None:
    agent = msg.get("agent", "unknown")
    text = msg.get("message", "")
    color = AGENT_COLORS.get(agent, "#444444")
    html = f"""
    <div style='border-radius:8px;padding:8px;margin:6px 0;background-color:{color};color:white;'>
      <strong>{agent}</strong><div style='font-size:90%'>{text}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_agent_trace(agent_steps: List[Dict[str, Any]]) -> None:
    st.subheader("Agent execution trace")
    st.caption("Proves each step used live Groq or an offline fallback.")
    for step in agent_steps:
        llm = step.get("llm_used", False)
        badge = "🟢 Groq" if llm else "⚪ Offline"
        key_line = ""
        if step.get("key_used"):
            key_line = f" · Groq key **{step['key_used']}**"
        st.markdown(
            f"**{step.get('agent')}** — {badge} · "
            f"model `{step.get('model_used', '—')}` · "
            f"**{step.get('latency_ms', 0)} ms**{key_line}"
        )
        if step.get("llm_error"):
            st.caption(f"Fallback reason: {step['llm_error']}")
        if step.get("error"):
            st.error(f"Agent error: {step['error']}")


def _match_coord_key(zone: str, coords: Dict[str, tuple]) -> Optional[str]:
    if zone in coords:
        return zone
    zl = zone.lower()
    for key in coords:
        kl = key.lower()
        if kl in zl or zl in kl:
            return key
    return None


def build_map_df(
    scenario_text: str,
    plan: Dict[str, Any],
    routes: Dict[str, Any],
) -> pd.DataFrame:
    coords = zone_coords_for_scenario(scenario_text)
    triage_zones = plan.get("triage", {}).get("zones", {})
    route_by_zone = {r.get("zone"): r for r in routes.get("routes", [])}
    approximate = is_approximate_map(scenario_text, coords)

    rows: List[Dict[str, Any]] = []

    for zone, info in triage_zones.items():
        key = _match_coord_key(zone, coords)
        if key is None and approximate:
            key = list(coords.keys())[len(rows) % len(coords)]
        if key is None:
            continue
        lat, lon = coords[key]
        br = info.get("breakdown", {})
        r = route_by_zone.get(zone, route_by_zone.get(key, {}))
        rgb = _zone_rgb(br)
        rows.append({
            "zone": zone,
            "lat": lat,
            "lon": lon,
            "casualties": info.get("estimated_total", 0),
            "critical": br.get("Critical", 0),
            "serious": br.get("Serious", 0),
            "minor": br.get("Minor", 0),
            "eta_minutes": r.get("eta_minutes", "—"),
            "distance_km": r.get("distance_km", "—"),
            "approximate": "yes" if approximate else "no",
            "r": rgb[0],
            "g": rgb[1],
            "b": rgb[2],
        })

    if not rows:
        for zone, (lat, lon) in coords.items():
            r = route_by_zone.get(zone, {})
            rows.append({
                "zone": zone,
                "lat": lat,
                "lon": lon,
                "casualties": 0,
                "critical": 0,
                "serious": 0,
                "minor": 0,
                "eta_minutes": r.get("eta_minutes", "—"),
                "distance_km": r.get("distance_km", "—"),
                "approximate": "yes" if approximate else "no",
                "r": 100,
                "g": 180,
                "b": 255,
            })

    return pd.DataFrame(rows)


def render_map(
    scenario_text: str,
    plan: Dict[str, Any],
    routes: Dict[str, Any],
) -> None:
    coords = zone_coords_for_scenario(scenario_text)
    approximate = is_approximate_map(scenario_text, coords)

    if approximate:
        st.info(
            "**Approximate zone locations** — no exact map data for this scenario. "
            "Markers are placed near the closest recognised city from your text."
        )

    df = build_map_df(scenario_text, plan, routes)
    if df.empty:
        centre = zone_coords_for_scenario(scenario_text)
        lat = sum(c[0] for c in centre.values()) / len(centre)
        lon = sum(c[1] for c in centre.values()) / len(centre)
        df = pd.DataFrame([{
            "zone": "Centre",
            "lat": lat,
            "lon": lon,
            "casualties": 0,
            "critical": 0,
            "serious": 0,
            "minor": 0,
            "eta_minutes": "—",
            "distance_km": "—",
            "approximate": "yes",
            "r": 100,
            "g": 180,
            "b": 255,
        }])

    st.markdown(
        "**Legend:** 🔴 Critical-dominant · 🟠 Serious-dominant · "
        "🟢 Minor-dominant · 🔵 Approximate / unknown"
    )
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[lon, lat]",
        get_fill_color="[r, g, b, 200]",
        get_radius=1800,
        pickable=True,
    )
    
    zoom = zoom_for_scenario(scenario_text)
    name = detect_scenario_name(scenario_text)
    pitch = 45 if name and "Earthquake" in name else 30
    
    view = pdk.ViewState(
        latitude=float(df["lat"].mean()),
        longitude=float(df["lon"].mean()),
        zoom=zoom,
        pitch=pitch,
    )
    tooltip = {
        "html": (
            "<b>{zone}</b><br/>"
            "Casualties: {casualties}<br/>"
            "C:{critical} S:{serious} M:{minor}<br/>"
            "ETA: {eta_minutes} min<br/>"
            "Distance: {distance_km} km<br/>"
            "Approximate: {approximate}"
        ),
        "style": {"backgroundColor": "#1a1a2e", "color": "white"},
    }
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip))


def _render_swarm_results(out: Dict[str, Any]) -> None:
    plan = out.get("plan", {})
    situation = out.get("situation", {})
    analysis = out.get("analysis", {})
    verifier = out.get("verifier", {})
    transcript = out.get("transcript", [])
    agent_steps = out.get("agent_steps", [])
    agent_errors = out.get("agent_errors", [])
    scenario_for_map = st.session_state["last_scenario_text"]

    if agent_errors:
        st.error("**Agent errors during this run:**")
        for err in agent_errors:
            st.markdown(f"- {err}")

    llm_count = out.get("agents_with_llm", 0)
    total_steps = len(agent_steps)
    if llm_count == 0:
        st.warning("This run used **offline heuristics only** — see Agent Trace for details.")
    elif llm_count < total_steps:
        st.info(
            f"**Partial Groq run:** {llm_count} of {total_steps} steps used live AI. "
            "Check the Agent Trace tab for offline fallbacks."
        )

    total_casualties = sum(
        z.get("estimated_total", 0)
        for z in plan.get("triage", {}).get("zones", {}).values()
    )
    allocations = out.get("allocations", {}).get("allocations", [])
    total_ambulances = sum(a.get("ambulances", 0) for a in allocations)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Agents", len({s.get("agent") for s in agent_steps}))
    m2.metric("Casualties Triaged", total_casualties)
    m3.metric("Ambulances", total_ambulances)
    m4.metric(
        "Verifier",
        "✅ Approved" if verifier.get("approved") else "⚠️ Review",
        delta=f"{verifier.get('confidence_score', 0)}% confidence",
    )

    tab_ops, tab_map, tab_trace = st.tabs(["📋 Operations", "🗺️ Map View", "🔍 Agent Trace"])

    with tab_ops:
        if situation.get("summary"):
            st.subheader("Situation Understanding")
            st.write(situation.get("summary"))
            c1, c2, c3, c4 = st.columns(4)
            c1.caption(f"Type: {situation.get('disaster_type', '—')}")
            c2.caption(f"Location: {situation.get('location', '—')}")
            c3.caption(f"Severity: {situation.get('severity', '—')}")
            c4.caption(f"Source: {situation.get('source', '—')}")

        st.subheader("Operational Analysis")
        st.write(analysis.get("scenario_assessment", "No analysis available."))
        if analysis.get("coordination_notes"):
            st.info(analysis["coordination_notes"])
        if analysis.get("priority_zones"):
            st.markdown("**Priority zones:** " + ", ".join(analysis["priority_zones"]))
        if analysis.get("key_risks"):
            st.markdown("**Key risks**")
            for risk in analysis["key_risks"]:
                st.markdown(f"- {risk}")
        if analysis.get("recommended_actions"):
            st.markdown("**Recommended actions**")
            for action in analysis["recommended_actions"]:
                st.markdown(f"- {action}")

        if verifier:
            st.subheader("Verifier")
            vcol1, vcol2 = st.columns(2)
            vcol1.metric("Approved", str(verifier.get("approved", False)))
            vcol2.metric("Confidence", f"{verifier.get('confidence_score', 0)}%")
            if verifier.get("issues_found"):
                st.markdown("**Issues**")
                for issue in verifier["issues_found"]:
                    st.markdown(f"- {issue}")
            if verifier.get("corrections"):
                st.markdown("**Corrections**")
                for fix in verifier["corrections"]:
                    st.markdown(f"- {fix}")

        st.subheader("Live Conversation Log")
        for msg in transcript:
            render_message(msg)

        st.header("Reporter Summary")
        report = out.get("report", {})
        st.write(report.get("text_summary", "No report available."))
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.download_button(
                "⬇️ Download full report JSON",
                data=json.dumps(
                    {**report, "analysis": analysis, "verifier": verifier},
                    indent=2,
                ),
                file_name="crisis_report.json",
                mime="application/json",
            )
        with btn_col2:
            file_bytes, mime_type, file_name = generate_report_bytes(out)
            st.download_button(
                "⬇️ Download PDF Report" if REPORTLAB_AVAILABLE else "⬇️ Download HTML Report",
                data=file_bytes,
                file_name=file_name,
                mime=mime_type,
            )

        with st.expander("Raw Outputs"):
            st.json({
                "situation": situation,
                "plan": plan,
                "allocations": out.get("allocations"),
                "routes": out.get("routes"),
                "comms": out.get("comms"),
                "verifier": verifier,
                "analysis": analysis,
            })

    with tab_map:
        st.subheader("Zone map")
        render_map(scenario_for_map, plan, out.get("routes", {}))

    with tab_trace:
        render_agent_trace(agent_steps)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "scenario_input" not in st.session_state:
    st.session_state["scenario_input"] = load_demo_scenario()
if "swarm_out" not in st.session_state:
    st.session_state["swarm_out"] = None
if "last_scenario_text" not in st.session_state:
    st.session_state["last_scenario_text"] = st.session_state["scenario_input"]
if "approval_stage" not in st.session_state:
    st.session_state["approval_stage"] = "idle"
if "partial_out" not in st.session_state:
    st.session_state["partial_out"] = None

# ---------------------------------------------------------------------------
# Scenario selector
# ---------------------------------------------------------------------------
st.subheader("Disaster Scenario")

scenario_names = list(SCENARIOS.keys())
btn_cols = st.columns(5)
for i, name in enumerate(scenario_names):
    with btn_cols[i]:
        if st.button(
            SCENARIO_BUTTON_LABELS[name],
            use_container_width=True,
            key=f"scenario_btn_{i}",
        ):
            st.session_state["scenario_input"] = SCENARIOS[name]
            st.session_state["swarm_out"] = None
            st.session_state["partial_out"] = None
            st.session_state["approval_stage"] = "idle"
            st.rerun()

st.text_area(
    "Scenario text",
    key="scenario_input",
    height=140,
    help=(
        "Type a custom disaster scenario or use a preset button. "
        "Unknown locations use approximate map pins; built-in cities use exact zone coordinates."
    ),
)

# ---------------------------------------------------------------------------
# ACTIVATE SWARM
# ---------------------------------------------------------------------------
if st.button("🚨 ACTIVATE SWARM", type="primary", use_container_width=True):
    scenario = st.session_state["scenario_input"]
    
    with st.status("🚨 Swarm pipeline running...", expanded=True) as status:
        st.write("📡 Step 1/5 — Parsing disaster situation...")
        
        # Import what we need for inline steps
        from core.situation import parse_situation
        from core.context import SwarmContext
        from core.scenario import zone_coords_for_scenario
        import importlib, time
        from core.agent_llm import step_metadata
        from core import groq_client
        groq_client.reset_swarm_session()
        
        import time as _time
        t0 = _time.perf_counter()
        situation = parse_situation(scenario)
        lat_ms = int((_time.perf_counter() - t0) * 1000)
        
        src = "🟢 Groq" if situation.get("source") == "groq" else "⚪ Offline"
        loc = situation.get("location", "unknown location")
        dtype = situation.get("disaster_type", "disaster")
        st.write(f"✅ Situation parsed — {dtype} at {loc} ({src}, {lat_ms}ms)")
        
        st.write("⚔️ Step 2/5 — Commander + Triage assigning zones...")
        commander_mod = importlib.import_module("agents.commander")
        ctx = SwarmContext(scenario_text=scenario, situation=situation)
        commander = getattr(commander_mod, "Commander")()
        plan = commander.run_triage_then_plan(scenario, context=ctx)
        
        triage_zones = plan.get("triage", {}).get("zones", {})
        zone_summary = ", ".join(
            f"{z}: {info.get('estimated_total', 0)}"
            for z, info in list(triage_zones.items())[:3]
        )
        llm_badge = "🟢 Groq" if plan.get("llm_used") else "⚪ Offline"
        st.write(f"✅ Triage complete — {zone_summary} casualties ({llm_badge})")
        
        st.write("🏥 Step 3/5 — Resource allocating ambulances and teams...")
        resource_mod = importlib.import_module("agents.resource")
        allocations = resource_mod.allocate_resources(plan, context=ctx)
        
        total_amb = sum(
            a.get("ambulances", 0)
            for a in allocations.get("allocations", [])
        )
        llm_badge = "🟢 Groq" if allocations.get("llm_used") else "⚪ Offline"
        st.write(f"✅ Resources allocated — {total_amb} ambulances dispatched ({llm_badge})")
        
        st.write("🗺️ Step 4/5 — Routing planning ETAs and deployment order...")
        routing_mod = importlib.import_module("agents.routing")
        routes = routing_mod.plan_routes(
            plan.get("task_assignments", []),
            context=ctx,
            allocations=allocations,
        )
        
        engine = routes.get("routing_engine", "haversine")
        order = routes.get("route_order", [])
        order_str = " → ".join(order[:3]) if order else "zones"
        llm_badge = "🟢 Groq" if routes.get("llm_used") else "⚪ Offline"
        st.write(f"✅ Routes planned — {order_str} ({engine}, {llm_badge})")
        
        # Build partial_out manually (same structure as run_swarm_partial)
        from core.agent_llm import step_metadata
        from core.groq_client import get_last_key_used, resolve_model
        
        def _sit_step(sit, ms):
            groq_live = sit.get("source") == "groq"
            return {
                "agent": "Situation",
                "llm_used": groq_live,
                "model_used": resolve_model() if groq_live else "offline",
                "latency_ms": ms,
                "mode": "groq" if groq_live else "offline",
                "llm_error": sit.get("parse_error"),
            }
        
        agent_steps = [
            _sit_step(situation, lat_ms),
            step_metadata(plan, "Commander"),
        ]
        triage = plan.get("triage") or {}
        if triage:
            agent_steps.append(step_metadata(triage, "Triage"))
        agent_steps.append(step_metadata(allocations, "Resource"))
        agent_steps.append(step_metadata(routes, "Routing"))
        
        partial_out = {
            "situation": situation,
            "plan": plan,
            "allocations": allocations,
            "routes": routes,
            "agent_steps": agent_steps,
        }
        
        st.write("⚠️ Step 5/5 — Awaiting human approval before Comms...")
        status.update(
            label="✅ Initial pipeline complete — review plan below",
            state="complete",
            expanded=False,
        )
    
    st.session_state["partial_out"] = partial_out
    st.session_state["last_scenario_text"] = scenario
    st.session_state["approval_stage"] = "awaiting_approval"
    st.session_state["swarm_out"] = None
    st.rerun()

if st.session_state["approval_stage"] == "awaiting_approval":
    out = st.session_state["partial_out"]
    if not out:
        st.session_state["approval_stage"] = "idle"
        st.rerun()

    if out.get("error"):
        st.error(out.get("error"))
        if out.get("trace"):
            st.code(out["trace"])
        if st.button("Reset"):
            st.session_state["approval_stage"] = "idle"
            st.session_state["partial_out"] = None
            st.rerun()
    else:
        tab_ops, tab_map, tab_trace = st.tabs(["📋 Operations", "🗺️ Map View", "🔍 Agent Trace"])

        with tab_ops:
            situation = out.get("situation", {})
            plan = out.get("plan", {})
            allocations = out.get("allocations", {})
            routes = out.get("routes", {})

            st.subheader("Situation Understanding")
            st.write(situation.get("summary", "No summary available."))

            st.subheader("Triage Zones")
            for z, info in plan.get("triage", {}).get("zones", {}).items():
                st.write(f"- **{z}**: {info.get('estimated_total', 0)} casualties")

            st.subheader("Resource Allocations")
            for a in allocations.get("allocations", []):
                st.write(f"- **{a.get('zone', '')}**: {a.get('ambulances', 0)} ambulances, {a.get('medical_teams', 0)} medical teams")

            st.subheader("Routing ETAs")
            for r in routes.get("routes", []):
                st.write(f"- **{r.get('zone', '')}**: ETA {r.get('eta_minutes', 0)} min")

            st.warning("⚠️ Review the plan above before broadcasting alerts to hospitals and responders.")
            
            st.markdown("---")
            approved = st.checkbox("I have reviewed the plan and approve broadcasting communications")
            
            col1, col2 = st.columns(2)
            if approved:
                if col1.button("✅ APPROVE & SEND COMMS", type="primary"):
                    import importlib
                    from core.analysis import build_analysis_payload
                    from core.agent_llm import step_metadata
                    
                    partial = st.session_state["partial_out"]
                    scenario = st.session_state["last_scenario_text"]
                    situation = partial.get("situation", {})
                    plan = partial.get("plan", {})
                    allocations = partial.get("allocations", {})
                    routes = partial.get("routes", {})
                    agent_steps = list(partial.get("agent_steps", []))
                    
                    from core.context import SwarmContext
                    ctx = SwarmContext(scenario_text=scenario, situation=situation)
                    
                    with st.status("📡 Broadcasting alerts...", expanded=True) as status:
                        st.write("📢 Step 6/8 — Comms broadcasting alerts...")
                        comms_mod = importlib.import_module("agents.comms")
                        comms = comms_mod.send_alerts(
                            context=ctx, plan=plan,
                            allocations=allocations, routes=routes,
                        )
                        delivery_count = len(comms.get("delivery_log", []))
                        llm_badge = "🟢 Groq" if comms.get("llm_used") else "⚪ Offline"
                        agent_steps.append(step_metadata(comms, "Comms"))
                        st.write(f"✅ Comms sent — {delivery_count} alerts dispatched ({llm_badge})")
                        
                        st.write("🔍 Step 7/8 — Verifier cross-checking all outputs...")
                        verifier_mod = importlib.import_module("agents.verifier")
                        verifier = verifier_mod.verify_outputs(
                            ctx, plan, allocations, routes, comms
                        )
                        approved_str = "APPROVED ✅" if verifier.get("approved") else "REVIEW NEEDED ⚠️"
                        score = verifier.get("confidence_score", 0)
                        llm_badge = "🟢 Groq" if verifier.get("llm_used") else "⚪ Offline"
                        agent_steps.append(step_metadata(verifier, "Verifier"))
                        st.write(f"✅ Verifier: {approved_str} — {score}% confidence ({llm_badge})")
                        
                        st.write("📊 Step 8/8 — Analysis and Reporter generating SitRep...")
                        analysis = build_analysis_payload(
                            scenario, plan, allocations, routes,
                            context=ctx, comms=comms
                        )
                        agent_steps.append(step_metadata(analysis, "Analysis"))
                        
                        reporter_mod = importlib.import_module("agents.reporter")
                        report = reporter_mod.generate_report(
                            plan, allocations, routes,
                            context=ctx, comms=comms,
                            analysis=analysis, verifier=verifier,
                        )
                        agent_steps.append(step_metadata(report, "Reporter"))
                        
                        action_count = len(analysis.get("recommended_actions", []))
                        st.write(f"✅ SitRep complete — {action_count} recommended actions")
                        
                        status.update(
                            label="🚨 Swarm complete — full report ready",
                            state="complete",
                            expanded=False,
                        )
                    
                    # Build full output
                    from core.swarm import build_transcript, _collect_agent_errors
                    outputs = {
                        "plan": plan, "allocations": allocations, "routes": routes,
                        "comms": comms, "verifier": verifier,
                        "analysis": analysis, "report": report,
                    }
                    transcript = build_transcript(ctx, outputs)
                    llm_agents = sum(1 for s in agent_steps if s.get("llm_used"))
                    agent_errors = _collect_agent_errors(outputs)
                    mode = "groq_multi_agent" if llm_agents >= 3 else (
                        "groq_partial" if llm_agents > 0 else "offline_pipeline"
                    )
                    
                    full_out = {
                        "mode": mode,
                        "groq_live": llm_agents > 0,
                        "groq_status": f"{llm_agents} of {len(agent_steps)} agents used Groq",
                        "groq_model": groq_client.resolve_model() if groq_client.is_configured() else None,
                        "situation": situation, "plan": plan,
                        "allocations": allocations, "routes": routes,
                        "comms": comms, "verifier": verifier,
                        "report": report, "analysis": analysis,
                        "transcript": transcript, "agent_steps": agent_steps,
                        "agents_with_llm": llm_agents,
                        "agent_errors": agent_errors,
                    }
                    
                    st.session_state["swarm_out"] = full_out
                    st.session_state["approval_stage"] = "complete"
                    st.rerun()
                        
            if col2.button("❌ Cancel & Re-run"):
                st.session_state["approval_stage"] = "idle"
                st.session_state["partial_out"] = None
                st.session_state["swarm_out"] = None
                st.rerun()

        with tab_map:
            st.subheader("Zone map")
            render_map(st.session_state["last_scenario_text"], plan, routes)

        with tab_trace:
            render_agent_trace(out.get("agent_steps", []))

elif st.session_state["approval_stage"] == "complete":
    out = st.session_state["swarm_out"]
    if out.get("error"):
        st.error(out.get("error"))
        if out.get("trace"):
            st.code(out["trace"])
        if st.button("Reset"):
            st.session_state["approval_stage"] = "idle"
            st.session_state["partial_out"] = None
            st.session_state["swarm_out"] = None
            st.rerun()
    else:
        _render_swarm_results(out)
else:
    st.info("Pick a scenario (or write your own) and click **🚨 ACTIVATE SWARM**.")
