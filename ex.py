import cv2
from pyzbar.pyzbar import decode

def scan_barcode_from_camera():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image from camera")
            break
        
        # Convert frame to grayscale (optional depending on barcode type)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Find barcodes and decode them
        barcodes = decode(gray)
        
        for barcode in barcodes:
            # Extract barcode data and draw a rectangle around it
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            # Convert barcode data from bytes to string
            barcode_data = barcode.data.decode("utf-8")
            
            # Print barcode type and data
            print(f"Barcode Type: {barcode.type}, Barcode Data: {barcode_data}")
            
            # Display the barcode data on the frame
            cv2.putText(frame, barcode_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow('Barcode Scanner', frame)
        
        # Check for 'q' key press to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()

# Run the barcode scanning function
scan_barcode_from_camera()
