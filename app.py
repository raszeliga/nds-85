#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 16:11:38 2026

@author: rafaelszeliga
"""

# para rodar no streamlit
#### para rodar no terminal:
#### streamlit run app.py

# pip install pydeck

from dashboard_fatores import render_fatores#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 16:11:38 2026

@author: rafaelszeliga
"""

# para rodar no streamlit
#### para rodar no terminal:
#### streamlit run app.py

# pip install pydeck

from dashboard_fatores import render_fatores
from dashboard_modelos import render_modelos
from dashboard_fatais import render_fatais
import streamlit as st

st.set_page_config(layout="wide", page_title="Urban Spatial Analysis")

# Seletor no topo da sidebar
menu_modulo = st.sidebar.selectbox(
    "Select the Analysis Module:",
    ["Contributing Factors", "Predictive Models", "Fatal Accidents"],
)

st.sidebar.markdown("---")

if menu_modulo == "Contributing Factors":
  render_fatores()
elif menu_modulo == "Predictive Models":
  render_modelos()
elif menu_modulo == "Fatal Accidents":
  render_fatais() 

from dashboard_modelos import render_modelos
from dashboard_fatais import render_fatais
import streamlit as st

st.set_page_config(layout="wide", page_title="Urban Spatial Analysis")

# Seletor no topo da sidebar
menu_modulo = st.sidebar.selectbox(
    "Select the Analysis Module:",
    ["Contributing Factors", "Predictive Models", "Fatal Accidents"],
)

st.sidebar.markdown("---")

if menu_modulo == "Contributing Factors":
  render_fatores()
elif menu_modulo == "Predictive Models":
  render_modelos()
elif menu_modulo == "Fatal Accidents":
  render_fatais() 
