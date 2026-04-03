import requests
import pandas as pd
import urllib3
from database import conectar

# Desativa os avisos chatos na tela dizendo que estamos ignorando a segurança do SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def coletar_dados_governo():
    print("-> Buscando políticas e acordos internacionais na Câmara dos Deputados...")
    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&ordem=DESC&ordenarPor=id&itens=5&keywords=internacional"

    try:
        # headers: o "disfarce" para o governo achar que somos um navegador real
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        # verify=False: ignora o certificado quebrado do governo
        resposta = requests.get(url, headers=headers, verify=False, timeout=10)
        dados_brutos = resposta.json().get('dados', [])

        if not dados_brutos:
            print("Nenhum dado encontrado com esse filtro.")
            return pd.DataFrame()

        df = pd.DataFrame(dados_brutos)

        df_renomeado = df.rename(columns={
            'id': 'id_noticia',
            'numero': 'numero_lei',
            'ano': 'ano_lei',
            'ementa': 'ementa_oficial'
        })

        df_limpo = df_renomeado[['id_noticia', 'numero_lei', 'ano_lei', 'ementa_oficial']]
        return df_limpo

    except Exception as e:
        print(f"-> Erro ao conectar com o governo: {e}")
        return pd.DataFrame()


def salvar_noticias(df):
    if df.empty:
        return

    conn = conectar()
    try:
        df.to_sql('noticias', conn, if_exists='append', index=False)
        print(f"-> Sucesso! Projetos salvos na tabela 'noticias'.")
    except Exception as e:
        pass  # Ignora erro silenciosamente se a lei já existir no banco
    finally:
        conn.close()


def executar_ingestao():
    df_dados = coletar_dados_governo()
    salvar_noticias(df_dados)


if __name__ == "__main__":
    executar_ingestao()