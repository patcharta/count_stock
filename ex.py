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
                product_data['Status'], product_data['Condition']
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

def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'enter_by' not in st.session_state:
        st.session_state.enter_by = None

    if st.session_state.authenticated:
        st.title("ERP Stock Count")

        st.write("เลือกวิธีการค้นหา:")
        search_option = st.radio("ค้นหาสินค้าด้วย:", ("ค้นหาด้วยข้อความ", "ค้นหาด้วย QR code"))

        company_options = ['K.G. Corporation Co.,Ltd.', 'The Chill Resort & Spa Co., Ltd.']
        selected_company = st.selectbox("เลือกบริษัท", options=company_options, index=None)

        selected_product_name = None
        selected_item = None

        if search_option == "ค้นหาด้วยข้อความ":
            selected_product_name, selected_item = select_product_by_text(selected_company)
        elif search_option == "ค้นหาด้วย QR code":
            selected_product_name, selected_item = select_product_by_qr(selected_company)

        if selected_product_name:
            st.write("เลือกคลังสินค้า")
            warehouse_options = ['0101 - คลังสินค้าสำเร็จรูป', '0404 - คลังสินค้าสำเร็จรูป (Site)']
            selected_whcid = st.selectbox("เลือกคลังสินค้า", options=warehouse_options, index=None)

            if selected_whcid:
                filtered_items_df = load_data(selected_product_name, selected_whcid, get_connection_string(selected_company))
                if not filtered_items_df.empty:
                    for index, row in filtered_items_df.iterrows():
                        with st.form(key=f'form_{index}'):
                            quantity = st.number_input(f"กรอกจำนวนสินค้าคงเหลือ: (Batch: {row['BATCH_NO']})", min_value=0.0, value=0.0)
                            remark = st.text_input("หมายเหตุ", value="")
                            submit_button = st.form_submit_button(label="บันทึกข้อมูล")
                            if submit_button:
                                product_data = {
                                    'Time': datetime.now(pytz.timezone('Asia/Bangkok')),
                                    'Enter_By': st.session_state.enter_by,
                                    'Product_ID': row['ITMID'],
                                    'Product_Name': row['NAME_TH'],
                                    'Purchasing_UOM': row['PURCHASING_UOM'],
                                    'Quantity': quantity,
                                    'Total_Balance': row['INSTOCK'],
                                    'Remark': remark,
                                    'whcid': selected_whcid.split(' - ')[0],
                                    'Status': 'รอผลตรวจนับ',
                                    'Condition': 'ปกติ'
                                }
                                save_to_database(product_data, get_connection_string(selected_company))
                else:
                    st.warning("ไม่พบข้อมูลสินค้าที่เลือกในคลังสินค้าที่เลือก")
    else:
        st.title("ERP Stock Count")
        st.write("Please login to continue")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user_role = check_credentials(username, password)
            if user_role:
                st.session_state.authenticated = True
                st.session_state.user_role = user_role
                st.session_state.enter_by = username
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

if __name__ == "__main__":
    main()
