import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner

# Display the QR code scanner component
qr_code = qrcode_scanner(key='qrcode_scanner')

# Check if a QR code has been scanned
if qr_code:
    # Define the custom CSS style for the scanning box
    st.markdown(
        f"""
        <style>
        .st-qrcode-scanner {{
            width: 250px !important;
            height: 250px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Display the QR code
    st.image(qr_code, use_column_width=True)
