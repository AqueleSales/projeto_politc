import requests
from database import conectar
from groq import Groq
import os
from dotenv import load_dotenv

# Abre o cofre e pega a chave da Groq
load_dotenv()
CHAVE_API = os.getenv("GROQ_API_KEY")
client = Groq(api_key=CHAVE_API)

MODELO = "llama-3.1-8b-instant"


def gerar_titulo_ia(ementa):
    """Pede para a IA gerar um título curto e chamativo baseado na ementa bruta do governo."""
    try:
        response = client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system",
                 "content": "Você é um editor de jornal focado em política. Crie um título extremamente curto, chamativo e em linguagem popular (máximo 7 palavras) para a lei baseada na ementa fornecida. JAMAIS use a palavra 'Título:', aspas, asteriscos ou emojis. Vá direto ao ponto. NÃO coloque a primeira letra de todas as palavras em maiúscula, use a formatação normal do português."},
                {"role": "user", "content": f"Ementa da lei: {ementa}"}
            ],
            temperature=0.3 # Deixa a IA focada e impede invenções de palavras
        )
        titulo_gerado = response.choices[0].message.content.strip().replace('"', '')
        return titulo_gerado
    except Exception as e:
        print(f"⚠️ Erro na Groq ao gerar título: {e}")
        return "Nova lei em tramitação na Câmara"


def buscar_novas_leis():
    print("📡 Conectando à API da Câmara dos Deputados...")
    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"

    parametros = {
        "siglaTipo": "PL",
        "ordem": "DESC",
        "ordenarPor": "id",
        "itens": 30 # Aumentado para 30 leis!
    }

    try:
        resposta = requests.get(url, params=parametros)
        resposta.raise_for_status()
        dados = resposta.json().get('dados', [])

        if not dados:
            print("⚠️ Nenhuma lei encontrada na API.")
            return

        conn = conectar()
        cursor = conn.cursor()

        novas_leis_adicionadas = 0

        for proposicao in dados:
            id_oficial = proposicao['id']
            ementa = proposicao['ementa']

            if not ementa:
                continue

            # Verifica se já existe
            cursor.execute("SELECT id_noticia FROM noticias WHERE id_noticia = %s", (id_oficial,))
            existe = cursor.fetchone()

            if not existe:
                # 👉 AQUI ENTRA A IA: Gerando o título atrativo em tempo real
                print(f"🧠 Lendo juridiquês da lei ID {id_oficial} e gerando título...")
                titulo_atrativo = gerar_titulo_ia(ementa)

                # Salva no banco!
                cursor.execute('''
                               INSERT INTO noticias (id_noticia, titulo_vitrine, ementa_oficial)
                               VALUES (%s, %s, %s)
                               ''', (id_oficial, titulo_atrativo, ementa))

                print(f"✅ SALVO: '{titulo_atrativo}'")
                novas_leis_adicionadas += 1
            else:
                print(f"⏭️  Lei ID {id_oficial} já existe no banco. Pulando...")

        conn.commit()
        conn.close()

        print(f"\n🚀 Ingestão concluída! {novas_leis_adicionadas} novas leis foram adicionadas.")

    except Exception as e:
        print(f"❌ Erro ao buscar dados do governo: {e}")


if __name__ == "__main__":
    print("\n=======================================")
    buscar_novas_leis()
    print("=======================================")
    print("🏁 Varredura finalizada. Encerrando processo.")