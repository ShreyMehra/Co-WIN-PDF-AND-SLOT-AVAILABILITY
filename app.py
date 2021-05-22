import datetime
import json
import numpy as np
import requests
import pandas as pd
import streamlit as st
from copy import deepcopy
import base64
import copy
from collections import Counter
from inputimeout import inputimeout, TimeoutOccurred
import tabulate, copy, time, datetime, requests, sys, os, random
from hashlib import sha256
beneficiaries = 'https://cdn-api.co-vin.in/api/v2/appointment/beneficiaries'
OTP_PUBLIC_URL = 'https://cdn-api.co-vin.in/api/v2/auth/public/generateOTP'
OTP_PRO_URL = 'https://cdn-api.co-vin.in/api/v2/auth/generateMobileOTP'
OTP_VERIFY = 'https://cdn-api.co-vin.in/api/v2/auth/validateMobileOtp'
PDF = "https://cdn-api.co-vin.in/api/v2/registration/certificate/download?beneficiary_reference_id={0}"

rename_mapping = {
    'date': 'Date',
    'min_age_limit': 'Minimum Age Limit',
    'available_capacity_dose1': 'Available Capacity Dose1',
    'available_capacity_dose2': 'Available Capacity Dose2',
    'vaccine': 'Vaccine',
    'pincode': 'Pincode',
    'name': 'Hospital Name',
    'state_name' : 'State',
    'district_name' : 'District',
    'block_name': 'Block Name',
    'fee_type' : 'Fees'
    }


browser_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

@st.cache(allow_output_mutation=True, suppress_st_warning=True, ttl = 300,max_entries=1)
def send_otp(mobile,request_header):
    if not mobile:
        print("Mobile can't be empty")
    data = {
        "mobile":mobile,
        "secret": "U2FsdGVkX1+z/4Nr9nta+2DrVJSv7KS6VoQUSQ1ZXYDx/CJUkWxFYG6P3iM/VW+6jLQ9RDQVzp/RcZ8kbT41xw=="
    }
    txnID = requests.post(url = OTP_PRO_URL,json = data,headers = request_header)
    if txnID.status_code == 200:
        print("Successfully sent the OTP")
        txnID = txnID.json()['txnId']
        valid_token = True
        return txnID
    else:
        print("Unable to generate OTP")
        print(txnID.status_code,txnID.text)
        retry = input("Retry with {mobile} or no")
        retry = retry if retry else 'y'
        if (retry == 'y'):
            pass
        else:
            sys.exit()

@st.cache(allow_output_mutation=True, suppress_st_warning=True, ttl = 300,max_entries=1)
def verify_otp(OTP,request_header,txnID):
    if not OTP:
        print("OTP can't be empty")
    data = {
                "otp": sha256(str(OTP).encode('utf-8')).hexdigest(),
                "txnId": txnID
    }
    token = requests.post(url = OTP_VERIFY, json = data, headers = request_header)
    if token.status_code == 200:
        print("OTP Verified")
        token = token.json()['token']
        print('token generated')
        return token
    elif token.status_code == 400:
        st.write("OTP has expired,enter on phone number")
    else:
        print("Unable to verify token")
        print(token.status_code)
        print(token.text)
        retry = st.text_input("Retry with {mobile} or no",10)
        retry = retry if retry else 'y'
        if (retry == 'y'):
            OTP = st.text_input("OTP")
        else:
            sys.exit()

@st.cache(allow_output_mutation=True, suppress_st_warning=True, ttl = 300,max_entries=1)
def fetch_pdf(request_header,bref_id):
    resp = requests.get(url=PDF.format(bref_id), headers=request_header)

    print(resp.status_code)
    print(resp)
    from pathlib import Path
    import webbrowser
    filename = Path('certificate.pdf')
    filename.write_bytes(resp.content)
    base64_pdf = resp.content
    base64_pdf = base64.b64encode(resp.content).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="1370" height="1024" type="application/pdf">'
    return pdf_display

@st.cache(allow_output_mutation=True, suppress_st_warning=True, ttl = 300,max_entries=1)
def fetch_details(request_header):
    resp = requests.get(url = beneficiaries,headers = request_header)
    print(resp.status_code)
    print(resp.content)
    resp_json = resp.json()
    name = []
    dict_bref = dict()
    for beneficiary in resp_json['beneficiaries']:
        name.append(beneficiary['name'])
        print(beneficiary['name'])
        dict_bref[beneficiary['name']] = beneficiary['beneficiary_reference_id']
    return name,dict_bref


base_request_header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        }

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_state_mapping():
    URL = "https://cdn-api.co-vin.in/api/v2/admin/location/states"
    response = requests.get(URL,headers=browser_header)
    print(response)
    state_df = json.loads(response.text)["states"]
    state_df = pd.DataFrame(state_df)
    state_dict = pd.Series(state_df["state_id"].values,
                         index = state_df["state_name"].values).to_dict()
    mapping_state_dict = pd.Series(state_df["state_id"].values,
                         index = state_df["state_name"].values).to_dict()
    print(state_dict)
    unique_state = list(state_df["state_name"].unique())
    unique_state.sort()
    print(unique_state)
    return state_df, mapping_state_dict,unique_state

def load_district_mapping(state_id):
    URL = "https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}".format(state_id)
    print(selected_state,state_id)
    response = requests.get(URL, headers=browser_header)
    district_df = json.loads(response.text)["districts"]
    district_df = pd.DataFrame(district_df)
    mapping_district_dict = pd.Series(district_df["district_id"].values,
                         index = district_df["district_name"].values).to_dict()
    print(mapping_district_dict)
    unique_districts = list(district_df["district_name"].unique())
    unique_districts.sort()
    print(unique_districts)
    return district_df,mapping_district_dict,unique_districts

def filter_col(df, col, value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp

def filter_capacity(df, col, value):
    df_temp = deepcopy(df.loc[df[col] > value, :])
    return df_temp

def gather_data(numdays,DorP,type):
    base = datetime.datetime.today()
    date_list = [base + datetime.timedelta(days=x) for x in range(numdays)]
    date_str = [x.strftime("%d-%m-%Y") for x in date_list]

    final_df = None
    for INP_DATE in date_str:
        if type == "district":
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(DorP, INP_DATE)
        elif type == "pincode":
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={}&date={}".format(DorP, INP_DATE)
        response = requests.get(URL, headers=browser_header)
        print(response.content)
        if (response.ok) and ('centers' in json.loads(response.text)):
            resp_json = json.loads(response.text)['centers']
            if resp_json is not None:
                df = pd.DataFrame(resp_json)
                if len(df):
                    df = df.explode("sessions")
                    df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
                    df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
                    df['available_capacity_dose1'] = df.sessions.apply(lambda x: x['available_capacity_dose1'])
                    df['available_capacity_dose2'] = df.sessions.apply(lambda x: x['available_capacity_dose2'])
                    df['date'] = df.sessions.apply(lambda x: x['date'])
                    df = df[["date", "available_capacity_dose1","available_capacity_dose2", "vaccine", "min_age_limit", "pincode", "name", "state_name", "district_name", "block_name", "fee_type"]]
                    if final_df is not None:
                        final_df = pd.concat([final_df, df])
                    else:
                        final_df = deepcopy(df)
                else:
                    st.error("No rows in the data Extracted from the API")
        else:
            st.error("Invalid response")
    
    if (final_df is not None) and (len(final_df)):
        final_df.drop_duplicates(inplace=True)
        final_df.rename(columns=rename_mapping, inplace=True)
        left_col3 , lcenter_col3, rcenter_col3, right_col3 = st.beta_columns(4) 
    
        with left_col3:
            choices2 = [18, 45]
            age = st.selectbox('Select Minimum Age', [""] + choices2)
            if age != "":
                final_df = filter_col(final_df, "Minimum Age Limit", age)

        with lcenter_col3:
            choices3 = ["Free","Paid"]
            fees = st.selectbox("Payment",[""]+choices3)
            if fees != "":
                final_df = filter_col(final_df,"Fees",fees)
        with rcenter_col3:
            choices4 = ["COVISHIELD","COVAXIN","SPUTN"]
            type_of_vaccine = st.selectbox("Type of Vaccine",[""]+choices4)
            if type_of_vaccine != "":
                final_df = filter_col(final_df,"Vaccine",type_of_vaccine)
        with right_col3:
            choices5 = ['Available']
            capacity = st.selectbox("Avaiablility",[""]+choices5)
            if capacity != "":
                final_df = filter_capacity(final_df,"Available Capacity",0)

    
        table = deepcopy(final_df)
        table.reset_index(drop = True,inplace = True)

        print(table)
        st.table(table)

    else:
        st.error("Unable to fetch data currently, please try after sometime")
    
    

st.title("CoWIN Vaccine Appointment")
st.info("This uses CoWIN API's provided by _Govt of India_, due to some crawlers it may not work properly as Govt had just released some guidelines to use these APIs")
st.markdown("Also, This is all ethical I am doing, just for educational purposes, _*just to clarify*_")


choices = ["Find Appointment Slot","Fetch PDF"]
option_select = st.radio("Select want you want",choices)
print(option_select)
if option_select     == "Find Appointment Slot":
    choices1 = ["Using Pin","Using District"]
    option_selected = st.radio("Check your nearest vaccination center and slots availability",choices1)
    
    if option_selected == "Using Pin":
        left_col1 ,right_col1 = st.beta_columns(2)
        with left_col1:
            numdays = st.slider('Select Date Range', 1, 7, 2)
        with right_col1:
            pincode = st.text_input("Enter your Pincode",key=2)
        if len(str(pincode))!=int(6):
            print("yes")
            st.write("Please enter Correct Pincode")
        else:
            gather_data(numdays,pincode,"pincode")
    
    else:
        mapping_state_df, mapping_state_dict, unique_states = load_state_mapping()
        left_col2, center_col2 , right_col2 = st.beta_columns(3)
        with left_col2:
            numdays = st.slider('Select Date Range', 1, 7, 2)
        with center_col2:
            selected_state = st.selectbox("Select State",unique_states)
        state_id = mapping_state_dict.get(selected_state)
        mapping_district_df, mapping_district_dict, unique_districts = load_district_mapping(state_id)
        with right_col2:
            selected_district = st.selectbox("Select District",unique_districts)
        district_id = mapping_district_dict.get(selected_district)    
        gather_data(numdays,district_id,"district")

elif option_select == "Fetch PDF":
    mobile = st.text_input(label = "Phone Number",key="1")

    if len(mobile)!=0 :
        
        txnID = send_otp(mobile,base_request_header)    
        print(txnID)
        OTP = st.text_input(label = "OTP",key = "2")
            
        if len(OTP)!=0:
            n = ""
            print(n)
            if n == "":
                token = verify_otp(OTP,base_request_header,txnID)
                n += "1"
                print(token)
                
                request_header = copy.deepcopy(base_request_header)
                request_header["Authorization"] = f"Bearer {token}"
                print(request_header)
                choices2,dict_bref = fetch_details(request_header)
                print(dict_bref)
                option_selected_2 = st.radio("Select the Name whom to fetch PDF",choices2)
                pdf = fetch_pdf(request_header,dict_bref[option_selected_2])
                st.markdown(pdf, unsafe_allow_html=True)
                
