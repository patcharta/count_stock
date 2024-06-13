import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

class BarcodeScanner(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = decode(img)
        for barcode in barcodes:
            x, y, w, h = barcode.rect
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = f'{barcode_data} ({barcode_type})'
            cv2.putText(img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return img

st.title("Barcode Scanner")
webrtc_streamer(key="example", video_transformer_factory=BarcodeScanner)
