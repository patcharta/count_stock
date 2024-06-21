import streamlit as st
from streamlit.components.v1 import html
from streamlit_qrcode_scanner import qrcode_scanner

# Define the HTML and CSS for a square scanner area
scanner_html = """
<div style="display: flex; justify-content: center; align-items: center; height: 100vh;">
  <div id="qrcode-scanner" style="width: 300px; height: 300px;"></div>
</div>
<script>
  const videoElement = document.querySelector('video');
  if (videoElement) {
    videoElement.style.objectFit = 'cover';
  }
</script>
"""

# Render the scanner HTML
html(scanner_html, height=400)

# Use the QR code scanner
qr_code = qrcode_scanner(key='qrcode_scanner')

# Display the QR code result if available
if qr_code:
    st.write(qr_code)
