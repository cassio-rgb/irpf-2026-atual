import io
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


# -----------------------------
# Constantes (baseadas nos seus arquivos)
# -----------------------------

# Tabela progressiva mensal (a partir de maio/2025) – usada nos exemplos de 2026
# Fonte: IN RFB 2.299/2025 (Anexo II) :contentReference[oaicite:6]{index=6}
TABELA_PROGRESSIVA = [
    # (limite_superior, aliquota, parcela_a_deduzir)
    (2428.80, 0.00, 0.00),
    (2826.65, 0.075, 182.16),
    (3751.05, 0.15, 394.16),
    (4664.68, 0.225, 675.49),
    (float("inf"), 0.275, 908.73),
]

# Dedução por dependente (valor usado nos exemplos do PDF que você mandou) :contentReference[oaicite:7]{index=7}
DEDUCAO_DEPENDENTE = 189.59

# Desconto simplificado mensal (25% de 2.428,80) – aparece no Exemplo 1 :contentReference[oaicite:8]{index=8}
DESCONTO_SIMPLIFICADO_MAX = 2428.80 * 0.25  # 607,20

# Redução do IR a partir de 01/01/2026 (Lei 15.270/2025):
# - até 5.000: reduz até zerar (limitado ao imposto)
# - 5.000,01 a 7.350: 978,62 - (0,133145 x rendimento)
# - acima de 7.350: sem redução
# Fonte: PDF + IN (Anexo X) :contentReference[oaicite:9]{index=9}
REDUCAO_A = 978.62
REDUCAO_B = 0.133145
LIMITE_ISENCAO_REDUCAO = 5000.00
LIMITE_FIM_REDUCAO = 7350.00


# -----------------------------
# Funções de cálculo
# -----------------------------

def calcula_ir_tabela_progressiva(base_calculo: float) -> dict:
    """
    Retorna:
      - aliquota_faixa
      - parcela_a_deduzir
      - ir_apurado (antes da redução Lei 15.270/2025)
    """
    for limite, aliquota, parcela in TABELA_PROGRESSIVA:
        if base_calculo <= limite:
            ir = max(0.0, base_calculo * aliquota - parcela)
            return {
                "aliquota_faixa": aliquota,
                "parcela_deduzir": parcela,
                "ir_apurado": ir,
            }
    # fallback (não deve acontecer)
    return {"aliquota_faixa": 0.0, "parcela_deduzir": 0.0, "ir_apurado": 0.0}


def calcula_reducao_lei_15270(rendimento_tributavel_mes: float, ir_apurado: float) -> float:
    """
    A redução é aplicada sobre o imposto apurado na forma da tabela progressiva,
    considerando o 'rendimento tributável sujeito à incidência mensal' (nos exemplos: rendimento bruto).
    A redução é limitada ao valor do imposto (não pode gerar imposto negativo).
    """
    if rendimento_tributavel_mes <= LIMITE_ISENCAO_REDUCAO:
        # “até R$ 312,89 de modo que o imposto devido seja zero” -> na prática: reduz até zerar
        return min(ir_apurado, ir_apurado)

    if LIMITE_ISENCAO_REDUCAO < rendimento_tributavel_mes <= LIMITE_FIM_REDUCAO:
        reducao = REDUCAO_A - (REDUCAO_B * rendimento_tributavel_mes)
        reducao = max(0.0, reducao)
        return min(ir_apurado, reducao)

    return 0.0


def calcula_irpf_mensal_2026(
    rendimento_bruto: float,
    inss: float,
    dependentes: int,
    usar_simplificado: bool,
) -> dict:
    """
    Calcula IRPF mensal 2026 com:
    - Base = rendimento - INSS - (dependentes*189,59) - (desconto simplificado, se escolhido)
    - IR apurado = tabela progressiva
    - Redução Lei 15.270/2025 aplicada no IR apurado (com base no rendimento tributável do mês)
    """
    ded_depend = dependentes * DEDUCAO_DEPENDENTE
    desconto_simplificado = DESCONTO_SIMPLIFICADO_MAX if usar_simplificado else 0.0

    base = rendimento_bruto - inss - ded_depend - desconto_simplificado
    base = max(0.0, base)

    info_tab = calcula_ir_tabela_progressiva(base)
    ir_apurado = info_tab["ir_apurado"]

    # Redução calculada com base no rendimento tributável sujeito à incidência mensal.
    # Nos exemplos do seu PDF, a fórmula usa o rendimento bruto. :contentReference[oaicite:10]{index=10}
    reducao = calcula_reducao_lei_15270(rendimento_bruto, ir_apurado)

    ir_final = max(0.0, ir_apurado - reducao)

    aliquota_faixa = info_tab["aliquota_faixa"]
    aliquota_efetiva = (ir_final / rendimento_bruto) if rendimento_bruto > 0 else 0.0

    return {
        "base_calculo": base,
        "aliquota_faixa": aliquota_faixa,
        "parcela_deduzir": info_tab["parcela_deduzir"],
        "ir_apurado": ir_apurado,
        "reducao": reducao,
        "ir_final": ir_final,
        "ded_dependentes": ded_depend,
        "desconto_simplificado": desconto_simplificado,
        "aliquota_efetiva": aliquota_efetiva,
    }


def escolhe_melhor_metodo(rendimento_bruto: float, inss: float, dependentes: int) -> dict:
    """
    Escolhe automaticamente o menor IR entre:
      - LEGAL (sem simplificado)
      - SIMPLIFICADO (com desconto simplificado mensal)
    """
    legal = calcula_irpf_mensal_2026(rendimento_bruto, inss, dependentes, usar_simplificado=False)
    simpl = calcula_irpf_mensal_2026(rendimento_bruto, inss, dependentes, usar_simplificado=True)

    if simpl["ir_final"] < legal["ir_final"]:
        return {"metodo": "SIMPLIFICADO", "resultado": simpl, "comparacao": {"legal": legal, "simplificado": simpl}}
    else:
        return {"metodo": "LEGAL", "resultado": legal, "comparacao": {"legal": legal, "simplificado": simpl}}


# -----------------------------
# PDF
# -----------------------------

def gerar_pdf_calculo(
    logo_path: str,
    data_calculo: datetime,
    rendimento_bruto: float,
    inss: float,
    dependentes: int,
    metodo: str,
    res: dict,
) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Logo
    try:
        c.drawImage(logo_path, 2*cm, h - 4.0*cm, width=6.5*cm, height=2.5*cm, mask='auto')
    except Exception:
        # Se não achar o logo, segue sem travar
        pass

    y = h - 4.5*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, "Atual Assessoria Contábil e Gerencial")
    y -= 0.7*cm

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, f"Data do cálculo: {data_calculo.strftime('%d/%m/%Y %H:%M')}")
    y -= 0.8*cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Cálculo IRPF Mensal – Regras 2026")
    y -= 0.6*cm

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, "Base: Lei 15.270/2025 e IN RFB 2.299/2025")
    y -= 1.0*cm

    # Entradas
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Entradas")
    y -= 0.6*cm

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, f"Rendimento bruto: R$ {rendimento_bruto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    y -= 0.5*cm
    c.drawString(2*cm, y, f"INSS: R$ {inss:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Dependentes: {dependentes}")
    y -= 0.8*cm

    # Resultado
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Resultado")
    y -= 0.6*cm

    def brl(v: float) -> str:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, f"Método escolhido: {metodo}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Base de cálculo: {brl(res['base_calculo'])}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Alíquota da faixa: {res['aliquota_faixa']*100:.1f}%")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"IR apurado (tabela): {brl(res['ir_apurado'])}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Redução Lei 15.270/2025: {brl(res['reducao'])}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"IR a recolher: {brl(res['ir_final'])}")
    y -= 0.5*cm
    c.drawString(2*cm, y, f"Alíquota efetiva: {res['aliquota_efetiva']*100:.2f}%")
    y -= 1.0*cm

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2*cm, 1.5*cm, "Uso interno – Simulação sujeita à conferência conforme legislação vigente.")
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.read()


# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="Cálculo IRPF Mensal 2026 - Atual", page_icon="🧮", layout="centered")

st.title("🧮 Cálculo IRPF Mensal – Regras 2026")
st.caption("Lei 15.270/2025 • IN RFB 2.299/2025")

col1, col2 = st.columns(2)
with col1:
    rendimento_bruto = st.number_input("Rendimento Bruto (R$)", min_value=0.0, value=6000.0, step=100.0, format="%.2f")
with col2:
    inss = st.number_input("INSS (R$)", min_value=0.0, value=649.60, step=10.0, format="%.2f")

dependentes = st.number_input("Número de dependentes", min_value=0, value=1, step=1)

st.divider()

calc = escolhe_melhor_metodo(rendimento_bruto, inss, dependentes)
metodo = calc["metodo"]
res = calc["resultado"]

st.subheader("📊 Resultado do Cálculo")
st.write(f"**Método escolhido automaticamente:** {metodo}")

st.write(f"**Base de cálculo:** R$ {res['base_calculo']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
st.write(f"**Alíquota da faixa:** {res['aliquota_faixa']*100:.1f}%")
st.write(f"**Alíquota efetiva:** {res['aliquota_efetiva']*100:.2f}%")
st.write(f"**IR apurado (tabela):** R$ {res['ir_apurado']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
st.write(f"**Redução Lei 15.270/2025:** R$ {res['reducao']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.success(f"IR a recolher: R$ {res['ir_final']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with st.expander("Ver detalhes do cálculo"):
    st.write(f"- Dedução dependentes: R$ {res['ded_dependentes']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.write(f"- Desconto simplificado: R$ {res['desconto_simplificado']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.write(f"- Parcela a deduzir (tabela): R$ {res['parcela_deduzir']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.divider()

logo_path = "logo_atual.png"  # tem que estar no mesmo repositório/pasta do app

if st.button("📄 Gerar PDF do Cálculo"):
    pdf_bytes = gerar_pdf_calculo(
        logo_path=logo_path,
        data_calculo=datetime.now(),
        rendimento_bruto=rendimento_bruto,
        inss=inss,
        dependentes=int(dependentes),
        metodo=metodo,
        res=res,
    )

    st.download_button(
        label="⬇️ Baixar PDF",
        data=pdf_bytes,
        file_name=f"IRPF_2026_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
    )
