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
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    .main { background-color: #0d1117; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* KPI Cards */
    .kpi-card {
        background: #161b22;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 8px;
        border-top: 2px solid;
    }
    .kpi-card.green  { border-top-color: #3fb950; }
    .kpi-card.red    { border-top-color: #f85149; }
    .kpi-card.blue   { border-top-color: #58a6ff; }
    .kpi-card.gold   { border-top-color: #e3b341; }
    .kpi-card.purple { border-top-color: #bc8cff; }

    .kpi-label { font-family: 'IBM Plex Mono', monospace; font-size: 10px;
                 letter-spacing: 2px; text-transform: uppercase; color: #8b949e; margin-bottom: 8px; }
    .kpi-value { font-size: 26px; font-weight: 700; color: #e6edf3; margin-bottom: 6px; }
    .kpi-delta-up   { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #3fb950; }
    .kpi-delta-down { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #f85149; }
    .kpi-delta-neutral { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #8b949e; }

    /* Insight cards */
    .insight-card {
        background: #161b22; border: 1px solid #2d3748;
        border-radius: 8px; padding: 18px; margin-bottom: 10px;
        border-left: 3px solid;
    }
    .insight-card.green  { border-left-color: #3fb950; }
    .insight-card.red    { border-left-color: #f85149; }
    .insight-card.gold   { border-left-color: #e3b341; }
    .insight-card.blue   { border-left-color: #58a6ff; }

    .insight-badge {
        font-family: 'IBM Plex Mono', monospace; font-size: 9px;
        letter-spacing: 2px; text-transform: uppercase;
        padding: 2px 8px; border-radius: 2px; display: inline-block; margin-bottom: 8px;
    }
    .badge-green  { background: rgba(63,185,80,.15);  color: #3fb950; }
    .badge-red    { background: rgba(248,81,73,.15);  color: #f85149; }
    .badge-gold   { background: rgba(227,179,65,.15); color: #e3b341; }
    .badge-blue   { background: rgba(88,166,255,.15); color: #58a6ff; }

    .insight-title { font-size: 14px; font-weight: 600; color: #e6edf3; margin-bottom: 6px; }
    .insight-text  { font-size: 12px; color: #8b949e; line-height: 1.7; }
    .insight-text strong { color: #e6edf3; }

    /* Section headers */
    .section-header {
        font-family: 'IBM Plex Mono', monospace; font-size: 10px;
        letter-spacing: 3px; text-transform: uppercase; color: #8b949e;
        border-bottom: 1px solid #2d3748; padding-bottom: 8px; margin-bottom: 16px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #2d3748; }
    [data-testid="stSidebar"] .stSelectbox label { color: #8b949e !important; }

    /* Plotly charts background */
    .js-plotly-plot { border-radius: 8px; }

    /* Status badge */
    .status-connected { color: #3fb950; font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
    .status-error     { color: #f85149; font-family: 'IBM Plex Mono', monospace; font-size: 11px; }

    /* Heatmap table */
    .heatmap-table { width: 100%; border-collapse: collapse; font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
    .heatmap-table th { padding: 6px 8px; color: #8b949e; font-weight: 400; text-align: center; font-size: 10px; letter-spacing: 1px; }
    .heatmap-table td { padding: 6px 8px; text-align: center; border: 1px solid #0d1117; }
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
        colorscale=[[0, '#1a2a1a'], [0.5, '#1a5c2a'], [1, '#3fb950']],
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
    df['Receita Anual']    = df['Receita Anual'].apply(fmt_brl)
    df['% do Total']       = df['% do Total'].apply(lambda x: f"{x:.1f}%")
    df['Ticket Médio/Mês'] = df['Ticket Médio/Mês'].apply(fmt_brl)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            '#':                st.column_config.NumberColumn(width='small'),
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
            <div style="background:#29053b;width:48px;height:48px;border-radius:4px;
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:24px;font-weight:900;color:#000;margin-bottom:10px;">T</div>
            <div style="font-size:20px;font-weight:700;">
                <span style="color:#29053b !important;">Tex</span><span style="color:#ffffff !important;">view</span>
            </div>
            <div style="font-size:11px;color:#8b949e;margin-top:4px;
                        font-family:'IBM Plex Mono',monospace;letter-spacing:1px;">
                Dashboard Financeiro
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#8b949e;margin-bottom:12px;">Conexão Google Sheets</div>', unsafe_allow_html=True)

        sheet_id = st.text_input(
            "ID da Planilha",
            value=st.session_state.get('sheet_id', ''),
            placeholder="Cole o ID da planilha aqui",
            help="Encontre na URL: docs.google.com/spreadsheets/d/SEU_ID/edit"
        )

        creds_file = None

        conectar = st.button("🔗 Conectar Planilha", use_container_width=True, type="primary")

        st.markdown("---")

        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown('<div style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#8b949e;margin-bottom:12px;">Modo Demo</div>', unsafe_allow_html=True)
        demo = st.button("▶ Ver Dados de Demonstração", use_container_width=True)

        return sheet_id, creds_file, conectar, demo

# ══════════════════════════════════════════
# DADOS DE DEMO (dados reais da Texview)
# ══════════════════════════════════════════
def dados_demo():
    return {
        "2020":{"receita_mensal":[7776.24,20586.89,23603.53,19507.47,14279.49,14088.94,15392.91,25016.98,23695.88,37292.26,29039.14,33894.29],"desp_mensal":[4026.47,4825.66,5642.49,14992.46,4998.72,3322.77,5224.21,4337.77,4971.51,4910.05,5743.61,5435.64],"saldo_mensal":[3749.77,15761.23,17961.04,4515.01,9280.77,10766.17,10168.7,20679.21,18724.37,32382.21,23295.53,28458.65],"receita_empresas":{"Farbe":[4395.4,16418.74,15956.32,9416.78,6430.31,5684.12,8576.83,14997.24,14790.78,27890.71,24804.56,19868.77],"Milesima":[283.89,1106.04,2646.7,4167.82,5519,1123.65,2424.64,1520.39,2332.94,654.65,842.1,369],"BHM":[2396.84,2338.36,4214.31,5128.61,2000,7281.17,3956.25,8131.27,5495.46,5693.13,1620.45,9975.73],"Blufitex":[589.27,555.75,786.2,711.43,330.18,0,435.19,368.08,1076.7,756.82,822.03,534.25],"Stamp Lite":[0,0,0,0,0,0,0,0,0,1799.95,0,2275.92]},"desp_cats":{"Kathia":[0,2225,2225,2225,2225,2225,2225,2225,2225,2225,2225,2225],"Simples":[1427.1,503.66,1313.04,11555.22,1555.22,0,947.47,1011.8,1630.84,1575.03,2408.59,2040.24],"Contabilidade":[1039,200,200,200,200,200,200,200,200,200,200,200],"GPS":[550,550,550,550,550,550,550,550,550,550,550,550],"Telefone":[277.97,277,284.45,284.55,277.77,277.77,284.27,277.97,295.67,290.02,290.02,350.4]}},
        "2021":{"receita_mensal":[27205.22,22430.66,26829.95,34033.21,38209.86,41978.45,37573,35384.22,41421.49,39691.91,32409.37,36263.77],"desp_mensal":[6419.72,5415.15,5250.66,5363.97,6125.39,8077.96,8477.69,8198.53,7789.44,8601.34,8713.88,8081.79],"saldo_mensal":[20785.5,17015.51,21579.29,28669.24,32084.47,33900.49,29095.31,27185.69,33632.05,31090.57,23695.49,28181.98],"receita_empresas":{"Farbe":[18748.76,18126.05,17452.23,27526.84,30018.48,31060.25,31231.07,24240.15,28945.83,30794.37,27421.98,24160.76],"Milesima":[1961.13,1984.77,4256.54,562.33,3489.47,1077.9,1452.21,6115.04,3519.12,2248.41,1208.25,5701.69],"BHM":[4303.3,1492.86,1513.08,3152.07,2589.14,8424.88,2663.51,368.71,4743.39,2420,2502.75,1473.32],"Blufitex":[107.41,629.4,1258.05,2134.93,1424.8,550.65,1081.83,1023.06,1511.11,571.56,504.17,695.05],"Stamp Lite":[1776,0,1959.33,0,531.97,541.51,1144.38,2969.7,2269.14,2715.03,727.32,2087]},"desp_cats":{"Kathia":[2225,2225,2225,2225,2225,2225,2225,2225,2225,2225,2225,2225],"Simples":[2273.75,1887.18,1722.69,1836,2597.42,2981.84,3382.97,3082.37,2653.96,3462.95,3211.78,2823.75],"BDMG":[0,0,0,0,0,1611.15,1609.75,1631.19,1644.53,1646.7,1819.67,1665.85],"Contabilidade":[200,344,344,344,344,344,344,344,344,344,516,344],"GPS":[550,550,550,550,550,550,550,550,550,550,550,550]}},
        "2022":{"receita_mensal":[13715.51,30564.32,40706.41,29737.2,28376.39,40694.33,32064.57,38918.34,35169.34,30924.48,24016.08,31760.92],"desp_mensal":[8563.23,12178.23,14562.06,16911.77,15647.97,14273.68,13316.47,12068.75,10881.98,14067.21,10499.89,9330.38],"saldo_mensal":[5152.28,18386.09,26144.35,12825.43,12728.42,26420.65,18748.1,26849.59,24287.36,16857.27,13516.19,22430.54],"receita_empresas":{"Farbe":[11387.84,25703.45,30237.26,26740.95,24667.15,35033.26,26935.51,31517.03,30171.44,25449.06,19553.4,22463.22],"Milesima":[835.23,881.29,5416.36,248.66,1473.17,952.96,2323.76,4134.07,1401.77,2745.89,239.13,1276.59],"BHM":[560,1834.78,1344.17,1634.17,265.8,1875.95,950,0,799.3,0,687.2,0],"Stamp Lite":[612.54,1304.1,2141.91,0,1218.42,896.16,1135.08,2736,2146.59,2175.51,2114.85,3415.77]},"desp_cats":{"Kathia":[2225,4793,4793,4793,4793,4793,4973,4506.84,3783,3783,3783,3783],"IRRF/INSS":[0,2732,2414,2414,2414,2414,2414,2414,1434.08,1434.08,1434.08,1434.68],"BDMG":[1712.42,1712.79,1682,1711.73,1687.42,1718.68,1680.98,1699.7,1659.35,1660.58,1783.63,1600.13],"Simples":[2872.26,2073.59,4796.59,6445.95,0,4506.84,3412.07,2610.83,3143.65,6045.76,2639.89,1786.74]}},
        "2023":{"receita_mensal":[14215.57,23307.54,33371.1,36507.74,28325.95,30373.98,34727.89,31090.21,36945.05,24150.29,37035.35,28865.13],"desp_mensal":[9622.52,8712.9,10468.5,10631.12,11361.72,9844.33,9788.65,10083.08,9808.67,8804.17,9543.21,10123.32],"saldo_mensal":[4593.05,14594.64,22902.6,25876.62,16964.23,20529.65,24939.24,21007.13,27136.38,15346.12,27492.14,18741.81],"receita_empresas":{"Farbe":[11473.65,17751.89,23194.36,24517.23,25395.91,24850.89,29437.33,21855.03,26847.84,20595.16,25026.29,20023.02],"Milesima":[1173.19,3740.84,327.85,7815.99,181.45,943.79,1799.48,5119.03,5924.47,839.07,5198.06,4969.34],"Stamp Lite":[0,0,7554.36,2178.96,375.03,1918.86,1663.74,1572.75,2601.72,862.44,3809.52,912.51],"Minas Bojo":[909.2,503.04,1452.31,624.14,515.46,1157.32,420.08,824.2,283.23,590.37,482.69,1950.36]},"desp_cats":{"Kathia":[3783,3783,3783,3783,3783,3799,3799,3799,3798,3799,3798,3798],"IRRF/INSS":[1434.68,1434.68,1434.68,1434.68,1434.68,0,0,0,0,1403.48,1438.96,1403.48],"Simples":[2095.04,1128.41,1858.56,2054.31,2808.74,2293.18,2283.78,2598.45,2342.31,2797.96,1850,2676.9],"DARF":[0,0,0,0,0,1403.48,1403.48,1403.48,1403.48,0,0,0]}},
        "2024":{"receita_mensal":[16722.65,22365.18,32013.09,36845.14,37511.25,41963.24,24910.93,18881.17,31769.82,19963.41,33946.07,47750.34],"desp_mensal":[10746.21,8809.65,9458.67,9960.98,10549.62,10522.35,11089.88,9394.64,8944.12,9676.02,10346.87,10927.5],"saldo_mensal":[5976.44,13555.53,22554.42,26884.16,26961.63,31440.89,13821.05,9486.53,22825.7,10287.39,23599.2,36822.84],"receita_empresas":{"Farbe":[12995.54,18676.58,21828.64,24390.85,24183.36,35657.49,15968.95,11386.91,22244.23,12049.75,20618.3,29586.4],"Milesima":[1286.58,1850.33,4550,5486.57,7203.3,4975.02,3784.23,3927.78,3583.12,2726.02,214.59,3490.47],"Stamp Lite":[1097.37,0,2566.56,3808.77,2101.65,39.88,1202.94,0,3931.71,980.16,3100.02,4762.68],"Nova Textil":[0,0,1040,1216.84,1636.62,0,0,0,0,1857.47,4940,3924.81],"Malhas Wilson":[912.86,730.86,489.94,126.62,313.33,375.55,193.6,103.11,0,348.6,2654.12,3816.66]},"desp_cats":{"Kathia":[3798,3798,3809,3809,3810,3809,3809,3810,3810,3810,3810,3810],"IRRF/INSS":[1403.48,1403.48,1384.4,1381.4,1381.4,1381.4,1381.4,1381.4,1381.4,1381.4,1381.4,1381.4],"DAS":[0,1275.95,1802.52,2296.25,2616.79,2714.79,3498,1956.44,1495,2283.77,1384.13,2065.47],"Unimed":[1760.24,1438.96,1438.96,1438.96,1438.96,1438.96,1438.96,1438.96,1438.96,1438.96,1572.2,1572.7],"Contabilidade":[427.13,457.86,457.86,457.86,457.86,457.86,457.86,457.86,457.86,457.86,457.86,457.86]}},
        "2025":{"receita_mensal":[20412.62,25711.23,34050.07,29026.73,26609.61,29732.98,25154.64,35066.24,29103.67,34688.12,34505.72,36032.22],"desp_mensal":[12943.87,10262.31,10460.95,11399.39,10864.65,10637.87,10994.43,10838.68,11302.38,10983.42,11239.31,11568.28],"saldo_mensal":[7468.75,15448.92,23589.12,17627.34,15744.96,19095.11,14160.21,24227.56,17801.29,23704.7,23266.41,24463.94],"receita_empresas":{"Farbe":[13259.57,14389.37,21544.27,14838.77,15413.37,17438.73,16039.42,23031.81,20829.12,23389.97,23167.8,28880.64],"Nova Textil":[3761,4276.43,5318,3730,5507.41,2006,1316.51,3442.68,3219.35,4260,1400,2100],"Malhas Wilson":[2847.62,408.95,489.14,930.23,1397.61,958.86,1201.01,2659.9,1101.18,1295.05,2098.39,1060.1],"Stamp Lite":[322.2,2847.9,2456.85,3645.18,678.06,3935.37,1036.84,1839.99,718.5,1652.1,2678.61,1032.6],"Milesima":[119.03,1424.93,2970.73,4458.98,2161.67,4140.32,5002.47,3181.5,1773.21,1661.41,3980.47,2495.78]},"desp_cats":{"Kathia":[3809,3809,3810,3810,3810,3822,3822,3822,3822,3822,3822,3822],"IRRF/INSS":[1381.4,1381.4,1381.4,1381.4,1381.4,1355.96,1355.96,1355.96,1355.96,1355.96,1355.96,1355.96],"DAS":[3095.67,1340.5,1486.61,2077.41,1736.16,1628.23,1853.95,1758.97,2294.56,1982.6,2242.97,2394.81],"Pronamp":[1562.45,1550,1486.31,1500,1534.8,1497.69,1533.8,1536.43,1535,1479.24,1442.16,1406.71],"Unimed":[1572.7,1572.7,1572.7,1682.27,1682.27,1682.27,1682.27,1682.27,1682.27,1682.27,1834.36,1834.36]}}
    }

# ══════════════════════════════════════════
# APP PRINCIPAL
# ══════════════════════════════════════════
def main():
    sheet_id, creds_file, conectar, demo = render_sidebar()

    # Inicializa session state
    if 'dados' not in st.session_state:
        st.session_state.dados = None
    if 'modo' not in st.session_state:
        st.session_state.modo = None

    # Botão demo
    if demo:
        st.session_state.dados = dados_demo()
        st.session_state.modo  = 'demo'

    # Botão conectar
    if conectar:
        if not sheet_id:
            st.sidebar.error("Cole o ID da planilha.")
        else:
            with st.spinner("Conectando ao Google Sheets..."):
                try:
                    dados = carregar_google_sheets(sheet_id)
                    st.session_state.dados = dados
                    st.session_state.modo  = 'sheets'
                    st.session_state.sheet_id = sheet_id
                    st.sidebar.success(f"✅ Conectado! {len(dados)} anos carregados.")
                except Exception as e:
                    st.sidebar.error(f"Erro: {str(e)}")

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
    main()
