import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner

# Add CSS to make sure the scanning area is highlighted correctly
st.markdown(
    """
    <style>
    .qr-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
    }
    .qr-scanner {
        width: 400px;  /* Adjust width as needed */
        height: 400px; /* Adjust height as needed */
        position: relative;
    }
    .qr-scanner canvas {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 250px;
        height: 250px;
        margin-left: -125px; /* Half of width */
        margin-top: -125px; /* Half of height */
        box-shadow: 0 0 0 1000px rgba(0, 0, 0, 0.5); /* Shading the rest of the viewfinder */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display the QR code scanner with the specified qrbox dimensions
st.markdown('<div class="qr-container"><div class="qr-scanner">', unsafe_allow_html=True)

# Define the configuration for the qrbox
qrbox_config = {
    "qrbox": {
        "width": 250,
        "height": 250
    }
}

qrcode = qrcode_scanner(config=qrbox_config)
st.markdown('</div></div>', unsafe_allow_html=True)

# Display the scanned QR code
if qrcode:
    st.write(f'Scanned QR Code: {qrcode}')
