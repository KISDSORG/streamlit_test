import streamlit as st
import warnings
import pandas as pd
import json
import pickle
import requests
from bs4 import BeautifulSoup
import zipfile
from io import BytesIO
import xmltodict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

warnings.filterwarnings('ignore')
API_KEY = 'd7d1be298b9cac1558eab570011f2bb40e2a6825'
headers= {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
          'Accept-Encoding': '*', 'Connection': 'keep-alive'}
options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--headless')

@st.experimental_singleton
def get_driver():
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 고유번호-회사명 매칭 리스트
def get_corp_dict():
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    response = requests.get(url, params={'crtfc_key': API_KEY}, verify=False)
    zf = zipfile.ZipFile(BytesIO(response.content))
    file = zf.read('CORPCODE.xml').decode('utf-8')
    data_odict = xmltodict.parse(file)
    data_dict = json.loads(json.dumps(data_odict))
    data = data_dict.get('result', {}).get('list')
    corp_dict = {}
    for i in range(len(data)):
        corp_dict[data[i]['corp_name']] = data[i]['corp_code']
        # corp_nm_list.append(data[i]['corp_name'])
    return corp_dict

# 보고서명, 일자로 검색해서 보고서접수번호 추출(최대 호출 가능기간: 3개월)
def get_rcept_no(report_nm, bgn_de, end_de):
    rcept_no_list = []
    # bgn_de = bgn_de.strftime('%Y%m%d')
    # end_de = end_de.strftime('%Y%m%d')
    url = 'https://opendart.fss.or.kr/api/list.xml'
    params = {'crtfc_key': API_KEY
        , 'bgn_de': bgn_de
        , 'end_de': end_de
        , 'pblntf_detail_ty': 'B001'
        , 'last_reprt_at': 'Y'}
    try:
        response = requests.get(url, params=params, headers=headers, verify=False)
        soup = BeautifulSoup(response.content, features='html.parser')
        total_page = soup.find('total_page').get_text()

        for i in range(1, int(total_page) + 1):
            params = {'crtfc_key': API_KEY
                , 'bgn_de': bgn_de
                , 'end_de': end_de
                , 'pblntf_detail_ty': 'B001'
                , 'page_no': str(i)
                , 'last_reprt_at': 'Y'}
            response = requests.get(url, params=params, headers=headers, verify=False)
            soup = BeautifulSoup(response.content, features='html.parser')
            for c in soup.find_all('list'):
                if report_nm in c.report_nm.get_text():
                    rcept_no_list.append(c.rcept_no.get_text())
    except Exception as e:
        print(e)
        rcept_no_list = []

    print('보고서명:', report_nm, ', 보고서수: ', len(rcept_no_list))

    return rcept_no_list

# 고유번호, 보고서명, 일자로 검색해서 보고서접수번호 추출
def get_rcept_no_by_corp(corp_code, report_nm, bgn_de, end_de):
    rcept_no_list = []
    url = 'https://opendart.fss.or.kr/api/list.xml'
    params = {'crtfc_key': API_KEY
        , 'corp_code': corp_code
        , 'bgn_de': bgn_de
        , 'end_de': end_de
        , 'pblntf_detail_ty': 'B001'
        , 'last_reprt_at': 'Y'}
    try:
        response = requests.get(url, params=params, headers=headers, verify=False)
        soup = BeautifulSoup(response.content, features='html.parser')
        total_page = soup.find('total_page').get_text()

        for i in range(1, int(total_page) + 1):
            params = {'crtfc_key': API_KEY
                , 'corp_code': corp_code
                , 'bgn_de': bgn_de
                , 'end_de': end_de
                , 'pblntf_detail_ty': 'B001'
                , 'page_no': str(i)
                , 'last_reprt_at': 'Y'}
            response = requests.get(url, params=params, headers=headers, verify=False)
            soup = BeautifulSoup(response.content, features='html.parser')
            for c in soup.find_all('list'):
                if report_nm in c.report_nm.get_text():
                    rcept_no_list.append(c.rcept_no.get_text())
    except Exception as e:
        print(e)
        rcept_no_list = []

    print('보고서명:', report_nm, ', 보고서수: ', len(rcept_no_list))

    return rcept_no_list

# 주요사항보고서(메자닌채권) 호출
def get_mezn_data(knd, corp_nm, start_dt, end_dt, intr_ex_min, intr_ex_max, intr_sf_min, intr_sf_max):
    with open('./Mezzanine_new.pkl', 'rb') as f:
        df = pickle.load(f)
        df = df[df['종류'].isin(knd)]
        df['표면이자율(%)'] = df['표면이자율(%)'].str.strip()
        df['만기이자율(%)'] = df['만기이자율(%)'].str.strip()
        df.loc[df['표면이자율(%)'] == '-', '표면이자율(%)'] = -1000
        df.loc[df['만기이자율(%)'] == '-', '만기이자율(%)'] = -1000
        df = df[(((df['표면이자율(%)'].astype(float) >= intr_ex_min) & (df['표면이자율(%)'].astype(float) <= intr_ex_max)) | (
                    df['표면이자율(%)'].astype(float) == -1000))
                & (((df['만기이자율(%)'].astype(float) >= intr_sf_min) & (df['만기이자율(%)'].astype(float) <= intr_sf_max)) | (
                    df['만기이자율(%)'].astype(float) == -1000))]
        if corp_nm == '':
            df = df[(df['공시일'] >= start_dt.strftime('%Y%m%d')) & (df['공시일'] <= end_dt.strftime('%Y%m%d'))]
        else:
            df['발행사'] = df['발행사'].str.replace('주식회사', '').str.replace('(주)', '').str.replace('(', '').str.replace(')',
                                                                                                                  '').str.strip()
            df = df[(df['공시일'] >= start_dt.strftime('%Y%m%d')) & (df['공시일'] <= end_dt.strftime('%Y%m%d'))
                    & (df['발행사'] == corp_nm)]
        df.loc[df['표면이자율(%)'] == -1000, '표면이자율(%)'] = '-'
        df.loc[df['만기이자율(%)'] == -1000, '만기이자율(%)'] = '-'
    return df

# 주요사항보고서(자본으로인정되는채무증권발행결정) 호출
def get_perp_data(start_dt, end_dt, corp_code=None):
    rcept_name = '주요사항보고서(자본으로인정되는채무증권발행결정)'
    rcept_no_list = []
    start_dt = start_dt.strftime('%Y%m%d')
    end_dt = end_dt.strftime('%Y%m%d')
    if corp_code == '':
        rcept_no_list.extend(get_rcept_no(rcept_name, start_dt, end_dt))
    else:
        rcept_no_list.extend(get_rcept_no_by_corp(corp_code, rcept_name, start_dt, end_dt))
    rows = []
    for rcept in rcept_no_list:
        row = get_perp_docu(rcept)
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty == False :
        df = df.dropna(subset=['발행사'])
    return df

# 주요사항보고서(자본으로인정되는채무증권발행결정) 상세정보 추출
def get_perp_docu(rcept_no):
    url = 'https://opendart.fss.or.kr/api/document.xml'
    params = {'crtfc_key': API_KEY, 'rcept_no': rcept_no}
    response = requests.get(url, params=params, headers=headers)
    try:
        zf = zipfile.ZipFile(BytesIO(response.content))
        fp = zf.read('{}.xml'.format(rcept_no))
        try:
            xml_str = fp.decode('cp949')
            xml_str = xml_str.replace('<=', '')
            xml = xml_str.encode('cp949')
        except:
            xml_str = fp.decode('utf-8')
            xml_str = xml_str.replace('<=', '')
            xml = xml_str.encode('utf-8')

        soup = BeautifulSoup(xml, features='html.parser')
        table = soup.find('table-group', attrs={'aclass': 'CB_PUB'})
        pl_knd = table.find('te', attrs={'acode': 'PL_KND'}).get_text()  # 사채의 종류
        if '신종자본증권' in pl_knd:
            company_nm = soup.find('company-name').get_text()  # 발행사
            rcept_dt = rcept_no[:8]  # 공시일
            dnm_sum = table.find('te', attrs={'acode': 'DNM_SUM'}).get_text()  # 권면총액
            fnd_use1 = table.find('te', attrs={'acode': 'FND_USE1'}).get_text().strip()  # 시설자금
            fnd_use_sq = table.find('te', attrs={'acode': 'FND_USE_SQ'}).get_text().strip()  # 영업양수자금
            fnd_use2 = table.find('te', attrs={'acode': 'FND_USE2'}).get_text().strip()  # 운영자금
            fnd_use_rd = table.find('te', attrs={'acode': 'FND_USE_RD'}).get_text().strip()  # 채무상환자금
            anc_acq_prc = table.find('te', attrs={'acode': 'ANC_ACQ_PRC'}).get_text().strip()  # 타법인증권취득자금
            fnd_use3 = table.find('te', attrs={'acode': 'FND_USE3'}).get_text().strip()  # 기타자금
            fnd = '' + (("시설자금(원): " + fnd_use1 + "\n") if fnd_use1 != '-' else '') \
                  + (("영업양수자금(원): " + fnd_use_sq + "\n") if fnd_use_sq != '-' else '') \
                  + (("운영자금(원): " + fnd_use2 + "\n") if fnd_use2 != '-' else '') \
                  + (("채무상환자금(원): " + fnd_use_rd + "\n") if fnd_use_rd != '-' else '') \
                  + (("타법인증권취득자금(원): " + anc_acq_prc + "\n") if anc_acq_prc != '-' else '') \
                  + (("기타자금(원): " + fnd_use3 + "\n") if fnd_use3 != '-' else '')
            exp_dt = table.find('tu', attrs={'aunit': 'EXP_DT'}).get_text()  # 사채만기일
            exp_dt = '' if exp_dt == '-' else exp_dt
            exp_dt_dur = table.find('te', attrs={'acode': 'EXP_DT_DUR'}).get_text()  # 사채만기기간
            int_gv_mth = table.find('te', attrs={'acode': 'INT_GV_MTH'}).get_text().replace('\n', '').replace('-', '')  # 이자지급방법
            int_stp = table.find('te', attrs={'acode': 'INT_STP'}).get_text().replace('\n', '').replace('-', '')  # 이자지급 정지(유예) 가능여부 및 조건
            int_stp_acm = table.find('te', attrs={'acode': 'INT_STP_ACM'}).get_text().replace('\n', '').replace('-', '')  # 유예이자 누적 여부
            int_st_up = table.find('te', attrs={'acode': 'INT_ST_UP'}).get_text().replace('\n',
                                                                                          '').replace('-', '')  # 금리상향조정 등 이자율 조정 조건
            rtn_mth = table.find('te', attrs={'acode': 'RTN_MTH'}).get_text().replace('\n', '').replace('-', '')  # 원금 만기상환방법
            erl_rtn_mth = table.find('te', attrs={'acode': 'ERL_RTN_MTH'}).get_text().replace('\n',
                                                                                              '').replace('-', '')  # 원금 조기상환 가능시점 및 조건
            exp_rnw_mth = table.find('te', attrs={'acode': 'EXP_RNW_MTH'}).get_text().replace('\n',
                                                                                              '').replace('-', '')  # 원금 상환 만기연장 조건 및 방법
            opt_fct = table.find('te', attrs={'acode': 'OPT_FCT'}).get_text().replace('\n', '').replace('-', '')  # 옵션에 관한 사항
            chf_agn = table.find('te', attrs={'acode': 'CHF_AGN'}).get_text()  # 대표주관회사
            issu_table_group = soup.find('table-group', attrs={'aclass': 'CRP_ISSU'})  # 인수인(특정인에 대한 대상자별 사채발행내역)
            issu_table = issu_table_group.find('table', attrs={'aclass': 'EXTRACTION'})
            issu_nms = issu_table.tbody.find_all('tr')
            issu_nm = ""
            for i in issu_nms:
                issu_temp = i.find('te', attrs={'acode': "ISSU_NM"}).get_text()
                if issu_temp != '-':
                    issu_nm = issu_nm + issu_temp + ","
            issu_nm = issu_nm[:-1]

            row = {'발행사': company_nm, '종류': pl_knd, '공시일': rcept_dt, '권면총액': dnm_sum, '자금조달의 목적': fnd, '사채만기일(기간)': exp_dt + "(" + exp_dt_dur + ")",
                   '이자지급방법': int_gv_mth, '이자지급 정지(유예) 가능여부 및 조건': int_stp, '유예이자 누적여부': int_stp_acm, '이자율 조정 조건': int_st_up,
                   '원금 만기상환방법': rtn_mth, '원금 조기상환 조건': erl_rtn_mth, '원금 만기연장 조건 및 방법': exp_rnw_mth,
                   '옵션': opt_fct, '대표주관회사': chf_agn, '인수인': issu_nm}
        else:
            row = {}
            pass

    except Exception as e:
        print(rcept_no + " Error!")
        print(e)

    return row

# 주요사항보고서(유상증자결정) 호출
def get_cps_data(start_dt, end_dt, corp_code=None):
    rcept_name = '주요사항보고서(유상증자결정)'
    rcept_no_list = []
    start_dt = start_dt.strftime('%Y%m%d')
    end_dt = end_dt.strftime('%Y%m%d')
    if corp_code == '':
        rcept_no_list.extend(get_rcept_no(rcept_name, start_dt, end_dt))
    else:
        rcept_no_list.extend(get_rcept_no_by_corp(corp_code, rcept_name, start_dt, end_dt))
    rows = []
    for rcept in rcept_no_list:
        row = get_cps_docu(rcept)
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty == False :
        df = df.dropna(subset=['발행사'])
    return df

# 주요사항보고서(유상증자결정) 상세정보 추출
def get_cps_docu(rcept_no):
    print("보고서 번호:", rcept_no)
    driver = get_driver()
    url = 'https://dart.fss.or.kr/dsaf001/main.do?rcpNo=' + rcept_no
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    company_nm = soup.select('body > div.wrapper > div > div.header > div.top > div.nameWrap > span:nth-child(2)')[
        0].get_text()
    iframe_src = driver.find_element(by=By.XPATH, value='//*[@id="ifrm"]').get_attribute("src")
    response = requests.get(iframe_src, headers=headers)
    soup = BeautifulSoup(response.content, features='html.parser')

    nstk_estk = soup.select('td:-soup-contains("기타주식 (주)")')  # 기타주식(주) 위치 찾기
    if not nstk_estk:
        row = {}
    else:
        nstk_estk_cnt = nstk_estk[0].next_sibling.next_sibling.get_text()  # 신주의 종류와 수

        if nstk_estk_cnt.strip() in ('-', 0) :
            row = {}
        else:
            rcept_dt = rcept_no[:8]
            tbody1 = nstk_estk[0].parent.parent
            fv_ps = tbody1.select('tr:nth-child(3) > td:nth-child(2)')[0].get_text()  # 1주당 액면가액
            ic_mthn = soup.select('td:-soup-contains("증자방식")')[0].next_sibling.next_sibling.get_text() # 증자방식
            try:
                vtr_info = soup.select('td:-soup-contains("의결권에 관한 사항")')[0].next_sibling.next_sibling.get_text()
                dvd_info = soup.select('td:-soup-contains("이익배당에 관한 사항")')[0].next_sibling.next_sibling.get_text()
            except:
                vtr_info = '-'
                dvd_info = '-'
            pst_std_val = soup.select('td:-soup-contains("기타주식 (원)")')[0].next_sibling.next_sibling.get_text()  # 신주발행가액
            try:
                dc_rate = soup.select('td:-soup-contains("기준주가에 대한 할인율 또는 할증율")')[
                0].next_sibling.next_sibling.get_text()  # 할인율 또는 할증율
            except:
                dc_rate ='-'

            row = {'발행사': company_nm, '공시일': rcept_dt, '신주의 종류와 수': nstk_estk_cnt, '1주당 액면가액': fv_ps, '증자방식': ic_mthn,
                   '의결권': vtr_info, '이익배당': dvd_info, '신주발행가액': pst_std_val, '할인율 또는 할증율(%)': dc_rate}
    return row

# Dataframe 변환 및 다운로드
def set_df(df, file_nm):
    df = df.reset_index(drop=True)
    df.index += 1
    st.dataframe(df)

    csv = df.to_csv().encode('utf-8-sig')
    st.download_button(
        label="Download",
        data=csv,
        file_name='{}.csv'.format(file_nm),
        mime='text/csv'
    )
