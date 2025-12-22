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
h1, h2, h3 {
    color: #b08d57;
}
.resultado {
    background-color: #e6f4ea;
    padding: 15px;
    border-radius: 8px;
    border-left: 6px solid #1a7f37;
    font-size: 18px;
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
# TOPO COM LOGO
# ===============================
st.image("logo_atual.png", width=280)
st.markdown("""
<h1>Cálculo IRPF Mensal – Regras 2026</h1>
<p><b>Atual Assessoria Contábil e Gerencial</b></p>
<p>Lei 15.270/2025 • IN RFB 2.299/2025</p>
""", unsafe_allow_html=True)

# ===============================
# ENTRADAS
# ===============================
rendimento = st.number_input("Rendimento Bruto (R$)", min_value=0.0, value=6500.0, step=100.0)
inss = st.number_input("INSS (R$)", min_value=0.0, value=700.0, step=50.0)
dependentes = st.number_input("Número de dependentes", min_value=0, step=1)

# ===============================
# FUNÇÕES DE CÁLCULO
# ===============================
DEDUCAO_DEP = 189.59

def calcular_ir(base):
    if base <= 2259.20:
        return 0.0
    elif base <= 2826.65:
        return base * 0.075 - 169.44
    elif base <= 3751.05:
        return base * 0.15 - 381.44
    elif base <= 4664.68:
        return base * 0.225 - 662.77
    else:
        return base * 0.275 - 896.00

# ===============================
# CÁLCULO LEGAL
# ===============================
base_legal = rendimento - inss - (dependentes * DEDUCAO_DEP)
ir_legal = calcular_ir(base_legal)

# ===============================
# CÁLCULO SIMPLIFICADO
# ===============================
desconto_simplificado = min(rendimento * 0.20, 528.00)
base_simplificado = rendimento - desconto_simplificado
ir_simplificado = calcular_ir(base_simplificado)

# ===============================
# ESCOLHA AUTOMÁTICA
# ===============================
if ir_legal <= ir_simplificado:
    metodo = "LEGAL"
    ir_final = ir_legal
    base_final = base_legal
    reducao = 113.18 if base_final <= 2826.65 else 0.0
else:
    metodo = "SIMPLIFICADO"
    ir_final = ir_simplificado
    base_final = base_simplificado
    reducao = 0.0

ir_recolher = max(ir_final - reducao, 0)

# ===============================
# RESULTADO
# ===============================
st.subheader("📊 Resultado do Cálculo")
st.write(f"**Método escolhido automaticamente:** {metodo}")
st.write(f"Base de cálculo: R$ {base_final:,.2f}")
st.write(f"IR apurado: R$ {ir_final:,.2f}")
st.write(f"Redução Lei 15.270: R$ {reducao:,.2f}")

st.markdown(f"""
<div class="resultado">
<b>IR a recolher:</b> R$ {ir_recolher:,.2f}
</div>
""", unsafe_allow_html=True)

# ===============================
# GERAR PDF
# ===============================
if st.button("📄 Gerar PDF do Cálculo"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        c = canvas.Canvas(tmp.name, pagesize=A4)
        largura, altura = A4

        logo_path = "logo_atual.png"
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 2*cm, altura-4*cm, width=6*cm, preserveAspectRatio=True)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, altura-5*cm, "Cálculo IRPF Mensal – 2026")

        c.setFont("Helvetica", 11)
        y = altura - 7*cm
        linhas = [
            f"Rendimento Bruto: R$ {rendimento:,.2f}",
            f"INSS: R$ {inss:,.2f}",
            f"Dependentes: {dependentes}",
            f"Método escolhido: {metodo}",
            f"Base de cálculo: R$ {base_final:,.2f}",
            f"IR apurado: R$ {ir_final:,.2f}",
            f"Redução Lei 15.270: R$ {reducao:,.2f}",
            f"IR a recolher: R$ {ir_recolher:,.2f}",
            f"Data do cálculo: {datetime.now().strftime('%d/%m/%Y')}"
        ]

        for linha in linhas:
            c.drawString(2*cm, y, linha)
            y -= 1*cm

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(2*cm, 2*cm, "Uso interno – Atual Assessoria Contábil e Gerencial")

        c.save()

        st.download_button(
            label="📥 Baixar PDF",
            data=open(tmp.name, "rb"),
            file_name="Calculo_IRPF_2026.pdf"
        )

# ===============================
# RODAPÉ
# ===============================
st.markdown("""
<div class="footer">
Uso interno – Atual Assessoria Contábil e Gerencial<br>
Simulação sujeita à conferência final.
</div>
""", unsafe_allow_html=True)
