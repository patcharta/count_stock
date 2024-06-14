import streamlit as st
import cv2
import numpy as np

# Function to scan barcode using OpenCV
def scan_barcode_opencv(frame):
    try:
        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Load the barcode detector (you may need to adjust parameters)
        detector = cv2.QRCodeDetector()

        # Detect and decode the barcode
        data, bbox, _ = detector.detectAndDecode(gray)

        # If barcode is detected, return the data
        if bbox is not None:
            return data

    except Exception as e:
        st.error(f"Error scanning barcode: {e}")

    return None

# Streamlit app
def main():
    st.title("Barcode Scanner using OpenCV and Streamlit")

    # Instructions
    st.write("Move a barcode in front of your webcam to scan it.")

    # OpenCV's VideoCapture for webcam
    cap = cv2.VideoCapture(0)

    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # Scan barcode
            barcode_data = scan_barcode_opencv(frame)
            if barcode_data:
                st.write(f"Barcode Detected: {barcode_data}")
        cap.release()
    else:
        st.error("Unable to access the webcam.")

if __name__ == "__main__":
    main()
