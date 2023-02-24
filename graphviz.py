import streamlit as st
import pandas as pd
import openpyxl

uploaded_file = st.file_uploader("Choose a file", type='xlsx')

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file)

    st.dataframe(df)
    st.table(df)
