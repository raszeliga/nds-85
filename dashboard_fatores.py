#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 10:35:53 2026

@author: rafaelszeliga
"""

# para rodar no streamlit
#### para rodar no terminal:
#### streamlit run teste-02.py

# pip install pydeck
# pip install mapclassify

import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import streamlit.components.v1 as components
import mapclassify
from matplotlib.colors import BoundaryNorm, ListedColormap

# from matplotlib import colormaps
# list(colormaps)

def render_fatores():
    st.title("Contributing Factors Viewer")
    
    # 0. Dicionário de Configurações (14 Variáveis)
    CONFIG_VARIAVEIS = {
        "Population": {
            "cmap": "YlGnBu",
            "label": "Population",
            "unidade": "Inhabitants"
        },
        "Households": {
            "cmap": "Blues",
            "label": "Households",
            "unidade": "Households"
        },
        "Stop Signs": {
            "cmap": "OrRd",
            "label": "Stop Signs",
            "unidade": "Units"
        },
        "Crosswalk": {
            "cmap": "YlOrBr",
            "label": "Crosswalks",
            "unidade": "Units"
        },
        "Roadbumps": {
            "cmap": "YlOrRd",
            "label": "Roadbumps",
            "unidade": "Units"
        },
        "Traffic Lights": {
            "cmap": "Reds",
            "label": "Traffic Lights",
            "unidade": "Units"
        },
        "Speed Cameras": {
            "cmap": "Reds",
            "label": "Speed Cameras",
            "unidade": "Units"
        },
        "Bus Stops": {
            "cmap": "Purples",
            "label": "Bus Stops",
            "unidade": "Units"
        },
        "Intersections": {
            "cmap": "Oranges",
            "label": "Intersections",
            "unidade": "Units"
        },
        "Hierarchy": {
            "cmap": "Greys_r",
            "label": "Hierarchy Score",
            "unidade": "Class"
        },
        "Posted Speed": {
            "cmap": "Reds",
            "label": "Posted Speed",
            "unidade": "km/h"
        },
        "Bike Lanes": {
            "cmap": "Greens",
            "label": "Bike Lanes Length",
            "unidade": "m"
        },
        "Schools and Universities": {
            "cmap": "PuRd",
            "label": "Schools & Universities",
            "unidade": "Units"
        },
        "POI": {
            "cmap": "Greys",
            "label": "Points of Interest (POI)",
            "unidade": "Units"
        },
        "default": {
            "cmap": "viridis",
            "label": "Value",
            "unidade": ""
        }
    }
    
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
    caminho_hex = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/gdf_dash_fatores.gpkg"
    caminho_limite = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/bairros_dissolvido.gpkg"
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
    
    # 2. Sidebar - Controles
    st.sidebar.header("Analysis Variable")
    
    # Lista priorizando as 14 variáveis que de fato existem no GeoDataFrame
    variaveis_alvo = [var for var in CONFIG_VARIAVEIS.keys() if var != "default" and var in gdf_hex.columns]
    
    # Caso as colunas no GPKG tenham outro formato, cai nas numéricas gerais
    if not variaveis_alvo:
        variaveis_alvo = list(gdf_hex.select_dtypes(include=[np.number]).columns)
    
    if not variaveis_alvo:
        st.error("No numeric column found in the GPKG file")
        st.stop()
    
    coluna_alvo = st.sidebar.selectbox("Choose a continuous variable:", variaveis_alvo)
    
    # Resgate da configuração específica da variável
    cfg = CONFIG_VARIAVEIS.get(coluna_alvo, CONFIG_VARIAVEIS["default"])
    nome_cmap = cfg["cmap"]
    unidade = cfg["unidade"]
    label_legenda = cfg["label"]
    
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
    alpha_hex = int(255 * 0.65) # grau de transparência
    dados_coluna = pd.to_numeric(gdf_hex[coluna_alvo], errors="coerce")
    
    # Isola valores estritamente positivos (maiores que 0)
    valores_pos = dados_coluna[dados_coluna > 0].dropna()
    colormap_base = plt.colormaps[nome_cmap]
    
    N_CLASSES = 5
    
    if not valores_pos.empty:
        # Ajusta k caso a coluna tenha menos de 5 valores únicos distintos
        k_ajustado = min(N_CLASSES, valores_pos.nunique())
        
        # Algoritmo de Jenks
        jenks = mapclassify.NaturalBreaks(valores_pos, k=k_ajustado)
        
        # Cria os limites de corte (bins) incluindo o valor mínimo
        bins = [float(valores_pos.min())] + [float(b) for b in jenks.bins]
        
        # Remove duplicatas e ordena para evitar erro no BoundaryNorm
        bins = sorted(list(set(bins)))
        if len(bins) < 2:
            bins = [float(valores_pos.min()), float(valores_pos.max()) + 1]
            
        n_intervalos = len(bins) - 1
        
        # --- CORTE DO TOM CLARO ---
        # Amostra de 0.25 (segundo tom/mais vivo) até 1.0 (tom mais escuro)
        amostras = np.linspace(0.25, 1.0, n_intervalos)
        cores_ajustadas = colormap_base(amostras)
        colormap = ListedColormap(cores_ajustadas)
        
        norm = BoundaryNorm(bins, ncolors=colormap.N, clip=True)
        vmax = float(valores_pos.max())
    else:
        bins = [0.0, 1.0]
        colormap = colormap_base
        norm = mcolors.Normalize(vmin=0, vmax=1)
        vmax = 0.0

    def mapear_cor_jenks(val):
        if pd.isna(val) or val <= 0:
            return [0, 0, 0, 0]
        r, g, b, _ = colormap(norm(val))
        return [int(r * 255), int(g * 255), int(b * 255), alpha_hex]

    gdf_hex["fill_color"] = dados_coluna.apply(mapear_cor_jenks)
    
    gdf_hex["valor_formatado"] = dados_coluna.apply(
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
            get_line_color=hex_to_rgba("#1C1C1E", 255),  # Av. das Torres
            line_width_min_pixels=2.0,
            pickable=False
        )
        camadas_mapa.append(layer_comend)
        
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
    
        # Geração dos blocos de legenda para as classes de Jenks
        blocos_html = []
        num_intervalos = len(bins) - 1
        
        for i in range(num_intervalos):
            val_inf = bins[i]
            val_sup = bins[i+1]
            
            # Pega exatamente a cor da i-ésima classe criada
            r, g, b, _ = colormap(i)
            cor_rgb = f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})"
            
            if val_sup.is_integer() and val_inf.is_integer():
                label_classe = f"{int(val_inf)} – {int(val_sup)}"
            else:
                label_classe = f"{val_inf:.1f} – {val_sup:.1f}"
            
            bloco = f"""
            <div style="flex: 1; text-align: center; margin: 0 2px;">
                <div style="background: {cor_rgb}; height: 16px; border-radius: 3px; border: 1px solid #666; box-shadow: inset 0 1px 2px rgba(0,0,0,0.15);"></div>
                <span style="font-size: 10px; color: #333; font-family: -apple-system, sans-serif; display: block; margin-top: 4px; font-weight: 500;">{label_classe}</span>
            </div>
            """
            blocos_html.append(bloco)
            
        legenda_blocos = "".join(blocos_html)
        unidade_legenda = f" ({unidade})" if unidade else ""
        
        html_legenda = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 10px 12px; background: rgba(248, 248, 248, 0.95); border-radius: 6px; border: 1px solid #dcdcdc; box-sizing: border-box;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; font-weight: 600; color: #222;">
                <span>Scale{unidade_legenda}: {label_legenda}</span>
                <span style="font-weight: normal; color: #666; font-size: 11px;">Jenks (5 Classes) | Max: {vmax:.1f}</span>
            </div>
            <div style="display: flex; width: 100%;">
                {legenda_blocos}
            </div>
        </div>
        """
        
        components.html(html_legenda, height=90)
    
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
        m6.metric("Total Count", f"{int(serie_limpa.count()):,}")
        
        # --- CAIXA DE TEXTO FIXA ---
        with st.container(border=False):
            st.markdown("About the Database")
            st.markdown("""
            - **Spatial Resolution:** Hexagonal grid H3 Resolution 9 (the hexagons are approximately 200m on each side)
            - **Scope:** Municipality of Curitiba / Urban Limits
            - **Linear Systems:** Main roads and public transport layers can be activated via the side menu to provide context for urban corridors
            - **POI:** Includes eating, shopping and entertainment activities
            - **Data:** IPPUC / Municipal open data (2023–2026) and OpenStreetMap Data
            """)
