import time
from google import genai
from database import conectar

# Substitua pela sua CHAVE NOVA gerada no Google AI Studio (Não compartilhe!)
CHAVE_API = "XXXX"
client = genai.Client(api_key=CHAVE_API)


def agente_editor(ementa):
    """IA 1: Cria o título e o resumo curto para a vitrine."""
    prompt = f"""
    Você é um editor-chefe de um portal de notícias de política internacional.
    Leia a seguinte ementa de um projeto de lei e crie:
    1. Um título curto e chamativo (máximo de 8 palavras).
    2. Um resumo simples e direto para o cidadão comum (máximo de 3 frases).

    Formato obrigatório da sua resposta:
    TÍTULO: [Seu título aqui]
    RESUMO: [Seu resumo aqui]

    Ementa original: {ementa}
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        texto = response.text
        partes = texto.split('RESUMO:')
        titulo = partes[0].replace('TÍTULO:', '').strip()
        resumo = partes[1].strip() if len(partes) > 1 else "Resumo não gerado."
        return titulo, resumo
    except Exception as e:
        print(f"Erro no Agente Editor: {e}")
        return "Título Indisponível", "Resumo Indisponível"


def agente_jornalista(ementa):
    """IA 2: Escreve a matéria completa, explicando o impacto."""
    prompt = f"""
    Você é um jornalista especializado em Relações Internacionais e Economia Brasileira.
    Escreva uma matéria envolvente (cerca de 3 a 4 parágrafos) explicando o seguinte projeto de lei.
    Explique o contexto, o que ele muda na prática e qual o possível impacto para o Brasil e para os trabalhadores.
    Use uma linguagem clara, sem jargões jurídicos. Seja imparcial e informativo.

    Ementa original: {ementa}
    """
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Erro no Agente Jornalista: {e}")
        return "Matéria completa indisponível no momento."


# ==========================================
# AS DUAS NOVAS FUNÇÕES DE LAZY LOADING
# ==========================================

def gerar_titulos_pendentes(limite=3):
    """Acorda o Agente 1 (Editor) apenas para um lote pequeno de notícias."""
    conn = conectar()
    cursor = conn.cursor()

    # Busca apenas 'X' notícias que ainda não têm título
    cursor.execute("SELECT id_noticia, ementa_oficial FROM noticias WHERE titulo_vitrine IS NULL LIMIT ?", (limite,))
    pendentes = cursor.fetchall()

    if not pendentes:
        conn.close()
        return False  # Retorna falso se não tinha nada novo para gerar

    print(f"\n[Agente 1] Gerando títulos chamativos para {len(pendentes)} leis...")

    for i, (id_noticia, ementa) in enumerate(pendentes):
        titulo, resumo = agente_editor(ementa)

        # Salva no banco de dados imediatamente
        cursor.execute('''
                       UPDATE noticias
                       SET titulo_vitrine = ?,
                           resumo_vitrine = ?
                       WHERE id_noticia = ?
                       ''', (titulo, resumo, id_noticia))

        print(f"  -> Título gerado: {titulo}")

        # Pausa de 15s APENAS se houver uma próxima lei na fila, para não estourar a cota
        if i < len(pendentes) - 1:
            time.sleep(15)

    conn.commit()
    conn.close()
    return True


def gerar_materia_sob_demanda(id_noticia):
    """Acorda o Agente 2 (Jornalista) APENAS quando o usuário clica na notícia."""
    conn = conectar()
    cursor = conn.cursor()

    # Verifica se já existe matéria escrita para não gastar API à toa (O Cache!)
    cursor.execute("SELECT ementa_oficial, materia_completa FROM noticias WHERE id_noticia = ?", (id_noticia,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return "Erro: Notícia não encontrada no banco."

    ementa, materia_existente = resultado

    # CACHE: Se já foi escrita antes, devolve instantaneamente
    if materia_existente and materia_existente != "Matéria completa indisponível no momento.":
        conn.close()
        return materia_existente

    # Se a matéria estiver em branco, aciona a IA
    print(f"\n[Agente 2] Lendo documento oficial e redigindo matéria exclusiva. Aguarde...")
    nova_materia = agente_jornalista(ementa)

    # Salva no banco de dados para a próxima vez ser instantânea
    cursor.execute("UPDATE noticias SET materia_completa = ? WHERE id_noticia = ?", (nova_materia, id_noticia))
    conn.commit()
    conn.close()

    return nova_materia