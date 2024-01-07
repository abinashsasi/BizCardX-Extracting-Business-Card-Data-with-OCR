import easyocr
import re
import mysql.connector
import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image 
from streamlit_option_menu import option_menu


mysql_connection=mysql.connector.connect(
        host="localhost", #127.0.0.1
        user="root",
        password="",
        database='bizcard'
    )
cursor=mysql_connection.cursor()
cursor.execute("create database if not exists bizcard")

cursor.execute("""
        CREATE TABLE IF NOT EXISTS business_cards (
        name VARCHAR(255),
        designation VARCHAR(255),
        company VARCHAR(255),
        email VARCHAR(255),
        website VARCHAR(255),
        primary_no VARCHAR(255),
        secondary_no VARCHAR(255),
        address TEXT,
        pincode INT,
        image LONGBLOB
    )
    """)    
mysql_connection.commit()


icon=Image.open("ocr.jpg")
st.set_page_config(page_title="BizCardX: Extracting Business Card Data with OCR | By Arshad Ayub Ahmed",
                   page_icon=icon,
                   layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={'About': """# This OCR app is created by *Arshad Ayub Ahmed*!"""})
st.markdown("<h1 style='text-align: center; color: white;'>BizCardX: Extracting Business Card Data with OCR</h1>", unsafe_allow_html=True)

# SETTING-UP BACKGROUND IMAGE

st.markdown(f""" 
<style>
    .stApp {{
        background: linear-gradient(to right, #2b5876, #4e4376);
        background-size: cover;
        transition: background 0.5s ease;
    }}
    h1,h2,h3,h4,h5,h6 {{
        color: #F3F3F3;
        font-family: 'Roboto', sans-serif;
    }}
    .stButton>button {{
        color: #4e4376;
        background-color: #f3f3f3;
        transition: all 0.3s ease-in-out;
    }}
    .stButton>button:hover {{
        color: #f3f3f3;
        background-color: #2b5876;
    }}
    .stTextInput>div>div>input {{
        color: #4e4376;
        background-color: ##FFFFFF;
    }}
</style>
""",unsafe_allow_html=True) 

reader = easyocr.Reader(['en'], gpu=False)

def extract_data(extract):

    result = ' '.join(extract)

    # pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    website_pattern = r'[www|WWW|wwW]+[\.|\s]+[a-zA-Z0-9]+[\.|\][a-zA-Z]+'
    phone_pattern = r'(?:\+)?\d{3}-\d{3}-\d{4}'
    phone_pattern2 = r"(?:\+91[-\s])?(?:\d{4,5}[-\s])?\d{3}[-\s]?\d{4}"
    name_pattern = r'[A-Za-z]+\b'
    designation_pattern = r'\b[A-Za-z\s]+\b'
    address_pattern = r'\d+\s[A-Za-z\s,]+'
    pincode_pattern = r'\b\d{6}\b'

    name = designation = company = email = website = primary = secondary = address = pincode = None

    
    # Extract email
    email_match = re.search(email_pattern, result)
    if email_match:
        email = email_match.group()
        result = result.replace(email, '')
        email = email.lower()

    # Extract website
    website_match = re.search(website_pattern, result)
    if website_match:
        website = website_match.group()
        result = result.replace(website, '')
        website = website.lower()


    # Extract phone numbers
    phone_matches = re.findall(phone_pattern + '|' + phone_pattern2, result)
    if len(phone_matches) > 0:
        primary = phone_matches[0]
        result = result.replace(primary, '')
        if len(phone_matches) > 1:
            secondary = phone_matches[1]
            result = result.replace(secondary, '')  
 

    # Extract pincode
    pincode_match = re.search(pincode_pattern, result)
    if pincode_match:
        pincode = int(pincode_match.group())
        result = result.replace(str(pincode), '')

    # Extract name and designation
    name_match = re.search(name_pattern, result)
    if name_match:
        name = name_match.group()
        result = result.replace(name, '')

    designation_match = re.search(designation_pattern, result)
    if designation_match:
        designation = designation_match.group()
        result = result.replace(designation, '')


    # Extract address and company
    address_match = re.search(address_pattern, result)
    if address_match:
        address = address_match.group()
        result = result.replace(address, '')

    company = extract[-1]


    data = [name, designation, company, email, website, primary, secondary, address, pincode, result]
    return data

reader = easyocr.Reader(['en'], gpu=False)
# CREATING OPTION MENU
choice = option_menu(None,["Home","Extract & upload","Modify and Delete"], 
                       icons=["home","cloud-upload-alt","edit"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "25px", "text-align": "centre", "margin": "0px", "--hover-color": "#AB63FA", "transition": "color 0.3s ease, background-color 0.3s ease"},
                               "icon": {"font-size": "25px"},
                               "container" : {"max-width": "6000px", "padding": "10px", "border-radius": "5px"},
                               "nav-link-selected": {"background-color": "#AB63FA", "color": "white"}})

if choice == "Home":
    #st.title("# :blue[BizCardX - Business Card Data Extraction]")
    st.markdown(
        "### :rainbow[Technologies used :]  Python, easyOCR, PostgreSQL, pandas, Streamlit.")
    st.markdown(
        "### :rainbow[About :] Bizcard is a python application designed to extract information from business cards.")
    st.write()
    st.markdown("### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the image")

elif choice == "Extract & upload":
    uploaded_file = st.file_uploader("Choose a image file",type=["jpg", "jpeg", "png"])
    if uploaded_file != None:
        image = uploaded_file.read()
        st.image(image)
    
        result = reader.readtext(image, detail=0)
        info = extract_data(result)
        st.table(pd.Series(info, index=['Name', 'Designation', 'Company', 'Email ID', 'Website', 'Primary Contact', 'Secondary Contact', 'Address', 'Pincode', 'Other'],name='extracted information'))
        a = st.button("upload to database")
        if a:
            cursor.execute("INSERT INTO business_cards (name, designation, company, email, website, primary_no, secondary_no,address, pincode, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (info[0], info[1], info[2], info[3], info[4], info[5], info[6], info[7], info[8], info[9]))
            mysql_connection.commit()
            st.success('Details stored successfully in database', icon="✅")

elif choice == 'Modify and Delete':
    col1, col2, col3 = st.columns([2,2,4])
    with col1:
        cursor.execute('select name from business_cards')
        y = cursor.fetchall()
        contact = [x[0] for x in y]
        contact.sort()
        selected_contact = st.selectbox('Name',contact)
    with col2:
        mode_list = ['','View','Modify','Delete']
        selected_mode = st.selectbox('Mode',mode_list,index = 0)

    if selected_mode == 'View':
        col5,col6 = st.columns(2)
        with col5:
            cursor.execute(f"select name, designation, company, email, website, primary_no, secondary_no,address, pincode from business_cards where name = '{selected_contact}'")
            y = cursor.fetchall()
            st.table(pd.Series(y[0],index=['Name', 'Designation', 'Company', 'Email ID', 'Website', 'Primary Contact', 'Secondary Contact', 'Address', 'Pincode'],name='Card Information'))

    elif selected_mode == 'Modify':
        cursor.execute(f"select name, designation, company, email, website, primary_no, secondary_no,address, pincode from business_cards where name = '{selected_contact}'")
        info = cursor.fetchone()
        col5, col6 = st.columns(2)
        with col5:
            names = st.text_input('Name:', info[0])
            desig = st.text_input('Designation:', info[1])
            Com = st.text_input('Company:', info[2])
            mail = st.text_input('Email ID:', info[3])
            url = st.text_input('Website:', info[4])
            phno1 = st.text_input('Primary Contact:', info[5])
            phno2 = st.text_input('Secondary Contact:', info[6])
            add = st.text_input('Address:', info[7])
            pin = st.number_input('Pincode:', info[8])
            a = st.button("Update")
            if a:
                query = f"update business_cards set name = %s, designation = %s, company = %s, email = %s, website = %s,primary_no = %s, secondary_no = %s, address = %s, pincode = %s where name = '{selected_contact}'"
                val = (names, desig, Com, mail, url, phno1, phno2, add, pin)
                cursor.execute(query, val)
                mysql_connection.commit()
                st.success('updated successfully', icon="✅")

    elif selected_mode == 'Delete':
        if st.button('Delete'):
            query = f"DELETE FROM business_cards where name = '{selected_contact}'"
            cursor.execute(query)
            mysql_connection.commit()
            st.success('removed successfully', icon="✅")

    
    