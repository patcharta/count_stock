import streamlit as st
import cv2
import numpy as np
from PIL import Image

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

    # Capture image from webcam
    camera = st.camera_input("Scan Your Barcode Here", key="webcam")

    if camera is not None:
        # Convert the image to OpenCV format (RGB to BGR)
        frame = np.array(camera)  # Convert PIL image to numpy array
        frame = cv2.cvtColor(frame[:, :, ::-1], cv2.COLOR_RGB2BGR)  # Convert RGB to BGR

        # Scan barcode
        barcode_data = scan_barcode_opencv(frame)
        if barcode_data:
            st.write(f"Barcode Detected: {barcode_data}")

if __name__ == "__main__":
    main()
