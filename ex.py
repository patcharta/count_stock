import streamlit as st
from PIL import Image
import cv2
import numpy as np
from pyzbar.pyzbar import decode

def scan_barcode(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    barcodes = decode(gray)

    if barcodes:
        barcode_data = barcodes[0].data.decode('utf-8')
        return barcode_data
    return None

def main():
    st.title('Barcode Scanner')

    camera = st.camera_input('Scan Your Barcode Here', key='camerabarcode', help='Place barcode inside the frame.')

    if camera is not None:
        try:
            img = Image.open(camera)
            frame = np.array(img)

            barcode_data = scan_barcode(frame)
            
            if barcode_data:
                st.write(f'Barcode Detected: {barcode_data}')
            else:
                st.write('No barcode detected.')

        except Exception as e:
            st.error(f'Error processing barcode: {e}')

if __name__ == '__main__':
    main()
