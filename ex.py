import pyodbc
import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import re
import os
from PIL import Image
import cv2
import numpy as np
import time

# Set page configuration
st.set_page_config(layout="wide")

# Function to check user credentials
@st.cache_data
def check_credentials(username, password):
    user_db = {
        'nui': ('1234', 'regular'),
        'pan': ('5678', 'regular'),
        'sand': ('9876', 'regular'),
        'fai': ('5432', 'regular'),
        'io': ('1234', 'regular'),
        'dream': ('5678', 'regular'),
        'admin1': ('adminpassword', 'regular'),
        'tan': ('9876', 'special'),
        'admin': ('adminpassword', 'special'),
        'vasz': ('1234', 'special')
    }
    user_info = user_db.get(username.lower())
    if user_info and user_info[0] == password:
        return user_info[1]
    return None

@st.cache_data
def get_connection_string(company):
    if company == 'K.G. Corporation Co.,Ltd.':
        server = '61.91.59.134'
        port = '1544'
        db_username = 'sa'
        db_password = 'kg@dm1nUsr!'
        database = 'KGE'
    elif company == 'The Chill Resort & Spa Co., Ltd.':
        server = '61.91.59.134'
        port = '1544'
        db_username = 'sa'
        db_password = 'kg@dm1nUsr!'
        database = 'THECHILL'

    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};DATABASE={database};UID={db_username};PWD={db_password}'
    return conn_str

@st.cache_data
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
                product_data['Status'], product_data['Condition'] # Adding status and condition
            ]
            cursor.execute(query, data)
            conn.commit()
        st.success("Data saved successfully!")
    except pyodbc.Error as e:
        st.error(f"Error inserting data: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

@st.cache_data
def load_data(selected_product_name, selected_whcid, conn_str):
    query_detail = '''
    SELECT
        a.ITMID, a.NAME_TH, a.PURCHASING_UOM, a.MODEL,
        b.BRAND_NAME, c.CAB_NAME, d.SHE_NAME, e.BLK_NAME,
        p.WHCID, w.NAME_TH AS WAREHOUSE_NAME, p.BATCH_NO, p.BALANCE AS INSTOCK
    FROM
        ERP_ITEM_MASTER_DATA a
        LEFT JOIN ERP_GOODS_RECEIPT_PO_BATCH p ON a.ITMID = p.ITMID
        LEFT JOIN ERP_BRAND b ON a.BRAID = b.BRAID
        LEFT JOIN ERP_CABINET c ON p.CABID = c.CABID
        LEFT JOIN ERP_SHELF d ON p.SHEID = d.SHEID
        LEFT JOIN ERP_BLOCK e ON p.BLKID = e.BLKID
        LEFT JOIN ERP_WAREHOUSES_CODE w ON p.WHCID = w.WHCID
    WHERE
        a.EDITDATE IS NULL AND
        a.GRPID IN ('11', '71', '77', '73', '76', '75') AND
        a.ITMID + ' - ' + a.NAME_TH + ' - ' + a.MODEL + ' - ' + COALESCE(b.BRAND_NAME, '') = ? AND
        p.WHCID = ?
    '''
    try:
        with pyodbc.connect(conn_str) as conn:
            filtered_items_df = pd.read_sql(query_detail, conn, params=(selected_product_name, selected_whcid.split(' -')[0]))
        return filtered_items_df
    except pyodbc.Error as e:
        st.error(f"Error loading data: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

@st.cache_data
def fetch_products(company):
    conn_str = get_connection_string(company)
    try:
        with pyodbc.connect(conn_str) as conn:
            product_query = '''
            SELECT x.ITMID, x.NAME_TH, x.MODEL, x.EDITDATE, q.BRAND_NAME
            FROM ERP_ITEM_MASTER_DATA x
            LEFT JOIN ERP_BRAND q ON x.BRAID = q.BRAID
            WHERE x.EDITDATE IS NULL AND x.GRPID IN ('11', '71', '77', '73', '76', '75')
            '''
            items_df = pd.read_sql(product_query, conn)
        return items_df.fillna('')
    except pyodbc.Error as e:
        st.error(f"Error fetching products: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

def select_product(company, conn_str):
    st.write("ค้นหาสินค้า 🔎")
    items_df = fetch_products(company)
    items_options = list(items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'])

    # Adding CSS for word wrap
    st.markdown("""
        <style>
        .wrap-text .css-1wa3eu0 {
            white-space: normal !important;
            overflow-wrap: anywhere;
        }
        </style>
        """, unsafe_allow_html=True)

    selected_product_name = st.selectbox("เลือกสินค้า", options=items_options, index=None, key='selected_product')

    # QR code scanning section
    st.write("หรือ Scan QR Code เพื่อค้นหาสินค้า:")
    camera = st.camera_input("Scan Your QR Code Here", key="cameraqrcode", help="Place QR code inside the frame.")
    if camera is not None:
        try:
            # Read the camera input as an image
            img = Image.open(camera)
            frame = np.array(img)
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            qr_detector = cv2.QRCodeDetector()
            retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(gray)

            if retval:
                for code in decoded_info:
                    qr_data = code  # No need to decode, already a string
                    st.write(f"QR Code Detected: {qr_data}")

                    # Assuming QR code contains product ID or name
                    matching_products = items_df[items_df['ITMID'].str.contains(qr_data)]
                    if not matching_products.empty:
                        selected_product_name = matching_products.iloc[0]['ITMID'] + ' - ' + matching_products.iloc[0]['NAME_TH'] + ' - ' + matching_products.iloc[0]['MODEL'] + ' - ' + matching_products.iloc[0]['BRAND_NAME']
                        st.write(f"Matching Product: {selected_product_name}")
                        return selected_product_name, matching_products.iloc[0]
            else:
                st.write("No QR code detected.")

        except cv2.error as e:
            st.error(f"OpenCV Error: {e}")

        except Exception as e:
            st.error(f"Error processing QR code: {e}")

    if selected_product_name:
        selected_item = items_df[items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'] == selected_product_name]
        return selected_product_name, selected_item

    return None, None

def count_product(selected_product_name, selected_item, conn_str):
    filtered_items_df = load_data(selected_product_name, st.session_state.selected_whcid, conn_str)
    total_balance = 0

    if not filtered_items_df.empty:
        st.write("รายละเอียดสินค้า:")
        filtered_items_df['Location'] = filtered_items_df[['CAB_NAME', 'SHE_NAME', 'BLK_NAME']].apply(lambda x: ' / '.join(x.astype(str)), axis=1)
        filtered_items_df_positive_balance = filtered_items_df[filtered_items_df['INSTOCK'] > 0]

        display_columns = ['Location', 'BATCH_NO']
        if st.session_state.user_role == 'special':
            display_columns.append('INSTOCK')

        if not filtered_items_df_positive_balance.empty:
            filtered_items_df_positive_balance = filtered_items_df_positive_balance[display_columns]
            filtered_items_df_positive_balance.index = range(1, len(filtered_items_df_positive_balance) + 1)
            st.dataframe(filtered_items_df_positive_balance)
            if 'INSTOCK' in display_columns:
                total_balance = filtered_items_df_positive_balance['INSTOCK'].sum()
                st.write(f"รวมยอดสินค้าในคลัง: {total_balance}")
        else:
            st.write("ไม่มีสินค้าที่มียอดเหลือในคลัง")

        if not filtered_items_df.empty:
            product_name = f"{filtered_items_df['NAME_TH'].iloc[0]} {filtered_items_df['MODEL'].iloc[0]} {filtered_items_df['BRAND_NAME'].iloc[0]}"
        else:
            product_name = f"{selected_item['NAME_TH'].iloc[0]} {selected_item['MODEL'].iloc[0]} {selected_item['BRAND_NAME'].iloc[0]}"

        image_url = get_image_url(product_name)
        if image_url:
            st.image(image_url, width=300)
        else:
            st.write("ไม่พบรูปภาพของสินค้า")
    else:
        st.warning("ไม่พบข้อมูลสินค้าที่เลือก")

    if st.session_state.user_role == 'regular' and 'INSTOCK' in filtered_items_df.columns:
        # Calculate total_balance only if the user is not special (regular)
        total_balance = filtered_items_df['INSTOCK'].sum()
    
    product_quantity = st.number_input(label='จำนวนสินค้า 🛒', min_value=0, value=st.session_state.product_quantity)
    status = st.selectbox("สถานะ 📝", ["มือหนึ่ง", "มือสอง", "ผสม", "รอเคลม", "รอคืน", "รอขาย"], index=None)
    condition = st.selectbox("สภาพสินค้า 📝", ["ใหม่", "เก่าเก็บ", "พอใช้ได้", "แย่", "เสียหาย", "ผสม"], index=None)
    remark = st.text_area('หมายเหตุ 💬  \nระบุ สถานะ : ผสม (ใหม่+ของคืน)  \nสภาพสินค้า: ผสม (ใหม่+เก่า+เศษ+อื่นๆ)', value=st.session_state.remark)
    st.markdown("---")

    if st.button('👉 Enter'):
        if status is None or condition is None:
            st.error("กรุณาเลือก 'สถานะ' และ 'สภาพสินค้า' ก่อนบันทึกข้อมูล")
        elif status == "ผสม" and not remark.strip():
            st.error("กรุณาใส่ 'หมายเหตุ' เมื่อเลือกสถานะ 'ผสม'")
        elif product_quantity >= 0:
            timezone = pytz.timezone('Asia/Bangkok')
            current_time = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
            product_data = {
                'Time': current_time,
                'Enter_By': st.session_state.username.upper(),
                'Product_ID': str(filtered_items_df['ITMID'].iloc[0] if not filtered_items_df.empty else selected_item['ITMID'].iloc[0]),
                'Product_Name': str(filtered_items_df['NAME_TH'].iloc[0] if not filtered_items_df.empty else selected_item['NAME_TH'].iloc[0]),
                'Model': str(filtered_items_df['MODEL'].iloc[0] if not filtered_items_df.empty else selected_item['MODEL'].iloc[0]),
                'Brand_Name': str(filtered_items_df['BRAND_NAME'].iloc[0] if not filtered_items_df.empty else selected_item['BRAND_NAME'].iloc[0]),
                'Cabinet': str(filtered_items_df['CAB_NAME'].iloc[0] if not filtered_items_df.empty else ""),
                'Shelf': str(filtered_items_df['SHE_NAME'].iloc[0] if not filtered_items_df.empty else ""),
                'Block': str(filtered_items_df['BLK_NAME'].iloc[0] if not filtered_items_df.empty else ""),
                'Warehouse_ID': str(filtered_items_df['WHCID'].iloc[0] if not filtered_items_df.empty else st.session_state.selected_whcid.split(' -')[0]),
                'Warehouse_Name': str(filtered_items_df['WAREHOUSE_NAME'].iloc[0] if not filtered_items_df.empty else st.session_state.selected_whcid.split(' -')[1]),
                'Batch_No': str(filtered_items_df['BATCH_NO'].iloc[0] if not filtered_items_df.empty else ""),
                'Purchasing_UOM': str(filtered_items_df['PURCHASING_UOM'].iloc[0] if not filtered_items_df.empty else selected_item['PURCHASING_UOM'].iloc[0]),
                'Total_Balance': int(total_balance) if not filtered_items_df.empty else 0,
                'Quantity': int(product_quantity),
                'Remark': remark,
                'whcid': filtered_items_df['WHCID'].iloc[0] if not filtered_items_df.empty else st.session_state.selected_whcid.split(' -')[0],
                'Status': status,
                'Condition': condition
            }
            st.session_state.product_data.append(product_data)
            save_to_database(product_data, conn_str)
            st.session_state.product_data = []
            st.session_state.product_quantity = 0
            st.session_state.remark = ""
            time.sleep(2)
            del st.session_state['selected_product']
            st.experimental_rerun()

# Main function to run the app
def main():
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'company' not in st.session_state:
        st.session_state.company = ''

    st.title("Inventory Count App")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        user_type = check_credentials(username, password)
        if user_type:
            st.session_state.username = username
            st.session_state.user_type = user_type
            st.session_state.company = 'K.G. Corporation Co.,Ltd.'  # or set dynamically if needed
            st.success("Login successful!")
        else:
            st.error("Invalid username or password")

    if st.session_state.username:
        st.header(f"Welcome, {st.session_state.username}")
        st.write(f"Logged in as: {st.session_state.user_type}")
        conn_str = get_connection_string(st.session_state.company)
        selected_product_name, selected_item = select_product(st.session_state.company, conn_str)
        if selected_product_name and not selected_item.empty:
            count_product(selected_item, conn_str)
        else:
            st.warning("No product selected or QR code not matched.")

if __name__ == "__main__":
    main()
