import streamlit as st
import cv2
from pyzbar.pyzbar import decode

st.title('QR Code Reader')

uploaded_file = st.file_uploader("Upload an image containing QR code", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # อ่านไฟล์ภาพจากอัปโหลด
    img = cv2.imdecode(np.fromstring(uploaded_file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    # ใช้ pyzbar เพื่ออ่าน QR code
    decoded_objects = decode(img)

    if decoded_objects:
        st.header("Decoded QR Code:")
        for obj in decoded_objects:
            st.write(f"Data: {obj.data.decode('utf-8')}")
            st.image(img, caption='Uploaded Image', use_column_width=True)
    else:
        st.write("No QR code detected in the uploaded image.")
