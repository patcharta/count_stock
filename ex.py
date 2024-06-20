import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner

# เพิ่ม CSS เพื่อปรับแต่งขนาดของพื้นที่สแกน
st.markdown(
    """
    <style>
    .qr-container {
        display: flex;
        justify-content: center;
    }
    .qr-container div {
        position: relative;
        width: 400px; /* ตั้งขนาดเป็นสี่เหลี่ยมจัตุรัส */
        padding-top: 400px; /* ตั้งขนาดเป็นสี่เหลี่ยมจัตุรัส */
    }
    .qr-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# เพิ่ม wrapper div ที่มี class="qr-container"
st.markdown('<div class="qr-container"><div>', unsafe_allow_html=True)
qrcode = qrcode_scanner()
st.markdown('</div></div>', unsafe_allow_html=True)

# แสดงผล QR Code ที่สแกนได้
if qrcode:
    st.write(f'Scanned QR Code: {qrcode}')
