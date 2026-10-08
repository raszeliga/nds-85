#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 10:35:53 2026

@author: rafaelszeliga
"""

# pip install pydeck

import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import streamlit.components.v1 as components

def render_fatais():
    st.title("Fatal Accidents Viewer from 2019 to 2023")
    
    # 0. Configuração da Variável Única
    COLUNA_ALVO = "Fatal Accidents"  # <-- Nome exato da coluna numérica no GPKG
    
    CONFIG_VAR = {
        "cmap": "hot_r",             # Outros Colormaps: 'hot_r', 'Reds', 'OrRd', 'YlOrRd', 'inferno'
        "label": "Fatal Crashes",
        "unidade": "Occurrences"
    }
    
    coluna_alvo = COLUNA_ALVO
    nome_cmap = CONFIG_VAR["cmap"]
    unidade = CONFIG_VAR["unidade"]
    label_legenda = CONFIG_VAR["label"]
    
    # Função auxiliar: converte '#RRGGBB' para [R, G, B, 255]
    def hex_to_rgba(hex_str, alpha=255):
        hex_str = hex_str.lstrip("#")
        return [int(hex_str[i:i+2], 16) for i in (0, 2, 4)] + [alpha]
    
    # 1. Carregamento dos Dados
    @st.cache_data
    def carregar_camada(caminho_gpkg):
        gdf = gpd.read_file(caminho_gpkg)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        return gdf
    
    # Caminhos dos arquivos
    caminho_fatais = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/3_Contagem_fatais_2019-2023.gpkg"
    caminho_limite = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/bairros_dissolvido.gpkg"
    caminho_bairros = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/divisa_bairros_2.gpkg"
    
    # Caminhos dos corredores de transporte
    caminho_biarticulado = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/rota_bi-articulados_dissolv.gpkg"
    caminho_linha_verde = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/Linha_Verde_Dissolv_2.gpkg"
    caminho_contorno = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/Contorno_dissolv.gpkg"
    caminho_br277 = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/BR-277.gpkg"
    caminho_comend = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/comend_franco.gpkg"
    
    try:
        gdf_fatais = carregar_camada(caminho_fatais)
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
    
    # 2. Sidebar - Controles
    st.sidebar.header("Analysis Variable")
    
    # Validação da coluna no GeoDataFrame
    if coluna_alvo not in gdf_fatais.columns:
        st.error(
            f"A coluna '{coluna_alvo}' não foi encontrada no GPKG. "
            f"Colunas disponíveis: {list(gdf_fatais.columns)}"
        )
        st.stop()
    
    st.sidebar.info(f"**Variable:** {label_legenda}")
    
    st.sidebar.markdown("---")
    st.sidebar.header("Transportation Corridors")
    
    mostrar_biarticulado = st.sidebar.checkbox(
        r"$\textcolor{#D00000}{\text{━━━}}$ Structuring Axes", 
        value=False
    )
    
    mostrar_linha_verde = st.sidebar.checkbox(
        r"$\textcolor{#009E60}{\text{━━━}}$ Linha Verde", 
        value=False
    )
    
    mostrar_contorno = st.sidebar.checkbox(
        r"$\textcolor{#696969}{\text{━━━}}$ Ringroad", 
        value=False
    )
    
    mostrar_277 = st.sidebar.checkbox(
        r"$\textcolor{#5E17EB}{\text{━━━}}$ Roadway BR-277", 
        value=False
    )
    
    mostrar_comend = st.sidebar.checkbox(
        r"$\textcolor{#1C1C1E}{\text{━━━}}$ Av das Torres (Comendador Franco)", 
        value=False
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("Administrative Divisions")
    mostrar_bairros = st.sidebar.checkbox("Neighborhoods Boundaries", value=False)
    
    # 3. Processamento de Cores e Métricas
    alpha_hex = int(255 * 0.65)
    dados_coluna = pd.to_numeric(gdf_fatais[coluna_alvo], errors="coerce")
    
    vmin = float(dados_coluna.min())
    vmax = float(dados_coluna.max())
    
    # Normalização com proteção para vmin == vmax
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax if vmax > vmin else vmin + 1)
    colormap = plt.colormaps[nome_cmap]
    
    def mapear_cor_linear(val):
        if pd.isna(val):
            return [180, 180, 180, alpha_hex]
        r, g, b, _ = colormap(norm(val))
        return [int(r * 255), int(g * 255), int(b * 255), alpha_hex]
    
    gdf_fatais["fill_color"] = dados_coluna.apply(mapear_cor_linear)
    
    # Formatação condicional para o tooltip
    gdf_fatais["valor_formatado"] = dados_coluna.apply(
        lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A"
    )
    
    # 4. Ajuste da Câmera
    bounds = gdf_limite.total_bounds
    centro_lat = (bounds[1] + bounds[3]) / 2
    centro_lon = (bounds[0] + bounds[2]) / 2
    
    view_state = pdk.ViewState(
        latitude=centro_lat,
        longitude=centro_lon,
        zoom=10,
        pitch=0
    )
    
    # 5. Configuração das Camadas PyDeck
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
    
    camada_hex = pdk.Layer(
        "GeoJsonLayer",
        gdf_fatais.__geo_interface__,
        id="layer-hex",
        stroked=True,
        filled=True,
        get_fill_color="properties.fill_color",
        get_line_color=[180, 180, 180, 80],
        line_width_min_pixels=0.5,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 0, 200]
    )
    
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
    
    camadas_mapa = [camada_esri_base, camada_hex, camada_limite]
    
    if mostrar_bairros:
        layer_bairros = pdk.Layer(
            "GeoJsonLayer",
            gdf_bairros.__geo_interface__,
            id="layer-bairros",
            stroked=True,
            filled=False,
            get_line_color=[100, 100, 100, 160],
            line_width_min_pixels=0.8,
            pickable=False
        )
        camadas_mapa.append(layer_bairros)
    
    if mostrar_biarticulado:
        layer_biarticulado = pdk.Layer(
            "GeoJsonLayer",
            gdf_biarticulado.__geo_interface__,
            id="layer-biarticulado",
            stroked=True,
            filled=False,
            get_line_color=hex_to_rgba("#D00000", 255),
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
            get_line_color=hex_to_rgba("#009E60", 255),
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
            get_line_color=hex_to_rgba("#696969", 255),
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
            get_line_color=hex_to_rgba("#5E17EB", 255),
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
            get_line_color=hex_to_rgba("#1C1C1E", 255),
            line_width_min_pixels=2.0,
            pickable=False
        )
        camadas_mapa.append(layer_comend)
    
    # Tooltip dinâmico com a unidade correspondente
    texto_unidade = f" {unidade}" if unidade else ""
    tooltip = {
        "html": f"<b>{label_legenda}:</b> {{valor_formatado}}{texto_unidade}",
        "style": {
            "backgroundColor": "rgba(20, 20, 20, 0.85)",
            "color": "#ffffff",
            "fontFamily": "sans-serif",
            "fontSize": "11px",
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
    
    # ======================== COLUNA DA ESQUERDA: MAPA + LEGENDA ========================
    with col_mapa:
        st.subheader("Spatial Distribution")
        st.pydeck_chart(deck, use_container_width=True)
        
        # Geração dos stops CSS com base no colormap dinâmico
        N_STOPS = 10
        stops = []
        for i in range(N_STOPS):
            t = i / (N_STOPS - 1)
            r, g, b, _ = colormap(t)
            stops.append(f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)}) {t * 100:.1f}%")
        css_gradient = f"linear-gradient(to right, {', '.join(stops)})"
        
        # Marcadores proporcionais lineares (5 pontos)
        N_TICKS = 5
        ticks = np.linspace(vmin, vmax, N_TICKS)
        marcos_html = "".join([
            f'<span style="font-size: 11px; color: #444; font-family: monospace;">{val:.1f}</span>'
            for val in ticks
        ])
        
        # Legenda HTML estilizada
        unidade_legenda = f" ({unidade})" if unidade else ""
        html_legenda = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 8px 12px; background: rgba(245, 245, 245, 0.9); border-radius: 6px; border: 1px solid #dcdcdc; box-sizing: border-box;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">
                <span>Scale{unidade_legenda}: {label_legenda}</span>
                <span style="font-weight: normal; color: #666; font-size: 12px;">Min: {vmin:.1f} | Max: {vmax:.1f}</span>
            </div>
            <div style="width: 100%; height: 16px; background: {css_gradient}; border-radius: 4px; border: 1px solid #777; box-shadow: inset 0 1px 2px rgba(0,0,0,0.15);"></div>
            <div style="display: flex; justify-content: space-between; width: 100%; margin-top: 5px;">
                {marcos_html}
            </div>
        </div>
        """
        
        components.html(html_legenda, height=85)
    
    # ======================== COLUNA DA DIREITA: ESTATÍSTICAS ========================
    with col_graficos:
        st.subheader(f"Distribution: {label_legenda}")
        
        serie_limpa = dados_coluna.dropna()
        
        st.markdown("""
            <style>
            [data-testid="stMetricValue"] {
                font-size: 1.35rem !important;
                line-height: 1.2 !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.85rem !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Linha 1: Medidas de tendência central e contagem
        m1, m2, m3 = st.columns(3)
        m1.metric("Mean", f"{serie_limpa.mean():.2f}")
        m2.metric("Median", f"{serie_limpa.median():.2f}")
        m3.metric("Std Dev", f"{serie_limpa.std():.2f}")
        
        # Linha 2: Extremos e total
        m4, m5, m6 = st.columns(3)
        m4.metric("Minimum", f"{serie_limpa.min():.2f}")
        m5.metric("Maximum", f"{serie_limpa.max():.2f}")
        m6.metric("Total Count", f"{829}")
        
        # --- CAIXA DE TEXTO FIXA ---
        with st.container(border=False):
            st.markdown("### About the Database")
            st.markdown("""
            - **Spatial Resolution:** Hexagonal grid H3 Resolution 9 (the hexagons are approximately 200m on each side)
            - **Scope:** Municipality of Curitiba / Urban Limits
            - **Linear Systems:** Main roads and public transport layers can be activated via the side menu to provide context for urban corridors
            - **Data:** IPPUC / Municipal open data and OpenStreetMap Data
            - For this Dashboard, data obtained from https://geoapp.ippuc.org.br/AcidentesDeTransito/dashboard.html
            """)
