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

    # Attempt to access webcam
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # Scan barcode
                barcode_data = scan_barcode_opencv(frame)
                if barcode_data:
                    st.write(f"Barcode Detected: {barcode_data}")
            else:
                st.error("Unable to read frame from webcam.")
        else:
            st.error("Failed to open webcam. Check if it's being used by another application or if permissions are set correctly.")
        
        cap.release()  # Release the capture object

    except Exception as e:
        st.error(f"Error accessing webcam: {e}")

if __name__ == "__main__":
    main()
