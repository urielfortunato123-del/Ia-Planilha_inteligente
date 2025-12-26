import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# --- AI Configuration ---
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

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
    mapping = {"data": None, "medicao": None, "valor": None, "responsavel": None, "local": None, "unidade": None}
    
    keywords = {
        "data": ["data", "date", "periodo", "mes", "mês"],
        "medicao": ["medicao", "medição", "quantidade", "qty", "amount", "medido", "qtd"],
        "valor": ["valor", "preço", "custo", "total", "price", "value"],
        "responsavel": ["responsavel", "responsável", "quem", "executado"],
        "local": ["local", "trecho", "estaca", "km"],
        "unidade": ["unidade", "un", "unid"]
    }
    
    for col in columns:
        col_str = str(col)
        col_lower = col_str.lower()
        for key, words in keywords.items():
            if mapping.get(key) is None and any(word in col_lower for word in words):
                mapping[key] = col
                
    return mapping

def carregar_planilha_completa(file):
    try:
        # Load all sheets to let user choose
        xl = pd.ExcelFile(file)
        return xl
    except Exception as e:
        st.error(f"Erro ao ler abas do Excel: {e}")
        return None

def main():
    st.title("🏗️ Engenharia Inteligente")
    st.subheader("O marco da medição automatizada")

    if 'extra_data' not in st.session_state:
        st.session_state['extra_data'] = pd.DataFrame()

    with st.sidebar:
        st.header("📂 Entrada de Dados")
        uploaded_file = st.file_uploader("Upload do Boletim (BM)", type=["xlsx", "csv"])
        
        df = None
        if uploaded_file:
            if uploaded_file.name.endswith('.xlsx'):
                xl = carregar_planilha_completa(uploaded_file)
                if xl:
                    aba = st.selectbox("Selecione a Aba (Sheet)", xl.sheet_names)
                    pular_linhas = st.number_input("Pular Linhas (Cabeçalho)", min_value=0, value=0, help="Quantas linhas do topo ignorar até o título das colunas.")
                    df = pd.read_excel(uploaded_file, sheet_name=aba, skiprows=pular_linhas)
            else:
                df = pd.read_csv(uploaded_file)

            st.divider()
            st.markdown("### ⚡ Centro de Agilidade")
            with st.expander("➕ Lançamento Rápido (Campo)"):
                with st.form("quick_entry"):
                    new_date = st.date_input("Data da Medição")
                    new_med = st.number_input("Quantidade Medida", min_value=0.0)
                    new_val = st.number_input("Valor (R$)", min_value=0.0)
                    submit = st.form_submit_button("Lançar Medição")
                    if submit:
                        new_row = pd.DataFrame([{"Data": new_date.strftime("%Y-%m-%d"), "Medição": new_med, "Valor": new_val}])
                        st.session_state['extra_data'] = pd.concat([st.session_state['extra_data'], new_row], ignore_index=True)
                        st.success("Lançamento concluído!")
            
            do_audit = st.toggle("🔍 Auditoria Inteligente", value=True)
            st.divider()
            theme_color = st.color_picker("Cor do Projeto", "#ff4b4b")

    if df is not None:
        # Extension for engineering BMs mapping
        mapping = mapear_colunas_inteligentes(df.columns)
        keywords_eng = {
            "disciplina": ["disciplina", "tipo", "grupo", "atividadeserviço", "atividade"],
            "saldo": ["saldo", "restante", "balance"],
            "acumulado": ["acumulado", "total medido", "total qty"]
        }
        for col in df.columns:
            col_lower = str(col).lower()
            for key, words in keywords_eng.items():
                if mapping.get(key) is None and any(word in col_lower for word in words):
                    mapping[key] = col

        # --- Sidebar Quick Filters ---
        with st.sidebar:
            st.divider()
            st.markdown("### 🔍 Filtros Rápidos")
            
            # Identify columns for filtering
            c_resp = mapping.get("responsavel")
            c_local = mapping.get("local")
            c_disc = mapping.get("disciplina")
            
            f_resp = "Todos"
            if c_resp in df.columns:
                unique_resp = ["Todos"] + sorted(df[c_resp].dropna().unique().tolist())
                f_resp = st.selectbox("Responsável", unique_resp)
            
            f_local = "Todos"
            if c_local in df.columns:
                unique_local = ["Todos"] + sorted(df[c_local].dropna().unique().tolist())
                f_local = st.selectbox("Local/Trecho", unique_local)

        # Apply Filters
        df_filtered = df.copy()
        if f_resp != "Todos":
            df_filtered = df_filtered[df_filtered[c_resp] == f_resp]
        if f_local != "Todos":
            df_filtered = df_filtered[df_filtered[c_local] == f_local]

        # --- Hierarchical Cleaning ---
        # Heuristic: If 'medicao' is null, it's likely a header row, not a measurement.
        c_med = mapping.get("medicao")
        c_val = mapping.get("valor")
        
        if c_med in df_filtered.columns:
            # We keep rows where measurement is NOT null or 0 (unless we are just looking at labels)
            df_active = df_filtered[df_filtered[c_med].notnull() & (pd.to_numeric(df_filtered[c_med], errors='coerce') != 0)]
        else:
            df_active = df_filtered

        with st.expander("⚙️ Ajuste de Mapeamento (Engenharia)"):
            c_data = st.selectbox("Data", df.columns, index=list(df.columns).index(mapping["data"]) if mapping.get("data") in df.columns else 0)
            c_med = st.selectbox("Medição (Qtd)", df.columns, index=list(df.columns).index(mapping["medicao"]) if mapping.get("medicao") in df.columns else 0)
            c_val = st.selectbox("Valor (R$)", df.columns, index=list(df.columns).index(mapping["valor"]) if mapping.get("valor") in df.columns else 0)
            c_disc = st.selectbox("Disciplina/Atividade", df.columns, index=list(df.columns).index(mapping["disciplina"]) if mapping.get("disciplina") in df.columns else 0)

        # 1. Audit (on full filtered data to detect errors in headers too)
        if do_audit and c_med in df_active.columns:
            try:
                valid_med = pd.to_numeric(df_active[c_med], errors='coerce').dropna()
                if not valid_med.empty:
                    mean_v = valid_med.mean()
                    std_v = valid_med.std()
                    outliers = valid_med[valid_med > (mean_v + 3 * std_v)]
                    if not outliers.empty:
                        st.warning(f"🩺 **Auditoria**: Identificamos {len(outliers)} medições com volume excepcional para os filtros selecionados.")
            except: pass

        # 2. Executive View
        st.markdown(f"### 📊 Painel: {f_resp if f_resp != 'Todos' else 'Geral'} | {f_local if f_local != 'Todos' else 'Todos Locais'}")
        try:
            total_m = pd.to_numeric(df_active[c_med], errors='coerce').sum() if c_med in df_active.columns else 0
            total_v = pd.to_numeric(df_active[c_val], errors='coerce').sum() if c_val in df_active.columns else 0
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Medido", f"{total_m:,.2f}")
            m2.metric("Valor Total", f"R$ {total_v:,.2f}")
            
            if c_disc in df_active.columns:
                n_disc = df_active[c_disc].nunique()
                m3.metric("Itens/Atividades", n_disc)
        except: st.error("Erro no cálculo dos KPIs. Verifique o mapeamento.")

        # 3. Visualizations
        st.divider()
        col_v1, col_v2 = st.columns([2, 1])
        
        with col_v1:
            st.markdown(f"### 📈 Evolução por {c_disc if c_disc in df_active.columns else 'Item'}")
            if c_disc in df_active.columns:
                # Top 10 activities by volume
                top_df = df_active.groupby(c_disc)[c_med].sum().sort_values(ascending=False).head(12).reset_index()
                fig = px.bar(top_df, x=c_disc, y=c_med, template="plotly_dark", color_discrete_sequence=[theme_color])
            else:
                fig = px.area(df_active, y=c_med, template="plotly_dark", color_discrete_sequence=[theme_color])
            st.plotly_chart(fig, use_container_width=True)

        with col_v2:
            st.markdown("### 🛠️ Composição")
            if c_disc in df_active.columns:
                fig_pie = px.pie(df_active, names=c_disc, values=c_med, hole=0.4, template="plotly_dark")
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Mapping: Atividade não identificada.")

        # 4. AI Assistant
        st.divider()
        st.markdown("### 🤖 Assistente de Engenharia")
        if model:
            q = st.text_input("💬 Pergunte sobre esta seleção (ex: 'Quanto falta de pintura no local X?')")
            if st.button("Analisar Seleção"):
                with st.spinner("O Gemini está lendo os dados filtrados..."):
                    # Send a summary of active data to AI
                    active_summary = df_active.head(20).to_string()
                    context = f"DADOS ATUAIS (FILTRADOS): {f_resp}/{f_local}. Total {total_m}. Top Itens: {active_summary}. Pergunta: {q}"
                    st.info(model.generate_content(context).text)

        with st.expander("🔍 Navegador de Dados"):
            st.dataframe(df, use_container_width=True)

    else:
        st.write("---")
        st.info("🏗️ **Pronto para analisar seu Boletim de Medição.** Suba o arquivo ao lado.")
        st.markdown("""
        **Suporte especializado para BMs de Engenharia:**
        - Seleção de qualquer aba do Excel (Boletim, Controle, Análise).
        - Ajuste dinâmico de cabeçalho (pula logos e linhas de projeto).
        - Agrupamento inteligente por Disciplina.
        """)
