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

from dashboard_observed import render_observed
from dashboard_fatores import render_fatores
from dashboard_modelos import render_modelos
from dashboard_ruas import render_ruas_rf
import streamlit as st

st.set_page_config(layout="wide", page_title="Urban Spatial Analysis")

# Seletor no topo da sidebar
menu_modulo = st.sidebar.selectbox(
    "Select the Analysis Module:",
    ["Contributing Factors (Hexagons)", "Observed Speeds (Hexagons)", "Predictive Models (Hexagons)", "Predictive Model: Random Forest (Street)"],
)

st.sidebar.markdown("---")

if menu_modulo == "Contributing Factors (Hexagons)":
  render_fatores()
elif menu_modulo == "Observed Speeds (Hexagons)":
  render_observed()
elif menu_modulo == "Predictive Models (Hexagons)":
  render_modelos()
elif menu_modulo == "Predictive Model: Random Forest (Street)":
  render_ruas_rf() 
