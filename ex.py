import streamlit as st
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(layout="wide")

def app():
    st.title("QR Code Scanner with Square Box")
    
    # Define the CSS for a square scanning box
    st.markdown(
        """
        <style>
        .qr-box {
            position: relative;
            width: 500px;
            height: 500px;
            border: 5px solid #ffa726;
            margin: auto;
        }
        .qr-scanner video {
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

    st.write("Scan your QR code within the box below:")

    # Display the QR code scanner with the square box
    qr_code = qrcode_scanner(key="qr_code_scanner")

    if qr_code:
        st.success(f"QR Code detected: {qr_code}")

    st.markdown('<div class="qr-box"><div class="qr-scanner"></div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    app()
