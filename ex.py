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

    selected_product_name = st.selectbox("เลือกสินค้า", options=items_options, index=None, key='selected_product')

    if selected_product_name:
        selected_item = items_df[items_df['ITMID'] + ' - ' + items_df['NAME_TH'] + ' - ' + items_df['MODEL'] + ' - ' + items_df['BRAND_NAME'] == selected_product_name]
        st.write(f"คุณเลือกสินค้า: {selected_product_name}")
        st.markdown("---")
        return selected_product_name, selected_item
    else:
        return None, None

def select_product(company):
    st.write("## ค้นหาสินค้า")
    search_method = st.radio("เลือกรูปแบบการค้นหา", options=["พิมพ์เพื่อค้นหา 🔎", "ค้นหาจาก QR Code 🔍"], index=0, key='search_method')

    if search_method == "พิมพ์เพื่อค้นหา 🔎":
        selected_product_name, selected_item = select_product_by_text(company)
    elif search_method == "ค้นหาจาก QR Code 🔍":
        selected_product_name, selected_item = select_product_by_qr(company)
    else:
        selected_product_name, selected_item = None, None

    return selected_product_name, selected_item

def display_product_details(filtered_items_df):
    try:
        if not filtered_items_df.empty:
            product_id = filtered_items_df['ITMID'].values[0]
            product_name = filtered_items_df['NAME_TH'].values[0]
            purchasing_uom = filtered_items_df['PURCHASING_UOM'].values[0]
            model = filtered_items_df['MODEL'].values[0]
            brand_name = filtered_items_df['BRAND_NAME'].values[0]
            cab_name = filtered_items_df['CAB_NAME'].values[0]
            she_name = filtered_items_df['SHE_NAME'].values[0]
            blk_name = filtered_items_df['BLK_NAME'].values[0]
            whcid = filtered_items_df['WHCID'].values[0]
            warehouse_name = filtered_items_df['WAREHOUSE_NAME'].values[0]
            batch_no = filtered_items_df['BATCH_NO'].values[0]
            in_stock = filtered_items_df['INSTOCK'].values[0]
            return product_id, product_name, purchasing_uom, model, brand_name, cab_name, she_name, blk_name, whcid, warehouse_name, batch_no, in_stock
        else:
            st.error("No data found for the selected product in the specified warehouse.")
            return None
    except Exception as e:
        st.error(f"Error displaying product details: {e}")
        return None

def main():
    st.title("🌐 KG Data Analytics System")

    with st.sidebar:
        st.image("kg_logo.png", use_column_width=True)
        st.subheader("🔐 Login")
        st.session_state.search_method = "พิมพ์เพื่อค้นหา 🔎"
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        company = st.selectbox("เลือกบริษัท", ["K.G. Corporation Co.,Ltd.", "The Chill Resort & Spa Co., Ltd."])

    if st.button("👉 Enter"):
        user_role = check_credentials(username, password)
        if user_role:
            st.session_state.search_method = "พิมพ์เพื่อค้นหา 🔎"
            st.session_state.logged_in = True
        else:
            st.error("Invalid username or password.")

    if st.session_state.get('logged_in'):
        st.subheader("Welcome to KG Data Analytics System")

        selected_product_name, selected_item = select_product(company)

        if selected_product_name:
            with st.expander("🔍 View product details"):
                st.write(f"### Selected product: {selected_product_name}")
                filtered_items_df = load_data(selected_product_name, company, conn_str)
                product_details = display_product_details(filtered_items_df)

            if product_details:
                with st.form(key='product_data_form'):
                    product_id, product_name, purchasing_uom, model, brand_name, cab_name, she_name, blk_name, whcid, warehouse_name, batch_no, in_stock = product_details

                    st.write("### Product Information")
                    st.write(f"**Product ID:** {product_id}")
                    st.write(f"**Product Name:** {product_name}")
                    st.write(f"**Purchasing UOM:** {purchasing_uom}")
                    st.write(f"**Model:** {model}")
                    st.write(f"**Brand Name:** {brand_name}")
                    st.write(f"**Cabinet:** {cab_name}")
                    st.write(f"**Shelf:** {she_name}")
                    st.write(f"**Block:** {blk_name}")
                    st.write(f"**Warehouse ID:** {whcid}")
                    st.write(f"**Warehouse Name:** {warehouse_name}")
                    st.write(f"**Batch No.:** {batch_no}")
                    st.write(f"**In Stock:** {in_stock}")

                    st.markdown("---")

                    st.write("### Update Stock Information")
                    st.number_input("Actual Quantity", min_value=0.0, step=1.0, format="%.2f", key='actual_quantity')
                    st.text_area("Remark", key='remark')

                    submit_button = st.form_submit_button("Submit")
                    if submit_button:
                        product_data = {
                            "Product_ID": product_id,
                            "Product_Name": product_name,
                            "Purchasing_UOM": purchasing_uom,
                            "Model": model,
                            "Brand_Name": brand_name,
                            "Cab_Name": cab_name,
                            "She_Name": she_name,
                            "Blk_Name": blk_name,
                            "Whcid": whcid,
                            "Warehouse_Name": warehouse_name,
                            "Batch_No": batch_no,
                            "In_Stock": in_stock,
                            "Actual_Quantity": st.session_state.actual_quantity,
                            "Remark": st.session_state.remark,
                            "Enter_By": username,
                            "Status": "Pending",
                            "Condition": "New"
                        }

                        save_to_database(product_data, conn_str)

                    st.markdown("---")

            else:
                st.warning("No product details to display.")
    else:
        st.warning("Please log in to access the system.")

if __name__ == "__main__":
    main()
