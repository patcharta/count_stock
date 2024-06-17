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
        selected_product_name = items_df[items_df['ITMID'] == qr_code]
        if not selected_product_name.empty:
            selected_product_name = selected_product_name.iloc[0]['ITMID'] + ' - ' + selected_product_name.iloc[0]['NAME_TH'] + ' - ' + selected_product_name.iloc[0]['MODEL'] + ' - ' + selected_product_name.iloc[0]['BRAND_NAME']
            selected_item = items_df[items_df['ITMID'] == qr_code]
            st.write(f"คุณเลือกสินค้า: {selected_product_name}")
            st.markdown("---")
            return selected_product_name, selected_item

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
        total_balance = filtered_items_df_positive_balance['INSTOCK'].sum()

        st.table(filtered_items_df_positive_balance[['ITMID', 'NAME_TH', 'MODEL', 'BRAND_NAME', 'WAREHOUSE_NAME', 'Location', 'BATCH_NO', 'INSTOCK']])

    st.markdown("---")

    quantity = st.number_input("ใส่จำนวนสินค้า:", min_value=0, step=1, key='quantity')

    if st.button("บันทึก"):
        now = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d %H:%M:%S')
        product_data = {
            'Time': now,
            'Enter_By': st.session_state.username,
            'Product_ID': selected_item.iloc[0]['ITMID'],
            'Product_Name': selected_item.iloc[0]['NAME_TH'],
            'Purchasing_UOM': selected_item.iloc[0]['PURCHASING_UOM'],
            'Quantity': quantity,
            'Total_Balance': total_balance,
            'whcid': st.session_state.selected_whcid.split(' -')[0],
            'Status': st.selectbox("สถานะสินค้า", ["", "ปกติ", "ชำรุด", "เสื่อมสภาพ"]),
            'Condition': st.text_area("หมายเหตุ")
        }
        save_to_database(product_data, conn_str)
    st.markdown("---")

def main():
    if 'username' not in st.session_state:
        st.session_state.username = ''
        st.session_state.password = ''
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        st.sidebar.success(f"Logged in as {st.session_state.username}")
        if st.button("Log out"):
            st.session_state.username = ''
            st.session_state.password = ''
            st.session_state.logged_in = False
            st.experimental_rerun()
    else:
        st.sidebar.header("Login")
        username = st.sidebar.text_input("Username", value=st.session_state.username)
        password = st.sidebar.text_input("Password", type="password", value=st.session_state.password)
        if st.sidebar.button("Login"):
            role = check_credentials(username, password)
            if role:
                st.session_state.username = username
                st.session_state.password = password
                st.session_state.logged_in = True
                st.session_state.role = role
                st.success("Login successful!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    if st.session_state.logged_in:
        company = st.selectbox("เลือกบริษัท", ["K.G. Corporation Co.,Ltd.", "The Chill Resort & Spa Co., Ltd."])
        if company:
            conn_str = get_connection_string(company)
            warehouses = {
                'K.G. Corporation Co.,Ltd.': [
                    'KGE08 - คลังสินค้าสำเร็จรูป (พนม)', 
                    'KGE09 - คลังวัตถุดิบ (พนม)', 
                    'KGE10 - คลังสินค้าสำเร็จรูป (ไทย)',
                    'KGE11 - คลังวัตถุดิบ (ไทย)'
                ],
                'The Chill Resort & Spa Co., Ltd.': [
                    'TC101 - คลังหลัก'
                ]
            }
            st.session_state.selected_whcid = st.selectbox("เลือกคลังสินค้า", warehouses[company])

            if st.session_state.selected_whcid:
                selected_product_name, selected_item = select_product(company)
                if selected_product_name and selected_item is not None:
                    image_url = get_image_url(selected_product_name)
                    if image_url:
                        st.image(image_url, caption=selected_product_name, use_column_width=True)
                    count_product(selected_product_name, selected_item, conn_str)


if __name__ == "__main__":
    main()
