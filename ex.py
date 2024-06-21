import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner

# QR code scanner with 1:1 aspect ratio for square shape
qr_code = qrcode_scanner(key='qrcode_scanner', aspect_ratio='1:1')

if qr_code:
    st.write(qr_code)
