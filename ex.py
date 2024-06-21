import streamlit as st
import cv2
import numpy as np
import qrtools

# สร้างหน้าต่าง Streamlit
st.title('QR Code Scanner from Camera')

# เปิดกล้อง
camera = cv2.VideoCapture(0)

# สร้าง instance ของ qrtools.QR()
qr = qrtools.QR()

# ลูปอ่านภาพจากกล้อง
while True:
    # อ่านภาพจากกล้อง
    _, frame = camera.read()
    
    # แปลงภาพให้เป็น grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # ใช้ qrtools เพื่ออ่าน QR code จากกล้อง
    qr.decode_webcam(camera_index=0, show_video=False)
    
    # แสดงผลลัพธ์
    if qr.data:
        st.success(f"Found QR code with data: {qr.data}")
        break
    
    # แสดงภาพจากกล้องใน Streamlit
    st.image(frame, channels='BGR', use_column_width=True)

# หยุดกล้องเมื่อเสร็จสิ้น
camera.release()
