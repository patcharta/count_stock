import cv2
from pyzbar.pyzbar import decode
import streamlit as st

st.title('QR Code Scanner from Camera')

camera = cv2.VideoCapture(0)

while True:
    _, frame = camera.read()

    # Decode QR codes
    decoded_objs = decode(frame)

    for obj in decoded_objs:
        # Print the QR code data
        st.success(f"Found QR code with data: {obj.data.decode('utf-8')}")
        break  # Break to display only the first QR code found

    # Display the camera feed in Streamlit
    st.image(frame, channels='BGR', use_column_width=True)

    # Exit condition
    if st.button('Stop'):
        break

# Release the camera
camera.release()
