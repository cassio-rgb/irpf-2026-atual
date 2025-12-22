import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import tempfile
import os

# ======================================================
# CONSTANTES OFICIAIS
# ======================================================

# Tabela progressiva mensal (vigente desde maio/2025)
TABELA_IR = [
    (0, 2428.80, 0.0, 0.0),
    (2428.81, 2826.65, 0.075, 182.16),
    (2826.66, 3751.05, 0.15, 394.16),
    (3751.06, 4664.68, 0.225, 675.49),
    (4664.69, 999999, 0.275, 908.73),
]

DEDUCAO_DEPENDENTE = 189.59
DESCONTO_SIMPLIFICADO = 607.20  # valor FIXO mensal
LOGO_PATH = r"C:\IRPF_2026_APP\logo_atual.png"

# ======================================================
# FUNÇÕES DE CÁLCULO
# ======================================================

def calcular_ir(base):
    for faixa in TABELA_IR:
        if faixa[0] <= base <= faixa[1]:
            return max(0, base * faixa[2] - faixa[3])
    return 0.0

def calcular_reducao_2026(rendimento, ir_apurado):
    if rendimento <= 5000:
        return min(312.89, ir_apurado)
    elif rendimento <= 7350:
        reducao = 978.62 - (0.133145 * rendimento)
        return max(0, min(reducao, ir_apurado))
    return 0.0

# ======================================================
# INTERFACE
# ======================================================

st.title("🧮 Cálculo IRPF Mensal – Regras 2026")
st.write("Lei 15.270/2025 • IN RFB 2.299/2025")

salario = st.number_input("Rendimento Bruto (R$)", min_value=0.0, step=100.0)
inss = st.number_input("INSS (R$)", min_value=0.0, step=10.0)
dependentes = st.number_input("Número de dependentes", min_value=0, step=1)

# ======================================================
# MÉTODO LEGAL
# ======================================================

base_legal = max(0, salario - inss - (dependentes * DEDUCAO_DEPENDENTE))
ir_legal = calcular_ir(base_legal)
reducao_legal = calcular_reducao_2026(salario, ir_legal)
ir_final_legal = max(0, ir_legal - reducao_legal)

# ======================================================
# MÉTODO SIMPLIFICADO
# ======================================================

base_simplificado = max(0, salario - DESCONTO_SIMPLIFICADO)
ir_simplificado = calcular_ir(base_simplificado)
reducao_simplificado = calcular_reducao_2026(salario, ir_simplificado)
ir_final_simplificado = max(0, ir_simplificado - reducao_simplificado)

# ======================================================
# ESCOLHA AUTOMÁTICA DO MELHOR MÉTODO
# ======================================================

if ir_final_simplificado < ir_final_legal:
    metodo = "SIMPLIFICADO"
    base_calculo = base_simplificado
    ir_apurado = ir_simplificado
    reducao = reducao_simplificado
    ir_final = ir_final_simplificado
else:
    metodo = "LEGAL"
    base_calculo = base_legal
    ir_apurado = ir_legal
    reducao = reducao_legal
    ir_final = ir_final_legal

# ======================================================
# RESULTADO NA TELA
# ======================================================

st.subheader("📊 Resultado do Cálculo")

st.write(f"**Método escolhido automaticamente:** {metodo}")
st.write(f"Base de cálculo: R$ {base_calculo:,.2f}")
st.write(f"IR apurado: R$ {ir_apurado:,.2f}")
st.write(f"Redução Lei 15.270: R$ {reducao:,.2f}")
st.success(f"IR a recolher: R$ {ir_final:,.2f}")

# ======================================================
# GERAÇÃO DO PDF
# ======================================================

if st.button("📄 Gerar PDF do Cálculo"):
    data_calculo = datetime.now().strftime("%d/%m/%Y")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)

    # Logo
    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 50, 770, width=150, height=60, preserveAspectRatio=True)

    # Cabeçalho
    c.setFont("Helvetica-Bold", 14)
    c.drawString(220, 800, "CÁLCULO IRPF – PESSOA FÍSICA")
    c.setFont("Helvetica", 10)
    c.drawString(220, 785, f"Data do cálculo: {data_calculo}")

    y = 740
    c.setFont("Helvetica", 11)

    c.drawString(50, y, f"Método escolhido: {metodo}")
    y -= 25
    c.drawString(50, y, f"Rendimento Bruto: R$ {salario:,.2f}")
    y -= 20
    c.drawString(50, y, f"INSS: R$ {inss:,.2f}")
    y -= 20
    c.drawString(50, y, f"Dependentes: {dependentes}")
    y -= 30

    c.drawString(50, y, f"Base de cálculo: R$ {base_calculo:,.2f}")
    y -= 20
    c.drawString(50, y, f"IR apurado: R$ {ir_apurado:,.2f}")
    y -= 20
    c.drawString(50, y, f"Redução (Lei 15.270): R$ {reducao:,.2f}")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"IR A RECOLHER: R$ {ir_final:,.2f}")

    c.showPage()
    c.save()

    with open(temp_file.name, "rb") as f:
        st.download_button(
            "⬇️ Baixar PDF",
            data=f,
            file_name="calculo_irpf_2026.pdf",
            mime="application/pdf"
        )

    os.unlink(temp_file.name)
