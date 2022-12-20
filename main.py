import streamlit as st
import requests
import zipfile
import os
import pandas as pd
from bs4 import BeautifulSoup

api_key = 'd7d1be298b9cac1558eab570011f2bb40e2a6825'
st.set_page_config(layout='wide')

def get_corp_code(corp, start, end):
    # 기업 고유번호 가져오기
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    params = {'crtfc_key': api_key}
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.content, features='lxml')
    corp_code = ''
    for c in soup.find_all('list'):
        if c.corp_name.get_text() == '삼성전자':
            corp_code = c.corp_code.get_text()
            break
        else:
            corp_code = ''

    # 보고서 번호 리스트 가져오기
    rcept_no_list = []
    url = 'https://opendart.fss.or.kr/api/list.xml'
    params = {'crtfc_key': api_key
              , 'corp_code': corp_code
              , 'bgn_de': start.strftime('%Y%m%d') #YYYYMMDD 형태로 변환 필요
              , 'end_de': end.strftime('%Y%m%d') #YYYYMMDD 형태로 변환 필요
              , 'pblntf_detail_ty': 'D001'}
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.content, features='lxml')
    rcept_no_list = []
    for c in soup.find_all('list'):
        if c.report_nm.get_text() == '주식등의대량보유상황보고서(일반)':
            rcept_no_list.append(c.rcept_no.get_text())

    df_all = pd.DataFrame()
    for r in rcept_no_list:
        df = get_corp_docu(r)
        if df.empty:
            continue
        else:
            df_all = pd.concat([df_all, df])

    df_all = df_all[df_all['성명(명칭)']!= '-']

    return df_all


def get_corp_docu(rcept_no):

    url = 'https://opendart.fss.or.kr/api/document.xml'
    params = {'crtfc_key': api_key, 'rcept_no': rcept_no}
    response = requests.get(url, params=params)
    with open('./corp_document.zip', 'wb') as fp:
        fp.write(response.content)
    try:
        zf = zipfile.ZipFile('./corp_document.zip')
        zf.extractall('./')
        xml_path = os.path.abspath('./{}.xml'.format(rcept_no))
        fp = open(xml_path, 'r', encoding='utf-8')
        soup = BeautifulSoup(fp, features='lxml')
        table = soup.find('table-group', attrs={'aclass': 'TRD_RVL'})
        table_head = table.find('thead')
        columns = []
        for item in table_head.find_all('th'):
            columns.append(item.string)

        table_body = table.find('tbody')
        data = table_body.find_all('tr')
        rows = []
        for item in data[:-1]:
            no = item.find('te', attrs={'acode': 'SEQ_NO2'}).get_text()
            spc_nm = item.find('te', attrs={'acode': 'SPC_NM'}).get_text()
            rlt = item.find('tu', attrs={'aunit': 'IFR_RLT2'}).get_text()
            spc_id = item.find('te', attrs={'acode': 'SPC_ID2'}).get_text()
            stk_knd = item.find('tu', attrs={'aunit': 'STK_KND'}).get_text()
            cnt = item.find('te', attrs={'acode': 'STK_CNT'}).get_text()
            rvl = item.find('te', attrs={'acode': 'TRD_RVL'}).get_text()
            trd_knd = item.find('te', attrs={'acode': 'TRD_KND'}).get_text()
            trd_sin = item.find('tu', attrs={'aunit': 'TRD_SIN'}).get_text()
            trd_prd = item.find('te', attrs={'acode': 'TRD_PRD'}).get_text()
            trd_rt = item.find('te', attrs={'acode': 'TRD_RT'}).get_text()
            trd_rmk = item.find('te', attrs={'acode': 'TRD_RMK'}).get_text()

            rows.append({"연번": no, "성명(명칭)": spc_nm, '보고자와의관계': rlt, '생년월일 또는사업자등록번호 등': spc_id,
                         '주식등의종류': stk_knd, '주식등의수': cnt, '계약 상대방': rvl, '계약의종류': trd_knd,
                         "계약체결(변경)일": trd_sin, "계약기간": trd_prd, "비율": trd_rt, "비고": trd_rmk})
            df = pd.DataFrame(rows, columns=columns)
    except:
        pass

    return df

def convert_df(df):
    return df.to_csv().encode('utf-8-sig')


if __name__ == '__main__':

    st.title('대주주 담보대출 현황 :money_with_wings:')
    corp = st.text_input('기업명', '삼성전자')
    start = st.date_input('시작일')
    end = st.date_input('종료일', min_value=start)

    # button 생성하기
    if st.button('조회'):
        df = get_corp_code(corp, start, end)
        st.dataframe(df)

        csv = convert_df(df)

        st.download_button(
            label="Download",
            data=csv,
            file_name='st_sample.csv',
            mime='text/csv'
        )