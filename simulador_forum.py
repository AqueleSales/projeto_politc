import time
import json
from google import genai
from database import conectar

# COLE SUA CHAVE AQUI (Escondida dos robôs do Google!)
CHAVE_API = "AIzaSyBiU_QdbzfGol8CNx9alnbrmKGHHdrQqAU"
client = genai.Client(api_key=CHAVE_API)


def gerar_comentarios_falsos(id_noticia, ementa, qtd=4):
    prompt = f"""
    Você é um gerador de dados para um simulador.
    Leia a ementa da lei abaixo e crie {qtd} comentários fictícios simulando a reação da população brasileira na internet.
    Crie personas variadas (ex: Estudante, Caminhoneiro, Empresário, Professor, Aposentado, Advogado).
    Alguns devem apoiar a lei, outros devem criticar fortemente. Seja realista e use linguagem coloquial!

    Ementa: {ementa}
    """

    for tentativa in range(3):
        try:
            # Aqui está a mágica do JSON estruturado!
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "ARRAY",
                        "description": "Lista de feedbacks fictícios",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "nome": {"type": "STRING", "description": "Nome e sobrenome fictício"},
                                "categoria": {"type": "STRING", "description": "Profissão ou perfil social"},
                                "comentario": {"type": "STRING", "description": "A opinião realista da pessoa"},
                                "nota": {"type": "NUMBER", "description": "Nota de 0 a 5 (ex: 3.5, 1.0, 5.0)"},
                                "util": {"type": "STRING", "description": "Apenas as palavras 'Útil' ou 'Não Útil'"}
                            },
                            "required": ["nome", "categoria", "comentario", "nota", "util"]
                        }
                    }
                )
            )

            # O Python lê o JSON da IA e transforma em uma lista de dicionários na hora
            dados = json.loads(response.text)
            return dados

        except Exception as e:
            erro = str(e)
            if '429' in erro:
                print(f"      ⚠️ Cota da API estourou. Aguardando 30s... ({tentativa + 1}/3)")
                time.sleep(30)
            elif '503' in erro:
                print(f"      ⚠️ Servidor ocupado. Aguardando 20s... ({tentativa + 1}/3)")
                time.sleep(20)
            else:
                print(f"Erro no Simulador: {e}")
                break

    return []


def executar_simulador():
    print("\n🤖 Iniciando o Simulador de Fórum (Bots ativados)...")
    conn = conectar()
    cursor = conn.cursor()

    # Busca apenas leis que já estão bonitinhas com título na nossa vitrine
    cursor.execute("SELECT id_noticia, titulo_vitrine, ementa_oficial FROM noticias WHERE titulo_vitrine IS NOT NULL")
    noticias = cursor.fetchall()

    if not noticias:
        print("Nenhuma notícia pronta no banco para comentar.")
        conn.close()
        return

    for id_noticia, titulo, ementa in noticias:
        # Verifica se já geramos comentários para essa lei hoje para não poluir o banco
        cursor.execute("SELECT COUNT(*) FROM forum WHERE id_noticia = ? AND nome_usuario != 'Usuário Real'",
                       (id_noticia,))
        qtd_existente = cursor.fetchone()[0]

        if qtd_existente > 0:
            print(f"⏭️  A notícia '{titulo}' já possui {qtd_existente} comentários falsos. Pulando...")
            continue

        print(f"\n🧠 Analisando a lei: '{titulo}'")
        print("   -> Injetando 4 personas e opiniões...")

        feedbacks = gerar_comentarios_falsos(id_noticia, ementa, qtd=4)

        for fb in feedbacks:
            # Salva na mesma Tabela 2 onde o seu feedback humano foi salvo!
            cursor.execute('''
                           INSERT INTO forum (id_noticia, nome_usuario, categoria_trabalhador, texto_comentario,
                                              nota_impacto, classificacao_ia)
                           VALUES (?, ?, ?, ?, ?, ?)
                           ''', (id_noticia, fb['nome'], fb['categoria'], fb['comentario'], fb['nota'], fb['util']))

            print(f"      👤 {fb['nome']} ({fb['categoria']}): Nota {fb['nota']} - {fb['util']}")

        conn.commit()
        print("   ✅ Lote salvo no banco!")
        time.sleep(15)  # Pausa de segurança para não tomar Erro 429

    conn.close()
    print("\n🎉 Simulação concluída! O banco de dados está cheio de opiniões prontas para a Ciência de Dados.")


if __name__ == "__main__":
    executar_simulador()