import streamlit as st

html_code = '''
<div id="reader" style="width: 600px; height: 600px;"></div>
<script src="./dist/html5-qrcode.js"></script>
<script>
    var resultContainer = document.createElement('div');
    resultContainer.id = 'results';
    document.body.appendChild(resultContainer);

    var html5QrcodeScanner = new Html5QrcodeScanner(
        "reader", { fps: 10, qrbox: 250 });
    
    html5QrcodeScanner.render(onScanSuccess);
    
    function onScanSuccess(qrCodeMessage) {
        document.getElementById('results').innerText = qrCodeMessage;
    }
</script>
'''

st.components.v1.html(html_code)
