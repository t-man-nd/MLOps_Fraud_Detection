import streamlit as st
import requests
import pandas as pd
import numpy as np
import json
import plotly.express as px

# ====================== CONFIG ======================
st.set_page_config(page_title="Fraud Detection System", page_icon="🔒", layout="wide")

API_URL = "http://127.0.0.1:8000/predict_raw"
HEALTH_URL = "http://127.0.0.1:8000/health"

# ====================== UTILS ======================


def clean_data(obj):
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: clean_data(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_data(i) for i in obj]
    return obj


@st.cache_data(ttl=60)
def check_health():
    try:
        return requests.get(HEALTH_URL, timeout=5).json()
    except requests.RequestException:
        return None


# ====================== SIDEBAR ======================
with st.sidebar:
    st.title("🛡️ Fraud Detection")
    st.markdown("**MLOps Production Demo**")
    st.subheader("⚙️ Control Panel")
    ui_threshold = st.slider("Decision Threshold", 0.0, 1.0, 0.72, 0.01)

    st.subheader("📊 System Status")

    health = check_health()
    if health:
        st.success("API Connected")
        st.caption(f"Model: {health.get('model_name', 'Unknown')}")
    else:
        st.error("API Not Connected")

# ====================== MAIN ======================
st.title("💳 Fraud Detection System")

uploaded = st.file_uploader("Upload JSON file", type=["json"])

if uploaded:
    try:
        data = json.load(uploaded)
        records = data.get("records", [])
        context = data.get("context", None)
        df_input = pd.DataFrame(records)

        st.success(f"Loaded {len(records)} transactions")

        with st.expander("### 📥 Input Preview"):
            st.dataframe(df_input.head(5), use_container_width=True)

        if st.button("🚀 Run Prediction"):
            with st.spinner("Processing batch..."):
                payload = {"records": clean_data(records), "context": clean_data(context)}
                res = requests.post(API_URL, json=payload)

                if res.status_code == 200:
                    df = pd.DataFrame(res.json().get("results", []))
                    if "TransactionID" in df_input.columns:
                        df["TransactionID"] = df_input["TransactionID"].values
                    else:
                        st.error("Column 'TransactionID' is not found!")

                    fraud_count = (df["prediction"] == 1).sum()
                    total = len(df)
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Cases", total)
                    col2.metric("Fraud Cases", fraud_count)
                    col3.metric("Fraud Rate", f"{fraud_count/total:.2%}")
                    col4.metric("Average Risk Score", f"{df['risk_score'].mean():.2f}")

                    st.markdown("---")

                    cols_to_show = [
                        c for c in df.columns if c not in ["request_id", "prediction_id"]
                    ]
                    df_display = df[cols_to_show]

                    st.subheader("🚨 Prediction Summary")
                    st.dataframe(
                        df_display.sort_values("fraud_probability", ascending=False),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "fraud_probability": st.column_config.ProgressColumn(
                                "Probability", format="%.2f", min_value=0, max_value=1
                            ),
                        }
                    )

                    # ===== CHART =====
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        st.markdown("### 📈 Distribution")
                        fig = px.histogram(
                            df,
                            x="fraud_probability",
                            nbins=20,
                            color_discrete_sequence=["#ef4444"],
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col_chart2:
                        st.markdown("### 📊 Fraud vs Clean Rate")
                        fig_pie = px.pie(
                            df,
                            names="prediction",
                            hole=0.3,
                            color_discrete_sequence=["#22c55e", "#ef4444"],
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)

                    # ===== DOWNLOAD =====
                    st.download_button(
                        "Download Results",
                        df.to_csv(index=False),
                        "fraud_results.csv",
                    )

                else:
                    st.error(res.text)

    except Exception as e:
        st.error(f"Error: {e}")

st.caption("Fraud Detection System | FastAPI + Streamlit | Demo")
