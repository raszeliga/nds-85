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
import streamlit.components.v1 as components

def render_modelos():
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
    caminho_hex = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/gdf_dash_modelos.gpkg"
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
        
        # Carregar os bairros (ippuc)
        gdf_bairros = carregar_camada(caminho_bairros)
        
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
    
    coluna_alvo = st.sidebar.selectbox("Chose a continuous variable:", colunas_numericas)
    
    st.sidebar.markdown("---")
    st.sidebar.header("Transportation Corridors")
    
    # Camadas lineares com cores temáticas fixas
    
    # Funções/tags auxiliares para criar a linha indicadora da legenda
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
    
    # 3. Tratamento de Cores por Estratificação Fixa (0-10, 10-20, 20-40, 40-50, 50+)
    alpha_hex = int(255 * 0.65)
    dados_coluna = gdf_hex[coluna_alvo]
    
    # Limites das classes fixadas
    cortes_velocidade = [0, 30, 40, 50, 70, np.inf]
    N_CLASSES = 5
    colormap = plt.colormaps["YlOrRd"]
    
    # Amostra 5 cores da rampa YlOrRd
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
    
    gdf_hex["fill_color"] = gdf_hex[coluna_alvo].apply(calc_cor_faixas)
    
    # Formatação com 2 casas decimais para o tooltip
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
        get_line_color=[180, 180, 180, 80],
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
    
    # Base Map
    camadas_mapa = [camada_esri_base, camada_hex, camada_limite]
    
    # 5.4 Adição das redes lineares (sempre sobrepostas a todas as camadas anteriores)
    if mostrar_biarticulado:
        layer_biarticulado = pdk.Layer(
            "GeoJsonLayer",
            gdf_biarticulado.__geo_interface__,
            id="layer-biarticulado",
            stroked=True,
            filled=False,
            get_line_color=hex_to_rgba("#D00000", 255),  # Eixos Biarticulado
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
            get_line_color=hex_to_rgba("#009E60", 255),  # Linha Verde
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
            get_line_color=hex_to_rgba("#696969", 255),  # Contorno Rodoviário
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
            get_line_color=hex_to_rgba("#5E17EB", 255),  # BR-277
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
            get_line_color=hex_to_rgba("#1C1C1E", 255),  # BR-277
            line_width_min_pixels=2.0,
            pickable=False
        )
        camadas_mapa.append(layer_comend)
    
    # Se a camada estiver ativa, criamos o contorno e os rótulos de texto
    if mostrar_bairros:
        # 1. Contorno vazado dos bairros
        layer_contorno_bairros = pdk.Layer(
            "GeoJsonLayer",
            gdf_bairros.__geo_interface__,
            id="layer-bairros-linhas",
            stroked=True,
            filled=False,
            get_line_color=[90, 90, 90, 180],
            line_width_min_pixels=1.0,
            pickable=False
        )
        camadas_mapa.append(layer_contorno_bairros)
    
        # 2. Extração dos pontos para um DataFrame comum (crucial para o TextLayer)
        pontos = gdf_bairros.geometry.representative_point()
        
        # Criamos um DataFrame limpo do Pandas apenas com dados tabulares
        df_labels = pd.DataFrame({
            "lon": pontos.x.values,
            "lat": pontos.y.values,
            "nome": gdf_bairros["NOME"].astype(str).str.strip().str.upper().values
        })
        
        # Remove eventuais linhas com NaN ou vazias
        df_labels = df_labels[df_labels["nome"] != ""]
    
    #    # 3. Mostra os nomes dos bairros (retirado por enquanto) TextLayer configurado em pixels de tela
    #    layer_texto_bairros = pdk.Layer(
    #        "TextLayer",
    #        data=df_labels,
    #        id="layer-bairros-texto",
    #        get_position="[lon, lat]",       # Sintaxe Deck.gl avaliada sobre cada registro
    #        get_text="nome",
    #        get_size=12,
    #        size_units="'pixels'",           # Força o tamanho a ser em pixels de tela
    #        get_color=[30, 30, 30, 240],     # Cinza escuro quase opaco
    #        get_text_anchor="'middle'",
    #        get_alignment_baseline="'center'",
    #        billboard=True,                  # Garante que o texto fique sempre virado para a câmera
    #        background=True,                 # Adiciona um pequeno fundo suave para contraste
    #        get_background_color=[255, 255, 255, 170], # Fundo branco semi-transparente
    #        background_padding=[3, 2, 3, 2],
    #        pickable=False
    #    )
    #    camadas_mapa.append(layer_texto_bairros)
    
    tooltip = {
        "html": f"<b>{coluna_alvo}:</b> {{valor_formatado}} km/h",
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
    
    # --- BARRA DE LEGENDA DISCRETA DO MAPA ---
        cores_rgb_str = [f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})" for r, g, b, _ in cores_rgba]
        largura_pct = 100.0 / N_CLASSES
    
        celulas_cores = "".join([
            f'<div style="width: {largura_pct}%; background-color: {cor}; height: 16px; border-right: 1px solid rgba(0,0,0,0.2);"></div>'
            for cor in cores_rgb_str
        ])
    
        # Rótulos dos intervalos: 0, 10, 20, 40, 50 e 50+
        rotulos_classes = ["30", "40", "50", "70", "70+"]
        marcos_html = "".join([
            f'<span style="font-size: 11px; color: #444; font-family: monospace;">{rot}</span>'
            for rot in rotulos_classes
        ])
    
        html_legenda = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 8px 12px; background: rgba(245, 245, 245, 0.9); border-radius: 6px; border: 1px solid #dcdcdc; box-sizing: border-box;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 13px; font-weight: 600; color: #333;">
                <span>Legend (km/h): {coluna_alvo}</span>
                <span style="font-weight: normal; color: #666; font-size: 12px;">Classes: 0-30 | 30-40 | 40-50 | 50-70 | 70+</span>
            </div>
            <div style="display: flex; width: 100%; border-radius: 4px; border: 1px solid #777; overflow: hidden; box-shadow: inset 0 1px 2px rgba(0,0,0,0.15);">
                {celulas_cores}
            </div>
            <div style="display: flex; justify-content: space-between; width: 100%; margin-top: 5px;">
                {marcos_html}
            </div>
        </div>
        """
    
        components.html(html_legenda, height=85)
        
        # --- CAIXA DE TEXTO FIXA ---
        with st.container(border=False):
            st.markdown("About the Database")
            st.markdown("""
            - **Spatial Resolution:** Hexagonal grid H3 Resolution 9 (the hexagons are approximately 200m on each side)
            - **Scope:** Municipality of Curitiba / Urban Limits
            - **Linear Systems:** Main roads and public transport layers can be activated via the side menu to provide context for urban corridors
            - **Data:** IPPUC / Municipal open data (2023–2026) and OpenStreetMap Data
            """)
            st.markdown("About the Machine Learning Models Applied")
            st.markdown("""
            - Decision Tree Model
            - Random Forest Model 
            - XGBosst Model
            - Machine Learning Models by Szeliga et al (2026):** Publication available in xxxxxxxx
            """)
        
    # ======================== COLUNA DA DIREITA: GRÁFICOS + MÉTRICAS ========================
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
                fillcolor="rgba(253, 174, 107, 0.65)",
                line=dict(
                    color="#1a1a1a",
                    width=1.0
                ),
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
            height=480,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            bargap=0.05
        )
    
        fig.update_yaxes(showticklabels=False, row=1, col=1)
        fig.update_yaxes(title_text="Frequency", gridcolor="rgba(200, 200, 200, 0.25)", row=2, col=1)
        
        fig.update_xaxes(
            title_text=coluna_alvo, 
            dtick=10, 
            gridcolor="rgba(200, 200, 200, 0.25)", 
            row=2, col=1
        )
    
        st.plotly_chart(fig, use_container_width=True)
    
        # Métricas organizadas em 2 linhas de 3 colunas
        # Reduz o tamanho das fontes dos cards de métricas
        st.markdown("""
            <style>
            [data-testid="stMetricValue"] {
                font-size: 1.35rem !important;  /* Tamanho do número (padrão é ~2rem) */
                line-height: 1.2 !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.85rem !important;  /* Tamanho do título (Mean, Median, etc.) */
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Linha 1: Medidas de tendência central e dispersão
        m1, m2, m3 = st.columns(3)
        m1.metric("Mean", f"{serie_limpa.mean():.2f}")
        m2.metric("Median", f"{serie_limpa.median():.2f}")
        m3.metric("St Dv", f"{serie_limpa.std():.2f}")
        
        # Linha 2: Extremos e integridade dos dados
        m4, m5, m6 = st.columns(3)
        m4.metric("Minimum", f"{serie_limpa.min():.2f}")
        m5.metric("Maximum", f"{serie_limpa.max():.2f}")
        m6.metric("Null", f"{dados_coluna.isna().sum()}")
    
