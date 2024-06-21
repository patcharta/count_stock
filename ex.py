import streamlit as st
import streamlit.components.v1 as components

# Create a simple HTML and CSS to display the scanner in a square
html_code = """
<!DOCTYPE html>
<html>
  <head>
    <style>
      .scanner {
        width: 100%;
        max-width: 400px; /* Adjust as necessary */
        padding-top: 100%; /* 1:1 Aspect Ratio */
        position: relative;
      }
      .scanner iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
      }
    </style>
  </head>
  <body>
    <div class="scanner">
      <iframe src="YOUR_QR_SCANNER_URL_HERE" frameborder="0"></iframe>
    </div>
  </body>
</html>
"""

components.html(html_code, height=400)

qr_code = st.text_input("Enter scanned QR code manually here:")

if qr_code:
    st.write(qr_code)
