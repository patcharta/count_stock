import pyodbc
import pandas as pd
import streamlit as st
from datetime import datetime
import time
import pytz
import requests
from bs4 import BeautifulSoup
import re
import qrcode
from PIL import Image
import io

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

    if not filtered_items_df.empty:
        st.write("รายละเอียดสินค้า:")
        filtered_items_df['Location'] = filtered_items_df[['CAB_NAME', 'SHE_NAME', 'BLK_NAME']].apply(lambda x: ' / '.join(x.astype(str)), axis=1)
        filtered_items_df_positive_balance = filtered_items_df[filtered_items_df['INSTOCK'] > 0]
        total_balance = filtered_items_df_positive_balance['INSTOCK'].sum()
        if not filtered_items_df_positive_balance.empty:
            display_cols = ['ITMID', 'NAME_TH', 'INSTOCK', 'WAREHOUSE_NAME', 'Location', 'BATCH_NO']
            filtered_items_df_display = filtered_items_df_positive_balance[display_cols]
            filtered_items_df_display.rename(columns={
                'ITMID': 'รหัสสินค้า', 'NAME_TH': 'ชื่อสินค้า', 'INSTOCK': 'ยอดคงเหลือ', 
                'WAREHOUSE_NAME': 'โกดังสินค้า', 'Location': 'ที่ตั้ง', 'BATCH_NO': 'หมายเลขแบทช์'
            }, inplace=True)
            st.dataframe(filtered_items_df_display)
        else:
            st.write("ไม่พบสินค้าที่มีอยู่ในคลัง")
    else:
        st.write("ไม่พบรายละเอียดสินค้าสำหรับรายการที่เลือก")

    remark = st.text_area("หมายเหตุ")
    quantity = st.number_input("กรอกจำนวนที่นับได้", min_value=0, value=0)

    status_options = ["Normal", "Defective", "Expired"]
    condition_options = ["New", "Used", "Damaged"]

    status = st.selectbox("เลือกสถานะของสินค้า", status_options)
    condition = st.selectbox("เลือกสภาพของสินค้า", condition_options)

    if st.button("บันทึกข้อมูล"):
        now = datetime.now(pytz.timezone('Asia/Bangkok'))
        product_data = {
            'Enter_By': st.session_state.username,
            'Time': now,
            'Product_ID': selected_item['ITMID'].values[0],
            'Product_Name': selected_item['NAME_TH'].values[0],
            'Purchasing_UOM': selected_item['PURCHASING_UOM'].values[0],
            'Remark': remark,
            'Quantity': quantity,
            'Total_Balance': total_balance,
            'whcid': st.session_state.selected_whcid.split(' -')[0],
            'Status': status,
            'Condition': condition
        }
        save_to_database(product_data, conn_str)

def select_product_by_qr(company):
    st.write("QR Code Scanner")
    st.write("กรุณาใช้กล้องในการสแกน QR Code")

    uploaded_file = st.file_uploader("Upload an image containing a QR code", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image.format)
        img_bytes = img_byte_arr.getvalue()

        # Use an online API to decode QR code from the image
        url = "https://api.qrserver.com/v1/read-qr-code/"
        files = {'file': img_bytes}
        response = requests.post(url, files=files)
        qr_data = response.json()

        if qr_data and 'symbol' in qr_data[0] and qr_data[0]['symbol'][0]['data']:
            decoded_data = qr_data[0]['symbol'][0]['data']
            st.success(f"QR Code data: {decoded_data}")
            items_df = fetch_products(company)
            selected_item = items_df[items_df['ITMID'] == decoded_data]

            if not selected_item.empty:
                selected_product_name = f"{selected_item['ITMID'].values[0]} - {selected_item['NAME_TH'].values[0]} - {selected_item['MODEL'].values[0]} - {selected_item['BRAND_NAME'].values[0]}"
                st.markdown(f'คุณเลือกสินค้า: <strong style="background-color: #ffa726; padding: 2px 5px; border-radius: 5px; color: black;">{selected_product_name}</strong>', unsafe_allow_html=True)
                st.markdown("---")
                return selected_product_name, selected_item
            else:
                st.error("QR Code data not found in product list")
                return None, None
        else:
            st.error("Failed to decode QR Code")
            return None, None

    return None, None

def main():
    st.title("ระบบตรวจนับสินค้า 📦")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user_type = check_credentials(username, password)
        if user_type:
            st.session_state.username = username
            st.session_state.user_type = user_type
            st.success("Login successful!")
            st.write(f"Welcome, {username} ({user_type})")

            company_options = ['K.G. Corporation Co.,Ltd.', 'The Chill Resort & Spa Co., Ltd.']
            selected_company = st.selectbox("เลือกบริษัท", options=company_options)

            whcid_query = '''
            SELECT WHCID, NAME_TH FROM ERP_WAREHOUSES_CODE
            WHERE EDITDATE IS NULL
            '''
            conn_str = get_connection_string(selected_company)
            try:
                with pyodbc.connect(conn_str) as conn:
                    whcid_df = pd.read_sql(whcid_query, conn)
                    whcid_options = list(whcid_df['WHCID'] + ' - ' + whcid_df['NAME_TH'])
                    selected_whcid = st.selectbox("เลือกคลังสินค้า", options=whcid_options)
                    st.session_state.selected_whcid = selected_whcid
            except pyodbc.Error as e:
                st.error(f"Error loading warehouses: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

            if selected_company and st.session_state.selected_whcid:
                selected_product_name, selected_item = select_product(selected_company)
                if selected_product_name:
                    count_product(selected_product_name, selected_item, conn_str)
        else:
            st.error("Invalid username or password")

if __name__ == "__main__":
    main()
