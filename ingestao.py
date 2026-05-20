import requests
from database import conectar

def buscar_projetos_camara(quantidade=15):
    print("\n📡 Conectando à API de Dados Abertos da Câmara dos Deputados...")

    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"

    params = {
        "siglaTipo": "PL",
        "itens": quantidade,
        "ordem": "DESC",
        "ordenarPor": "id"
    }

    try:
        resposta = requests.get(url, params=params)
        resposta.raise_for_status()
        dados = resposta.json()['dados']
        return dados
    except Exception as e:
        print(f"❌ Erro ao buscar dados na API da Câmara: {e}")
        return []

def popular_banco():
    projetos = buscar_projetos_camara(quantidade=10)

    if not projetos:
        print("Nenhum dado retornado da API.")
        return

    conn = conectar()
    cursor = conn.cursor()
    novos_inseridos = 0

    print("🔍 Processando as ementas e verificando duplicatas...")

    for proj in projetos:
        # AGORA CAPTURAMOS O ID OFICIAL DA API
        id_noticia = proj['id']
        numero_lei = str(proj['numero'])
        ano_lei = proj['ano']
        ementa_oficial = proj['ementa']

        if not ementa_oficial:
            continue

        # Usamos o id_noticia para verificar se já existe (é mais rápido e seguro)
        cursor.execute("SELECT COUNT(*) FROM noticias WHERE id_noticia = %s", (id_noticia,))
        existe = cursor.fetchone()[0]

        if existe == 0:
            # INCLUÍMOS O id_noticia NO INSERT
            cursor.execute('''
                           INSERT INTO noticias (id_noticia, numero_lei, ano_lei, ementa_oficial)
                           VALUES (%s, %s, %s, %s)
                           ''', (id_noticia, numero_lei, ano_lei, ementa_oficial))

            novos_inseridos += 1
            print(f"   ✅ Novo PL Inserido: {numero_lei}/{ano_lei} (ID: {id_noticia})")
        else:
            print(f"   ⏭️ PL {numero_lei}/{ano_lei} já existe no banco Neon. Pulando...")

    conn.commit()
    conn.close()

    print(f"\n🎉 Ingestão concluída! {novos_inseridos} novas leis foram adicionadas ao banco de dados.")
    if novos_inseridos > 0:
        print("🤖 Dica: Agora você já pode rodar seus Agentes de IA para gerar os títulos e matérias dessas novas leis!")

if __name__ == "__main__":
    popular_banco()