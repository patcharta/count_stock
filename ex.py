import cv2
import numpy as np
import streamlit as st
from pyzbar.pyzbar import decode

st.set_page_config(layout="wide")

def scan_qr_code():
    cap = cv2.VideoCapture(0)
    st.write("Scanning for QR code...")

    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to capture image")
            break

        # Define square scan area
        height, width, _ = frame.shape
        square_size = min(height, width) // 2
        top_left_x = (width - square_size) // 2
        top_left_y = (height - square_size) // 2

        # Draw square scan box
        cv2.rectangle(frame, (top_left_x, top_left_y), (top_left_x + square_size, top_left_y + square_size), (0, 255, 0), 2)

        # Crop to the square scan box
        scan_area = frame[top_left_y:top_left_y + square_size, top_left_x:top_left_x + square_size]

        decoded_objects = decode(scan_area)
        for obj in decoded_objects:
            st.success(f"QR Code detected: {obj.data.decode('utf-8')}")
            cap.release()
            cv2.destroyAllWindows()
            return obj.data.decode('utf-8')

        # Display the video frame with the scan box
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st.image(frame_rgb, channels="RGB")

    cap.release()
    cv2.destroyAllWindows()

if st.button("Start QR Code Scanner"):
    qr_code_data = scan_qr_code()
    if qr_code_data:
        st.write(f"Scanned QR Code: {qr_code_data}")
