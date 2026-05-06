import time
from google import genai
from database import conectar

# CHAVE API AQUI
CHAVE_API = "AIzaSyC2LZmRhhxGK_Ol0ozGHYBNwjl52et73XI"
client = genai.Client(api_key=CHAVE_API)

def agente_editor(ementa):
    prompt = f"""
    Você é um editor-chefe de um portal de notícias focado em Políticas Públicas e Política Internacional.
    Leia a seguinte ementa de um projeto de lei e crie:
    1. Um título curto e chamativo (máximo de 8 palavras).
    2. Um resumo simples e direto para o cidadão comum (máximo de 3 frases).

    Formato obrigatório:
    TÍTULO: [Seu título aqui]
    RESUMO: [Seu resumo aqui]

    Ementa original: {ementa}
    """
    for tentativa in range(3):
        try:
            response = client.models.generate_content(model='gemini-3.1-flash-lite-preview', contents=prompt)
            texto = response.text
            partes = texto.split('RESUMO:')
            titulo = partes[0].replace('TÍTULO:', '').strip()
            resumo = partes[1].strip() if len(partes) > 1 else "Resumo não gerado."
            return titulo, resumo
        except Exception as e:
            erro = str(e)
            if '429' in erro:
                print(f"      ⚠️ Cota por minuto atingida (Erro 429). Respirando fundo por 30s... ({tentativa + 1}/3)")
                time.sleep(30)
            elif '503' in erro:
                print(f"      ⚠️ Google ocupado (Erro 503). Pausando 20s e tentando de novo... ({tentativa + 1}/3)")
                time.sleep(20)
            else:
                print(f"Erro no Agente Editor: {e}")
                break

    return "Título Indisponível", "Resumo Indisponível"

def agente_jornalista(ementa):
    prompt = f"""
    Você é um jornalista investigativo especializado em Políticas Públicas, Economia e Relações Internacionais.
    Escreva uma matéria envolvente (cerca de 3 a 4 parágrafos) explicando o seguinte projeto de lei.

    A sua prioridade absoluta é explicar o IMPACTO NA VIDA DO CIDADÃO: 
    Como essa lei muda o dia a dia do brasileiro? Vai afetar o bolso, a saúde, a segurança ou o trabalho das pessoas?
    Use uma linguagem clara, sem jargões jurídicos. Seja imparcial, mas mostre os prós e contras práticos.

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

    cursor.execute(
        "SELECT id_noticia, ementa_oficial FROM noticias WHERE titulo_vitrine IS NULL OR titulo_vitrine = 'Título Indisponível' ORDER BY id_noticia ASC LIMIT %s",
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
                       SET titulo_vitrine = %s,
                           resumo_vitrine = %s
                       WHERE id_noticia = %s
                       ''', (titulo, resumo, id_noticia))

        print(f"  -> Título gerado: {titulo}")
        if i < len(pendentes) - 1:
            time.sleep(20)

    conn.commit()
    conn.close()
    return True

def gerar_materia_sob_demanda(id_noticia):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT ementa_oficial, materia_completa FROM noticias WHERE id_noticia = %s", (id_noticia,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return "Erro: Notícia não encontrada no banco."

    ementa, materia_existente = resultado

    if materia_existente and materia_existente != "Matéria completa indisponível no momento.":
        conn.close()
        return materia_existente

    print(f"\n[Agente 2] Lendo documento oficial e redigindo matéria exclusiva. Aguarde...")
    nova_materia = agente_jornalista(ementa)

    cursor.execute("UPDATE noticias SET materia_completa = %s WHERE id_noticia = %s", (nova_materia, id_noticia))
    conn.commit()
    conn.close()

    return nova_materia