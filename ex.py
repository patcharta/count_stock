import streamlit as st
import cv2
from PIL import Image
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

# Function to display webcam input
def display_webcam():
    try:
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to capture frame from webcam")
                break

            # Display the frame in Streamlit
            st.image(frame, channels="BGR", use_column_width=True)

            # Scan barcode
            barcode_data = scan_barcode_opencv(frame)
            if barcode_data:
                st.write(f"Barcode Detected: {barcode_data}")
                break

        cap.release()
    except Exception as e:
        st.error(f"Error accessing webcam: {e}")

# Streamlit app
def main():
    st.title("Barcode Scanner using OpenCV")

    # Display webcam input and scan barcode
    display_webcam()

if __name__ == "__main__":
    main()
