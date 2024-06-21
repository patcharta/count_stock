import streamlit as st
import barcode
from barcode.writer import ImageWriter

st.title('QR Code Generator and Scanner from Camera')

data = st.text_input("Enter data for QR code generation:")

if data:
    qr = barcode.get_barcode_class('qrcode')
    qr_code = qr(data, writer=ImageWriter())
    qr_code_img = qr_code.save('qr_code.png')
    st.image('qr_code.png', caption='Generated QR Code', use_column_width=True)

    st.write("Scan the QR code using the camera:")

    camera = cv2.VideoCapture(0)
    
    while True:
        _, frame = camera.read()

        # แสดงภาพจากกล้องใน Streamlit
        st.image(frame, channels='BGR', use_column_width=True)
    
    # หยุดกล้องเมื่อเสร็จสิ้น
    camera.release()
