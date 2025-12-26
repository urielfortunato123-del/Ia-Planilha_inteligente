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
    mapping = {"data": None, "medicao": None, "valor": None}
    
    keywords = {
        "data": ["data", "date", "periodo", "mes", "mês"],
        "medicao": ["medicao", "medição", "quantidade", "qty", "amount", "medido"],
        "valor": ["valor", "preço", "custo", "total", "price", "value"]
    }
    
    for col in columns:
        col_str = str(col)
        col_lower = col_str.lower()
        for key, words in keywords.items():
            if mapping[key] is None and any(word in col_lower for word in words):
                mapping[key] = col
                
    return mapping

def main():
    st.title("🏗️ Engenharia Inteligente")
    st.subheader("O marco da medição automatizada")

    # --- Session State for Real-Time Agility ---
    if 'extra_data' not in st.session_state:
        st.session_state['extra_data'] = pd.DataFrame()

    # --- Sidebar ---
    with st.sidebar:
        st.header("📂 Entrada de Dados")
        uploaded_file = st.file_uploader("Upload da Planilha de Medição", type=["xlsx", "csv"])
        
        if uploaded_file:
            st.divider()
            st.markdown("### ⚡ Centro de Agilidade")
            with st.expander("➕ Lançamento Rápido (Campo)"):
                st.write("Adicione medições sem abrir o Excel.")
                with st.form("quick_entry"):
                    new_date = st.date_input("Data da Medição")
                    new_med = st.number_input("Quantidade Medida", min_value=0.0)
                    new_val = st.number_input("Valor (R$)", min_value=0.0)
                    submit = st.form_submit_button("Lançar Medição")
                    
                    if submit:
                        new_row = pd.DataFrame([{
                            "Data": new_date.strftime("%Y-%m-%d"),
                            "Medição": new_med,
                            "Valor": new_val
                        }])
                        st.session_state['extra_data'] = pd.concat([st.session_state['extra_data'], new_row], ignore_index=True)
                        st.success("Lançamento concluído!")
            
            do_audit = st.toggle("🔍 Auditoria Inteligente (Beta)", value=True, help="Detecta anomalias e erros de digitação automaticamente.")
            
            st.divider()
            st.markdown("### 🎨 Visual")
            theme_color = st.color_picker("Cor Principal do Projeto", "#ff4b4b")

    if uploaded_file:
        raw_df = carregar_dados(uploaded_file)
        
        if raw_df is not None:
            # Merge with session data for immediate agility
            if not st.session_state['extra_data'].empty:
                # Map session data columns to match raw_df if possible
                mapping_temp = mapear_colunas_inteligentes(raw_df.columns)
                mapped_extra = st.session_state['extra_data'].copy()
                mapped_extra.columns = [mapping_temp['data'] or 'Data', mapping_temp['medicao'] or 'Medição', mapping_temp['valor'] or 'Valor']
                df = pd.concat([raw_df, mapped_extra], ignore_index=True)
            else:
                df = raw_df

            # 1. Smart Mapping
            mapping = mapear_colunas_inteligentes(df.columns)
            
            # Allow manual override if needed but with smart defaults
            with st.expander("⚙️ Ajuste de Mapeamento (Opcional)"):
                col_data = st.selectbox("Coluna de Data/Tempo", df.columns, index=list(df.columns).index(mapping["data"]) if mapping["data"] in df.columns else 0)
                col_med = st.selectbox("Coluna de Medição", df.columns, index=list(df.columns).index(mapping["medicao"]) if mapping["medicao"] in df.columns else 0)
                col_val = st.selectbox("Coluna de Valor (R$)", df.columns, index=list(df.columns).index(mapping["valor"]) if mapping["valor"] in df.columns else 0)

            # --- SMART AUDIT LAYER ---
            if do_audit:
                anomalies = []
                mean_med = df[col_med].mean()
                std_med = df[col_med].std()
                
                # Check for outliers (> 2 standard deviations)
                outliers = df[df[col_med] > (mean_med + 2 * std_med)]
                if not outliers.empty:
                    anomalies.append(f"🚩 **Atenção**: Detectadas {len(outliers)} medições suspeitas (muito acima da média).")
                
                # Check for negative values
                negatives = df[df[col_med] < 0]
                if not negatives.empty:
                    anomalies.append(f"⚠️ **Erro Crítico**: Existem {len(negatives)} valores negativos na coluna de medição.")

                if anomalies:
                    with st.container():
                        st.warning("🩺 **Diagnóstico de Auditoria**")
                        for a in anomalies:
                            st.write(a)
                        st.caption("Agilidade é focar no que precisa de correção.")

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
                target = st.number_input("Definir Meta Total", value=float(total_medido * 1.2) if total_medido > 0 else 1000.0, step=100.0)
                
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

            # 5. Gemini AI Analysis Section
            st.divider()
            st.markdown("### 🤖 Assistente de Engenharia (IA)")
            
            if model:
                user_question = st.text_input("💬 Pergunte algo sobre os dados (ex: 'Qual a projeção para o próximo mês?')")
                
                if st.button("Consultar Especialista"):
                    with st.spinner("Analisando..."):
                        try:
                            # Context with data for AI
                            dataset_summary = df.tail(10).to_string() # Envia as últimas 10 linhas como contexto
                            context = f"""
                            Você é o Assistente de Engenharia Inteligente.
                            DADOS DO PROJETO:
                            - Total Medido: {total_medido:,.2f}
                            - Valor Total: R$ {total_valor:,.2f}
                            - Meta: {target:,.2f}
                            - Últimas Medições:
                            {dataset_summary}
                            
                            PERGUNTA DO USUÁRIO: {user_question if user_question else "Faça uma análise geral da saúde do projeto."}
                            
                            Responda de forma técnica, porém ágil e direta. Se houver riscos, aponte-os.
                            """
                            response = model.generate_content(context)
                            st.info("💡 Insight da IA")
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"Erro na consulta: {e}")
            else:
                st.warning("⚠️ Configure 'GOOGLE_API_KEY' para ativar o assistente.")

            # 6. Data Explorer
            with st.expander("🔍 Explorar Dados Completos"):
                if not st.session_state['extra_data'].empty:
                    st.write("Incluindo lançamentos rápidos feitos nesta sessão.")
                st.dataframe(df, use_container_width=True)

    else:
        # Welcome Screen
        st.write("---")
        st.info("👋 **Canteiro de Obras Digital.** Suba sua planilha ou comece a lançar dados.")
        
        st.markdown("""
        ### Foco em Agilidade Real:
        - **Smart Audit**: Detecta erros de digitação e desvios de medição na hora.
        - **Lançamento Direto**: Adicione dados pelo celular sem abrir o Excel.
        - **Assistente IA**: Pergunte sobre o projeto e receba respostas baseadas nos dados.
        """)
        st.caption("Dica: Use colunas com nomes simples como 'Data', 'Medição' e 'Valor'.")

if __name__ == "__main__":
    main()
