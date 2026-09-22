#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 10:35:53 2026

@author: rafaelszeliga
"""

# para rodar no streamlit
#### para rodar no terminal:
#### streamlit run teste-01.py

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

st.set_page_config(layout="wide", page_title="Hexagonal Network - Viewer")

st.title("Speed Viewer")

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
caminho_hex = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/grade_h9_DT_nds_v3_dados_inferidos_DT_RF_simplificado.gpkg"
caminho_limite = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/bairros_dissolvido.gpkg"

# Caminhos dos corredores de transporte
caminho_biarticulado = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/rota_bi-articulados_dissolv.gpkg"
caminho_linha_verde = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/Linha_Verde_Dissolv_2.gpkg"
caminho_contorno = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/Contorno_dissolv.gpkg"
caminho_br277 = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/BR-277.gpkg"
caminho_comend = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/comend_franco.gpkg"

try:
    gdf_hex = carregar_camada(caminho_hex)
    gdf_limite = carregar_camada(caminho_limite)
    
    # Carregamento dos eixos de transporte
    gdf_biarticulado = carregar_camada(caminho_biarticulado)
    gdf_linha_verde = carregar_camada(caminho_linha_verde)
    gdf_contorno = carregar_camada(caminho_contorno)
    gdf_277 = carregar_camada(caminho_br277)
    gdf_comend = carregar_camada(caminho_comend)
except Exception as e:
    st.error(f"Erro ao carregar os arquivos GPKG: {e}")
    st.stop()
    
# 2. Sidebar - Controles
st.sidebar.header("Analysis Variable")
colunas_numericas = list(gdf_hex.select_dtypes(include=[np.number]).columns)
if not colunas_numericas:
    st.error("No numeric column found in the GPKG file")
    st.stop()

coluna_alvo = st.sidebar.selectbox("Continuous variable:", colunas_numericas)

st.sidebar.markdown("---")
st.sidebar.header("Transportation Corridors")

# Camadas lineares com cores temáticas fixas

# Funções/tags auxiliares para criar a linha indicadora da legenda
mostrar_biarticulado = st.sidebar.checkbox(
    ":red[━━━] Structuring Axes", 
    value=False
)

mostrar_linha_verde = st.sidebar.checkbox(
    ":green[━━━] Linha Verde", 
    value=False
)

mostrar_contorno = st.sidebar.checkbox(
    ":orange[━━━] Ringroad", 
    value=False
)

mostrar_277 = st.sidebar.checkbox(
    ":violet[━━━] Roadway BR-277", 
    value=False
)

mostrar_comend = st.sidebar.checkbox(
    ":gray[━━━] Av das Torres (Comendador Franco)", 
    value=False
)

# 3. Tratamento de Cores dos Hexágonos (Transparência 0.65 -> alpha ~ 166 de 255)
# colormap = cm.get_cmap("viridis")
alpha_hex = int(255 * 0.65)
dados_coluna = gdf_hex[coluna_alvo]

vmin = float(dados_coluna.dropna().min())
vmax = float(dados_coluna.dropna().max())
norm = mcolors.Normalize(vmin=vmin, vmax=vmax if vmin != vmax else vmin + 1)
colormap = plt.colormaps["YlOrRd"]

def calc_cor(val):
    if np.isnan(val):
        return [180, 180, 180, alpha_hex]
    rgba = colormap(norm(val))
    return [int(c * 255) for c in rgba[:3]] + [alpha_hex]

gdf_hex["fill_color"] = gdf_hex[coluna_alvo].apply(calc_cor)

# Formatação com 2 casas decimais (ou "N/A" se for nulo)
gdf_hex["valor_formatado"] = gdf_hex[coluna_alvo].apply(
    lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A"
)
    

# 4. Ajuste da Câmera (baseado na extensão do limite municipal)
bounds = gdf_limite.total_bounds
centro_lat = (bounds[1] + bounds[3]) / 2
centro_lon = (bounds[0] + bounds[2]) / 2

view_state = pdk.ViewState(
    latitude=centro_lat,
    longitude=centro_lon,
    zoom=10,
    pitch=0
)

# 5.1 Camada BASE: ESRI Gray (Light) Canvas
# Nota: O ArcGIS utiliza a rota /tile/{z}/{y}/{x}
url_esri_gray = "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"

camada_esri_base = pdk.Layer(
    "TileLayer",
    id="esri-gray-canvas",
    data=url_esri_gray,
    min_zoom=0,
    max_zoom=16,
    tile_size=256,
    pickable=False
)

# 5.2 Hexágonos
camada_hex = pdk.Layer(
    "GeoJsonLayer",
    gdf_hex.__geo_interface__,
    id="layer-hex",
    stroked=True,
    filled=True,
    get_fill_color="properties.fill_color",
    get_line_color=[80, 80, 80, 120],
    line_width_min_pixels=0.5,
    pickable=True,
    auto_highlight=True,
    highlight_color=[255, 255, 0, 200]
)

# 5.3 Limite Municipal
camada_limite = pdk.Layer(
    "GeoJsonLayer",
    gdf_limite.__geo_interface__,
    id="layer-limite",
    stroked=True,
    filled=False,
    get_line_color=[30, 30, 30, 255],
    line_width_min_pixels=1.2,
    pickable=False
)

# Base do mapa
camadas_mapa = [camada_esri_base, camada_hex, camada_limite]

# 5.4 Adição das redes lineares (sempre sobrepostas a todas as camadas anteriores)
if mostrar_biarticulado:
    layer_biarticulado = pdk.Layer(
        "GeoJsonLayer",
        gdf_biarticulado.__geo_interface__,
        id="layer-biarticulado",
        stroked=True,
        filled=False,
        get_line_color=hex_to_rgba("#e82227", 255),  # Eixos Biarticulado
        line_width_min_pixels=2.5,
        pickable=False
    )
    camadas_mapa.append(layer_biarticulado)

if mostrar_linha_verde:
    layer_linha_verde = pdk.Layer(
        "GeoJsonLayer",
        gdf_linha_verde.__geo_interface__,
        id="layer-linha-verde",
        stroked=True,
        filled=False,
        get_line_color=hex_to_rgba("#009c05", 255),  # Linha Verde
        line_width_min_pixels=2.5,
        pickable=False
    )
    camadas_mapa.append(layer_linha_verde)

if mostrar_contorno:
    layer_contorno = pdk.Layer(
        "GeoJsonLayer",
        gdf_contorno.__geo_interface__,
        id="layer-contorno",
        stroked=True,
        filled=False,
        get_line_color=hex_to_rgba("#f07436", 255),  # Contorno Rodoviário
        line_width_min_pixels=2.0,
        pickable=False
    )
    camadas_mapa.append(layer_contorno)
    
if mostrar_277:
    layer_277 = pdk.Layer(
        "GeoJsonLayer",
        gdf_277.__geo_interface__,
        id="layer-277",
        stroked=True,
        filled=False,
        get_line_color=hex_to_rgba("#7F00FF", 255),  # BR-277
        line_width_min_pixels=2.0,
        pickable=False
    )
    camadas_mapa.append(layer_277)
    
    
if mostrar_comend:
    layer_comend = pdk.Layer(
        "GeoJsonLayer",
        gdf_comend.__geo_interface__,
        id="layer-comend",
        stroked=True,
        filled=False,
        get_line_color=hex_to_rgba("#7b7b7b", 255),  # BR-277
        line_width_min_pixels=2.0,
        pickable=False
    )
    camadas_mapa.append(layer_comend)

tooltip = {
    "html": f"<b>{coluna_alvo}:</b> {{valor_formatado}} km/h",
    "style": {
        "backgroundColor": "rgba(20, 20, 20, 0.85)",
        "color": "#ffffff",
        "fontFamily": "sans-serif",
        "fontSize": "13px",
        "padding": "6px 10px",
        "borderRadius": "4px"
    }
}

deck = pdk.Deck(
    layers=camadas_mapa,
    initial_view_state=view_state,
    map_style=None,
    tooltip=tooltip
)

# 6. Layout Principal: 2 Colunas (60% Mapa, 40% Estatística)
col_mapa, col_graficos = st.columns([3, 2], gap="medium")

with col_mapa:
    st.subheader("Spatial Distribution")
    st.pydeck_chart(deck, use_container_width=True)

# --- BARRA DE LEGENDA DO MAPA ---
    # Amostra cores ao longo da rampa (YlOrRd) para gerar o gradiente CSS
    n_passos = 10
    gradiente_amostras = [colormap(i / (n_passos - 1)) for i in range(n_passos)]
    gradiente_css = ", ".join([f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})" for r, g, b, _ in gradiente_amostras])

    # Interpolação para 5 marcos intermediários de valores
    marcos = np.linspace(vmin, vmax, 5)

    st.markdown(
        f"""
        <div style="margin-top: 10px; margin-bottom: 25px; padding: 10px 14px; background: rgba(245, 245, 245, 0.7); border-radius: 6px; border: 1px solid #e0e0e0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">
                <span>Legenda: {coluna_alvo}</span>
                <span style="font-weight: normal; color: #666; font-size: 12px;">Transparência: 65%</span>
            </div>
            <!-- Barra Gradiente -->
            <div style="
                height: 14px;
                width: 100%;
                border-radius: 3px;
                background: linear-gradient(to right, {gradiente_css});
                border: 1px solid #999;
                box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
            "></div>
            <!-- Rótulos dos Valores -->
            <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 12px; color: #444; font-family: monospace;">
                <span>{marcos[0]:.2f}</span>
                <span>{marcos[1]:.2f}</span>
                <span>{marcos[2]:.2f}</span>
                <span>{marcos[3]:.2f}</span>
                <span>{marcos[4]:.2f}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_graficos:
    st.subheader(f"Distribution: {coluna_alvo}")
    
    serie_limpa = dados_coluna.dropna()
    
    fig = make_subplots(
        rows=2, 
        cols=1, 
        shared_xaxes=True,
        row_heights=[0.25, 0.75],
        vertical_spacing=0.03
    )

    # 1. Boxplot (topo)
    fig.add_trace(
        go.Box(
            x=serie_limpa,
            name="",
            orientation="h",
            # Preenchimento interior alaranjado
            fillcolor="rgba(253, 174, 107, 0.65)",
            # Linhas finas e pretas (contorno, mediana e bigodes)
            line=dict(
                color="#1a1a1a",
                width=1.0
            ),
            # Outliers: pontos menores e em preto
            boxpoints="outliers",
            jitter=0.15,
            marker=dict(
                color="#1a1a1a",
                size=3.5,
                opacity=0.75
            ),
            showlegend=False
        ),
        row=1, col=1
    )

    # 2. Histograma (baixo) com bins redondos (de 2 em 2 km/h)
    fig.add_trace(
        go.Histogram(
            x=serie_limpa,
            name="Frequência",
            marker_color="#fdae6b",
            opacity=0.85,
            marker_line=dict(color="#333333", width=0.6),
            xbins=dict(
                start=np.floor(serie_limpa.min()),
                end=np.ceil(serie_limpa.max()),
                size=2.0  # Agrupa de 2 em 2 km/h
            ),
            showlegend=False
        ),
        row=2, col=1
    )

    # Linhas de referência para Média e Mediana
    media_val = serie_limpa.mean()
    mediana_val = serie_limpa.median()

    fig.add_vline(
        x=media_val, 
        line_width=1.5, 
        line_dash="dash", 
        line_color="#2b83ba",
        annotation_text=f"Média: {media_val:.1f}", 
        annotation_position="top left",
        row=2, col=1
    )
    fig.add_vline(
        x=mediana_val, 
        line_width=1.5, 
        line_dash="dot", 
        line_color="#008837",
        annotation_text=f"Mediana: {mediana_val:.1f}", 
        annotation_position="top right",
        row=2, col=1
    )

    fig.update_layout(
        height=480,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.05
    )

    fig.update_yaxes(showticklabels=False, row=1, col=1)
    fig.update_yaxes(title_text="Frequência", gridcolor="rgba(200, 200, 200, 0.25)", row=2, col=1)
    
    # Eixo X com marcações claras de 10 em 10 (10, 20, 30 ... 140)
    fig.update_xaxes(
        title_text=coluna_alvo, 
        dtick=10, 
        gridcolor="rgba(200, 200, 200, 0.25)", 
        row=2, col=1
    )

    st.plotly_chart(fig, use_container_width=True)

    # Linha 1: Medidas de tendência central e dispersão
    m1, m2, m3 = st.columns(3)
    m1.metric("Média", f"{serie_limpa.mean():.2f}")
    m2.metric("Mediana", f"{serie_limpa.median():.2f}")
    m3.metric("Desv. Padrão", f"{serie_limpa.std():.2f}")

    # Linha 2: Extremos e integridade dos dados
    m4, m5, m6 = st.columns(3)
    m4.metric("Mínimo", f"{serie_limpa.min():.2f}")
    m5.metric("Máximo", f"{serie_limpa.max():.2f}")
    m6.metric("Nulos", f"{dados_coluna.isna().sum()}")
    
# 7. Tooltip apontando para o valor formatado
tooltip = {
    "html": f"<b>{coluna_alvo}:</b> {{valor_formatado}}",
    "style": {
        "backgroundColor": "rgba(20, 20, 20, 0.85)",
        "color": "#ffffff",
        "fontFamily": "sans-serif",
        "fontSize": "13px",
        "padding": "6px 10px",
        "borderRadius": "4px"
    }
}
