import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner

# เพิ่ม CSS เพื่อปรับแต่งขนาดของพื้นที่สแกน
st.markdown(
    """
    <style>
    .qrcode-scanner {
        width: 100%;
        max-width: 400px; /* ตั้งค่าสูงสุด */
        height: 400px; /* ปรับความสูงให้เป็นสี่เหลี่ยมจัตุรัส */
        margin: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# เพิ่ม wrapper div ที่มี class="qrcode-scanner"
st.markdown('<div class="qrcode-scanner">', unsafe_allow_html=True)
qrcode = qrcode_scanner()
st.markdown('</div>', unsafe_allow_html=True)

# แสดงผล QR Code ที่สแกนได้
if qrcode:
    st.write(f'Scanned QR Code: {qrcode}')
