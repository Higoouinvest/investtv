import streamlit as st
import pandas as pd
import time
from b3_bot import B3SimulatorBot

st.set_page_config(
    page_title="Simulador de Margem B3",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #00D084;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #00A36C;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .status-info { background-color: #e1f5fe; color: #0277bd; }
    .status-success { background-color: #e8f5e9; color: #2e7d32; }
    .status-warning { background-color: #fff3e0; color: #ef6c00; }
    .status-error { background-color: #ffebee; color: #c62828; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Simulador de Margem B3")
st.markdown("Automatize o cálculo de margem de garantia utilizando o simulador oficial da B3.")

# Sidebar Disclaimer
with st.sidebar:
    st.header("⚠️ Disclaimer")
    st.warning("""
    **Aviso Importante:**
    
    Esta ferramenta automatiza o acesso ao simulador oficial da B3 para fins de cálculo de margem de garantia.
    
    - Os resultados são estimativas e podem não refletir valores exatos
    - Use por sua conta e risco
    - Não nos responsabilizamos por decisões tomadas com base nos resultados
    - Sempre verifique os valores diretamente no site da B3
    """)
    st.info("💡 O navegador executa em modo invisível para melhor performance.")

# Always use headless mode
headless_mode = True


# Main Content
tab1, tab2 = st.tabs(["📂 Upload de Planilha", "✍️ Cadastro Manual"])

positions_to_process = []

with tab1:
    st.markdown("### Importar dados do Excel")
    uploaded_file = st.file_uploader("Escolha um arquivo Excel (.xlsx)", type="xlsx")
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            # Normalize columns
            df.columns = [c.strip() for c in df.columns]
            
            required_cols = ["Ativo", "Qtd"]
            if all(col in df.columns for col in required_cols):
                st.success(f"Arquivo carregado com sucesso! {len(df)} linhas encontradas.")
                st.dataframe(df.head())
                
                # Prepare data
                for _, row in df.iterrows():
                    qtd = row["Qtd"]
                    # Auto-detect operation type from quantity sign
                    if qtd < 0:
                        op_type = "Venda"
                    else:
                        op_type = row.get("Operação", "Compra")
                    
                    positions_to_process.append({
                        "asset": str(row["Ativo"]),
                        "quantity": abs(qtd),  # Store absolute value
                        "type": op_type
                    })
            else:
                st.error(f"Colunas obrigatórias não encontradas. O arquivo deve ter: {', '.join(required_cols)}")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

with tab2:
    st.markdown("### Adicionar Posições Manualmente")
    
    if "manual_df" not in st.session_state:
        st.session_state.manual_df = pd.DataFrame(columns=["Ativo", "Qtd", "Operação"])

    edited_df = st.data_editor(
        st.session_state.manual_df,
        num_rows="dynamic",
        column_config={
            "Ativo": st.column_config.TextColumn("Ativo (Ex: PETR4)"),
            "Qtd": st.column_config.NumberColumn("Quantidade", min_value=1, step=100),
            "Operação": st.column_config.SelectboxColumn("Operação", options=["Compra", "Venda"], required=True)
        },
        use_container_width=True
    )
    
    if not edited_df.empty:
        # Use manual data if tab2 is active or if no file uploaded
        # But logic below prioritizes file if both exist, or we can merge. 
        # For simplicity, let's use manual data only if file is not present or user is in this tab.
        # Actually, let's just overwrite positions_to_process if this tab is used last? 
        # Better: Check which tab is active? Streamlit doesn't easily give active tab.
        # Let's just append if the user clicks Start in this context.
        pass

# Action Section
st.divider()

if st.button("🚀 Iniciar Simulação", type="primary"):
    # Determine source
    final_positions = []
    
    # If file uploaded, use it. If manual data exists, use it.
    # If both, maybe warn? Let's prioritize file if uploaded, else manual.
    if uploaded_file and positions_to_process:
        final_positions = positions_to_process
        st.info("Usando dados da planilha importada.")
    elif not edited_df.empty:
        for _, row in edited_df.iterrows():
             if row["Ativo"] and row["Qtd"]:
                final_positions.append({
                    "asset": str(row["Ativo"]),
                    "quantity": row["Qtd"],
                    "type": row["Operação"]
                })
        st.info("Usando dados da tabela manual.")
    
    if not final_positions:
        st.warning("Nenhuma posição para processar. Adicione itens na tabela manual ou faça upload de uma planilha.")
    else:
        # Run Simulation
        bot = B3SimulatorBot(headless=headless_mode)
        
        progress_bar = st.progress(0)
        status_area = st.empty()
        log_area = st.container()
        
        with log_area:
            st.markdown("### Logs de Execução")
            log_text = st.empty()
            logs = []
        
        total_steps = len(final_positions) # Approximate steps for progress
        current_step = 0
        
        try:
            for event in bot.process_simulation(final_positions):
                if event["type"] == "log":
                    msg = f"[{time.strftime('%H:%M:%S')}] {event['message']}"
                    logs.append(msg)
                    # Keep only last 10 logs to avoid clutter or show all in expander
                    log_text.text_area("Log Output", "\n".join(logs[::-1]), height=200)
                    
                    # Update status banner
                    if event["level"] == "info":
                        status_area.info(event["message"])
                    elif event["level"] == "success":
                        status_area.success(event["message"])
                    elif event["level"] == "warning":
                        status_area.warning(event["message"])
                    elif event["level"] == "error":
                        status_area.error(event["message"])
                        
                elif event["type"] == "progress":
                    current_step += event["value"]
                    progress = min(current_step / total_steps, 1.0)
                    progress_bar.progress(progress)
                    
                elif event["type"] == "result":
                    st.balloons()
                    res = event["data"]
                    st.success("### Resultado da Simulação")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Risco Total Estimado", f"R$ {res['risk']:,.2f}")
                    with col2:
                        st.metric("Data da Simulação", res["date"])
                        
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

