import requests # <-- serve para facilitar o envio de requisições HTTP e API's
import pandas as pd # <-- serve para manipulação, limpeza, tratamento e análise de dados tabulares estruturá-los em DataFrames
import urllib3 # <-- Requisições HTTP
import feedparser  # <-- ler e analisar feeds de notícias e conteúdos web (rss)
import hashlib  # <-- transformar dados de entrada para gerar um ID numérico único para as notas
from database import conectar

# Desativa os avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. O "PORTEIRO" (Filtro Inteligente e Gratuito)
# ==========================================
def eh_assunto_relevante(ementa):
#
#   Verifica se o texto contém palavras-chave do nosso interesse.
#
    if not ementa:
        return False

    palavras_chave = [
        'sanção', 'sanções', 'embaixada', 'diplomacia',
        'acordo bilateral', 'tratado', 'embargo',
        'relações exteriores', 'onu', 'mercosul', 'guerra'
    ]

    ementa_minuscula = ementa.lower()

    for palavra in palavras_chave:
        if palavra in ementa_minuscula:
            return True

    return False

# ==========================================
# 2. COLETOR 1: CÂMARA DOS DEPUTADOS (Leis)
# ==========================================
def coletar_dados_camara():
#
#    Aqui ele busca as ementas da câmara dos deputados no banco dos dados abertos.
#
    print("\n[COLETOR 1] -> Buscando projetos na Câmara dos Deputados...")
    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&ordem=DESC&ordenarPor=id&itens=100&keywords=internacional"
#
#   o link do dados aberto, veja que no https tem itens, ali onde vamos decider a quantidade de ementas, pegamos 100 para verifcar
#
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resposta = requests.get(url, headers=headers, verify=False, timeout=10)
        dados_brutos = resposta.json().get('dados', [])

        dados_filtrados = []
        for projeto in dados_brutos:
            ementa = projeto.get('ementa', '')
            # O Porteiro entra em ação
            if eh_assunto_relevante(ementa):
                dados_filtrados.append(projeto)

        if not dados_filtrados:
            print("  -> Nenhuma lei da Câmara passou no filtro de temas hoje.")
            return pd.DataFrame()

        df = pd.DataFrame(dados_filtrados)
        df_renomeado = df.rename(columns={
            'id': 'id_noticia',
            'numero': 'numero_lei',
            'ano': 'ano_lei',
            'ementa': 'ementa_oficial'
        })

        df_limpo = df_renomeado[['id_noticia', 'numero_lei', 'ano_lei', 'ementa_oficial']]
        print(f"  -> {len(df_limpo)} leis passaram no filtro e serão processadas!")
        return df_limpo

    except Exception as e:
        print(f"  -> Erro ao conectar com a Câmara: {e}")
        return pd.DataFrame()


# ==========================================
# 3. COLETOR 2: ITAMARATY (Notas Diplomáticas)
# ==========================================
def coletar_dados_itamaraty():
    print("\n[COLETOR 2] -> Buscando notas diplomáticas no Itamaraty (MRE)...")

    # URL oficial do RSS de Notas à Imprensa do Itamaraty
    url_rss = "https://www.gov.br/mre/pt-br/canais_atendimento/imprensa/notas-a-imprensa/RSS"

    try:
        feed = feedparser.parse(url_rss)
        dados_filtrados = []

        if not feed.entries:
            print("  -> Nenhuma nota encontrada no feed do Itamaraty.")
            return pd.DataFrame()

        for nota in feed.entries:
            # Juntamos o título e o resumo da nota para formar a "ementa"
            texto_nota = f"{nota.title} - {nota.summary}"

            # O mesmo porteiro avalia as notas do Itamaraty!
            if eh_assunto_relevante(texto_nota):
                # Como o RSS não tem um ID numérico, criamos um ID único baseado no link da nota
                id_unico = int(hashlib.md5(nota.link.encode()).hexdigest()[:8], 16)

                # Pegamos o ano atual
                ano_atual = pd.Timestamp.now().year

                dados_filtrados.append({
                    'id_noticia': id_unico,
                    'numero_lei': 'NOTA_MRE',  # Disfarce para caber no seu banco!
                    'ano_lei': ano_atual,
                    'ementa_oficial': texto_nota
                })

        if not dados_filtrados:
            print("  -> Nenhuma nota do Itamaraty passou no filtro de temas hoje.")
            return pd.DataFrame()

        df_limpo = pd.DataFrame(dados_filtrados)
        print(f"  -> {len(df_limpo)} notas do Itamaraty passaram no filtro!")
        return df_limpo

    except Exception as e:
        print(f"  -> Erro ao ler o feed do Itamaraty: {e}")
        return pd.DataFrame()


# ==========================================
# 4. FUNÇÕES DE BANCO DE DADOS
# ==========================================
def salvar_noticias(df):
    if df.empty:
        return
#   aqui ele conecta com sql e usa para salva as noticias
    conn = conectar()
    try:
        df.to_sql('noticias', conn, if_exists='append', index=False)
        print(f"  -> Sucesso! {len(df)} registros salvos na tabela 'noticias'.")
    except Exception as e:
        # Se der erro de PRIMARY KEY (id_noticia já existe), ignoramos, pois significa
        # que já baixamos essa lei/nota antes.
        pass
    finally:
        conn.close()


def executar_ingestao():
    print("Iniciando varredura multicanal do Governo...")

    # 1. Puxa e salva da Câmara
    df_camara = coletar_dados_camara()
    salvar_noticias(df_camara)

    # 2. Puxa e salva do Itamaraty
    df_itamaraty = coletar_dados_itamaraty()
    salvar_noticias(df_itamaraty)

    print("\nVarredura concluída!")


if __name__ == "__main__":
    executar_ingestao()