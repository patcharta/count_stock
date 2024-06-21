import streamlit as st
from streamlit.components.v1 import html
from streamlit_qrcode_scanner import qrcode_scanner

# Add custom CSS for square scanning area
custom_css = """
<style>
.qr-code-scanner {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
}

.qr-code-scanner video {
    position: absolute;
    top: 50%;
    left: 50%;
    width: auto;
    height: 100%;
    transform: translate(-50%, -50%);
}

.qr-code-scanner .qr-code-square {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 80%;
    height: 80%;
    max-width: 300px;
    max-height: 300px;
    border: 5px solid white;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
    transform: translate(-50%, -50%);
    box-sizing: border-box;
}
</style>
"""

# Include the CSS in your Streamlit app
st.markdown(custom_css, unsafe_allow_html=True)

# QR code scanner component
qr_code = qrcode_scanner(key='qrcode_scanner')

# Overlay the square scanning area
html('<div class="qr-code-scanner"><div class="qr-code-square"></div></div>', height=500)

if qr_code:
    st.write(qr_code)
