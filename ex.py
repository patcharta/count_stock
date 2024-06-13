import streamlit as st
from datetime import datetime
import time
import pytz
import requests
from bs4 import BeautifulSoup
import re
import pyodbc
import pandas as pd
import cv2
from pyzbar.pyzbar import decode
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoTransformerBase

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
            total_balance = filtered_items_df['INSTOCK'].sum()

        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            st.write("กรุณากรอกข้อมูลสินค้า")
            with st.form(key="product_count_form"):
                st.session_state.product_id = st.text_input("รหัสสินค้า", value=filtered_items_df['ITMID'].iloc[0] if not filtered_items_df.empty else "")
                st.session_state.product_name = st.text_input("ชื่อสินค้า", value=filtered_items_df['NAME_TH'].iloc[0] if not filtered_items_df.empty else "")
                st.session_state.product_model = st.text_input("รุ่น", value=filtered_items_df['MODEL'].iloc[0] if not filtered_items_df.empty else "")
                st.session_state.purchasing_uom = st.text_input("หน่วยนับ", value=filtered_items_df['PURCHASING_UOM'].iloc[0] if not filtered_items_df.empty else "")
                st.session_state.total_balance = st.number_input("ยอดคงเหลือในสต็อก", value=total_balance, format="%d")
                st.session_state.quantity = st.number_input("กรอกจำนวน", min_value=0, step=1, format="%d")
                st.session_state.condition = st.selectbox("Condition", ["Good", "Damaged", "Expired"])
                st.session_state.status = st.selectbox("Status", ["Available", "Unavailable"])
                st.session_state.remark = st.text_area("หมายเหตุ")
                submit_button = st.form_submit_button(label="บันทึกข้อมูล")

                if submit_button:
                    product_data = {
                        'Time': datetime.now(pytz.timezone('Asia/Bangkok')).strftime("%Y-%m-%d %H:%M:%S"),
                        'Enter_By': st.session_state.username,
                        'Product_ID': st.session_state.product_id,
                        'Product_Name': st.session_state.product_name,
                        'Model': st.session_state.product_model,
                        'Purchasing_UOM': st.session_state.purchasing_uom,
                        'Total_Balance': st.session_state.total_balance,
                        'Quantity': st.session_state.quantity,
                        'Remark': st.session_state.remark,
                        'Condition': st.session_state.condition,
                        'Status': st.session_state.status,
                        'whcid': st.session_state.selected_whcid
                    }
                    save_to_database(product_data, conn_str)

        with col2:
            product_image_url = get_image_url(st.session_state.product_name)
            if product_image_url:
                st.image(product_image_url, caption="Product Image", use_column_width=True)
            else:
                st.write("ไม่พบรูปภาพของสินค้า")

    else:
        st.write("ไม่พบข้อมูลสินค้าที่คุณเลือก")

def login():
    st.title("ระบบเช็คสต็อกสินค้า")
    st.write("กรุณาเข้าสู่ระบบเพื่อใช้งาน")

    with st.form(key="login_form"):
        username = st.text_input("ชื่อผู้ใช้")
        password = st.text_input("รหัสผ่าน", type="password")
        company = st.selectbox("เลือกบริษัท", ['K.G. Corporation Co.,Ltd.', 'The Chill Resort & Spa Co., Ltd.'])
        login_button = st.form_submit_button(label="เข้าสู่ระบบ")

        if login_button:
            user_role = check_credentials(username, password)
            if user_role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.company = company
                st.session_state.user_role = user_role
            else:
                st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

# Barcode Scanner functionality
class VideoTransformer(VideoTransformerBase):
    def __init__(self):
        self.barcode = None

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        for barcode in decode(img):
            self.barcode = barcode.data.decode('utf-8')
            pts = barcode.polygon
            if len(pts) == 4:
                pts = pts.reshape((4, 2))
                pts = pts.astype(int)
                cv2.polylines(img, [pts], True, (0, 255, 0), 3)
            rect = barcode.rect
            cv2.putText(img, self.barcode, (rect.left, rect.top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return img

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    company = st.session_state.company
    conn_str = get_connection_string(company)

    st.sidebar.header("เมนู")
    menu_options = ["หน้าแรก", "เลือกสินค้า", "ค้นหาสินค้า", "นับสินค้า", "บันทึกสินค้า", "บันทึกข้อมูลสินค้า"]
    selected_menu = st.sidebar.selectbox("เลือกเมนู", menu_options)

    if selected_menu == "เลือกสินค้า":
        product_name, selected_item = select_product(company)
        if product_name:
            st.session_state.selected_product_name = product_name
            st.session_state.selected_item = selected_item

    if selected_menu == "ค้นหาสินค้า":
        st.write("สแกนบาร์โค้ดสินค้า")
        ctx = webrtc_streamer(key="example", mode=WebRtcMode.SENDRECV, video_transformer_factory=VideoTransformer)
        if ctx.video_transformer:
            barcode = ctx.video_transformer.barcode
            if barcode:
                st.write(f"พบข้อมูลบาร์โค้ด: {barcode}")

    if selected_menu == "นับสินค้า" and 'selected_product_name' in st.session_state:
        count_product(st.session_state.selected_product_name, st.session_state.selected_item, conn_str)
    elif selected_menu == "นับสินค้า":
        st.write("กรุณาเลือกสินค้าก่อน")

    if selected_menu == "บันทึกสินค้า":
        st.write("เลือกคลังสินค้า")
        whcid_query = '''
        SELECT WHCID, NAME_TH FROM ERP_WAREHOUSES_CODE
        '''
        with pyodbc.connect(conn_str) as conn:
            whcid_df = pd.read_sql(whcid_query, conn)
        st.session_state.selected_whcid = st.selectbox("เลือกคลังสินค้า", options=whcid_df['WHCID'] + ' - ' + whcid_df['NAME_TH'])

    if selected_menu == "บันทึกข้อมูลสินค้า" and 'selected_whcid' in st.session_state:
        if 'selected_product_name' in st.session_state:
            count_product(st.session_state.selected_product_name, st.session_state.selected_item, conn_str)
        else:
            st.write("กรุณาเลือกสินค้าก่อน")
else:
    login()
    
if __name__ == "__main__":
    app()
