import pyodbc
import pandas as pd
import streamlit as st
from datetime import datetime
import time
import pytz
import requests
from bs4 import BeautifulSoup
import re
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
        a.EDITDATE IS NULL AND b.EDITDATE IS NULL AND c.EDITDATE IS NULL AND d.EDITDATE IS NULL AND e.EDITDATE IS NULL AND p.EDITDATE IS NULL AND
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
            WHERE x.EDITDATE IS NULL AND q.EDITDATE IS NULL AND
            x.GRPID IN ('11', '71', '77', '73', '76', '75')
            '''
            items_df = pd.read_sql(product_query, conn)
        return items_df.fillna('')
    except pyodbc.Error as e:
        st.error(f"Error fetching products: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

def select_product_by_text(company):
    st.write("ค้นหาสินค้า 🔎")
    items_df = fetch_products(company)
    items_options = list(items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'])

    selected_product_name = st.selectbox("พิมพ์เพื่อค้นหาใน:", options=items_options, index=None, key='selected_product')

    if selected_product_name:
        selected_item = items_df[items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'] == selected_product_name]
        st.write(f"คุณเลือกสินค้า: {selected_product_name}")
        st.markdown("---")
        return selected_product_name, selected_item
    else:
        return None, None

def select_product_by_qr(company):
    st.write("ค้นหาสินค้า 🔍")
    items_df = fetch_products(company)
    items_options = list(items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'])

    # QR code scanner
    qr_code = qrcode_scanner(key="qr_code_scanner")
    if qr_code:
        st.write(f"QR Code detected: {qr_code}")
        selected_product_name = items_df[items_df['ITMID'] == qr_code]
        if not selected_product_name.empty:
            selected_product_name = selected_product_name.iloc[0]['ITMID'] + ' - ' + selected_product_name.iloc[0]['NAME_TH'] + ' - ' + selected_product_name.iloc[0]['MODEL'] + ' - ' + selected_product_name.iloc[0]['BRAND_NAME']
            selected_item = items_df[items_df['ITMID'] == qr_code]
            st.write(f"คุณเลือกสินค้า: {selected_product_name}")
            st.markdown("---")
            return selected_product_name, selected_item

    st.markdown("""
        <style>
        .wrap-text .css-1wa3eu0 {
            white-space: normal !important;
            overflow-wrap: anywhere;
        }
        </style>
        """, unsafe_allow_html=True)

    selected_product_name = st.selectbox("เลือกสินค้า", options=items_options, index=None, key='selected_product_qr')

    if selected_product_name:
        selected_item = items_df[items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'] == selected_product_name]
        st.write(f"คุณเลือกสินค้า: {selected_product_name}")
        st.markdown("---")
        return selected_product_name, selected_item
    else:
        return None, None

def select_product(company):
    st.write("เลือกวิธีค้นหาสินค้า:")
    search_method = st.radio("ค้นหาสินค้าด้วย:", ('พิมพ์เพื่อค้นหา', 'ค้นหาด้วย QR Code'))

    if search_method == 'พิมพ์เพื่อค้นหา':
        selected_product_name, selected_item = select_product_by_text(company)
    else:
        selected_product_name, selected_item = select_product_by_qr(company)

    return selected_product_name, selected_item

def main():
    st.title("ระบบตรวจนับสินค้า")
    st.sidebar.title("Authentication")

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    company = st.sidebar.selectbox("เลือกบริษัท", ["K.G. Corporation Co.,Ltd.", "The Chill Resort & Spa Co., Ltd."])

    if st.sidebar.button("Login"):
        role = check_credentials(username, password)
        if role:
            st.sidebar.success(f"Logged in as {username}")
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.company = company
            st.session_state.role = role
        else:
            st.sidebar.error("Invalid username or password")

    if st.session_state.get("logged_in"):
        selected_product_name, selected_item = select_product(st.session_state.company)

        if selected_product_name:
            conn_str = get_connection_string(st.session_state.company)
            if st.button('👉 Enter'):
                filtered_items_df = load_data(selected_product_name, selected_whcid, conn_str)
                if not filtered_items_df.empty:
                    product_quantity_str = st.text_input("จำนวนที่นับได้")
                    status = st.selectbox("สถานะ", ["New", "Used", "Damaged"])
                    condition = st.selectbox("สภาพ", ["Good", "Fair", "Poor"])
                    remark = st.text_area("หมายเหตุ")

                    if st.button('บันทึก'):
                        product_data = {
                            'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'Enter_By': st.session_state.username,
                            'Product_ID': selected_item.iloc[0]['ITMID'],
                            'Product_Name': selected_item.iloc[0]['NAME_TH'],
                            'Purchasing_UOM': selected_item.iloc[0]['PURCHASING_UOM'],
                            'Quantity': product_quantity_str,
                            'Total_Balance': selected_item.iloc[0]['INSTOCK'],
                            'whcid': selected_item.iloc[0]['WHCID'],
                            'Status': status,
                            'Condition': condition,
                            'Remark': remark
                        }
                        save_to_database(product_data, conn_str)

if __name__ == "__main__":
    main()
