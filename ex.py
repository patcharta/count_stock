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

def select_product(company):
    st.write("เลือกวิธีค้นหาสินค้า:")
    search_method = st.radio("", ["QR เพื่อค้นหา", "พิมพ์เพื่อค้นหา"])

    if search_method == "QR เพื่อค้นหา":
        return select_product_by_qr(company)
    elif search_method == "พิมพ์เพื่อค้นหา":
        return select_product_by_text(company)
    else:
        return None, None

def select_product_by_text(company):
    st.write("ค้นหาสินค้า 🔎")
    items_df = fetch_products(company)
    items_options = list(items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'])

    selected_product_name = st.selectbox("พิมพ์เพื่อค้นหาใน:", options=items_options, index=None, key='selected_product')

    if selected_product_name:
        selected_item = items_df[items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'] == selected_product_name]
        #st.write(f"คุณเลือกสินค้า **{selected_product_name}**")
        #st.markdown(f'คุณเลือกสินค้า: **<span style="background-color: #ffa726; padding: 2px 5px; border-radius: 5px; color: black;">{selected_product_name}</span>**', unsafe_allow_html=True)       
        st.markdown(f'คุณเลือกสินค้า: <strong style="background-color: #ffa726; padding: 2px 5px; border-radius: 5px; color: black;">{selected_product_name}</strong>', unsafe_allow_html=True)
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

    # Assuming the rest of your logic follows

    # Handle form submission
    if st.form_submit_button('👉 Enter'):
        if status is None or condition is None:
            st.error("กรุณาเลือก 'สถานะ' และ 'สภาพสินค้า' ก่อนบันทึกข้อมูล")
        elif status == "ผสม" and not remark.strip():
            st.error("กรุณาใส่ 'หมายเหตุ' เมื่อเลือกสถานะ 'ผสม'")
        else:
            try:
                product_quantity = int(product_quantity_str)
                if product_quantity < 0:
                    st.error("กรุณากรอกจำนวนสินค้าที่มากกว่า 0")
                else:
                    timezone = pytz.timezone('Asia/Bangkok')
                    current_time = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
                    product_data = {
                        'Time': current_time,
                        'Enter_By': st.session_state.username.upper(),
                        'Product_ID': str(filtered_items_df['ITMID'].iloc[0] if not filtered_items_df.empty else selected_item['ITMID'].iloc[0]),
                        # Populate other fields accordingly
                    }
                    # Print out product_data for debugging
                    print(product_data)
                    # Save to database
                    save_to_database(product_data, conn_str)
                    # Clear session state or reset necessary values
                    st.session_state.product_data = []
                    st.session_state.product_quantity = 0
                    st.session_state.remark = ""
                    time.sleep(2)
                    if 'selected_product' in st.session_state:
                        del st.session_state['selected_product']
                    if 'qr_code_scanner' in st.session_state:
                        del st.session_state['qr_code_scanner']
                    # Rerun the app to reflect changes
                    st.experimental_rerun()
            except ValueError:
                st.error("กรุณากรอกจำนวนสินค้าที่ถูกต้อง")


def select_product_by_qr(company):
    st.write("ค้นหาสินค้า 🔍")
    items_df = fetch_products(company)
    
    qr_code = qrcode_scanner(key="qr_code_scanner")
    if qr_code:
        st.write(f"QR Code detected: {qr_code}")
        if st.button("ยืนยันการเลือกสินค้าจาก QR Code"):
            selected_product = items_df[items_df['ITMID'] == qr_code]
            if not selected_product.empty:
                selected_product_name = selected_product.iloc[0]['ITMID'] + ' - ' + selected_product.iloc[0]['NAME_TH'] + ' - ' + selected_product.iloc[0]['MODEL'] + ' - ' + selected_product.iloc[0]['BRAND_NAME']
                st.markdown(f'คุณเลือกสินค้า: <strong style="background-color: #ffa726; padding: 2px 5px; border-radius: 5px; color: black;">{selected_product_name}</strong>', unsafe_allow_html=True)
                st.markdown("---")
                return selected_product_name, selected_product

    return None, None
                
def login_section():
    st.write("## Login 🚚")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    company_options = ['K.G. Corporation Co.,Ltd.', 'The Chill Resort & Spa Co., Ltd.']
    company = st.selectbox("Company", options=company_options)
    if st.button(" 📥 Login"):
        # Set the selected company to the session state
        st.session_state.company = company
        # Get the connection string based on the selected company
        conn_str = get_connection_string(company)
        user_role = check_credentials(username, password)
        if user_role:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_role = user_role
            st.success(f"🎉🎉 Welcome {username}")
            time.sleep(1)
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

def main_section():
    st.write(f"👨🏻‍💼👩🏻‍💼 รายการสินค้าที่ {st.session_state.username.upper()} นับ")
    st.write(f"🏭🏭 {st.session_state.company}")

    if st.session_state.selected_whcid is None:
        st.write("เลือก WHCID")
        conn_str = get_connection_string(st.session_state.company)
        try:
            with pyodbc.connect(conn_str) as conn:
                whcid_query = '''
                SELECT y.WHCID, y.NAME_TH
                FROM ERP_WAREHOUSES_CODE y
                WHERE y.EDITDATE IS NULL
                '''
                whcid_df = pd.read_sql(whcid_query, conn)
                selected_whcid = st.selectbox("เลือก WHCID:", options=whcid_df['WHCID'] + ' - ' + whcid_df['NAME_TH'])
                if st.button("👉 Enter WHCID"):
                    st.session_state.selected_whcid = selected_whcid
                    st.experimental_rerun()
        except pyodbc.Error as e:
            st.error(f"Error connecting to the database: {e}")
    else:
        st.write(f"คุณเลือก WHCID: {st.session_state.selected_whcid}")
        st.markdown("---")
        selected_product_name, selected_item = select_product(st.session_state.company)
        if selected_product_name:
            conn_str = get_connection_string(st.session_state.company)
            count_product(selected_product_name, selected_item, conn_str)
        if st.button('📤 Logout'):
            st.session_state.logged_in = False
            st.session_state.username = ''
            st.session_state.selected_whcid = None
            st.session_state.selected_product_name = None
            st.session_state.product_data = []
            st.session_state.product_quantity = 0
            st.session_state.remark = ""
            st.experimental_rerun()

def app():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ''
        st.session_state.selected_whcid = None
        st.session_state.selected_product_name = None
        st.session_state.product_data = []
        st.session_state.product_quantity = 0
        st.session_state.remark = ""

    if st.session_state.logged_in:
        main_section()
    else:
        login_section()

if __name__ == "__main__":
    app()
