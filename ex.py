import streamlit as st
from streamlit.components.v1 import html

# Define the HTML and JavaScript for a square scanner area
scanner_html = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/html5-qrcode/minified/html5-qrcode.min.js"></script>
    <style>
        #reader {
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        #reader div {
            width: 300px; /* Adjust size to make it a square */
            height: 300px;
        }
    </style>
</head>
<body>
    <div id="reader"></div>
    <script>
        function onScanSuccess(qrMessage) {
            // handle the scanned code as you like, for example:
            Streamlit.setComponentValue(qrMessage);
        }

        function onScanError(errorMessage) {
            // handle scan error
        }

        let config = {
            fps: 10,
            qrbox: {width: 300, height: 300}, // Square scanner box
            rememberLastUsedCamera: true,
            supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA]
        };

        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", config, /* verbose= */ false);
        html5QrcodeScanner.render(onScanSuccess, onScanError);
    </script>
</body>
</html>
"""

# Render the scanner HTML
html(scanner_html, height=500)

# Placeholder for the scanned QR code
qr_code = st.empty()

# Display the QR code result if available
if 'qr_code' in st.session_state:
    qr_code.write(st.session_state.qr_code)
