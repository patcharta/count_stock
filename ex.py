import pyodbc
import pandas as pd
import streamlit as st
from datetime import datetime
import time
import pytz
import requests
from bs4 import BeautifulSoup
import re
import os
from PIL import Image
import cv2
import numpy as np
from camera_input_live import camera_input_live

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
            SELECT x.ITMID, x.NAME_TH, x.MODEL, x.EDITDATE, q.BRAND_NAME, p.WHCID
            FROM ERP_ITEM_MASTER_DATA x
            LEFT JOIN ERP_BRAND q ON x.BRAID = q.BRAID
            LEFT JOIN ERP_GOODS_RECEIPT_PO_BATCH p ON x.ITMID = p.ITMID  -- Adjusted join condition if needed
            WHERE x.EDITDATE IS NULL AND x.GRPID IN ('11', '71', '77', '73', '76', '75')
            '''
            items_df = pd.read_sql(product_query, conn)
        
        if items_df.empty:
            st.warning("No products found.")
            return pd.DataFrame(columns=['ITMID', 'NAME_TH', 'MODEL', 'EDITDATE', 'BRAND_NAME', 'WHCID'])  # Return empty DataFrame with correct columns

        return items_df.fillna('')
    
    except pyodbc.Error as e:
        st.error(f"Error fetching products: {e}")
        return pd.DataFrame(columns=['ITMID', 'NAME_TH', 'MODEL', 'EDITDATE', 'BRAND_NAME', 'WHCID'])  # Return empty DataFrame with correct columns
    
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame(columns=['ITMID', 'NAME_TH', 'MODEL', 'EDITDATE', 'BRAND_NAME', 'WHCID'])  # Return empty DataFrame with correct columns

def select_product(company):
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

    if selected_product_name:
        selected_item = items_df[items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'] == selected_product_name]
        st.write(f"คุณเลือกสินค้า: {selected_product_name}")
        st.markdown("---")
        return selected_product_name, selected_item
    else:
        return None, None

def get_image_url(product_name):
    try:
        query = "+".join(product_name.split())
        url = f"https://www.google.com/search?tbm=isch&q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        image_element = soup.find("img", {"src": re.compile("https://.*")})
        image_url = image_element["src"] if image_element else None
        return image_url
    except Exception as e:
        st.error(f"Error fetching image: {e}")
        return None

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
        else:
            st.write("No stock available for this product.")

    with st.form(key="counting_form"):
        quantity = st.number_input("จำนวนที่นับได้", min_value=0, step=1, value=0)
        remark = st.text_area("หมายเหตุ", "")
        status_options = ["Complete", "Incomplete"]
        selected_status = st.selectbox("สถานะการนับ", status_options)
        condition_options = ["New", "Damaged"]
        selected_condition = st.selectbox("สภาพสินค้า", condition_options)
        submit_button = st.form_submit_button("บันทึก")

        if submit_button:
            current_time = datetime.now(pytz.timezone('Asia/Bangkok'))
            timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
            product_data = {
                'Product_ID': selected_item.iloc[0]['ITMID'],
                'Product_Name': selected_item.iloc[0]['NAME_TH'],
                'Purchasing_UOM': selected_item.iloc[0]['PURCHASING_UOM'],
                'Quantity': quantity,
                'Time': timestamp,
                'Enter_By': st.session_state.username,
                'Remark': remark,
                'Total_Balance': total_balance,
                'whcid': st.session_state.selected_whcid,
                'Status': selected_status,
                'Condition': selected_condition
            }
            save_to_database(product_data, conn_str)

    # QR code scanning section
    st.write("Scan QR Code to Search Product:")
    camera = st.camera_input("Scan Your QR Code Here", key="cameraqrcode", help="Place QR code inside the frame.")
    if camera is not None:
        try:
            frame = np.array(camera)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            qr_detector = cv2.QRCodeDetector()
            retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(gray)  
        
        if retval:
            for code in decoded_info:
                qr_data = code.decode('utf-8')
                st.write(f"QR Code Detected: {qr_data}")
            
            # Assuming QR code contains product ID or name
            # You can adjust this part based on your actual QR code content
            matching_products = filtered_items_df[filtered_items_df['ITMID'].str.contains(qr_data)]
            if not matching_products.empty:
                selected_product_name = matching_products.iloc[0]['ITMID'] + ' - ' + matching_products.iloc[0]['NAME_TH'] + ' - ' + matching_products.iloc[0]['MODEL'] + ' - ' + matching_products.iloc[0]['BRAND_NAME']
                st.write(f"Matching Product: {selected_product_name}")
                count_product(selected_product_name, matching_products.iloc[0], conn_str)
        else:
            st.write("No QR code detected.")
    
    except cv2.error as e:
        st.error(f"OpenCV Error: {e}")
    
    except Exception as e:
        st.error(f"Error processing QR code: {e}")

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None

    if st.session_state.logged_in:
        st.sidebar.write(f"Logged in as {st.session_state.username}")
        company = st.sidebar.selectbox('เลือกบริษัท', ('K.G. Corporation Co.,Ltd.', 'The Chill Resort & Spa Co., Ltd.'))
        st.sidebar.write(f"User Role: {st.session_state.user_role}")

        if company:
            selected_product_name, selected_item = select_product(company)
            if selected_product_name:
                st.write("เลือกสถานที่จัดเก็บสินค้า 🏢")
                filtered_items_df = fetch_products(company)
                whcids = filtered_items_df['WHCID'].unique().tolist()
                st.session_state.selected_whcid = st.selectbox("เลือกสถานที่จัดเก็บสินค้า", whcids, index=0)
                conn_str = get_connection_string(company)
                if st.session_state.selected_whcid:
                    count_product(selected_product_name, selected_item, conn_str)

                # Adding barcode scanning section
                st.write("Scan Barcode to Search Product:")
                camera = camera_input_live()
                if camera is not None:
                    image = np.array(Image.open(camera))
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    barcode_detector = cv2.QRCodeDetector()
                    retval, decoded_info, points, _ = barcode_detector.detectAndDecodeMulti(gray)

                    if retval:
                        st.write("Barcode Detected")
                        for code in decoded_info:
                            st.write(f"Barcode: {code}")
                            # Assuming barcode contains product ID or name
                            # You can adjust this part based on your actual barcode content
                            matching_products = filtered_items_df[filtered_items_df['ITMID'].str.contains(code)]
                            if not matching_products.empty:
                                selected_product_name = matching_products.iloc[0]['ITMID'] + ' - ' + matching_products.iloc[0]['NAME_TH'] + ' - ' + matching_products.iloc[0]['MODEL'] + ' - ' + matching_products.iloc[0]['BRAND_NAME']
                                st.write(f"Matching Product: {selected_product_name}")
                                count_product(selected_product_name, matching_products.iloc[0], conn_str)
                    else:
                        st.write("No barcode detected.")

    else:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")

        if login_button:
            user_role = check_credentials(username, password)
            if user_role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_role = user_role
                st.success("Login successful!")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("Invalid username or password.")

if __name__ == "__main__":
    main()
