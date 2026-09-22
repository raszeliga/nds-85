#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  8 16:51:41 2026

@author: rafaelszeliga
"""
# verificar https://www.kaggle.com/code/illiyask/decision-tree-regressor
# https://www.kaggle.com/code/aakaashjois/simple-random-forest-regression

### Análise considerando as variáveis expicativas:
# "V85_on" --> excluído
# 'populacao_h3',
# 'domicilios_h3',
# 'stop_g1',
# 'crosswalk_zebra',
# 'roadbump_g2',
# 'traffic_signals',
# 'speed_cameras',
# 'pontosLinha',
# 'cruzamentos',
# 'HMP',
# 'VMP

###################################################
## Considerando uma Árvore de Decisão Regression ##
###################################################

### Ao final esse arquivo utiliza o kfold para analisar os daodos ###

import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
import seaborn as sns


# arquivo oriundo do script 7b contem as células que tem registro nds (excluindo a v85_on)
# arquivo grade_h9_DT_nds: /Users/rafaelszeliga/Library/CloudStorage/OneDrive-Pessoal/PósGrad/2023 PPGCG/Artigo_2025/Decision_Tree/grade_h9_DT_nds.gpkg
# arquivo completo: /Users/rafaelszeliga/Library/CloudStorage/OneDrive-Pessoal/PósGrad/2023 PPGCG/Artigo_2025/Decision_Tree/grade_h9_DT.gpkg
# PREPARAR ARQUIVO SÓ COM A REGIONAL MATRIZ PARA TESTAR
# arquivo regional matriz: /Users/rafaelszeliga/Library/CloudStorage/OneDrive-Pessoal/PósGrad/2023 PPGCG/Artigo_2025/Decision_Tree/grade_h9_DT_regional_matriz.gpkg
# arquivo regional matriz atualizado /Users/rafaelszeliga/Library/CloudStorage/OneDrive-Pessoal/PósGrad/2023 PPGCG/Artigo_2025/Decision_Tree/grade_h9_DT_regional_matriz_v3.gpkg
# grade_h9_DT
gdf = gpd.read_file(
    '/Users/rafaelszeliga/Library/CloudStorage/OneDrive-Pessoal/PósGrad/2023 PPGCG/Artigo_2025/Decision_Tree/grade_h9_DT_nds_v3.gpkg'
    )

print('The dataset has {} rows.'.format(len(gdf)))
print('The dataset has {} columns'.format(gdf.columns))

print(gdf.info())

print(gdf.isnull().any())

gdf2 = gdf.drop(columns=['geometry', 'h3_id', 'V85_nds_manha', 'V85_nds_noite']).copy() # escolher apenas uma das variáveis nds para manter

gdf2.columns
print(gdf2.isnull().any())

# tem que tirar os valores nulos
gdf2['HMP'].isna().sum()
gdf2['VMP'].isna().sum()

gdf2.dropna(subset=['HMP'], inplace = True)
gdf2.dropna(subset=['VMP'], inplace = True)

gdf2['HMP'].isna().sum()
gdf2['VMP'].isna().sum()

# V85_nds_tarde ainda tem valores nulos. São eles que queremos inferir os valores. Separar linhas com valor conhecido das linhas para inferência
mask_nulo = gdf2["V85_nds_tarde"].isna()
dados_rotulados = gdf2[~mask_nulo].copy()
dados_inferir = gdf2[mask_nulo].copy()


# Checking the correlation between all the features
sns.heatmap(dados_rotulados.corr(), annot=True)
sns.pairplot(dados_rotulados.drop(columns='V85_nds_tarde'))

# Variáveis explicativas
X = dados_rotulados.drop(columns=["V85_nds_tarde"]).copy()
X.columns

# Variável resposta
y = dados_rotulados["V85_nds_tarde"].copy()

X_inferir = dados_inferir.drop(columns=["V85_nds_tarde"]).copy()

# Divisão de treino e teste
X_train, X_test, y_train, y_test = train_test_split(X,
                                                    y,
                                                    random_state=42,
                                                    test_size=0.2)

X_train.describe()

# Treinar a Árvore de Decisão
# max_depth evita que a árvore decore os dados (overfitting)
dt = DecisionTreeRegressor(
    max_depth=4,  # Reduz a profundidade máxima
    min_samples_leaf=20,  # Exige pelo menos 20 vias por folha
    min_samples_split=40,  # Exige pelo menos 40 vias para permitir corte
    random_state=42,
)

dt.fit(X_train, y_train)

# Avaliação rápida no conjunto de teste
y_pred_test = dt.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
r2 = r2_score(y_test, y_pred_test)

print(f"RMSE (Teste): {rmse:.2f}")
print(f"R² (Teste): {r2:.2f}")

# Avaliar no treino para comparar
y_pred_train = dt.predict(X_train)
r2_train = r2_score(y_train, y_pred_train)
rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))

print(f"Treino -> R²: {r2_train:.2f} | RMSE: {rmse_train:.2f}")
print(f"Teste  -> R²: {r2:.2f} | RMSE: {rmse:.2f}")

# Inferência nos dados sem resposta
X_inferir = dados_inferir.drop(columns=["V85_nds_tarde"])

 # Treinar a Random Forest
rf = RandomForestRegressor(
    n_estimators=300,
    max_depth=10,
    min_samples_leaf=10,
    max_features="sqrt",
    random_state=42,
    n_jobs=-1,
)

# Treinar a Random Forest
# rf = RandomForestRegressor(
#    n_estimators=400,
#    max_depth=12,
#    min_samples_leaf=5,
#    max_features=0.4, # Avalia 40% das variáveis a cada nó
#    random_state=42,
#    n_jobs=-1,
#)

rf.fit(X_train, y_train)

# Predição no teste Random Forest
y_pred_rf = rf.predict(X_test)

# Mëtricas
# 1. Gerar predições para ambos os conjuntos
y_pred_train_rf = rf.predict(X_train)
y_pred_test_rf = rf.predict(X_test)

# 2. Métricas de Treino
r2_train = r2_score(y_train, y_pred_train_rf)
rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train_rf))
mae_train = mean_absolute_error(y_train, y_pred_train_rf)

# 3. Métricas de Teste
r2_test = r2_score(y_test, y_pred_test_rf)
rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test_rf))
mae_test = mean_absolute_error(y_test, y_pred_test_rf)

# 4. Exibição comparativa
print(f"--- Random Forest: TREINO ---")
print(f"R²:   {r2_train:.2f}")
print(f"RMSE: {rmse_train:.2f} km/h")
print(f"MAE:  {mae_train:.2f} km/h\n")

print(f"--- Random Forest: TESTE ---")
print(f"R²:   {r2_test:.2f}")
print(f"RMSE: {rmse_test:.2f} km/h")
print(f"MAE:  {mae_test:.2f} km/h")

# Gerar inferências para os trechos sem medição
predicoes_dt = dt.predict(X_inferir)
predicoes_rf = rf.predict(X_inferir)

# Criar o novo GeoDataFrame preservando o original intacto
gdf_completo = gdf.copy()

# Inicializa as duas novas colunas com os valores originais conhecidos
gdf_completo["V85_nds_tarde_DT"] = gdf_completo["V85_nds_tarde"]
gdf_completo["V85_nds_tarde_RF"] = gdf_completo["V85_nds_tarde"]

# Preenche os nulos de cada coluna com a respectiva predição
gdf_completo.loc[dados_inferir.index, "V85_nds_tarde_DT"] = predicoes_dt
gdf_completo.loc[dados_inferir.index, "V85_nds_tarde_RF"] = predicoes_rf

# (Opcional) Indicador da origem da linha
gdf_completo["origem_dado"] = "original"
gdf_completo.loc[dados_inferir.index, "origem_dado"] = "inferido"

# Comparar as predições geradas pelos dois modelos nas linhas inferidas
print(
    gdf_completo.loc[
        dados_inferir.index, ["V85_nds_tarde_DT", "V85_nds_tarde_RF"]
    ].head(10)
)

# Visualizar a Árvore
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree

# Ajuste o tamanho da figura conforme a profundidade da sua árvore
plt.figure(figsize=(20, 10))

plot_tree(
    dt,
    feature_names=X.columns,  # Nome das variáveis explicativas
    filled=True,  # Colore os nós indicando a média da predição
    rounded=True,  # Deixa os nós com cantos arredondados
    fontsize=10,
    max_depth=3,  # Opcional: limite a exibição se a árvore for muito profunda
)

plt.title("Visualização da Árvore de Decisão", fontsize=14)
plt.tight_layout()
plt.show()

from sklearn.tree import export_text

regras_texto = export_text(dt, feature_names=list(X.columns))
print(regras_texto)

gdf_completo['V85_nds_tarde'].isna().sum()

# salvar o resultado
gdf_completo.to_file(
    '/Users/rafaelszeliga/Library/CloudStorage/OneDrive-Pessoal/PósGrad/2023 PPGCG/Artigo_2025/Decision_Tree/grade_h9_DT_nds_v3_dados_inferidos_DT_RF.gpkg',
    driver="GPKG"
)

# Ainda é possível alterar os parâmetros da árvore #


gdf_completo.columns

# Validação cruzada de 5 folds comparando a média e o desvio padrão do R2
from sklearn.model_selection import cross_val_score

# Modelo A (mais regularizado)
rf_A = RandomForestRegressor(
    n_estimators=300,
    max_depth=10,
    min_samples_leaf=10,
    max_features="sqrt",
    random_state=42,
    n_jobs=-1,
)

# Modelo B (mais flexível)
rf_B = RandomForestRegressor(
    n_estimators=400,
    max_depth=12,
    min_samples_leaf=5,
    max_features=0.4,
    random_state=42,
    n_jobs=-1,
)

scores_A = cross_val_score(rf_A, X, y, cv=5, scoring="r2")
scores_B = cross_val_score(rf_B, X, y, cv=5, scoring="r2")

print(f"Modelo A (0.60/0.42): R² Médio = {scores_A.mean():.3f} (± {scores_A.std():.3f})")
print(f"Modelo B (0.70/0.43): R² Médio = {scores_B.mean():.3f} (± {scores_B.std():.3f})")


gdf_completo.columns
gdf_completo['V85_nds_tarde_RF'].describe()
