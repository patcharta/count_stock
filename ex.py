import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner

# Display the QR code scanner component
qr_code = qrcode_scanner(key='qrcode_scanner')

# Check if a QR code has been scanned
if qr_code:
    # Use HTML to set the fixed size for the QR code box
    st.write(f'<img src="data:image/png;base64,{qr_code}" style="width: 250px; height: 250px;">', unsafe_allow_html=True)
