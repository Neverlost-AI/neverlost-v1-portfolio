from pathlib import Path

import streamlit as st

from config import PROCESSED_DIR, REPORTS_DIR
from utils import read_json


st.set_page_config(page_title="Neverlost Healthcare Roadmap V1", layout="wide")

st.title("Neverlost Healthcare Roadmap V1")
st.caption("Local rule-based prototype. Not medical advice. Human review required.")

events = read_json(PROCESSED_DIR / "timeline.json", [])
bottlenecks = read_json(PROCESSED_DIR / "bottlenecks.json", [])
hidden = read_json(PROCESSED_DIR / "hidden_states.json", [])
trust = read_json(PROCESSED_DIR / "trust_thresholds.json", [])
windows = read_json(PROCESSED_DIR / "capacity_windows.json", [])

cols = st.columns(4)
cols[0].metric("Events", len(events))
cols[1].metric("Bottlenecks", len(bottlenecks))
cols[2].metric("Hidden States", len(hidden))
cols[3].metric("Capacity Windows", len(windows))

tab_timeline, tab_evidence, tab_bottlenecks, tab_capacity, tab_reports = st.tabs(["Timeline", "Evidence Matrix", "Bottlenecks", "Capacity Windows", "Reports"])

with tab_timeline:
    st.subheader("Medical Timeline")
    if events:
        st.dataframe(events, use_container_width=True)
    else:
        st.info("No events yet. Add documents to data/raw_documents and run python src/main.py.")

with tab_bottlenecks:
    st.subheader("Current Bottleneck Report")
    if bottlenecks:
        st.dataframe(bottlenecks, use_container_width=True)
    else:
        st.info("No bottlenecks detected yet.")

with tab_evidence:
    st.subheader("Evidence Matrix")
    matrix = read_json(PROCESSED_DIR / "evidence_matrix.json", [])
    if matrix:
        st.dataframe(matrix, use_container_width=True)
    else:
        st.info("No evidence matrix generated yet.")

with tab_capacity:
    st.subheader("Capacity Windows")
    if windows:
        st.dataframe(windows, use_container_width=True)
    else:
        st.info("No capacity windows detected yet.")

with tab_reports:
    st.subheader("Markdown Reports")
    report_files = sorted(REPORTS_DIR.glob("*.md"))
    if not report_files:
        st.info("No reports generated yet.")
    for report in report_files:
        with st.expander(report.name):
            st.markdown(report.read_text(encoding="utf-8"))
