import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="Engenharia Inteligente | Dashboard de Medição",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Themes & Aesthetics ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #ff4b4b;
    }
    .stAlert {
        border-radius: 10px;
    }
    .main {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def carregar_dados(file):
    try:
        if file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        return df
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return None

def mapear_colunas_inteligentes(columns):
    mapping = {"data": None, "medicao": None, "valor": None}
    
    keywords = {
        "data": ["data", "date", "periodo", "mes", "mês"],
        "medicao": ["medicao", "medição", "quantidade", "qty", "amount", "medido"],
        "valor": ["valor", "preço", "custo", "total", "price", "value"]
    }
    
    for col in columns:
        col_lower = col.lower()
        for key, words in keywords.items():
            if mapping[key] is None and any(word in col_lower for word in words):
                mapping[key] = col
                
    return mapping

def main():
    st.title("🏗️ Engenharia Inteligente")
    st.subheader("O marco da medição automatizada")

    # --- Sidebar ---
    with st.sidebar:
        st.header("📂 Entrada de Dados")
        uploaded_file = st.file_uploader("Upload da Planilha de Medição", type=["xlsx", "csv"])
        st.info("O sistema fará o trabalho pesado de análise automaticamente.")
        
        if uploaded_file:
            st.divider()
            st.markdown("### Configurações de Exibição")
            theme_color = st.color_picker("Cor Principal do Projeto", "#ff4b4b")

    if uploaded_file:
        df = carregar_dados(uploaded_file)
        
        if df is not None:
            # 1. Smart Mapping
            mapping = mapear_colunas_inteligentes(df.columns)
            
            # Allow manual override if needed but with smart defaults
            with st.expander("⚙️ Ajuste de Mapeamento (Opcional)"):
                col_data = st.selectbox("Coluna de Data/Tempo", df.columns, index=list(df.columns).index(mapping["data"]) if mapping["data"] in df.columns else 0)
                col_med = st.selectbox("Coluna de Medição", df.columns, index=list(df.columns).index(mapping["medicao"]) if mapping["medicao"] in df.columns else 0)
                col_val = st.selectbox("Coluna de Valor (R$)", df.columns, index=list(df.columns).index(mapping["valor"]) if mapping["valor"] in df.columns else 0)

            # 2. KPI Section (The "Heavy Lifting")
            st.markdown("### 📊 Painel Executivo")
            
            total_medido = df[col_med].sum()
            total_valor = df[col_val].sum() if col_val in df.columns else 0
            media_medicao = df[col_med].mean()
            
            # Trend calculation
            if len(df) >= 2:
                last_val = df[col_med].iloc[-1]
                prev_val = df[col_med].iloc[-2]
                delta = ((last_val - prev_val) / prev_val) * 100 if prev_val != 0 else 0
            else:
                delta = 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Medido", f"{total_medido:,.2f}", help="Soma total de todas as medições")
            m2.metric("Valor Total", f"R$ {total_valor:,.2f}")
            m3.metric("Média/Período", f"{media_medicao:,.2f}")
            m4.metric("Tendência (Última)", f"{delta:+.1f}%", delta=f"{delta:.1f}%")

            # 3. Main Visualizations
            st.divider()
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.markdown("### 📈 Evolução da Medição")
                fig_line = px.area(
                    df, x=col_data, y=col_med, 
                    title="Curva de Avanço",
                    template="plotly_dark",
                    color_discrete_sequence=[theme_color]
                )
                fig_line.update_layout(hovermode="x unified", xaxis_title=None, yaxis_title="Quantidade")
                st.plotly_chart(fig_line, use_container_width=True)

            with c2:
                st.markdown("### 🎯 Meta vs Realizado")
                # Simple gauge or progress tracker
                target = st.number_input("Definir Meta Total", value=float(total_medido * 1.2), step=100.0)
                progress = min(total_medido / target, 1.0) if target > 0 else 0
                
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = total_medido,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Progresso do Projeto", 'font': {'size': 24}},
                    delta = {'reference': target, 'increasing': {'color': "RebeccaPurple"}},
                    gauge = {
                        'axis': {'range': [None, target]},
                        'bar': {'color': theme_color},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, target * 0.5], 'color': '#262730'},
                            {'range': [target * 0.5, target * 0.9], 'color': '#31333F'}
                        ],
                    }
                ))
                fig_gauge.update_layout(template="plotly_dark", height=300, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            # 4. Detailed Comparison Tool
            st.divider()
            st.markdown("### ⚖️ Ferramenta de Comparação Rápida")
            comp_col1, comp_col2, comp_col3 = st.columns([1, 1, 2])
            
            with comp_col1:
                c_atual = st.number_input("Medição Atual", value=float(last_val) if len(df) > 0 else 0.0)
            with comp_col2:
                c_anterior = st.number_input("Medição Anterior", value=float(prev_val) if len(df) > 1 else 0.0)
            
            with comp_col3:
                diff = c_atual - c_anterior
                perc = (diff / c_anterior) * 100 if c_anterior != 0 else 0
                if diff >= 0:
                    st.success(f"Aumento de **{diff:,.2f}** units (+{perc:.1f}%)")
                else:
                    st.warning(f"Redução de **{abs(diff):,.2f}** units ({perc:.1f}%)")

            # 5. Data Explorer
            with st.expander("🔍 Explorar Dados Completos"):
                st.dataframe(df, use_container_width=True)

    else:
        # Welcome Screen
        st.write("---")
        st.info("👋 **Bem-vindo à Engenharia Inteligente.** Para começar, suba sua planilha de medição no menu lateral.")
        
        # Engineering Mockup / Preview
        st.markdown("""
        ### O que esta ferramenta faz por você:
        - **Mapeia Sozinha**: Identifica datas, quantidades e valores.
        - **Calcula Tendências**: Mostra automaticamente se o projeto está acelerando ou atrasando.
        - **Visão Executiva**: Gera KPIs prontos para relatórios de diretoria.
        - **Elimina Erros**: Processamento matemático preciso sem fórmulas de Excel complexas.
        """)
        
        # Example of how to structure the excel
        st.caption("Dica: Use colunas com nomes simples como 'Data', 'Medição' e 'Valor'.")

if __name__ == "__main__":
    main()
