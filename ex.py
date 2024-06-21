import streamlit as st
import streamlit.components.v1 as components

# HTML and CSS to display the QR code scanner in a square shape
html_code = """
<!DOCTYPE html>
<html>
  <head>
    <style>
      .scanner {
        width: 100%;
        max-width: 400px; /* Adjust width as necessary */
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
      <iframe src="https://www.qrstuff.com" frameborder="0"></iframe>
    </div>
  </body>
</html>
"""

# Display the HTML content with the embedded iframe
components.html(html_code, height=400)

# Placeholder text input for manually entering scanned QR code
qr_code = st.text_input("Enter scanned QR code manually here:")

if qr_code:
    st.write(qr_code)
