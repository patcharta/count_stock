import streamlit as st
import qrtools

st.title('QR Code Scanner from Camera')

camera = cv2.VideoCapture(0)

while True:
    _, frame = camera.read()
    
    # ใช้ qrtools เพื่ออ่าน QR code
    qr = qrtools.QR()
    qr.decode_webcam()
    
    # แสดงผลลัพธ์
    if qr.data:
        st.success(f"Found QR code with data: {qr.data}")
        break
    
    # แสดงภาพจากกล้องใน Streamlit
    st.image(frame, channels='BGR', use_column_width=True)

# หยุดกล้องเมื่อเสร็จสิ้น
camera.release()
