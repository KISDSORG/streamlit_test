import streamlit as st
import pandas as pd
import warnings
import pe_func

### API 관련 세팅 ###
warnings.filterwarnings(action='ignore')
API_KEY = 'd7d1be298b9cac1558eab570011f2bb40e2a6825'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
    'Accept-Encoding': '*', 'Connection': 'keep-alive'}
st.set_page_config(layout='wide')
all_yn = True

### 함수 세팅 ###
def convert_df(df):
    return df.to_csv().encode('utf-8-sig')

def get_cps_data(start_dt, end_dt, all_yn, corp_code=None):
    rcept_name = '주요사항보고서(유상증자결정)'
    rcept_no_list = []
    if all_yn:
        rcept_no_list.extend(pe_func.get_rcept_no(rcept_name, start_dt, end_dt))
    else:
        rcept_no_list.extend(pe_func.get_rcept_no_by_corp(corp_code, rcept_name, start_dt, end_dt))
    rows = []
    print(rcept_no_list)
    for rcept in rcept_no_list:
        row = pe_func.get_cps_docu(rcept)
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.dropna(subset=['발행사'])
    return df

### 화면 ###
with st.form(key='form1'):
    all_yn_box = st.checkbox('전체')
    start_dt = st.date_input('시작일')
    end_dt = st.date_input('종료일')
    form1_bt = st.form_submit_button('조회')

if form1_bt:
    if all_yn_box :
        df = get_cps_data(start_dt, end_dt, all_yn)
    else:
        all_yn = False
        corp_dict = pe_func.get_corp_dict()
        corp_nm_list = []
        for c in corp_dict:
            corp_nm_list.append(c)
        corp_nm = st.selectbox('기업명을 입력하세요', corp_nm_list)
        corp_code = corp_dict.get(corp_nm)
        df = get_cps_data(start_dt, end_dt, all_yn, corp_code)
    st.dataframe(df)
