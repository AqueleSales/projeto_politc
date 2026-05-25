import time
import json
from groq import Groq
from database import conectar

# CHAVE DA GROQ (A sua chave gratuita que começa com gsk_...)
CHAVE_API = "x"
client = Groq(api_key=CHAVE_API)

# Usando o Llama 3.1 da Meta (Gratuito, ultra-rápido e não foi aposentado!)
MODELO = "llama-3.1-8b-instant"


def gerar_comentarios_falsos(id_noticia, ementa, qtd=4):
    system_prompt = f"""Você é um gerador de dados para um simulador de banco de dados.
    Sua tarefa é retornar APENAS um objeto JSON válido.
    Crie uma chave "feedbacks" contendo uma lista de {qtd} comentários fictícios sobre a lei fornecida.
    Crie personas variadas (ex: Estudante, Caminhoneiro, Empresário, Professor).

    REGRAS RÍGIDAS DE FORMATAÇÃO:
    1. "comentario": A opinião da pessoa. É PROIBIDO o uso de emojis.
    2. "util": Você DEVE retornar EXATAMENTE a string "Útil" ou "Não Útil". É proibido usar "Sim", "Talvez" ou "Muito útil".

    O formato OBRIGATÓRIO do JSON:
    {{
      "feedbacks": [
        {{
          "nome": "Nome Fictício",
          "categoria": "Profissão",
          "comentario": "Opinião realista...",
          "nota": 4.5,
          "util": "Útil"
        }}
      ]
    }}"""
    user_prompt = f"Gere os comentários para a seguinte ementa:\n{ementa}"

    for tentativa in range(3):
        try:
            response = client.chat.completions.create(
                model=MODELO,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                # Forçando a saída limpa em JSON na Groq
                response_format={"type": "json_object"}
            )

            conteudo = response.choices[0].message.content
            dados = json.loads(conteudo)

            return dados.get("feedbacks", [])

        except Exception as e:
            print(f"      ⚠️ Erro na Groq. Aguardando 15s... ({tentativa + 1}/3) | Erro: {e}")
            time.sleep(15)

    return []


def executar_simulador():
    print(f"\n🤖 Iniciando o Simulador de Fórum (Groq Gratuito: {MODELO})...")
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id_noticia, titulo_vitrine, ementa_oficial FROM noticias WHERE titulo_vitrine IS NOT NULL")
    noticias = cursor.fetchall()

    if not noticias:
        print("Nenhuma notícia pronta no banco para comentar.")
        conn.close()
        return

    for id_noticia, titulo, ementa in noticias:
        cursor.execute("SELECT COUNT(*) FROM forum WHERE id_noticia = %s AND nome_usuario != 'Usuário Real'",
                       (id_noticia,))
        qtd_existente = cursor.fetchone()[0]

        if qtd_existente > 0:
            print(f"⏭️  A notícia '{titulo}' já possui {qtd_existente} comentários falsos. Pulando...")
            continue

        print(f"\n🧠 Analisando a lei: '{titulo}'")
        print("   -> Injetando 4 personas e opiniões...")

        feedbacks = gerar_comentarios_falsos(id_noticia, ementa, qtd=4)

        for fb in feedbacks:
            # --- PROGRAMAÇÃO DEFENSIVA: Blindando os dados da IA antes do Banco ---

            # 1. Garante que o texto não venha vazio
            texto_seguro = str(fb.get('comentario', 'Sem comentário.')).strip()
            if not texto_seguro:
                texto_seguro = "Acho que essa lei precisa ser melhor avaliada na prática."

            # 2. Força a nota a ser um número float. Se a IA mandar "", vira 3.0
            try:
                nota_segura = float(fb.get('nota', 3.0))
            except (ValueError, TypeError):
                nota_segura = 3.0

            # 3. Força a classificação a ser ESTRITAMENTE "Útil" ou "Não Útil"
            util_raw = str(fb.get('util', 'Útil')).strip()
            if "não" in util_raw.lower() or "inútil" in util_raw.lower():
                util_seguro = "Não Útil"
            else:
                util_seguro = "Útil"

            # 4. Garante valores para nome e categoria
            nome_seguro = str(fb.get('nome', 'Cidadão Anônimo')).strip() or 'Cidadão Anônimo'
            cat_segura = str(fb.get('categoria', 'Trabalhador')).strip() or 'Trabalhador'

            # ----------------------------------------------------------------------

            cursor.execute('''
                           INSERT INTO forum (id_noticia, nome_usuario, categoria_trabalhador, texto_comentario,
                                              nota_impacto, classificacao_ia)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ''', (id_noticia, nome_seguro, cat_segura, texto_seguro, nota_segura, util_seguro))

            print(f"      👤 {nome_seguro} ({cat_segura}): Nota {nota_segura} - {util_seguro}")

        conn.commit()
        print("   ✅ Lote salvo no banco Neon!")
        time.sleep(3)

    conn.close()
    print("\n🎉 Simulação concluída!")


if __name__ == "__main__":
    executar_simulador()