import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
import json
import numpy as np
from datetime import datetime

# ══════════════════════════════════════════
# AUTENTICAÇÃO
# ══════════════════════════════════════════
USUARIOS = {
    "texview":  "29263",
    "cliente":  "texview2024",
    "bernardo": "minhasenha",
}
SHEET_ID = "1DR9IRu6rltkOUvGBPtZqHoA8p6kiCYGwlLaTKOEFH14"  # ID fixo da planilha Texview

def check_login():
    if 'logado' not in st.session_state:
        st.session_state.logado = False

    if st.session_state.logado:
        return True

    col_left, col_right = st.columns([1, 1])

    with col_left:
        left_html = (
            '<div style="background:#0a0b12;min-height:100vh;display:flex;flex-direction:column;'
            'align-items:center;justify-content:center;padding:60px 48px;position:relative;overflow:hidden;">'

            # SVG logo X
            '<svg width="110" height="110" viewBox="0 0 110 110" fill="none" '
            'xmlns="http://www.w3.org/2000/svg" '
            'style="margin-bottom:28px;filter:drop-shadow(0 0 18px rgba(255,0,127,0.5));">'
            '<defs>'
            '<linearGradient id="gL1" x1="0%" y1="0%" x2="100%" y2="100%">'
            '<stop offset="0%" stop-color="#ff007f"/><stop offset="100%" stop-color="#c0006a"/>'
            '</linearGradient>'
            '<linearGradient id="gL2" x1="100%" y1="0%" x2="0%" y2="100%">'
            '<stop offset="0%" stop-color="#3d0030"/><stop offset="100%" stop-color="#1a0020"/>'
            '</linearGradient>'
            '</defs>'
            '<polygon points="8,10 38,10 102,100 72,100" fill="url(#gL1)" opacity="0.92"/>'
            '<polygon points="72,10 102,10 38,100 8,100" fill="url(#gL2)" opacity="0.85"/>'
            '<polygon points="45,48 65,48 58,62 38,62" fill="#ff007f" opacity="0.6"/>'
            '</svg>'

            # Título TEXVIEW
            '<div style="font-size:42px;font-weight:800;letter-spacing:5px;margin-bottom:6px;line-height:1;">'
            '<span style="color:#ff007f;">TEX</span><span style="color:#ffffff;">VIEW</span>'
            '</div>'

            # Separador neon
            '<div style="width:100%;max-width:280px;height:1px;'
            'background:linear-gradient(90deg,transparent,#ff007f,transparent);'
            'margin:10px 0 12px;"></div>'

            # Subtítulo
            '<div style="font-size:11px;color:#ff007f;letter-spacing:4px;'
            'text-transform:uppercase;font-weight:600;margin-bottom:28px;">CONTROLE FINANCEIRO</div>'

            # Descrição
            '<div style="font-size:14px;color:#6b7280;text-align:center;max-width:300px;line-height:1.75;">'
            'Visibilidade total sobre as finan\u00e7as da sua<br>empresa, em tempo real.'
            '</div>'

            '</div>'
        )
        st.markdown(left_html, unsafe_allow_html=True)




    with col_right:
        # Espaço superior para centralizar visualmente
        st.markdown('<div style="min-height:18vh;"></div>', unsafe_allow_html=True)

        st.markdown(
            '<div style="padding:0 8% 0 8%;">'
            '<div style="font-size:30px;font-weight:700;color:#ffffff;margin-bottom:6px;">Bem-vindo</div>'
            '<div style="font-size:14px;color:#6b7280;margin-bottom:32px;">Acesse sua conta para continuar</div>'
            '</div>',
            unsafe_allow_html=True
        )

        _, form_col, _ = st.columns([0.3, 5, 0.3])
        with form_col:
            st.markdown('<div style="font-size:10px;color:#9ca3af;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Usuário</div>', unsafe_allow_html=True)
            usuario = st.text_input("usr_hidden", label_visibility="collapsed", placeholder="seu@email.com")

            st.markdown('<div style="font-size:10px;color:#9ca3af;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;margin-top:12px;">Senha</div>', unsafe_allow_html=True)
            senha = st.text_input("pwd_hidden", label_visibility="collapsed", type="password", placeholder="••••••••")

            st.markdown('<div style="text-align:right;margin-top:4px;margin-bottom:16px;"><span style="font-size:12px;color:#ff007f;cursor:pointer;">Esqueceu sua senha?</span></div>', unsafe_allow_html=True)

            entrar = st.button("Entrar →", use_container_width=True, type="primary")

            if entrar:
                if usuario in USUARIOS and USUARIOS[usuario] == senha:
                    st.session_state.logado = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

            st.markdown('<div style="text-align:center;color:#4b5563;font-size:11px;margin-top:24px;">© 2026 Texview — Todos os direitos reservados.</div>', unsafe_allow_html=True)

    return False


# ══════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ══════════════════════════════════════════
st.set_page_config(
    page_title="Texview · Dashboard Financeiro",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════
# CSS CUSTOMIZADO
# ══════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Ocultar menu e footer do Streamlit */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Fundo principal */
    .stApp {
        background: linear-gradient(135deg, #0a0b14, #1a1b2e);
    }
    .main { background: transparent; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1b2e, #0a0b14) !important;
        border-right: 1px solid rgba(255,0,127,0.2) !important;
    }
    [data-testid="stSidebar"] .stSelectbox label { color: #9ca3af !important; }

    /* ── KPI CARDS ── */
    .kpi-card {
        background: linear-gradient(135deg, #1a1b2e, #0a0b14);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 8px;
        border-top: 3px solid;
        border-left: 1px solid;
        border-right: 1px solid rgba(255,0,127,0.08);
        border-bottom: 1px solid rgba(255,0,127,0.08);
        box-shadow: 0 0 20px rgba(255,0,127,0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 40px rgba(255,0,127,0.18);
    }
    .kpi-card.green  { border-top-color: #10b981; border-left-color: rgba(16,185,129,0.25); }
    .kpi-card.red    { border-top-color: #ff007f; border-left-color: rgba(255,0,127,0.25); }
    .kpi-card.blue   { border-top-color: #3b82f6; border-left-color: rgba(59,130,246,0.25); }
    .kpi-card.gold   { border-top-color: #f59e0b; border-left-color: rgba(245,158,11,0.25); }
    .kpi-card.purple { border-top-color: #8b5cf6; border-left-color: rgba(139,92,246,0.25); }

    .kpi-label {
        font-size: 10px; letter-spacing: 2px;
        text-transform: uppercase; color: #9ca3af; margin-bottom: 8px;
    }
    .kpi-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 6px; }
    .kpi-delta-up   { font-size: 11px; color: #10b981; }
    .kpi-delta-down { font-size: 11px; color: #ff007f; }
    .kpi-delta-neutral { font-size: 11px; color: #9ca3af; }

    /* ── INSIGHT CARDS ── */
    .insight-card {
        background: linear-gradient(135deg, #1a1b2e, #0a0b14);
        border: 1px solid rgba(255,0,127,0.1);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 10px;
        border-left: 3px solid;
        transition: transform 0.2s ease;
    }
    .insight-card:hover { transform: translateY(-2px); }
    .insight-card.green  { border-left-color: #10b981; }
    .insight-card.red    { border-left-color: #ff007f; }
    .insight-card.gold   { border-left-color: #f59e0b; }
    .insight-card.blue   { border-left-color: #3b82f6; }

    .insight-badge {
        font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
        padding: 3px 10px; border-radius: 20px;
        display: inline-block; margin-bottom: 8px;
    }
    .badge-green  { background: rgba(16,185,129,0.15);  color: #10b981; }
    .badge-red    { background: rgba(255,0,127,0.15);   color: #ff007f; }
    .badge-gold   { background: rgba(245,158,11,0.15);  color: #f59e0b; }
    .badge-blue   { background: rgba(59,130,246,0.15);  color: #3b82f6; }

    .insight-title { font-size: 14px; font-weight: 600; color: #ffffff; margin-bottom: 6px; }
    .insight-text  { font-size: 12px; color: #9ca3af; line-height: 1.7; }
    .insight-text strong { color: #ffffff; }

    /* ── SECTION HEADERS ── */
    .section-header {
        font-size: 10px;
        letter-spacing: 3px; text-transform: uppercase; color: #9ca3af;
        border-bottom: 1px solid rgba(255,0,127,0.2);
        padding-bottom: 8px; margin-bottom: 16px;
    }

    /* ── BOTÕES ── */
    .stButton > button {
        background: linear-gradient(90deg, #ff007f, #8b5cf6) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: box-shadow 0.2s ease, transform 0.2s ease !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 25px rgba(255,0,127,0.4) !important;
        transform: scale(1.02) !important;
    }

    /* ── INPUTS ── */
    .stTextInput > div > div > input {
        background: #0a0b14 !important;
        border: 1px solid rgba(139,92,246,0.3) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #ff007f !important;
        box-shadow: 0 0 0 3px rgba(255,0,127,0.2) !important;
    }

    /* ── SELECTBOX ── */
    .stSelectbox > div > div {
        background: #1a1b2e !important;
        border: 1px solid rgba(255,0,127,0.2) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }

    /* ── DATAFRAME ── */
    .stDataFrame {
        border: 1px solid rgba(255,0,127,0.2) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    .stDataFrame thead th {
        background: #1a1b2e !important;
        color: #9ca3af !important;
    }
    .stDataFrame tbody tr:hover td {
        background: rgba(255,0,127,0.05) !important;
    }

    /* Plotly charts */
    .js-plotly-plot { border-radius: 8px; }

    /* Status */
    .status-connected { color: #10b981; font-size: 11px; }
    .status-error     { color: #ff007f; font-size: 11px; }

    /* Heatmap table */
    .heatmap-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .heatmap-table th { padding: 6px 8px; color: #9ca3af; font-weight: 400; text-align: center; font-size: 10px; letter-spacing: 1px; }
    .heatmap-table td { padding: 6px 8px; text-align: center; border: 1px solid #0a0b14; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════
MESES = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
CORES = ['#3fb950','#58a6ff','#bc8cff','#e3b341','#f85149','#39d353','#79c0ff','#ffa657','#ff7b72','#56d364']
PLOTLY_LAYOUT = dict(
    paper_bgcolor='#161b22',
    plot_bgcolor='#161b22',
    font=dict(color='#8b949e', family='IBM Plex Sans'),
    xaxis=dict(gridcolor='rgba(255,255,255,0.04)', color='#8b949e'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.04)', color='#8b949e'),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=11)),
    margin=dict(l=10, r=10, t=30, b=10),
)

# ══════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════
def fmt_brl(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "R$ 0"
    return f"R$ {v:,.0f}".replace(",", ".")

def fmt_pct(v, decimals=1):
    return f"{v:.{decimals}f}%"

def delta_html(val, good_if_positive=True, suffix="%"):
    if val is None:
        return '<span class="kpi-delta-neutral">Primeiro ano</span>'
    good = val >= 0 if good_if_positive else val <= 0
    arrow = "▲" if val >= 0 else "▼"
    sign  = "+" if val >= 0 else ""
    cls   = "kpi-delta-up" if good else "kpi-delta-down"
    return f'<span class="{cls}">{arrow} {sign}{val:.1f}{suffix} vs ano anterior</span>'

def safe_num(v):
    try:
        if v is None or v == '' or (isinstance(v, float) and np.isnan(v)):
            return 0.0
        s = str(v).strip()
        s = s.replace('R$', '').replace('\xa0', '').strip()
        if ',' in s and '.' in s:
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            s = s.replace(',', '.')
        s = ''.join(c for c in s if c.isdigit() or c in '.,-')
        s = s.replace('-', '') if s.count('-') > 1 else s
        return float(s) if s and s not in ['.', ',', '-'] else 0.0
    except:
        return 0.0

# ══════════════════════════════════════════
# LEITURA DO GOOGLE SHEETS
# ══════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def carregar_google_sheets(sheet_id: str) -> dict:
    creds_dict = dict(st.secrets["gcp_service_account"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)

    sh = gc.open_by_key(sheet_id)
    abas = {ws.title: ws for ws in sh.worksheets() if ws.title.isdigit() and len(ws.title) == 4}

    dados = {}
    for ano, ws in sorted(abas.items()):
        valores = ws.get_all_values()
        if valores:
            dados[ano] = parsear_aba(valores)

    return dados
def parsear_aba(rows: list) -> dict:
    """
    Interpreta uma aba da planilha Texview.
    Estrutura: col A = Nível 1, col B = Nível 2, col C..N = Jan..Dez
    Seções identificadas por texto em col A: "1. Receita" e "2. Despesas"
    """
    def cell(r, c):
        row = rows[r] if r < len(rows) else []
        return str(row[c]).strip() if c < len(row) else ''

    def get_meses(r):
        # Meses sempre nas colunas 2..13 (C..N) conforme estrutura da planilha
        row = rows[r] if r < len(rows) else []
        return [safe_num(row[c]) if c < len(row) else 0.0 for c in range(2, 14)]

    linha_receita_total = -1
    linha_desp_total    = -1
    linha_saldo         = -1
    linhas_empresas     = []
    linhas_desp         = []
    em_receita          = False
    em_despesa          = False

    for r in range(len(rows)):
        a = cell(r, 0).strip()
        b = cell(r, 1).strip()
        a_low = a.lower()
        b_low = b.lower()

        # Detecta início de seção pela coluna A
        if 'receita' in a_low and ('1' in a_low or a_low.startswith('1')):
            em_receita = True; em_despesa = False
            # Verifica se já há uma empresa na coluna B desta mesma linha
            if b and b_low not in skip_b and 'total' not in b_low:
                linhas_empresas.append(r)
            continue
        if 'despesa' in a_low and ('2' in a_low or a_low.startswith('2')):
            em_receita = False; em_despesa = True
            if b and b_low not in skip_b and 'total' not in b_low:
                linhas_desp.append(r)
            continue

        # Total Mensal
        if 'total' in a_low and 'mensal' in a_low:
            if em_receita and linha_receita_total < 0:
                linha_receita_total = r
            elif em_despesa and linha_desp_total < 0:
                linha_desp_total = r
            continue

        # Saldo (col A)
        if a_low == 'saldo':
            linha_saldo = r
            continue

        # Linhas de dados: col A vazia, col B tem nome de empresa ou despesa
        skip_b = ['total', 'nivel', 'nível', 'nível 1', 'nível 2', '']
        if (not a) and b and b_low not in skip_b and not any(s in b_low for s in ['total mensal']):
            if em_receita:
                linhas_empresas.append(r)
            elif em_despesa:
                linhas_desp.append(r)

    # Fallback: busca nas linhas de resumo no final (col A = "Receita", "Despesas Totais", "Saldo")
    for r in range(len(rows)):
        a_low = cell(r, 0).lower()
        if a_low == 'receita' and linha_receita_total < 0:
            linha_receita_total = r
        if 'despesas totais' in a_low and linha_desp_total < 0:
            linha_desp_total = r
        if a_low == 'saldo' and linha_saldo < 0:
            linha_saldo = r

    receita_mensal = get_meses(linha_receita_total) if linha_receita_total >= 0 else [0.0]*12
    desp_mensal    = get_meses(linha_desp_total)    if linha_desp_total    >= 0 else [0.0]*12
    saldo_mensal   = get_meses(linha_saldo)         if linha_saldo         >= 0 else [0.0]*12

    receita_empresas = {}
    for r in linhas_empresas:
        nome = cell(r, 1)
        if not nome:
            continue
        vals = get_meses(r)
        if sum(vals) > 0:
            receita_empresas[nome] = vals

    desp_cats = {}
    for r in linhas_desp:
        nome = cell(r, 1)
        if not nome:
            continue
        vals = get_meses(r)
        if sum(vals) > 0:
            desp_cats[nome] = vals

    return {
        'receita_mensal':   receita_mensal,
        'desp_mensal':      desp_mensal,
        'saldo_mensal':     saldo_mensal,
        'receita_empresas': receita_empresas,
        'desp_cats':        desp_cats,
    }

# ══════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════
def render_kpis(d, d_prev, ano):
    tr = sum(d['receita_mensal'])
    td = sum(d['desp_mensal'])
    ts = sum(d['saldo_mensal'])
    margem = (ts / tr * 100) if tr else 0
    ratio  = (td / tr * 100) if tr else 0

    delta_r = delta_m = delta_d = delta_s = delta_ra = None
    if d_prev:
        ptr = sum(d_prev['receita_mensal'])
        ptd = sum(d_prev['desp_mensal'])
        pts = sum(d_prev['saldo_mensal'])
        pm  = (pts / ptr * 100) if ptr else 0
        pr  = (ptd / ptr * 100) if ptr else 0
        if ptr: delta_r  = (tr - ptr) / ptr * 100
        if ptd: delta_d  = (td - ptd) / ptd * 100
        if pts: delta_s  = (ts - pts) / pts * 100
        delta_m  = margem - pm
        delta_ra = ratio  - pr

    c1, c2, c3, c4, c5 = st.columns(5)

    kpis = [
        (c1, 'green',  'Receita Total',    fmt_brl(tr),          delta_html(delta_r, True)),
        (c2, 'red',    'Despesas Totais',  fmt_brl(td),          delta_html(delta_d, False)),
        (c3, 'blue',   'Saldo / Lucro',    fmt_brl(ts),          delta_html(delta_s, True)),
        (c4, 'gold',   'Margem Líquida',   fmt_pct(margem),      delta_html(delta_m, True, 'pp')),
        (c5, 'purple', 'Razão Desp/Rec',   fmt_pct(ratio),       delta_html(delta_ra, False, 'pp')),
    ]
    for col, cor, label, valor, delta in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card {cor}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{valor}</div>
                {delta}
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# GRÁFICO EVOLUÇÃO
# ══════════════════════════════════════════
def graf_evolucao(d):
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        name='Receita', x=MESES, y=d['receita_mensal'],
        marker_color='rgba(63,185,80,0.75)', offsetgroup=0
    ))
    fig.add_trace(go.Bar(
        name='Despesas', x=MESES, y=d['desp_mensal'],
        marker_color='rgba(248,81,73,0.75)', offsetgroup=1
    ))
    fig.add_trace(go.Scatter(
        name='Saldo', x=MESES, y=d['saldo_mensal'],
        mode='lines+markers', line=dict(color='#58a6ff', width=2),
        marker=dict(size=5), fill='tozeroy', fillcolor='rgba(88,166,255,0.06)'
    ), secondary_y=True)

    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(
        barmode='group', height=300,
        legend=dict(font=dict(color='#ffffff')),
        yaxis=dict(tickformat=',.0f', tickprefix='R$', gridcolor='rgba(255,255,255,0.04)', tickfont=dict(color='white')),
        yaxis2=dict(tickformat=',.0f', tickprefix='R$', gridcolor='rgba(0,0,0,0)', overlaying='y', side='right', tickfont=dict(color='white')),
        xaxis=dict(tickfont=dict(color='white')),
    )
    return fig

# ══════════════════════════════════════════
# GRÁFICO PIZZA DESPESAS
# ══════════════════════════════════════════
def graf_pizza_despesas(d):
    totais = {k: sum(v) for k, v in d['desp_cats'].items()}
    sorted_items = sorted(totais.items(), key=lambda x: x[1], reverse=True)[:8]

    fig = go.Figure(go.Pie(
        labels=[x[0] for x in sorted_items],
        values=[x[1] for x in sorted_items],
        hole=0.55,
        marker_colors=CORES,
        textinfo='percent',
        hovertemplate='<b>%{label}</b><br>R$ %{value:,.0f}<br>%{percent}<extra></extra>'
    ))
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(height=300, showlegend=True,
                      legend=dict(orientation='v', x=1.02, y=0.5, font=dict(size=10, color='white')))
    fig.update_traces(textfont=dict(color='white'))
    return fig

# ══════════════════════════════════════════
# GRÁFICO REPRESENTADAS
# ══════════════════════════════════════════
def graf_representadas(d):
    totais = {k: sum(v) for k, v in d['receita_empresas'].items() if sum(v) > 0}
    sorted_items = sorted(totais.items(), key=lambda x: x[1], reverse=True)

    fig = go.Figure(go.Bar(
        x=[x[1] for x in sorted_items],
        y=[x[0] for x in sorted_items],
        orientation='h',
        marker_color=[CORES[i % len(CORES)] for i in range(len(sorted_items))],
        hovertemplate='<b>%{y}</b><br>R$ %{x:,.0f}<extra></extra>'
    ))
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(height=280,
                      xaxis=dict(tickformat=',.0f', tickprefix='R$', gridcolor='rgba(255,255,255,0.04)'),
                      yaxis=dict(autorange='reversed'))
    return fig

# ══════════════════════════════════════════
# GRÁFICO SALDO ACUMULADO
# ══════════════════════════════════════════
def graf_saldo_acumulado(d):
    acum = list(np.cumsum(d['saldo_mensal']))
    fig = go.Figure(go.Scatter(
        x=MESES, y=acum, mode='lines+markers',
        line=dict(color='#e3b341', width=2),
        marker=dict(size=6, color='#e3b341',
                    line=dict(color='#0d1117', width=2)),
        fill='tozeroy', fillcolor='rgba(227,179,65,0.08)',
        hovertemplate='<b>%{x}</b><br>Acumulado: R$ %{y:,.0f}<extra></extra>'
    ))
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(height=280,
                      yaxis=dict(tickformat=',.0f', tickprefix='R$', gridcolor='rgba(255,255,255,0.04)'))
    return fig

# ══════════════════════════════════════════
# GRÁFICO COMPARATIVO ANUAL
# ══════════════════════════════════════════
def graf_comparativo_anual(dados):
    anos = sorted(dados.keys())
    receitas  = [sum(dados[a]['receita_mensal']) for a in anos]
    despesas  = [sum(dados[a]['desp_mensal'])    for a in anos]
    saldos    = [sum(dados[a]['saldo_mensal'])   for a in anos]

    fig = go.Figure()
    fig.add_trace(go.Bar(name='Receita',  x=anos, y=receitas,  marker_color='rgba(63,185,80,0.8)'))
    fig.add_trace(go.Bar(name='Despesas', x=anos, y=despesas,  marker_color='rgba(248,81,73,0.8)'))
    fig.add_trace(go.Scatter(name='Saldo', x=anos, y=saldos,
                             mode='lines+markers', line=dict(color='#58a6ff', width=2),
                             marker=dict(size=7)))
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(barmode='group', height=320,
                      yaxis=dict(tickformat=',.0f', tickprefix='R$', gridcolor='rgba(255,255,255,0.04)'),
                      legend=dict(orientation='h', y=1.12, font=dict(color='#ffffff')))
    return fig

# ══════════════════════════════════════════
# HEATMAP RECEITA
# ══════════════════════════════════════════
def graf_heatmap(dados):
    anos = sorted(dados.keys())
    matrix = [[dados[a]['receita_mensal'][m] for m in range(12)] for a in anos]

    fig = go.Figure(go.Heatmap(
        z=matrix, x=MESES, y=anos,
        colorscale=[[0, '#3fb950'], [0.5, '#1a5c2a'], [1, '#1a2a1a']],
        hovertemplate='<b>%{y} — %{x}</b><br>R$ %{z:,.0f}<extra></extra>',
        texttemplate='R$%{z:,.0f}',
        textfont=dict(size=9, color='white'),
        showscale=True,
        colorbar=dict(tickformat=',.0f', tickprefix='R$', tickfont=dict(color='#8b949e'), bgcolor='#161b22')
    ))
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(height=280,
                      xaxis=dict(side='top', gridcolor='rgba(0,0,0,0)'),
                      yaxis=dict(gridcolor='rgba(0,0,0,0)'))
    return fig

# ══════════════════════════════════════════
# TABELA REPRESENTADAS
# ══════════════════════════════════════════
def render_tabela_representadas(d, d_prev):
    totais = {k: sum(v) for k, v in d['receita_empresas'].items() if sum(v) > 0}
    total_r = sum(totais.values())
    sorted_items = sorted(totais.items(), key=lambda x: x[1], reverse=True)

    rows = []
    for i, (nome, val) in enumerate(sorted_items):
        pct = val / total_r * 100 if total_r else 0
        ticket = val / 12

        tendencia = "🆕 NOVA"
        if d_prev and nome in d_prev['receita_empresas']:
            vp = sum(d_prev['receita_empresas'][nome])
            if vp > 0:
                delta = (val - vp) / vp * 100
                tendencia = f"{'▲' if delta >= 0 else '▼'} {'+' if delta >= 0 else ''}{delta:.1f}%"

        rows.append({
            '#': i + 1,
            'Empresa': nome,
            'Receita Anual': val,
            '% do Total': pct,
            'Ticket Médio/Mês': ticket,
            'Tendência': tendencia
        })

    if not rows:
        st.info("Nenhuma empresa representada encontrada para este ano.")
        return

    df = pd.DataFrame(rows)

    # Linha de total
    total_ticket = df['Ticket Médio/Mês'].sum()
    total_row = pd.DataFrame([{
        '#': '',
        'Empresa': '▸ TOTAL',
        'Receita Anual': total_r,
        '% do Total': 100.0,
        'Ticket Médio/Mês': total_ticket,
        'Tendência': '',
    }])
    df = pd.concat([df, total_row], ignore_index=True)

    df['Receita Anual']    = df['Receita Anual'].apply(fmt_brl)
    df['% do Total']       = df['% do Total'].apply(lambda x: f"{x:.1f}%")
    df['Ticket Médio/Mês'] = df['Ticket Médio/Mês'].apply(fmt_brl)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            '#':                st.column_config.TextColumn(width='small'),
            'Empresa':          st.column_config.TextColumn(width='medium'),
            'Receita Anual':    st.column_config.TextColumn(width='medium'),
            '% do Total':       st.column_config.TextColumn(width='small'),
            'Ticket Médio/Mês': st.column_config.TextColumn(width='medium'),
            'Tendência':        st.column_config.TextColumn(width='small'),
        }
    )


# ══════════════════════════════════════════
# INSIGHTS
# ══════════════════════════════════════════
def render_insights(d, d_prev, ano):
    tr = sum(d['receita_mensal'])
    td = sum(d['desp_mensal'])
    ts = sum(d['saldo_mensal'])
    margem = (ts / tr * 100) if tr else 0

    melhor_idx = d['receita_mensal'].index(max(d['receita_mensal']))
    pior_idx   = d['receita_mensal'].index(min(d['receita_mensal']))

    totais_emp = {k: sum(v) for k, v in d['receita_empresas'].items() if sum(v) > 0}
    top1 = max(totais_emp.items(), key=lambda x: x[1]) if totais_emp else None
    top1_pct = (top1[1] / tr * 100) if top1 and tr else 0

    totais_desp = {k: sum(v) for k, v in d['desp_cats'].items()}
    top_desp = max(totais_desp.items(), key=lambda x: x[1]) if totais_desp else None
    top_desp_pct = (top_desp[1] / td * 100) if top_desp and td else 0

    tributos = sum(totais_desp.get(k, 0) for k in ['DAS', 'IRRF/INSS', 'Simples', 'DARF'])
    trib_pct = (tributos / td * 100) if td else 0

    n_reps = len([k for k, v in d['receita_empresas'].items() if sum(v) > 0])

    insights = [
        {
            'cor': 'green', 'badge': 'badge-green', 'tipo': 'OPORTUNIDADE',
            'titulo': f"{top1[0]} lidera com {top1_pct:.1f}% da receita" if top1 else "Receita concentrada",
            'texto': (f"A empresa <strong>{top1[0]}</strong> gerou <strong>{fmt_brl(top1[1])}</strong> em {ano} ({top1_pct:.1f}% do total). "
                      + ("Alta concentração — diversificar reduz risco." if top1_pct > 40 else "Portfólio relativamente bem distribuído.")) if top1 else "—"
        },
        {
            'cor': 'red', 'badge': 'badge-red', 'tipo': 'ALERTA',
            'titulo': f"{top_desp[0]} = {top_desp_pct:.1f}% das despesas" if top_desp else "Maior despesa",
            'texto': (f"<strong>{top_desp[0]}</strong> é o maior custo ({fmt_brl(top_desp[1])}). "
                      + ("Custo fixo de folha — avaliar produtividade." if top_desp and top_desp[0] == 'Kathia'
                         else "Carga tributária relevante — revisar regime fiscal com contador." if top_desp and top_desp[0] in ['Simples','DAS','IRRF/INSS']
                         else "Revisar pode gerar economia significativa.")) if top_desp else "—"
        },
        {
            'cor': 'gold', 'badge': 'badge-gold', 'tipo': 'SAZONALIDADE',
            'titulo': f"Melhor: {MESES[melhor_idx]} · Pior: {MESES[pior_idx]}",
            'texto': (f"<strong>{MESES[melhor_idx]}</strong> foi o mês mais forte ({fmt_brl(d['receita_mensal'][melhor_idx])}), "
                      f"enquanto <strong>{MESES[pior_idx]}</strong> foi o mais fraco ({fmt_brl(d['receita_mensal'][pior_idx])}). "
                      "Ações comerciais nos meses fracos suavizam o fluxo de caixa.")
        },
        {
            'cor': 'green', 'badge': 'badge-green', 'tipo': 'RESULTADO',
            'titulo': f"Margem líquida de {margem:.1f}%",
            'texto': (f"Saldo de <strong>{fmt_brl(ts)}</strong> em {ano}. "
                      + ("Excelente saúde — momento ideal para expandir." if margem > 60
                         else "Margem saudável — espaço para novos investimentos." if margem > 40
                         else "Margem pode melhorar com redução de custos variáveis."))
        },
        {
            'cor': 'blue', 'badge': 'badge-blue', 'tipo': 'ESTRATÉGIA',
            'titulo': f"Tributação = {trib_pct:.1f}% das despesas",
            'texto': (f"Encargos tributários totalizaram <strong>{fmt_brl(tributos)}</strong> em {ano}. "
                      "Uma revisão com contador especializado em representação comercial pode identificar oportunidades de redução legal.")
        },
        {
            'cor': 'red' if n_reps < 4 else 'gold',
            'badge': 'badge-red' if n_reps < 4 else 'badge-gold',
            'tipo': 'ALERTA' if n_reps < 4 else 'ATENÇÃO',
            'titulo': f"{'Carteira enxuta' if n_reps < 4 else 'Diversificação'}: {n_reps} representadas ativas",
            'texto': (f"Apenas <strong>{n_reps} representadas</strong> ativas em {ano}. Prospectar novas marcas pode estabilizar o faturamento." if n_reps < 4
                      else f"<strong>{n_reps} representadas</strong> ativas. Priorizar as que crescem e revisar as estagnadas aumenta eficiência.")
        },
    ]

    cols = st.columns(3)
    for i, ins in enumerate(insights):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="insight-card {ins['cor']}">
                <span class="insight-badge {ins['badge']}">{ins['tipo']}</span>
                <div class="insight-title">{ins['titulo']}</div>
                <div class="insight-text">{ins['texto']}</div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 16px 0 24px;">
            <div style="
                background: linear-gradient(135deg, #ff007f, #8b5cf6);
                width: 52px; height: 52px; border-radius: 12px;
                display: inline-flex; align-items: center; justify-content: center;
                font-size: 26px; font-weight: 900; color: #fff;
                box-shadow: 0 0 20px rgba(255,0,127,0.4);
                margin-bottom: 12px;
            ">T</div>
            <div style="
                font-size: 20px; font-weight: 800;
                background: linear-gradient(90deg, #ff007f, #8b5cf6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: 3px;
            ">TEXVIEW</div>
            <div style="font-size: 11px; color: #9ca3af; margin-top: 6px; letter-spacing: 1px;">
                Dashboard Financeiro
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.session_state.dados = None
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.session_state.dados = None
            st.rerun()

        return 

# ══════════════════════════════════════════
# APP PRINCIPAL
# ══════════════════════════════════════════
def main():
    if not check_login():
        return

    render_sidebar()

    if 'dados' not in st.session_state:
        st.session_state.dados = None
    if 'modo' not in st.session_state:
        st.session_state.modo = None

    # Carrega automaticamente ao fazer login
    if st.session_state.dados is None:
        with st.spinner("Carregando dados..."):
            try:
                dados = carregar_google_sheets(SHEET_ID)
                st.session_state.dados = dados
                st.session_state.modo  = 'sheets'
            except Exception as e:
                st.error(f"Erro ao carregar planilha: {str(e)}")
                return

    # Sem dados — tela inicial
    if st.session_state.dados is None:
        st.markdown("""
        <div style="text-align:center;padding:80px 40px;">
            <div style="font-size:64px;margin-bottom:16px;">🧵</div>
            <h1 style="font-size:36px;margin-bottom:8px;">
                <span style="color:#29053b;">Tex</span><span style="color:#8b949e;">view Dashboard</span>
            </h1>
            <p style="color:#8b949e;font-size:16px;max-width:500px;margin:0 auto 32px;">
                Conecte sua planilha do Google Sheets ou clique em
                <strong style="color:#e6edf3">Ver Dados de Demonstração</strong>
                para explorar o dashboard.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── DADOS CARREGADOS ──
    dados = st.session_state.dados
    anos  = sorted(dados.keys())

    # Status
    modo_txt = "📊 Modo demonstração" if st.session_state.modo == 'demo' else f"🔗 Google Sheets · {st.session_state.get('sheet_id','')[:20]}..."
    st.markdown(f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;color:#3fb950;margin-bottom:16px;">{modo_txt} · Atualizado {datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

    # Seletor de ano
    col_sel, col_info = st.columns([2, 8])
    with col_sel:
        ano = st.selectbox("Ano", anos, index=len(anos)-1, label_visibility="collapsed")

    d      = dados[ano]
    d_prev = dados.get(str(int(ano) - 1))

    # ── KPIs ──
    st.markdown('<div class="section-header">INDICADORES DO ANO</div>', unsafe_allow_html=True)
    render_kpis(d, d_prev, ano)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── COMPARATIVO HISTÓRICO ──
    st.markdown('<div class="section-header">EVOLUÇÃO HISTÓRICA</div>', unsafe_allow_html=True)
    st.plotly_chart(graf_comparativo_anual(dados), use_container_width=True, config={'displayModeBar': False})

    # ── EVOLUÇÃO + PIZZA ──
    st.markdown('<div class="section-header">ANÁLISE DO ANO SELECIONADO</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("**Receita × Despesas × Saldo Mensal**")
        st.plotly_chart(graf_evolucao(d), use_container_width=True, config={'displayModeBar': False})
    with c2:
        st.markdown("**Composição das Despesas**")
        st.plotly_chart(graf_pizza_despesas(d), use_container_width=True, config={'displayModeBar': False})

    # ── REP + ACUMULADO ──
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Receita por Empresa Representada**")
        st.plotly_chart(graf_representadas(d), use_container_width=True, config={'displayModeBar': False})
    with c4:
        st.markdown("**Saldo Acumulado no Ano**")
        st.plotly_chart(graf_saldo_acumulado(d), use_container_width=True, config={'displayModeBar': False})

    # ── HEATMAP ──
    st.markdown('<div class="section-header">MAPA DE CALOR — RECEITA MENSAL POR ANO</div>', unsafe_allow_html=True)
    st.plotly_chart(graf_heatmap(dados), use_container_width=True, config={'displayModeBar': False})

    # ── TABELA ──
    st.markdown('<div class="section-header">RANKING DE REPRESENTADAS</div>', unsafe_allow_html=True)
    render_tabela_representadas(d, d_prev)

    # ── INSIGHTS ──
    st.markdown('<div class="section-header">INSIGHTS & RECOMENDAÇÕES ESTRATÉGICAS</div>', unsafe_allow_html=True)
    render_insights(d, d_prev, ano)

    st.markdown("<br><hr style='border-color:#2d3748'><div style='text-align:center;font-family:IBM Plex Mono,monospace;font-size:10px;color:#4a5568;'>Texview · Dashboard Financeiro · Python + Streamlit</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    if check_login():
        main()
