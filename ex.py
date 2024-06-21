import streamlit as st
import cv2
from PIL import Image
import zbarlight

st.title('QR Code Scanner from Camera')

camera = cv2.VideoCapture(0)

while True:
    _, frame = camera.read()
    
    # แปลงภาพจาก OpenCV BGR เป็น RGB (สำหรับ zbarlight)
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # สร้างภาพ Image จาก OpenCV frame
    pil_img = Image.fromarray(img_rgb)
    
    # สแกน QR code จากภาพ
    codes = zbarlight.scan_codes('qrcode', pil_img)
    
    # แสดงผลลัพธ์
    if codes:
        st.success(f"Found QR code with data: {codes[0].decode('utf-8')}")
        break
    
    # แสดงภาพจากกล้องใน Streamlit
    st.image(frame, channels='BGR', use_column_width=True)

# หยุดกล้องเมื่อเสร็จสิ้น
camera.release()
