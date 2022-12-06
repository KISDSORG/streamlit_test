import streamlit as st
import requests
import zipfile
import os
import pandas as pd
from bs4 import BeautifulSoup

api_key = 'd7d1be298b9cac1558eab570011f2bb40e2a6825'

def get_corp_info(rcept_no):
    url = 'https://opendart.fss.or.kr/api/document.xml'
    params = {'crtfc_key': api_key, 'rcept_no': rcept_no}
    response = requests.get(url, params=params)
    with open('./corp_document.zip', 'wb') as fp:
        fp.write(response.content)
    zf = zipfile.ZipFile('./corp_document.zip')
    zf.extractall('./')
    xml_path = os.path.abspath('./{}.xml'.format(rcept_no))
    fp = open(xml_path, 'r')

    soup = BeautifulSoup(fp, features='xml')
    table = soup.find('TABLE-GROUP', attrs={'ACLASS': 'TRD_RVL'})
    table_head = table.find('THEAD')
    columns = []
    for item in table_head.find_all('TH'):
        columns.append(item.string)

    table_body = table.find('TBODY')
    data = table_body.find_all('TR')
    rows = []
    for item in data[:-1]:
        no = item.find('TE', attrs={'ACODE': 'SEQ_NO2'}).get_text()
        spc_nm = item.find('TE', attrs={'ACODE': 'SPC_NM'}).get_text()
        rlt = item.find('TU', attrs={'AUNIT': 'IFR_RLT2'}).get_text()
        spc_id = item.find('TE', attrs={'ACODE': 'SPC_ID2'}).get_text()
        stk_knd = item.find('TU', attrs={'AUNIT': 'STK_KND'}).get_text()
        cnt = item.find('TE', attrs={'ACODE': 'STK_CNT'}).get_text()
        rvl = item.find('TE', attrs={'ACODE': 'TRD_RVL'}).get_text()
        trd_knd = item.find('TE', attrs={'ACODE': 'TRD_KND'}).get_text()
        trd_sin = item.find('TU', attrs={'AUNIT': 'TRD_SIN'}).get_text()
        trd_prd = item.find('TE', attrs={'ACODE': 'TRD_PRD'}).get_text()
        trd_rt = item.find('TE', attrs={'ACODE': 'TRD_RT'}).get_text()
        trd_rmk = item.find('TE', attrs={'ACODE': 'TRD_RMK'}).get_text()

        rows.append({"연번": no, "성명(명칭)": spc_nm, '보고자와의관계': rlt, '생년월일 또는사업자등록번호 등': spc_id,
                     '주식등의종류': stk_knd, '주식등의수': cnt, '계약 상대방': rvl, '계약의종류': trd_knd,
                     "계약체결(변경)일": trd_sin, "계약기간": trd_prd, "비율": trd_rt, "비고": trd_rmk})
        df = pd.DataFrame(rows, columns=columns)

    return df

def print_hi(name):
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

    st.title('st test success!')
    st.write("hello world")
    st.write("""
    # MarkDown
    > comment
    - one
    - two
    """)

    st.dataframe(get_corp_info('20211221900349'))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')