import requests
import sqlite3
import pandas as pd


def configurar_banco():
    conexao = sqlite3.connect('banco_politico.db')
    cursor = conexao.cursor()
    # Criamos a tabela com campos mais detalhados
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS leis
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY,
                       numero
                       TEXT,
                       ano
                       INTEGER,
                       ementa
                       TEXT,
                       data_captura
                       DATETIME
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')
    conexao.commit()
    return conexao


def buscar_e_tratar_dados():
    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&ordem=DESC&ordenarPor=id"
    resposta = requests.get(url)
    dados_brutos = resposta.json()['dados']

    # --- ENTRA O PANDAS ---
    # Convertemos a lista de dicionários em um DataFrame (tabela do Pandas)
    df = pd.DataFrame(dados_brutos)

    # Selecionamos apenas as colunas que nos interessam para o banco
    df_limpo = df[['id', 'numero', 'ano', 'ementa']]

    return df_limpo


def salvar_no_banco(df, conexao):
    try:
        # Mudamos de 'append' para 'replace' apenas nesta execução
        # para ele recriar a tabela com as colunas certas (id, numero, ano, ementa)
        df.to_sql('leis', conexao, if_exists='replace', index=False)
        print(f"Sucesso! Tabela atualizada e {len(df)} leis foram salvas.")
    except Exception as e:
        print(f"Erro ao salvar: {e}")


if __name__ == "__main__":
    print("Iniciando Processamento de Dados Políticos...")

    # 1. Setup
    db_conn = configurar_banco()

    # 2. Coleta e Tratamento (Pandas)
    tabela_leis = buscar_e_tratar_dados()

    # Visualização rápida do que o Pandas fez (mostra as primeiras linhas)
    print("\nResumo da tabela gerada pelo Pandas:")
    print(tabela_leis.head())

    # 3. Persistência
    salvar_no_banco(tabela_leis, db_conn)

    db_conn.close()
    print("\nTrabalho concluído.")