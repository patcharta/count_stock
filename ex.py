import streamlit as st
import pandas as pd

# Mock function to fetch product data (replace with actual implementation)
def fetch_products(company):
    # Simulated dataframe for demonstration
    data = {
        'ITMID': ['QR123', 'QR456'],
        'NAME_TH': ['Product A', 'Product B'],
        'MODEL': ['Model A', 'Model B'],
        'BRAND_NAME': ['Brand X', 'Brand Y']
    }
    return pd.DataFrame(data)

def select_product_by_qr(company):
    # Display a message indicating QR code scanning process
    st.write("ค้นหาสินค้า 🔍")
    
    # Fetch product data based on the company (replace with actual fetch function)
    items_df = fetch_products(company)
    
    # Trigger QR code scanner to capture QR code
    qr_code = st.text_input("กรุณาสแกน QR Code")
    
    # Check if a QR code is detected
    if qr_code:
        st.write(f"QR Code detected: {qr_code}")
        
        # Filter the product dataframe to find the selected product
        selected_product = items_df[items_df['ITMID'] == qr_code]
        
        # Check if selected_product dataframe is not empty
        if not selected_product.empty:
            # Construct the selected product name to display
            selected_product_name = f"{selected_product.iloc[0]['ITMID']} - {selected_product.iloc[0]['NAME_TH']} - {selected_product.iloc[0]['MODEL']} - {selected_product.iloc[0]['BRAND_NAME']}"
            
            # Display the selected product name with styling
            st.markdown(f'คุณเลือกสินค้า: <strong style="background-color: #ffa726; padding: 2px 5px; border-radius: 5px; color: black;">{selected_product_name}</strong>', unsafe_allow_html=True)
            st.markdown("---")
            
            # Return selected product name and details
            return selected_product_name, selected_product
    
    # Return None if no QR code detected or selected product not found
    return None, None

# Example usage
company_name = "Company X"  # Replace with actual company name
selected_product_name, selected_product = select_product_by_qr(company_name)
