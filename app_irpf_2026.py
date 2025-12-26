import io
from datetime import datetime
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ======================================================
# CONFIGURAÇÃO DA PÁGINA
# ======================================================
st.set_page_config(
    page_title="IRPF 2026 | Atual Assessoria Contábil",
    page_icon="📊",
    layout="centered"
)

# ======================================================
# ESTILO VISUAL
# ======================================================
st.markdown("""
<style>
h1, h2, h3 { color: #b08d57; }

.caixa {
    background-color: #f4f4f4;
    padding: 14px;
    border-radius: 6px;
    margin-bottom: 10px;
}

.resultado {
    background-color: #e6f4ea;
    padding: 16px;
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

# ======================================================
# TOPO
# ======================================================
st.image("logo_atual.png", width=260)

st.markdown("""
<h1>Cálculo IRPF Mensal – 2026</h1>
<p><b>Atual Assessoria Contábil e Gerencial</b></p>
<p>Lei nº 15.270/2025 • IN RFB nº 2.299/2025</p>
""", unsafe_allow_html=True)

# ======================================================
# ENTRADAS
# ======================================================
col1, col2 = st.columns(2)

with col1:
    rendimento = st.number_input("Rendimento Bruto (R$)", value=7000.00, step=100.00, format="%.2f")
with col2:
    inss = st.number_input("INSS (R$)", value=789.60, step=10.00, format="%.2f")

dependentes = st.number_input("Número de dependentes", value=2, step=1)

DEDUCAO_DEP = 189.59
DESCONTO_SIMPLIFICADO = 607.20  # 25% de 2.428,80

# ======================================================
# FUNÇÕES
# ======================================================
def tabela_progressiva(base):
    if base <= 2428.80:
        return 0.0, 0.0, 0.0
    elif base <= 2826.65:
        return base * 0.075, 182.16, 7.5
    elif base <= 3751.05:
        return base * 0.15, 394.16, 15
    elif base <= 4664.68:
        return base * 0.225, 675.49, 22.5
    else:
        return base * 0.275, 908.73, 27.5

def reducao_lei_15270(rendimento):
    if rendimento <= 5000:
        return float("inf")
    elif rendimento <= 7350:
        return 978.62 - (0.133145 * rendimento)
    else:
        return 0.0

def calcular_metodo(rendimento, inss, dependentes, simplificado=False):
    base = rendimento - inss - (dependentes * DEDUCAO_DEP)
    if simplificado:
        base -= DESCONTO_SIMPLIFICADO
    base = max(base, 0)

    ir_bruto, parcela, aliquota = tabela_progressiva(base)
    ir_apurado = max(ir_bruto - parcela, 0)

    reducao = reducao_lei_15270(rendimento)
    reducao = min(ir_apurado, max(reducao, 0))

    ir_final = max(ir_apurado - reducao, 0)
    aliquota_efetiva = (ir_final / rendimento * 100) if rendimento > 0 else 0

    return {
        "base": base,
        "aliquota": aliquota,
        "ir_apurado": ir_apurado,
        "reducao": reducao,
        "ir_final": ir_final,
        "aliquota_efetiva": aliquota_efetiva
    }

# ======================================================
# CÁLCULOS
# ======================================================
legal = calcular_metodo(rendimento, inss, dependentes, False)
simpl = calcular_metodo(rendimento, inss, dependentes, True)

if simpl["ir_final"] < legal["ir_final"]:
    metodo_escolhido = "SIMPLIFICADO"
    resultado = simpl
else:
    metodo_escolhido = "LEGAL"
    resultado = legal

# ======================================================
# RESULTADOS NA TELA
# ======================================================
st.subheader("📊 Demonstração dos Cálculos")

st.markdown("### 🔹 Método LEGAL")
st.markdown(f"""
<div class="caixa">
Base de cálculo: R$ {legal['base']:,.2f}<br>
IR apurado: R$ {legal['ir_apurado']:,.2f}<br>
Redução Lei 15.270/2025: R$ {legal['reducao']:,.2f}<br>
<b>IR a recolher: R$ {legal['ir_final']:,.2f}</b>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🔹 Método SIMPLIFICADO")
st.markdown(f"""
<div class="caixa">
Base de cálculo: R$ {simpl['base']:,.2f}<br>
IR apurado: R$ {simpl['ir_apurado']:,.2f}<br>
Redução Lei 15.270/2025: R$ {simpl['reducao']:,.2f}<br>
<b>IR a recolher: R$ {simpl['ir_final']:,.2f}</b>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="resultado">
<b>Método mais vantajoso:</b> {metodo_escolhido}<br>
<b>IR a recolher:</b> R$ {resultado['ir_final']:,.2f}<br>
Alíquota da faixa: {resultado['aliquota']}%<br>
Alíquota efetiva: {resultado['aliquota_efetiva']:.2f}%
</div>
""", unsafe_allow_html=True)

# ======================================================
# PDF
# ======================================================
def gerar_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    y = h - 2.5 * cm

    def br(v):
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    try:
        c.drawImage("logo_atual.png", 2*cm, y, width=6*cm, height=2.2*cm, mask="auto")
    except:
        pass

    y -= 3*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, "Atual Assessoria Contábil e Gerencial")
    y -= 0.7*cm

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, f"Data do cálculo: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 1*cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Demonstração dos Cálculos")
    y -= 0.7*cm

    for nome, dados in [("LEGAL", legal), ("SIMPLIFICADO", simpl)]:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y, f"Método {nome}")
        y -= 0.5*cm
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y, f"Base de cálculo: {br(dados['base'])}")
        y -= 0.4*cm
        c.drawString(2*cm, y, f"IR apurado: {br(dados['ir_apurado'])}")
        y -= 0.4*cm
        c.drawString(2*cm, y, f"Redução Lei 15.270/2025: {br(dados['reducao'])}")
        y -= 0.4*cm
        c.drawString(2*cm, y, f"IR a recolher: {br(dados['ir_final'])}")
        y -= 0.7*cm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Base Legal do Cálculo")
    y -= 0.5*cm

    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y,
        "Cálculo efetuado conforme a Lei nº 15.270/2025 e a Instrução Normativa RFB nº 2.299/2025, "
        "considerando tabela progressiva mensal, deduções legais, desconto simplificado e redução "
        "do imposto para rendimentos mensais até R$ 7.350,00. Simulação para fins informativos."
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

if st.button("📄 Gerar PDF do Cálculo"):
    st.download_button(
        "⬇️ Baixar PDF",
        data=gerar_pdf(),
        file_name="IRPF_2026_Calculo.pdf",
        mime="application/pdf"
    )

# ======================================================
# RODAPÉ
# ======================================================
st.markdown("""
<div class="footer">
Uso interno – Atual Assessoria Contábil e Gerencial<br>
Simulação sujeita à conferência conforme legislação vigente.
</div>
""", unsafe_allow_html=True)
