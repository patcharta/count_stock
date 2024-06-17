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
from streamlit_qrcode_scanner import qrcode_scanner

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

def select_product(company):
    st.write("ค้นหาสินค้า 🔎")
    items_df = fetch_products(company)
    items_options = list(items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'])

    # QR code scanner
    qr_code = qrcode_scanner(key="qr_code_scanner")
    if qr_code:
        st.write(f"QR Code detected: {qr_code}")
        items_df = items_df[items_df['ITMID'] == qr_code]

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

        if st.session_state.user_role == 'special':
            st.table(filtered_items_df[display_columns])
        else:
            st.table(filtered_items_df_positive_balance[display_columns])

        if st.session_state.user_role == 'special':
            st.warning("Role: Special, all items shown")
        else:
            st.warning("Role: Regular, only items with positive balance shown")

        total_balance = filtered_items_df['INSTOCK'].sum()
    else:
        st.write("ไม่พบข้อมูลสินค้าที่เลือก")

    st.session_state.enter_by = st.text_input("Enter by:", value="", placeholder="Enter your name")
    product_id = selected_item.iloc[0]['ITMID']
    product_name = selected_item.iloc[0]['NAME_TH']
    purchasing_uom = selected_item.iloc[0]['PURCHASING_UOM']
    model = selected_item.iloc[0]['MODEL']
    brand_name = selected_item.iloc[0]['BRAND_NAME']
    whcid = st.session_state.selected_whcid

    st.write(f"Product ID: {product_id}")
    st.write(f"Product Name: {product_name}")
    st.write(f"Purchasing UOM: {purchasing_uom}")
    st.write(f"Model: {model}")
    st.write(f"Brand Name: {brand_name}")

    st.write(f"คลังที่เลือก: {whcid}")

    image_url = get_image_url(product_name)
    if image_url:
        st.image(image_url, caption=product_name, use_column_width=True)
    else:
        st.write("ไม่พบภาพสินค้าที่ต้องการ")

    quantity = st.number_input("กรุณากรอกยอดตรวจนับ:", min_value=0, step=1)

    if st.button("บันทึกข้อมูล"):
        product_data = {
            'Time': datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S'),
            'Enter_By': st.session_state.enter_by,
            'Product_ID': product_id,
            'Product_Name': product_name,
            'Purchasing_UOM': purchasing_uom,
            'Remark': '',
            'Quantity': quantity,
            'Total_Balance': total_balance,
            'whcid': whcid,
            'Status': 'Pending', # Example status
            'Condition': 'Good' # Example condition
        }
        save_to_database(product_data, conn_str)

def main_section():
    if st.session_state.authenticated:
        selected_product_name, selected_item = select_product(st.session_state.company)
        if selected_product_name and selected_item is not None:
            count_product(selected_product_name, selected_item, get_connection_string(st.session_state.company))

def app():
    st.title("นับสินค้า")

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'company' not in st.session_state:
        st.session_state.company = None
    if 'selected_whcid' not in st.session_state:
        st.session_state.selected_whcid = None

    if not st.session_state.authenticated:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        company = st.selectbox("Company", ['K.G. Corporation Co.,Ltd.', 'The Chill Resort & Spa Co., Ltd.'])
        if st.button("Login"):
            user_role = check_credentials(username, password)
            if user_role:
                st.session_state.authenticated = True
                st.session_state.user_role = user_role
                st.session_state.company = company
                st.success("Login successful!")
            else:
                st.error("Invalid username or password")
    else:
        whcids = {
            'K.G. Corporation Co.,Ltd.': ['WHCID1 - Warehouse 1', 'WHCID2 - Warehouse 2'],
            'The Chill Resort & Spa Co., Ltd.': ['WHCID3 - Warehouse 3', 'WHCID4 - Warehouse 4']
        }
        st.session_state.selected_whcid = st.selectbox("เลือกคลังสินค้า", whcids[st.session_state.company])
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.company = None
            st.session_state.selected_whcid = None
        main_section()

if __name__ == "__main__":
    app()
