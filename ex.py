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
@st.cache(allow_output_mutation=True)
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

@st.cache(allow_output_mutation=True)
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

@st.cache(allow_output_mutation=True)
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

@st.cache(allow_output_mutation=True)
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

@st.cache(allow_output_mutation=True)
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        images = soup.find_all("img", {"src": re.compile("gstatic.com")})
        return images[0]["src"] if images else None
    except Exception as e:
        st.error(f"Error fetching image URL: {e}")
        return None

def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("ERP Stock Count Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user_role = check_credentials(username, password)
            if user_role:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_role = user_role
                st.success("Login successful!")
            else:
                st.error("Invalid username or password")
        return

    st.title("ERP Stock Count")
    st.sidebar.title("User Information")
    st.sidebar.write(f"**Username:** {st.session_state.username}")
    st.sidebar.write(f"**Role:** {st.session_state.user_role}")

    companies = ["K.G. Corporation Co.,Ltd.", "The Chill Resort & Spa Co., Ltd."]
    selected_company = st.sidebar.selectbox("Select Company", companies)

    if not selected_company:
        st.error("Please select a company")
        return

    conn_str = get_connection_string(selected_company)
    product_name, product_info = select_product(selected_company, conn_str)

    if product_info is not None and not product_info.empty:
        product_info = product_info.iloc[0]
        st.markdown("### Product Information")
        st.write(f"**Product ID:** {product_info['ITMID']}")
        st.write(f"**Product Name:** {product_info['NAME_TH']}")
        st.write(f"**Purchasing UOM:** {product_info['PURCHASING_UOM']}")
        st.write(f"**Brand:** {product_info['BRAND_NAME']}")
        st.write(f"**Warehouse:** {product_info['WAREHOUSE_NAME']}")
        st.write(f"**Batch No.:** {product_info['BATCH_NO']}")
        st.write(f"**In Stock:** {product_info['INSTOCK']}")

        image_url = get_image_url(product_info['NAME_TH'])
        if image_url:
            st.image(image_url, caption=product_info['NAME_TH'], use_column_width=True)

        st.markdown("### Count Stock")
        with st.form(key="count_form"):
            enter_by = st.text_input("Enter By", st.session_state.username)
            actual = st.number_input("Actual", min_value=0, step=1)
            quantity = st.number_input("Quantity", min_value=0, step=1)
            remark = st.text_area("Remark")
            condition = st.selectbox("Condition", ["Good", "Damaged", "Expired"])
            status = st.selectbox("Status", ["Available", "Unavailable", "Reserved"])
            submit_button = st.form_submit_button(label="Submit")

            if submit_button:
                product_data = {
                    'Time': datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S'),
                    'Enter_By': enter_by,
                    'Product_ID': product_info['ITMID'],
                    'Product_Name': product_info['NAME_TH'],
                    'Purchasing_UOM': product_info['PURCHASING_UOM'],
                    'Remark': remark,
                    'Quantity': quantity,
                    'Total_Balance': product_info['INSTOCK'],
                    'whcid': product_info['WHCID'],
                    'Condition': condition,
                    'Status': status,
                }
                save_to_database(product_data, conn_str)

if __name__ == "__main__":
    main()
