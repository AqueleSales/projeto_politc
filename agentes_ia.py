import time
import json
# pip install groq (ou a biblioteca da provedora que for hospedar o Gemma)
from groq import Groq 
from database import conectar

# CHAVE API DA SUA PROVEDORA (Ex: Groq)
CHAVE_API = "AIzaSyDd6NlLGkuw4Q0-gvQDfXySxy6QGhBmO7A"
client = Groq(api_key=CHAVE_API)
MODELO_GEMMA = "gemma-4-26b-it" # A tag "it" significa Instruction Tuned

def agente_editor(ementa):
    # 1. MODO SYSTEM PROMPT (A personalidade inquebrável da IA)
    system_prompt = """Você é um editor-chefe de um portal de notícias focado em Políticas Públicas.
Sua tarefa é retornar APENAS um JSON válido contendo duas chaves:
1. "titulo": Um título curto e chamativo (máx 8 palavras).
2. "resumo": Um resumo simples e direto para o cidadão comum (máx 3 frases)."""

    # 2. MODO USER (Apenas os dados brutos)
    user_prompt = f"Ementa original:\n{ementa}"

    for tentativa in range(3):
        try:
            response = client.chat.completions.create(
                model=MODELO_GEMMA,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                # 3. FUNCTION CALLING / NATIVE JSON: Força a saída estruturada
                response_format={"type": "json_object"} 
            )
            
            # Pega o texto puro e converte direto para Dicionário Python
            conteudo = response.choices[0].message.content
            dados = json.loads(conteudo)
            
            return dados.get("titulo", "Título Indisponível"), dados.get("resumo", "Resumo não gerado.")

        except Exception as e:
            print(f"      ⚠️ Erro no modelo ou limite atingido. Respirando 10s... ({tentativa + 1}/3) | Erro: {e}")
            time.sleep(10)

    return "Título Indisponível", "Resumo Indisponível"

def agente_jornalista(ementa):
    system_prompt = """Você é um jornalista investigativo especializado em Políticas Públicas.
A sua prioridade absoluta é explicar o IMPACTO NA VIDA DO CIDADÃO: 
Como essa lei muda o dia a dia do brasileiro? Vai afetar o bolso, a saúde, a segurança ou o trabalho das pessoas?
Use uma linguagem clara, sem jargões jurídicos. Seja imparcial, mas mostre os prós e contras práticos.
Escreva uma matéria envolvente de 3 a 4 parágrafos."""

    user_prompt = f"Escreva a matéria para a seguinte ementa:\n{ementa}"

    for tentativa in range(3):
        try:
            # 4. CONTEXTO ESTENDIDO: O Gemma lê a ementa inteira com facilidade aqui
            response = client.chat.completions.create(
                model=MODELO_GEMMA,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"      ⚠️ Erro no modelo ou limite atingido. Respirando 15s... ({tentativa + 1}/3) | Erro: {e}")
            time.sleep(15)

    return "Matéria completa indisponível no momento."


# =====================================================================
# AS FUNÇÕES DE BANCO DE DADOS ABAIXO CONTINUAM EXATAMENTE IGUAIS
# O Python só manda os dados pra IA e grava no Neon do mesmo jeito!
# =====================================================================

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

    print(f"\n[Agente 1] Gerando títulos chamativos com Gemma 26B para {len(pendentes)} leis...")

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
            time.sleep(5) # Modelos abertos em APIs parrudas costumam exigir menos tempo de pausa

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

    print(f"\n[Agente 2] Lendo documento oficial e redigindo matéria exclusiva com Gemma 26B. Aguarde...")
    nova_materia = agente_jornalista(ementa)

    cursor.execute("UPDATE noticias SET materia_completa = %s WHERE id_noticia = %s", (nova_materia, id_noticia))
    conn.commit()
    conn.close()

    return nova_materia