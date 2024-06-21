import streamlit as st
import streamlit.components.v1 as components

st.title("QR Code Scanner")

# Create a div for the QR code scanner
components.html("""
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
        <div id="qr-reader" style="width:300px"></div>
        <div id="qr-reader-results"></div>
        <script>
            function onScanSuccess(qrMessage) {
                document.getElementById('qr-reader-results').innerText = `QR Code detected: ${qrMessage}`;
            }

            var html5QrcodeScanner = new Html5QrcodeScanner(
                "qr-reader", { fps: 10, qrbox: { width: 250, height: 250 } });
            html5QrcodeScanner.render(onScanSuccess);
        </script>
    </body>
    </html>
    """,
    height=600,
)
qr_code = qrcode_scanner(key='qrcode_scanner')
