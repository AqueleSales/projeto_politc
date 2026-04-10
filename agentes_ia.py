import time # <-- pega o tempo
import json # <--
from google import genai # <-- importa a IA gemini, para realizar as requisições
from database import conectar

#   Chave API do google
CHAVE_API = "AIzaSyBiU_QdbzfGol8CNx9alnbrmKGHHdrQqAU"
client = genai.Client(api_key=CHAVE_API)

#   primeiro agente IA  que faz um titulo curto e chamataivo
def agente_editor(ementa):
    # Mudamos o prompt para pedir um JSON perfeito
    prompt = f"""
    Você é um editor-chefe de um portal de notícias de política internacional.
    Leia a ementa de um projeto de lei e crie um título curto (máx 8 palavras) e um resumo (máx 3 frases).

    Ementa original: {ementa}
    """

    for tentativa in range(3):
        try:
            # Aqui está a mágica: Obrigamos a IA a cuspir um JSON
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    # Dizemos exatamente como queremos o dicionário
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "titulo": {"type": "STRING"},
                            "resumo": {"type": "STRING"}
                        },
                        "required": ["titulo", "resumo"]
                    }
                )
            )

            # O Python transforma a resposta da IA direto em um Dicionário nativo!
            dados = json.loads(response.text)

            return dados["titulo"], dados["resumo"]

        except Exception as e:
            erro = str(e)
            if '429' in erro:
                print(f"      ⚠️ Cota por minuto atingida. Respirando 30s... ({tentativa + 1}/3)")
                time.sleep(30)
            elif '503' in erro:
                print(f"      ⚠️ Google ocupado. Pausando 20s e tentando de novo... ({tentativa + 1}/3)")
                time.sleep(20)
            else:
                print(f"Erro no Agente Editor: {e}")
                break

    return "Título Indisponível", "Resumo Indisponível"


def agente_jornalista(ementa):
    prompt = f"""
    Você é um jornalista especializado em Relações Internacionais e Economia Brasileira.
    Escreva uma matéria envolvente (cerca de 3 a 4 parágrafos) explicando o seguinte projeto de lei.
    Explique o contexto, o que ele muda na prática e qual o possível impacto para o Brasil e para os trabalhadores.
    Use uma linguagem clara, sem jargões jurídicos. Seja imparcial e informativo.

    Ementa original: {ementa}
    """

    for tentativa in range(3):
        try:
            response = client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=prompt)
            return response.text.strip()
        except Exception as e:
            erro = str(e)
            if '429' in erro:
                print(f"      ⚠️ Cota por minuto atingida. Respirando 30s... ({tentativa + 1}/3)")
                time.sleep(60)
            elif '503' in erro:
                print(f"      ⚠️ Google ocupado. Pausando 20s e tentando de novo... ({tentativa + 1}/3)")
                time.sleep(60)
            else:
                print(f"Erro no Agente Jornalista: {e}")
                break

    return "Matéria completa indisponível no momento."


def gerar_titulos_pendentes(limite=3):
    conn = conectar()
    cursor = conn.cursor()

    # Usamos ASC para ele sempre processar os mais antigos primeiro (corrige a paginação)
    cursor.execute(
        "SELECT id_noticia, ementa_oficial FROM noticias WHERE titulo_vitrine IS NULL OR titulo_vitrine = 'Título Indisponível' ORDER BY id_noticia ASC LIMIT ?",
        (limite,)
    )
    pendentes = cursor.fetchall()

    if not pendentes:
        conn.close()
        return False

    print(f"\n[Agente 1] Gerando títulos chamativos para {len(pendentes)} leis...")

    for i, (id_noticia, ementa) in enumerate(pendentes):
        titulo, resumo = agente_editor(ementa)

        cursor.execute('''
                       UPDATE noticias
                       SET titulo_vitrine = ?,
                           resumo_vitrine = ?
                       WHERE id_noticia = ?
                       ''', (titulo, resumo, id_noticia))

        print(f"  -> Título gerado: {titulo}")

        # Pausa de segurança de 20s para evitar o Erro 429 proativamente
        if i < len(pendentes) - 1:
            time.sleep(20)

    conn.commit()
    conn.close()
    return True


def gerar_materia_sob_demanda(id_noticia):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT ementa_oficial, materia_completa FROM noticias WHERE id_noticia = ?", (id_noticia,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return "Erro: Notícia não encontrada no banco."

    ementa, materia_existente = resultado

    # Se a IA já escreveu antes, devolve do banco instantaneamente
    if materia_existente and materia_existente != "Matéria completa indisponível no momento.":
        conn.close()
        return materia_existente

    print(f"\n[Agente 2] Lendo documento oficial e redigindo matéria exclusiva. Aguarde...")
    nova_materia = agente_jornalista(ementa)

    cursor.execute("UPDATE noticias SET materia_completa = ? WHERE id_noticia = ?", (nova_materia, id_noticia))
    conn.commit()
    conn.close()

    return nova_materia