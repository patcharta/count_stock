import streamlit as st
import pyodbc
import pandas as pd
from streamlit_qrcode_scanner import qrcode_scanner

# เพื่อให้แน่ใจว่าค่าที่จะระบุมีการเปลี่ยนแปลง
# หลังจากสแกน QR และเลือกสินค้าเรียบร้อยแล้ว
# ข้อมูลของผู้ใช้ก็ไม่ได้รับการอัปเดต
def save_to_database(product_data, conn_str):
    try:
        remark = product_data.get('Remark', '')
        query = '''
        INSERT INTO ERP_COUNT_STOCK (
            ID, LOGDATE, ENTERBY, ITMID, ITEMNAME, UNIT, REMARK, ACTUAL, INSTOCK, WHCID, STATUS, CONDITION
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(ID), 0) FROM ERP_COUNT_STOCK")
            max_id = cursor.fetchone()[0]
            new_id = max_id + 1
            data = [
                new_id, product_data['Time'], product_data['Enter_By'],
                product_data['Product_ID'], product_data['Product_Name'],
                product_data['Purchasing_UOM'], remark,
                product_data['Quantity'], product_data['Total_Balance'], product_data['whcid'],
                product_data['Status'], product_data['Condition']
            ]
            cursor.execute(query, data)
            conn.commit()
        st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")
    except pyodbc.Error as e:
        st.error(f"เกิดข้อผิดพลาดในการแทรกข้อมูล: {e}")
    except Exception as e:
        st.error(f"ข้อผิดพลาดที่ไม่คาดคิด: {e}")

def main():
    selected_product_name = None
    product_data = []

    st.write("สแกน QR code เพื่อค้นหาสินค้า:")
    qr_code = qrcode_scanner(key="qr_code_scanner")
    if qr_code:
        st.write(f"สแกน QR code แล้ว: {qr_code}")
        if st.button("ยืนยันการเลือกสินค้าจาก QR code"):
            selected_product_name = qr_code
            st.experimental_rerun()

    if selected_product_name:
        st.write(f"คุณเลือกสินค้า: {selected_product_name}")
        product_data = {
            'Time': '2024-06-21 12:00:00',
            'Enter_By': 'Admin',
            'Product_ID': '123',
            'Product_Name': 'Product A',
            'Purchasing_UOM': 'PCS',
            'Quantity': 10,
            'Total_Balance': 100,
            'whcid': '001',
            'Status': 'New',
            'Condition': 'Good'
        }
        save_to_database(product_data, 'your_connection_string_here')

if __name__ == "__main__":
    main()
