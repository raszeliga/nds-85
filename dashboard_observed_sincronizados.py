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
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
import json

def render_observed_sincronizados():
    st.set_page_config(layout="wide")
    st.title("NDS Speed Viewer - Comparison Mode")
    st.subheader("See descriptive statistics below the maps")

    # 1. Carregamento dos Dados
    @st.cache_data
    def carregar_camada(caminho_gpkg):
        gdf = gpd.read_file(caminho_gpkg)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        return gdf

    caminho_hex = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/gdf_dash_observed.gpkg"
    caminho_limite = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/bairros_dissolvido.gpkg"
    caminho_bairros = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/divisa_bairros_2.gpkg"
    caminho_biarticulado = "https://github.com/raszeliga/nds-85/raw/refs/heads/main/rota_bi-articulados_dissolv_v2.gpkg"
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

    # 2. Sidebar
    colunas_numericas = list(gdf_hex.select_dtypes(include=[np.number]).columns)
    if not colunas_numericas:
        st.error("Nenhuma coluna numérica encontrada no arquivo GPKG")
        st.stop()

    st.sidebar.header("Variable Selection")
    coluna_esq = st.sidebar.selectbox("Left Map Variable:", colunas_numericas, index=0)
    idx_padrao_dir = 1 if len(colunas_numericas) > 1 else 0
    coluna_dir = st.sidebar.selectbox("Right Map Variable:", colunas_numericas, index=idx_padrao_dir)

    st.sidebar.markdown("---")
    st.sidebar.header("Layer Styling")
    opacidade_pct = st.sidebar.slider("Hexagon Opacity (%)", min_value=0, max_value=100, value=65, step=5)

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

    # 3. Preparação das cores e dados geográficos
    N_CLASSES = 5
    colormap = plt.colormaps["YlOrRd"]
    cores_rgba = [colormap((i + 0.5) / N_CLASSES) for i in range(N_CLASSES)]
    cores_hex = [mcolors.to_hex(cor) for cor in cores_rgba]

    bounds = gdf_limite.total_bounds
    centro_lat = (bounds[1] + bounds[3]) / 2
    centro_lon = (bounds[0] + bounds[2]) / 2

    # Exportar apenas as geometrias e colunas necessárias para o GeoJSON (otimiza render)
    gdf_hex_export = gdf_hex[['geometry', coluna_esq, coluna_dir]].copy()
    geojson_hex = gdf_hex_export.to_json()
    geojson_limite = gdf_limite[['geometry']].to_json()

    # Camadas opcionais
    json_biart = gdf_biarticulado[['geometry']].to_json() if mostrar_biarticulado else "null"
    json_lv = gdf_linha_verde[['geometry']].to_json() if mostrar_linha_verde else "null"
    json_cont = gdf_contorno[['geometry']].to_json() if mostrar_contorno else "null"
    json_277 = gdf_277[['geometry']].to_json() if mostrar_277 else "null"
    json_comend = gdf_comend[['geometry']].to_json() if mostrar_comend else "null"
    json_bairros = gdf_bairros[['geometry']].to_json() if mostrar_bairros else "null"

# --- 4. MAPAS SINCRONIZADOS VIA LEAFLET.SYNC COM GESTÃO DE TOOLTIPS ---
    map_sync_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.sync@0.2.4/L.Map.Sync.js"></script>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            .map-container {{
                display: flex;
                width: 100%;
                height: 520px;
                gap: 16px;
                box-sizing: border-box;
            }}
            .map-panel {{
                flex: 1;
                height: 100%;
                position: relative;
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid #d0d0d0;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .map-div {{
                width: 100%;
                height: 100%;
            }}
            .map-header {{
                position: absolute;
                top: 10px;
                left: 50px;
                z-index: 1000;
                background: rgba(255, 255, 255, 0.92);
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid #ccc;
                box-shadow: 0 1px 2px rgba(0,0,0,0.15);
            }}
            /* Impede que o tooltip capture o mouse e cause acúmulo */
            .leaflet-tooltip {{
                pointer-events: none !important;
                font-size: 11px !important;
                padding: 4px 8px !important;
                border-radius: 4px !important;
            }}
        </style>
    </head>
    <body>
        <div class="map-container">
            <div class="map-panel">
                <div class="map-header">Left: {coluna_esq}</div>
                <div id="map-left" class="map-div"></div>
            </div>
            <div class="map-panel">
                <div class="map-header">Right: {coluna_dir}</div>
                <div id="map-right" class="map-div"></div>
            </div>
        </div>

        <script>
            const coresHex = {json.dumps(cores_hex)};
            const opacidade = {opacidade_pct / 100.0};

            function getColor(val) {{
                if (val === null || val === undefined || isNaN(val)) return '#B4B4B4';
                if (val <= 20) return coresHex[0];
                if (val <= 30) return coresHex[1];
                if (val <= 40) return coresHex[2];
                if (val <= 50) return coresHex[3];
                return coresHex[4];
            }}

            const tileUrl = 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}';
            const tileAttribution = 'Tiles &copy; Esri';

            // 1. Inicializar os dois mapas
            const mapL = L.map('map-left', {{ zoomControl: true, zoomSnap: 0.25 }}).setView([{centro_lat}, {centro_lon}], 11);
            const mapR = L.map('map-right', {{ zoomControl: true, zoomSnap: 0.25 }}).setView([{centro_lat}, {centro_lon}], 11);

            L.tileLayer(tileUrl, {{ maxZoom: 16, attribution: tileAttribution }}).addTo(mapL);
            L.tileLayer(tileUrl, {{ maxZoom: 16, attribution: tileAttribution }}).addTo(mapR);

            // 2. Sincronização mútua com leaflet.sync
            mapL.sync(mapR);
            mapR.sync(mapL);

            // Controle de estado durante arraste do mapa
            let isDragging = false;

            function clearTooltips() {{
                mapL.eachLayer(l => {{ if (l.closeTooltip) l.closeTooltip(); }});
                mapR.eachLayer(l => {{ if (l.closeTooltip) l.closeTooltip(); }});
            }}

            [mapL, mapR].forEach(m => {{
                m.on('dragstart movestart', () => {{
                    isDragging = true;
                    clearTooltips();
                }});
                m.on('dragend moveend', () => {{
                    isDragging = false;
                    clearTooltips();
                }});
            }});

            const hexData = {geojson_hex};
            const limiteData = {geojson_limite};

            // Hexágonos - Painel Esquerdo
            L.geoJSON(hexData, {{
                style: function(feat) {{
                    const val = feat.properties['{coluna_esq}'];
                    return {{
                        fillColor: getColor(val),
                        weight: 0.5,
                        opacity: 0.6,
                        color: '#B4B4B4',
                        fillOpacity: opacidade
                    }};
                }},
                onEachFeature: function(feat, layer) {{
                    const v = feat.properties['{coluna_esq}'];
                    const txt = (v !== null && v !== undefined) ? v.toFixed(2) : 'N/A';
                    
                    layer.bindTooltip('<b>{coluna_esq}:</b> ' + txt + ' km/h', {{
                        sticky: true,
                        direction: 'top',
                        offset: [0, -10]
                    }});

                    layer.on({{
                        mouseover: function(e) {{
                            if (isDragging) {{
                                this.closeTooltip();
                            }}
                        }},
                        mouseout: function(e) {{
                            this.closeTooltip();
                        }}
                    }});
                }}
            }}).addTo(mapL);

            // Hexágonos - Painel Direito
            L.geoJSON(hexData, {{
                style: function(feat) {{
                    const val = feat.properties['{coluna_dir}'];
                    return {{
                        fillColor: getColor(val),
                        weight: 0.5,
                        opacity: 0.6,
                        color: '#B4B4B4',
                        fillOpacity: opacidade
                    }};
                }},
                onEachFeature: function(feat, layer) {{
                    const v = feat.properties['{coluna_dir}'];
                    const txt = (v !== null && v !== undefined) ? v.toFixed(2) : 'N/A';
                    
                    layer.bindTooltip('<b>{coluna_dir}:</b> ' + txt + ' km/h', {{
                        sticky: true,
                        direction: 'top',
                        offset: [0, -10]
                    }});

                    layer.on({{
                        mouseover: function(e) {{
                            if (isDragging) {{
                                this.closeTooltip();
                            }}
                        }},
                        mouseout: function(e) {{
                            this.closeTooltip();
                        }}
                    }});
                }}
            }}).addTo(mapR);

            // Limite Municipal
            const styleLimite = {{ color: '#1E1E1E', weight: 1.5, fill: false }};
            L.geoJSON(limiteData, {{ style: styleLimite }}).addTo(mapL);
            L.geoJSON(limiteData, {{ style: styleLimite }}).addTo(mapR);

            // Camadas lineares auxiliares
            function addCorridor(jsonData, color, weight) {{
                if (!jsonData) return;
                const style = {{ color: color, weight: weight, fill: false }};
                L.geoJSON(jsonData, {{ style: style }}).addTo(mapL);
                L.geoJSON(jsonData, {{ style: style }}).addTo(mapR);
            }}

            addCorridor({json_biart}, '#D00000', 2.5);
            addCorridor({json_lv}, '#009E60', 2.5);
            addCorridor({json_cont}, '#696969', 2.0);
            addCorridor({json_277}, '#5E17EB', 2.0);
            addCorridor({json_comend}, '#1C1C1E', 2.0);
            addCorridor({json_bairros}, 'rgba(90,90,90,0.7)', 1.0);
        </script>
    </body>
    </html>
    """

    # Renderiza o container com os dois mapas sincronizados
    components.html(map_sync_html, height=530)

    # --- 5. LEGENDAS, DISTRIBUIÇÕES E ESTATÍSTICAS ---
    def render_legenda(coluna_nome):
        faixas = ["≤ 20", "20 – 30", "30 – 40", "40 – 50", "> 50"]
        cores_str = [f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})" for r, g, b, _ in cores_rgba]
        blocos = "".join([
            f"""<div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 5px;">
                <div style="width: 100%; height: 18px; background-color: {cor}; border-radius: 4px; border: 1px solid rgba(0, 0, 0, 0.45); box-sizing: border-box;"></div>
                <span style="font-size: 11px; color: #222; font-family: sans-serif; white-space: nowrap;">{f}</span>
            </div>""" for cor, f in zip(cores_str, faixas)
        ])
        return f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 10px 14px; background: #fbfbfb; border-radius: 8px; border: 1px solid #d0d0d0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: #1c1c1e;">Scale (km/h): {coluna_nome}</span>
                <span style="font-size: 11px; color: #666;">Fixed (5 Classes)</span>
            </div>
            <div style="display: flex; gap: 8px; width: 100%;">{blocos}</div>
        </div>
        """

    def gerar_grafico_distribuicao(serie_limpa, coluna_nome):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.25, 0.75], vertical_spacing=0.03)
        fig.add_trace(go.Box(x=serie_limpa, name="", orientation="h", fillcolor="rgba(253, 174, 107, 0.65)", line=dict(color="#1a1a1a", width=1.0), boxpoints="outliers", jitter=0.15, marker=dict(color="#1a1a1a", size=3.5, opacity=0.75), showlegend=False), row=1, col=1)
        fig.add_trace(go.Histogram(x=serie_limpa, name="Frequency", marker_color="#fdae6b", opacity=0.85, marker_line=dict(color="#333333", width=0.6), xbins=dict(start=np.floor(serie_limpa.min()), end=np.ceil(serie_limpa.max()), size=2.0), showlegend=False), row=2, col=1)

        media_val, mediana_val = serie_limpa.mean(), serie_limpa.median()
        fig.add_vline(x=media_val, line_width=1.5, line_dash="dash", line_color="#2b83ba", annotation_text=f"Mean: {media_val:.1f}", annotation_position="top left", row=2, col=1)
        fig.add_vline(x=mediana_val, line_width=1.5, line_dash="dot", line_color="#008837", annotation_text=f"Median: {mediana_val:.1f}", annotation_position="top right", row=2, col=1)
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=15, b=20), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", bargap=0.05)
        fig.update_yaxes(showticklabels=False, row=1, col=1)
        fig.update_yaxes(title_text="Frequency", gridcolor="rgba(200, 200, 200, 0.25)", row=2, col=1)
        fig.update_xaxes(title_text=coluna_nome, dtick=10, gridcolor="rgba(200, 200, 200, 0.25)", row=2, col=1)
        return fig

    def renderizar_estatisticas(coluna_nome):
        components.html(render_legenda(coluna_nome), height=90)
        st.markdown(f"#### Distribution: {coluna_nome}")
        dados = gdf_hex[coluna_nome]
        limpos = dados.dropna()

        st.plotly_chart(gerar_grafico_distribuicao(limpos, coluna_nome), use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Mean", f"{limpos.mean():.2f}")
        m2.metric("Median", f"{limpos.median():.2f}")
        m3.metric("St Dv", f"{limpos.std():.2f}")

        m4, m5, m6 = st.columns(3)
        m4.metric("Minimum", f"{limpos.min():.2f}")
        m5.metric("Maximum", f"{limpos.max():.2f}")
        m6.metric("Null", f"{dados.isna().sum()}")

    col_esq, col_dir = st.columns(2, gap="large")
    with col_esq:
        renderizar_estatisticas(coluna_esq)
    with col_dir:
        renderizar_estatisticas(coluna_dir)

    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.25rem !important; line-height: 1.2 !important; }
        [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
        </style>
    """, unsafe_allow_html=True)
    
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
        render_observed_sincronizados()