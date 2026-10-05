#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 10:35:53 2026

@author: rafaelszeliga
"""

# para rodar no streamlit
#### para rodar no terminal:
#### streamlit run dashboard_modelos.py

# pip install pydeck

import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components

def render_modelos():
    st.set_page_config(layout="wide", page_title="Hexagonal Network - Viewer")
    
    st.title("Speed Viewer- Comparison Mode")
    
    # Função auxiliar: converte '#RRGGBB' para [R, G, B, 255]
    def hex_to_rgba(hex_str, alpha=255):
        hex_str = hex_str.lstrip("#")
        return [int(hex_str[i:i+2], 16) for i in (0, 2, 4)] + [alpha]
    
    # 1. Carregamento dos Dados
    @st.cache_data
    def carregar_camada(caminho_gpkg):
        gdf = gpd.read_file(caminho_gpkg)
        # PyDeck e Leaflet exigem coordenadas geográficas WGS84 (EPSG:4326)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        return gdf
    
    # Caminhos dos arquivos
    caminho_hex = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/gdf_dash_modelos_v3.gpkg"
    caminho_limite = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/bairros_dissolvido.gpkg"
    
    # bairos de Curitiba
    caminho_bairros = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/divisa_bairros_2.gpkg"
    
    # Caminhos dos corredores de transporte
    caminho_biarticulado = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/rota_bi-articulados_dissolv.gpkg"
    caminho_linha_verde = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/Linha_Verde_Dissolv_2.gpkg"
    caminho_contorno = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/Contorno_dissolv.gpkg"
    caminho_br277 = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/BR-277.gpkg"
    caminho_comend = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/comend_franco.gpkg"
    
    
    try:
        gdf_hex = carregar_camada(caminho_hex)
        gdf_limite = carregar_camada(caminho_limite)
        gdf_bairros = carregar_camada(caminho_bairros)
        gdf_biarticulado = carregar_camada(caminho_biarticulado)
        gdf_linha_verde = carregar_camada(caminho_linha_verde)
        gdf_contorno = carregar_camada(caminho_contorno)
        gdf_277 = carregar_camada(caminho_br277)
        gdf_comend = carregar_camada(caminho_comend)
    
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos GPKG: {e}")
        st.stop()
        
    # --- 2. SIDEBAR: SELETORES E CAMADAS ---
    colunas_numericas = list(gdf_hex.select_dtypes(include=[np.number]).columns)
    if not colunas_numericas:
        st.error("Nenhuma coluna numérica encontrada no arquivo GPKG")
        st.stop()

    st.sidebar.header("Variable Selection")
    coluna_esq = st.sidebar.selectbox("Left Map Variable:", colunas_numericas, index=0)
    idx_padrao_dir = 1 if len(colunas_numericas) > 1 else 0
    coluna_dir = st.sidebar.selectbox("Right Map Variable:", colunas_numericas, index=idx_padrao_dir)

    st.sidebar.markdown("---")
    st.sidebar.header("Transportation Corridors")
    mostrar_biarticulado = st.sidebar.checkbox(r"$\textcolor{#D00000}{\text{━━━}}$ Structuring Axes", value=False)
    mostrar_linha_verde = st.sidebar.checkbox(r"$\textcolor{#009E60}{\text{━━━}}$ Linha Verde", value=False)
    mostrar_contorno = st.sidebar.checkbox(r"$\textcolor{#696969}{\text{━━━}}$ Ringroad", value=False)
    mostrar_277 = st.sidebar.checkbox(r"$\textcolor{#5E17EB}{\text{━━━}}$ Roadway BR-277", value=False)
    mostrar_comend = st.sidebar.checkbox(r"$\textcolor{#1C1C1E}{\text{━━━}}$ Av das Torres", value=False)

    st.sidebar.markdown("---")
    st.sidebar.header("Administrative Divisions")
    mostrar_bairros = st.sidebar.checkbox("Neighborhoods Boundaries", value=False)
    
    # 3. Configurações Compartilhadas de Cores e Câmera
    alpha_hex = int(255 * 0.65)
    N_CLASSES = 5
    colormap = plt.colormaps["YlOrRd"]
    cores_rgba = [colormap((i + 0.5) / N_CLASSES) for i in range(N_CLASSES)]
    cores_hex_rgba = [[int(r * 255), int(g * 255), int(b * 255), alpha_hex] for r, g, b, _ in cores_rgba]
    
    def calc_cor_faixas(val):
        if pd.isna(val):
            return [180, 180, 180, 80]
        if val <= 30:
            return cores_hex_rgba[0] # 0 - 30
        elif val <= 40:
            return cores_hex_rgba[1] # 30 - 40
        elif val <= 50:
            return cores_hex_rgba[2] # 40 - 50
        elif val <= 70:
            return cores_hex_rgba[3] # 50 - 70
        else:
            return cores_hex_rgba[4] # 70+
    
    # Ajuste da Câmera (baseado na extensão do limite municipal)
    bounds = gdf_limite.total_bounds
    centro_lat = (bounds[1] + bounds[3]) / 2
    centro_lon = (bounds[0] + bounds[2]) / 2
    
    view_state = pdk.ViewState(
        latitude=centro_lat,
        longitude=centro_lon,
        zoom=10,
        pitch=0
    )
    
    # Camada BASE: ESRI Gray (Light) Canvas
    # Nota: O ArcGIS utiliza a rota /tile/{z}/{y}/{x}
    url_esri_gray = "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
    
    # 4. Funções geradoras de elementos
    def gerar_deck_e_legenda(coluna_nome, sufixo_id):
            df_temp = gdf_hex.copy()
            df_temp["fill_color"] = df_temp[coluna_nome].apply(calc_cor_faixas)
            df_temp["valor_formatado"] = df_temp[coluna_nome].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
    
            camadas = [
                pdk.Layer(
                    "TileLayer",
                    id=f"esri-base-{sufixo_id}",
                    data=url_esri_gray,
                    min_zoom=0,
                    max_zoom=16,
                    tile_size=256,
                    pickable=False
                ),
                pdk.Layer(
                    "GeoJsonLayer",
                    df_temp.__geo_interface__,
                    id=f"layer-hex-{sufixo_id}",
                    stroked=True,
                    filled=True,
                    get_fill_color="properties.fill_color",
                    get_line_color=[180, 180, 180, 80],
                    line_width_min_pixels=0.5,
                    pickable=True,
                    auto_highlight=True,
                    highlight_color=[255, 255, 0, 200]
                ),
                pdk.Layer(
                    "GeoJsonLayer",
                    gdf_limite.__geo_interface__,
                    id=f"layer-limite-{sufixo_id}",
                    stroked=True,
                    filled=False,
                    get_line_color=[30, 30, 30, 255],
                    line_width_min_pixels=1.2,
                    pickable=False
                )
            ]
    
    # Adição das redes lineares (sempre sobrepostas a todas as camadas anteriores)
            if mostrar_biarticulado:
                camadas.append(pdk.Layer("GeoJsonLayer", gdf_biarticulado.__geo_interface__, id=f"biart-{sufixo_id}", stroked=True, filled=False, get_line_color=hex_to_rgba("#D00000"), line_width_min_pixels=2.5))
            if mostrar_linha_verde:
                camadas.append(pdk.Layer("GeoJsonLayer", gdf_linha_verde.__geo_interface__, id=f"lv-{sufixo_id}", stroked=True, filled=False, get_line_color=hex_to_rgba("#009E60"), line_width_min_pixels=2.5))
            if mostrar_contorno:
                camadas.append(pdk.Layer("GeoJsonLayer", gdf_contorno.__geo_interface__, id=f"cont-{sufixo_id}", stroked=True, filled=False, get_line_color=hex_to_rgba("#696969"), line_width_min_pixels=2.0))
            if mostrar_277:
                camadas.append(pdk.Layer("GeoJsonLayer", gdf_277.__geo_interface__, id=f"br277-{sufixo_id}", stroked=True, filled=False, get_line_color=hex_to_rgba("#5E17EB"), line_width_min_pixels=2.0))
            if mostrar_comend:
                camadas.append(pdk.Layer("GeoJsonLayer", gdf_comend.__geo_interface__, id=f"comend-{sufixo_id}", stroked=True, filled=False, get_line_color=hex_to_rgba("#1C1C1E"), line_width_min_pixels=2.0))
            if mostrar_bairros:
                camadas.append(pdk.Layer("GeoJsonLayer", gdf_bairros.__geo_interface__, id=f"bairros-{sufixo_id}", stroked=True, filled=False, get_line_color=[90, 90, 90, 180], line_width_min_pixels=1.0))
    
            tooltip = {
                "html": f"<b>{coluna_nome}:</b> {{valor_formatado}} km/h",
                "style": {
                    "backgroundColor": "rgba(20, 20, 20, 0.85)",
                    "color": "#ffffff",
                    "fontFamily": "sans-serif",
                    "fontSize": "11px",
                    "padding": "6px 10px",
                    "borderRadius": "4px"
                }
            }
            
            deck = pdk.Deck(layers=camadas, initial_view_state=view_state, map_style=None, tooltip=tooltip)

            cores_rgb_str = [f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})" for r, g, b, _ in cores_rgba]
            largura_pct = 100.0 / N_CLASSES
            celulas_cores = "".join([f'<div style="width: {largura_pct}%; background-color: {c}; height: 14px; border-right: 1px solid rgba(0,0,0,0.2);"></div>' for c in cores_rgb_str])
            marcos_html = "".join([f'<span style="font-size: 10px; color: #444; font-family: monospace;">{r}</span>' for r in ["30", "40", "50", "70", "70+"]])
    
            legenda_html = f"""
            <div style="font-family: sans-serif; padding: 6px 10px; background: rgba(245, 245, 245, 0.9); border-radius: 4px; border: 1px solid #dcdcdc;">
                <div style="font-size: 11px; font-weight: 600; color: #333; margin-bottom: 4px;">{coluna_nome} (km/h)</div>
                <div style="display: flex; width: 100%; border-radius: 3px; border: 1px solid #777; overflow: hidden;">{celulas_cores}</div>
                <div style="display: flex; justify-content: space-between; width: 100%; margin-top: 3px;">{marcos_html}</div>
            </div>
            """
            return deck, legenda_html
        
    def gerar_grafico_distribuicao(serie_limpa, coluna_nome):
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            row_heights=[0.25, 0.75],
            vertical_spacing=0.03
        )

        # 1. Boxplot
        fig.add_trace(
            go.Box(
                x=serie_limpa,
                name="",
                orientation="h",
                fillcolor="rgba(253, 174, 107, 0.65)",
                line=dict(color="#1a1a1a", width=1.0),
                boxpoints="outliers",
                jitter=0.15,
                marker=dict(color="#1a1a1a", size=3.5, opacity=0.75),
                showlegend=False
            ),
            row=1, col=1
        )
        
        # 2. Histograma
        fig.add_trace(
            go.Histogram(
                x=serie_limpa,
                name="Frequency",
                marker_color="#fdae6b",
                opacity=0.85,
                marker_line=dict(color="#333333", width=0.6),
                xbins=dict(
                    start=np.floor(serie_limpa.min()),
                    end=np.ceil(serie_limpa.max()),
                    size=2.0
                ),
                showlegend=False
            ),
            row=2, col=1
        )

        media_val = serie_limpa.mean()
        mediana_val = serie_limpa.median()
        
        fig.add_vline(
            x=media_val,
            line_width=1.5,
            line_dash="dash",
            line_color="#2b83ba",
            annotation_text=f"Mean: {media_val:.1f}",
            annotation_position="top left",
            row=2, col=1
        )
        fig.add_vline(
            x=mediana_val,
            line_width=1.5,
            line_dash="dot",
            line_color="#008837",
            annotation_text=f"Median: {mediana_val:.1f}",
            annotation_position="top right",
            row=2, col=1
        )

        fig.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=15, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            bargap=0.05
        )
        
        fig.update_yaxes(showticklabels=False, row=1, col=1)
        fig.update_yaxes(title_text="Frequency", gridcolor="rgba(200, 200, 200, 0.25)", row=2, col=1)
        fig.update_xaxes(title_text=coluna_nome, dtick=10, gridcolor="rgba(200, 200, 200, 0.25)", row=2, col=1)
        
        return fig
    
    def renderizar_painel_coluna(coluna_nome, sufixo_id):
        # 1. Mapa + Legenda
        deck, leg = gerar_deck_e_legenda(coluna_nome, sufixo_id)
        st.pydeck_chart(deck, use_container_width=True)
        components.html(leg, height=75)

        st.markdown("---")

        # 2. Gráficos
        st.markdown(f"#### Distribution: {coluna_nome}")
        dados_coluna = gdf_hex[coluna_nome]
        serie_limpa = dados_coluna.dropna()

        fig = gerar_grafico_distribuicao(serie_limpa, coluna_nome)
        st.plotly_chart(fig, use_container_width=True)

        # 3. Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Mean", f"{serie_limpa.mean():.2f}")
        m2.metric("Median", f"{serie_limpa.median():.2f}")
        m3.metric("St Dv", f"{serie_limpa.std():.2f}")

        m4, m5, m6 = st.columns(3)
        m4.metric("Minimum", f"{serie_limpa.min():.2f}")
        m5.metric("Maximum", f"{serie_limpa.max():.2f}")
        m6.metric("Null", f"{dados_coluna.isna().sum()}")
        
        # 5. Estilização dos cartões de métricas
        st.markdown("""
            <style>
            [data-testid="stMetricValue"] {
                font-size: 1.25rem !important;
                line-height: 1.2 !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.8rem !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # 6. Renderização Lado a Lado
    col_esq, col_dir = st.columns(2, gap="large")

    with col_esq:
        st.subheader(f"Left: {coluna_esq}")
        renderizar_painel_coluna(coluna_esq, "left")

    with col_dir:
        st.subheader(f"Right: {coluna_dir}")
        renderizar_painel_coluna(coluna_dir, "right")
    
# Rodapé informativo
    st.markdown("---")
    with st.expander("About the Database and Machine Learning Models applied"):
        st.markdown("""
        - **Spatial Resolution:** Hexagonal grid H3 Resolution 9 (the hexagons are approximately 200m on each side).
        - **Scope:** Municipality of Curitiba / Urban Limits.
        - **Linear Systems:** Main roads and public transport layers can be activated via the side menu to provide context for urban corridors.
        - **Data:** IPPUC / Municipal open data (2023–2026) and OpenStreetMap Data.
        - Speeds for the morning, afternoon, evening, and early morning periods refer to field collected data.
        - The construcution of this Dashboard is part of Authors (2027) - https://zenodo.org/records/21605239
        - Machine Learning Models applied as seen in Authors (2027) - https://zenodo.org/records/21605239
        """)

if __name__ == "__main__":
    render_modelos()
    
