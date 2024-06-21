import streamlit as st
from streamlit_qrcode_scanner import st_qrcode

st.title('QR Code Scanner')

qr_code = st_qrcode()

if qr_code:
    st.image(qr_code, caption='Scanned QR Code', use_column_width=False)
