import streamlit as st
import streamlit.components.v1 as components

st.title("QR Code Scanner")

# HTML code with embedded script for QR code scanner
html_code = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/html5-qrcode/minified/html5-qrcode.min.js"></script>
    <style>
        #qr-reader {
            width: 100%;
            max-width: 500px;
            margin: auto;
        }
    </style>
</head>
<body>
    <div id="qr-reader" style="width: 300px"></div>
    <div id="qr-reader-results"></div>
    <script>
        function onScanSuccess(qrMessage) {
            document.getElementById('qr-reader-results').innerText = `QR Code detected: ${qrMessage}`;
        }

        function onScanError(errorMessage) {
            // handle scan error
        }

        document.addEventListener("DOMContentLoaded", function() {
            var html5QrcodeScanner = new Html5QrcodeScanner(
                "qr-reader", 
                { fps: 10, qrbox: { width: 250, height: 250 } },
                false
            );
            html5QrcodeScanner.render(onScanSuccess, onScanError);
        });
    </script>
</body>
</html>
"""

# Embed the HTML code in the Streamlit app
components.html(html_code, height=600)
