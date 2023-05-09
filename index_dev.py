import streamlit as st
from streamlit_option_menu import option_menu
import warnings
from dateutil.relativedelta import relativedelta
import pe_func

### API 관련 세팅 ###
warnings.filterwarnings(action='ignore')
API_KEY = 'd7d1be298b9cac1558eab570011f2bb40e2a6825'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
    'Accept-Encoding': '*', 'Connection': 'keep-alive'}
st.set_page_config(layout='wide')

### 화면 ###
with st.sidebar:
    selected = option_menu("Menu", ["CPS/RCPS", "신종자본증권"],
                           icons=['card-list', 'bank'],
                           menu_icon='cast', default_index=0)
if selected == "CPS/RCPS":
    st.header('CPS/RCPS')
    if "disabled" not in st.session_state:
        st.session_state.disabled = True
    corp_code = ''
    st.checkbox('전체', key="disabled")

    with st.form(key='form1'):
        if st.session_state.disabled == False:
            if "corp" not in st.session_state:
                with st.spinner("기업정보 최초 로딩 시 시간이 소요됩니다😅"):
                    corp_dict = pe_func.get_corp_dict()
                st.success('기업정보 로딩 완료!', icon="🙌")
                st.session_state.corp = corp_dict
            else:
                corp_dict = st.session_state.corp
            corp_nm_list = []
            for c in corp_dict:
                corp_nm_list.append(c)
            corp_nm = st.selectbox('기업명을 입력하세요', corp_nm_list)
            corp_code = corp_dict.get(corp_nm)

        c1, c2 = st.columns(2)
        with c1:
            start_dt = st.date_input('시작일')
        with c2:
            if st.session_state.disabled == True:
                end_dt = st.date_input('종료일(시작일로부터 3개월까지 조회 가능)')
            else:
                end_dt = st.date_input('종료일')
        form1_bt = st.form_submit_button('조회')

    if form1_bt:
        if corp_code == '':
            if end_dt > start_dt + relativedelta(months=3):
                st.warning('종료일을 확인해주세요', icon="⚠️")
            else:
                with st.spinner("데이터를 수집 중입니다🤖"):
                    df = pe_func.get_cps_data(start_dt, end_dt)
                if df.empty:
                    st.info('수집할 데이터가 없습니다', icon="🤔")
                else:
                    pe_func.set_df(df, "CPS_RCPS")
        else:
            with st.spinner("데이터를 수집 중입니다🤖"):
                df = pe_func.get_cps_data(start_dt, end_dt, corp_code)
            if df.empty:
                st.info('수집할 데이터가 없습니다', icon="🤔")
            else:
                pe_func.set_df(df, "CPS_RCPS")

else:
    st.header('신종자본증권(영구채) 발행내역')
    if "disabled" not in st.session_state:
        st.session_state.disabled = True
    corp_code = ''
    st.checkbox('전체', key="disabled")

    with st.form(key='form2'):
        if st.session_state.disabled == False:
            if "corp" not in st.session_state:
                with st.spinner("기업정보 최초 로딩 시 시간이 소요됩니다😅"):
                    corp_dict = pe_func.get_corp_dict()
                st.success('기업정보 로딩 완료!', icon="🙌")
                st.session_state.corp = corp_dict
            else:
                corp_dict = st.session_state.corp
            corp_nm_list = []
            for c in corp_dict:
                corp_nm_list.append(c)
            corp_nm = st.selectbox('기업명을 입력하세요', corp_nm_list)
            corp_code = corp_dict.get(corp_nm)

        c1, c2 = st.columns(2)
        with c1:
            start_dt = st.date_input('시작일')
        with c2:
            if st.session_state.disabled == True:
                end_dt = st.date_input('종료일(시작일로부터 3개월까지 조회 가능)')
            else:
                end_dt = st.date_input('종료일')
        form2_bt = st.form_submit_button('조회')

    if form2_bt:
        if corp_code == '':
            if end_dt > start_dt + relativedelta(months=3):
                st.warning('종료일을 확인해주세요', icon="⚠️")
            else:
                with st.spinner("데이터를 수집 중입니다🤖"):
                    df = pe_func.get_perp_data(start_dt, end_dt)
                if df.empty:
                    st.info('수집할 데이터가 없습니다', icon="🤔")
                else:
                    pe_func.set_df(df, "perp_bond")
        else:
            with st.spinner("데이터를 수집 중입니다🤖"):
                df = pe_func.get_perp_data(start_dt, end_dt, corp_code)
            if df.empty:
                st.info('수집할 데이터가 없습니다', icon="🤔")
            else:
                pe_func.set_df(df, "perp_bond")
