# 🧵 Texview — Dashboard Financeiro (Python + Streamlit)

Dashboard financeiro para representação comercial têxtil,
construído com Python, Streamlit e Plotly.

---

## 🚀 Como Rodar Localmente

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Rodar o app
```bash
streamlit run app.py
```

O dashboard abre automaticamente em `http://localhost:8501`

---

## 🔗 Conectar ao Google Sheets (Planilha Privada)

Esta versão usa **Service Account** — mais simples que OAuth para uso local.

### Passo 1 — Google Cloud Console
1. Acesse console.cloud.google.com
2. Crie ou selecione o projeto `Texview Dashboard`
3. Ative a **Google Sheets API**

### Passo 2 — Criar Service Account
1. APIs e Serviços → Credenciais → + Criar credencial → **Conta de serviço**
2. Nome: `texview-dashboard`
3. Após criar, clique na conta → aba **Chaves** → Adicionar chave → JSON
4. Baixe o arquivo `.json` gerado

### Passo 3 — Compartilhar a planilha
1. Abra o arquivo JSON e copie o campo `client_email`
   (algo como `texview-dashboard@projeto.iam.gserviceaccount.com`)
2. Na planilha Google Sheets, clique em **Compartilhar**
3. Cole o `client_email` com permissão de **Visualizador**

### Passo 4 — Conectar no Dashboard
1. Rode o app: `streamlit run app.py`
2. Na sidebar, cole o **ID da planilha**
3. Faça upload do arquivo **JSON de credenciais**
4. Clique em **Conectar Planilha**

---

## 📊 Estrutura da Planilha

A planilha deve ter abas nomeadas com o ano (ex: `2024`, `2025`).
Cada aba segue o padrão:

```
Linha 4:  Cabeçalhos (Nível 1 | Nível 2 | Janeiro | ... | Dezembro | Total)
Linha 5:  1. Receita  | Farbe     | [valores mensais]
...
Linha 14: (última empresa)
Linha 15: Total Mensal | | [totais mensais de receita]
Linha 16: 2. Despesas | GPS       | [valores mensais]
...
Linha 38: (última despesa)
Linha 39: Total Mensal | | [totais mensais de despesas]
Linha 42: Saldo        | | [saldo mensal]
```

---

## ☁️ Deploy na Nuvem (Streamlit Community Cloud — Gratuito)

1. Suba o projeto para um repositório GitHub
2. Acesse share.streamlit.io
3. Conecte o repositório e selecione `app.py`
4. Em **Secrets**, adicione as credenciais JSON:

```toml
# .streamlit/secrets.toml
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
client_email = "texview@projeto.iam.gserviceaccount.com"
...
```

---

## 🗂️ Estrutura do Projeto

```
texview_streamlit/
├── app.py              # App principal (toda a lógica)
├── requirements.txt    # Dependências Python
└── README.md           # Esta documentação
```

---

## 🛠️ Tecnologias

| Biblioteca    | Versão   | Uso                              |
|---------------|----------|----------------------------------|
| Streamlit     | ≥1.32    | Interface web                    |
| Plotly        | ≥5.19    | Gráficos interativos             |
| Pandas        | ≥2.0     | Manipulação de dados             |
| gspread       | ≥6.0     | Leitura do Google Sheets         |
| google-auth   | ≥2.27    | Autenticação Service Account     |
| NumPy         | ≥1.26    | Cálculos numéricos               |

---

## 💰 Custo Total: R$ 0,00

Todos os serviços utilizados são gratuitos.
