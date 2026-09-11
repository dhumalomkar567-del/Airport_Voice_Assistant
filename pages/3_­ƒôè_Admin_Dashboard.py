"""
3_📊_Admin_Dashboard.py
-------------------------
Admin analytics dashboard: overall stats, breakdown by language and
intent, queries-per-day trend, a searchable interaction log, and a
"reset data" control.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from database.db_manager import (
    init_db,
    get_summary_stats,
    fetch_all_interactions,
    clear_all_data,
)

st.set_page_config(page_title="Admin Dashboard", page_icon="📊", layout="wide")
init_db()

st.title("📊 Admin Dashboard")

stats = get_summary_stats()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Queries", stats["total"])
m2.metric("Successful", stats["success"])
m3.metric("Errors", stats["errors"])
success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] else 0
m4.metric("Success Rate", f"{success_rate:.1f}%")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🌐 Queries by Language")
    if stats["by_language"]:
        df_lang = pd.DataFrame(stats["by_language"], columns=["language", "count"])
        fig = px.pie(df_lang, names="language", values="count", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No data yet.")

with col2:
    st.subheader("🎯 Queries by Intent")
    if stats["by_intent"]:
        df_intent = pd.DataFrame(stats["by_intent"], columns=["intent", "count"])
        fig = px.bar(df_intent, x="intent", y="count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No data yet.")

st.subheader("📈 Queries per Day")
if stats["by_day"]:
    df_day = pd.DataFrame(stats["by_day"], columns=["day", "count"])
    fig = px.line(df_day, x="day", y="count", markers=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("No data yet.")

st.divider()

st.subheader("🗂️ Full Interaction Log")
rows = fetch_all_interactions()
if rows:
    df_all = pd.DataFrame([dict(r) for r in rows])
    search = st.text_input("🔎 Search query/response text")
    if search:
        mask = (
            df_all["query_text"].str.contains(search, case=False, na=False)
            | df_all["response_text"].str.contains(search, case=False, na=False)
        )
        df_all = df_all[mask]
    st.dataframe(df_all, use_container_width=True, height=400)

    csv = df_all.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export full log (CSV)",
        data=csv,
        file_name="interaction_log.csv",
        mime="text/csv",
    )
else:
    st.caption("No interactions logged yet.")

st.divider()
with st.expander("⚠️ Danger zone"):
    st.warning("This permanently deletes all logged interaction data.")
    if st.button("🗑️ Clear all data"):
        clear_all_data()
        st.success("All data cleared. Refresh the page to see the update.")
