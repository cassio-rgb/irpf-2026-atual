import streamlit as st
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os
import tempfile

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="IRPF 2026 | Atual Assessoria Contábil",
    page_icon="📊",
    layout="centered"
)

# ===============================
# CSS - IDENTIDADE VISUAL
# ===============================
st.markdown("""
<style>
h1, h2, h3 { color: #b08d57; }
.resultado {
    background-color: #e6f4ea;
    padding: 15px;
    border-radius: 8px;
    border-left: 6px solid #1a7f37;
    font-size: 18px;
}
.comparacao {
    background-color: #f0f0f0;
    padding: 12px;
    border-radius: 6px;
    font-size: 15px;
}
.footer {
    margin-top: 40px;
    padding-top: 10px;
    border-top: 1px solid #ddd;
    font-size: 12px;
    color: #666;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# TOPO
# ===============================
st.image("logo_atual.png", width=280)
st.markdown("""
<h1>Cálculo IRPF Mensal – 2026</h1>
<p><b>Atual Assessoria Contábil e Gerencial</b></p>
<p>Lei 15.270/2025 • IN RFB 2.299/2025</p>
""", unsafe_allow_html=True)

# ===============================
# ENTRADAS
# ===============================
rendimento = st.number_input("Rendimento Bruto (R$)", min_value=0.0, value=6500.0, step=100.0)
inss = st.number_input("INSS (R$)", min_value=0.0, value=700.0, step=50.0)
dependentes = st.number_input("Número de dependentes", min_value=0, step=1)

DEDUCAO_DEP = 189.59

# ===============================
# FUNÇÃO IR + ALÍQUOTA
# ===============================
def calcular_ir(base):
    if base <= 2259.20:
        return 0.0, 0.0
    elif base <= 2826.65:
        return base * 0.075 - 169.44, 7.5
    elif base <= 3751.05:
        return base * 0.15 - 381.44, 15.0
    elif base <= 4664.68:
        return base * 0.225 - 662.77, 22.5
    else:
        return base * 0.275 - 896.00, 27.5

# ===============================
# CÁLCULO 2026 – LEGAL
# ===============================
base_legal = rendimento - inss - (dependentes * DEDUCAO_DEP)
ir_legal, aliquota_legal = calcular_ir(base_legal)
reducao_legal = 113.18 if base_legal <= 2826.65 else 0.0
ir_legal_final = max(ir_legal - reducao_legal, 0)

# ===============================
# CÁLCULO 2026 – SIMPLIFICADO
# ===============================
desconto_simplificado = min(rendimento * 0.20, 528.00)
base_simpl = rendimento - desconto_simplificado
ir_simpl, aliquota_simpl = calcular_ir(base_simpl)

# ===============================
# ESCOLHA AUTOMÁTICA
# ===============================
if ir_legal_final <= ir_simpl:
    metodo = "LEGAL"
    base_final = base_legal
    ir_final = ir_legal_final
    aliquota = aliquota_legal
else:
    metodo = "SIMPLIFICADO"
    base_final = base_simpl
    ir_final = ir_simpl
    aliquota = aliquota_simpl
    reducao_legal = 0.0

# ===============================
# ALÍQUOTA EFETIVA
# ===============================
aliquota_efetiva = (ir_final / rendimento * 100) if rendimento > 0 else 0

# ===============================
# CÁLCULO 2025 (SEM LEI 15.270)
# ===============================
ir_2025, _ = calcular_ir(base_legal)

# ===============================
# RESULTADOS
# ===============================
st.subheader("📊 Resultado do Cálculo – 2026")

st.write(f"**Método escolhido:** {metodo}")
st.write(f"Base de cálculo: R$ {base_final:,.2f}")
st.write(f"Alíquota da faixa: {aliquota:.1f}%")
st.write(f"Alíquota efetiva: {aliquota_efetiva:.2f}%")

st.markdown(f"""
<div class="resultado">
<b>IR a recolher (2026):</b> R$ {ir_final:,.2f}
</div>
""", unsafe_allow_html=True)

# ===============================
# COMPARAÇÃO 2025 x 2026
# ===============================
diferenca = ir_2025 - ir_final

st.subheader("📉 Comparativo com 2025")
st.markdown(f"""
<div class="comparacao">
IR pelo critério 2025: R$ {ir_2025:,.2f}<br>
IR pelo critério 2026: R$ {ir_final:,.2f}<br>
<b>Diferença:</b> R$ {diferenca:,.2f}
</div>
""", unsafe_allow_html=True)

# ===============================
# RODAPÉ
# ===============================
st.markdown("""
<div class="footer">
Uso interno – Atual Assessoria Contábil e Gerencial<br>
Simulação sujeita à conferência final.
</div>
""", unsafe_allow_html=True)
