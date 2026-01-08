import streamlit as st

# Configuration
PUBLIC_IP = "51.21.180.222"  # Public IP of the EC2 instance
PORT_A = 8501
PORT_B = 8502

st.set_page_config(page_title="Quant Platform", layout="wide")

st.title("Quant Platform")
st.write("Single entry point to access Quant A and Quant B applications.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Quant A")
    st.write("Single-asset analysis / Strategy A.")
    st.link_button("Open Quant A", f"http://{PUBLIC_IP}:{PORT_A}")

with col2:
    st.subheader("Quant B")
    st.write("Multi-Asset Portfolio analysis / Strategy B.")
    st.link_button("Open Quant B", f"http://{PUBLIC_IP}:{PORT_B}")

st.divider()
st.caption("This page represents the integrated platform: a single access point to all modules.")
