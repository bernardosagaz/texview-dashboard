import json
import os

# Caminho do arquivo JSON de credenciais
# Altere para o caminho do seu arquivo JSON
json_path = input("Cole o caminho completo do arquivo JSON de credenciais: ").strip().strip('"')

if not os.path.exists(json_path):
    print(f"ERRO: Arquivo não encontrado em {json_path}")
    exit(1)

with open(json_path, 'r') as f:
    creds = json.load(f)

# Gera o secrets.toml formatado corretamente
toml_content = f'''[gcp_service_account]
type = "{creds.get('type', '')}"
project_id = "{creds.get('project_id', '')}"
private_key_id = "{creds.get('private_key_id', '')}"
private_key = """{creds.get('private_key', '')}"""
client_email = "{creds.get('client_email', '')}"
client_id = "{creds.get('client_id', '')}"
auth_uri = "{creds.get('auth_uri', '')}"
token_uri = "{creds.get('token_uri', '')}"
'''

# Salva o arquivo
output_path = os.path.join(os.path.dirname(json_path), 'secrets.toml')
with open(output_path, 'w') as f:
    f.write(toml_content)

print(f"\n✅ secrets.toml gerado em: {output_path}")
print("\nCopie o conteúdo abaixo e cole no campo Secrets do Streamlit Cloud:\n")
print("=" * 60)
print(toml_content)
print("=" * 60)
