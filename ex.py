import streamlit as st
import cv2
from pyzbar.pyzbar import decode

def main():
    st.title("QR Code Scanner")

    # Open camera
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to capture image from camera.")
            break

        # Convert frame to grayscale (optional)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect QR codes
        decoded_objects = decode(gray)

        # Display results
        for obj in decoded_objects:
            st.success(f"QR Code detected: {obj.data.decode('utf-8')}")

        # Display the camera feed
        st.image(frame, channels="BGR", use_column_width=True)

    cap.release()

if __name__ == "__main__":
    main()
