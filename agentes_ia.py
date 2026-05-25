import time
from groq import Groq
from database import conectar

CHAVE_API = "x"
client = Groq(api_key=CHAVE_API)
MODELO_GROQ = "llama-3.1-8b-instant"

def agente_jornalista(ementa):
    system_prompt = """Você é um jornalista investigativo focado em traduzir "juridiquês" para a população em geral.
    Sua tarefa é ler a ementa de uma lei e escrever uma matéria de 3 parágrafos explicando como isso muda a vida prática do cidadão.

    REGRAS DE OURO:
    1. JAMAIS use a palavra "TÍTULO:". 
    2. FORMATAÇÃO: NÃO coloque a primeira letra de cada palavra em maiúscula. Use as regras normais do português do Brasil.
    3. IDIOMA: Escreva em um português do Brasil gramaticalmente impecável. NUNCA invente palavras (neologismos como "punishonará").
    4. USE NOMES POPULARES: Se a lei trata de importação de pequeno valor, chame de "Taxa das Blusinhas". Se for sobre prisioneiros, cite a "Saidinha".
    5. SEJA IMPARCIAL: Mostre os prós e os contras de forma objetiva.
    """
    user_prompt = f"Escreva a matéria para a seguinte ementa:\n{ementa}"

    for tentativa in range(3):
        try:
            response = client.chat.completions.create(
                model=MODELO_GROQ,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"      ⚠️ Erro no modelo. Respirando 5s... ({tentativa + 1}/3) | Erro: {e}")
            time.sleep(5)

    return "Matéria completa indisponível no momento."

def gerar_materia_sob_demanda(id_noticia):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT ementa_oficial, materia_completa FROM noticias WHERE id_noticia = %s", (id_noticia,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return "Erro: Notícia não encontrada no banco."

    ementa, materia_existente = resultado

    # Só pede para IA gerar se ainda não existe no banco
    if materia_existente and materia_existente != "Matéria completa indisponível no momento.":
        conn.close()
        return materia_existente

    print(f"\n[Agente Jornalista] Redigindo matéria da Lei {id_noticia} com Llama 3.1...")
    nova_materia = agente_jornalista(ementa)

    cursor.execute("UPDATE noticias SET materia_completa = %s WHERE id_noticia = %s", (nova_materia, id_noticia))
    conn.commit()
    conn.close()

    return nova_materia