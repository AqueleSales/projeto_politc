import io
import matplotlib

matplotlib.use('Agg')  # <-- OBRIGATÓRIO para o Matplotlib funcionar dentro do Flask
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, render_template, jsonify, request, Response

from database import conectar, obter_engine_pandas
from agentes_ia import gerar_materia_sob_demanda  # Importa o seu agente da Groq

app = Flask(__name__)


# --- ROTA 1: PÁGINA PRINCIPAL ---
@app.route('/')
def index():
    return render_template('index.html')


# --- ROTA 2: FEED DE NOTÍCIAS COM PAGINAÇÃO, BUSCA E FILTROS ---
@app.route('/api/noticias')
def api_noticias():
    pagina = request.args.get('pagina', 1, type=int)
    termo_pesquisa = request.args.get('busca', '', type=str)
    filtros = request.args.get('filtros', '', type=str)  # <- Pega os filtros do JS

    itens_por_pagina = 12
    offset = (pagina - 1) * itens_por_pagina

    conn = conectar()
    cursor = conn.cursor()

    # Começamos a montar a Query Base
    query = "SELECT id_noticia, titulo_vitrine, resumo_vitrine FROM noticias WHERE titulo_vitrine IS NOT NULL AND titulo_vitrine != 'Título Indisponível'"
    params = []

    # 1. Adiciona a pesquisa por texto (se houver)
    if termo_pesquisa:
        query += " AND (titulo_vitrine ILIKE %s OR ementa_oficial ILIKE %s)"
        params.extend([f"%{termo_pesquisa}%", f"%{termo_pesquisa}%"])

    # 2. Adiciona os Filtros (Corrigido com %% para não quebrar o Python!)
    if filtros:
        lista_filtros = filtros.split(',')
        filtro_condicoes = []

        for f in lista_filtros:
            f = f.lower().strip()
            if f == 'trabalhista':
                filtro_condicoes.append(
                    "ementa_oficial ILIKE '%%trabalho%%' OR ementa_oficial ILIKE '%%emprego%%' OR ementa_oficial ILIKE '%%clt%%'")
            elif f == 'penal':
                filtro_condicoes.append(
                    "ementa_oficial ILIKE '%%penal%%' OR ementa_oficial ILIKE '%%crime%%' OR ementa_oficial ILIKE '%%prisão%%'")
            elif f == 'meio ambiente':
                filtro_condicoes.append(
                    "ementa_oficial ILIKE '%%ambiental%%' OR ementa_oficial ILIKE '%%meio ambiente%%'")
            elif f == 'tributário (impostos)':
                filtro_condicoes.append(
                    "ementa_oficial ILIKE '%%imposto%%' OR ementa_oficial ILIKE '%%tributo%%' OR ementa_oficial ILIKE '%%taxa%%'")
            elif f == 'nacional':
                filtro_condicoes.append("ementa_oficial ILIKE '%%nacional%%' OR ementa_oficial ILIKE '%%federal%%'")
            elif f == 'distrital':
                filtro_condicoes.append(
                    "ementa_oficial ILIKE '%%distrito federal%%' OR ementa_oficial ILIKE '%%distrital%%'")

        if filtro_condicoes:
            query += " AND (" + " OR ".join(filtro_condicoes) + ")"

    # Termina a Query com a paginação
    query += " ORDER BY id_noticia DESC LIMIT %s OFFSET %s"
    params.extend([itens_por_pagina, offset])

    cursor.execute(query, params)
    noticias_bd = cursor.fetchall()
    conn.close()

    resultado = []
    for noti in noticias_bd:
        resultado.append({
            "id": noti[0],
            "titulo": noti[1],
            "resumo": noti[2]
        })

    return jsonify(resultado)

# --- ROTA 3: LER MATÉRIA (CHAMA O AGENTE DA GROQ SE PRECISAR) ---
@app.route('/api/ler_materia/<int:id_noticia>')
def api_ler_materia(id_noticia):
    # A função já verifica se existe no banco. Se não, gera uma nova matéria na hora!
    texto_materia = gerar_materia_sob_demanda(id_noticia)
    return jsonify({"texto_materia": texto_materia})


# --- ROTA 4: FÓRUM FILTRADO POR LEI ---
@app.route('/api/forum/<int:id_noticia>')
def api_forum(id_noticia):
    conn = conectar()
    cursor = conn.cursor()

    # Filtra os debates estritamente para a notícia selecionada
    cursor.execute('''
                   SELECT nome_usuario, categoria_trabalhador, texto_comentario, nota_impacto, classificacao_ia
                   FROM forum
                   WHERE id_noticia = %s
                   ORDER BY id_comentario DESC
                   ''', (id_noticia,))

    resultados = cursor.fetchall()
    conn.close()

    # Estrutura os dados para o Front-End
    comentarios = [
        {
            "nome_usuario": linha[0],
            "categoria": linha[1],
            "texto": linha[2],
            "nota": linha[3],
            "classificacao": linha[4]
        } for linha in resultados
    ]
    return jsonify(comentarios)


# --- ROTA 5: DASHBOARD FILTRADO POR LEI (FIM DO TIMEOUT) ---
@app.route('/api/dashboard/<int:id_noticia>.png')
def obter_dashboard_dinamico(id_noticia):
    try:
        engine = obter_engine_pandas()

        # Query ultra rápida: calcula o sentimento apenas DESTE projeto de lei
        query = """
                SELECT CASE \
                           WHEN classificacao_ia ILIKE '%%não%%' OR \
                       classificacao_ia ILIKE '%%inútil%%' OR classificacao_ia ILIKE '%%pouco%%' THEN 'Não Útil'
                    ELSE 'Útil'
                END \
                as sentimento,
                COUNT(*) as total 
            FROM forum 
            WHERE id_noticia = \
                %s
                GROUP \
                BY \
                sentimento \
                """
        # Atenção: Ajustamos os % da query ILIKE para %% para não dar conflito com o %s no psycopg2
        df = pd.read_sql(query, engine, params=(id_noticia,))

        # Se df for uma tupla ao invés de dataframe, converte (proteção extra contra bugs do sqlalchemy)
        if isinstance(df, tuple):
            df = df[0]

        plt.figure(figsize=(4, 4))  # Tamanho menor para caber bonito na barra lateral

        if df.empty:
            # Gráfico de espera elegante (Sem Dados)
            plt.pie([1], labels=['Sem Dados'], colors=['#cbd5e0'],
                    textprops={'fontsize': 10, 'color': '#718096'})
        else:
            # Cores dinâmicas (Verde/Vermelho)
            cores = ['#2ecc71' if s == 'Útil' else '#e74c3c' for s in df['sentimento']]

            #  AQUI ESTÁ O AJUSTE FINAL: Sem título e centralizado
            plt.pie(df['total'], labels=df['sentimento'], autopct='%1.1f%%', startangle=140,
                    colors=cores, textprops={'fontsize': 10, 'weight': 'bold'},
                    wedgeprops={'edgecolor': 'white', 'linewidth': 2})

        plt.tight_layout()
        plt.subplots_adjust(left=0.18, right=0.93, top=0.95, bottom=0.05)

        # Salva e devolve a imagem
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, transparent=True)
        img_buffer.seek(0)
        plt.close()

        return Response(img_buffer.getvalue(), mimetype='image/png')

    except Exception as e:
        print(f"Erro ao gerar gráfico de pizza filtrado: {e}")
        return "Erro ao processar dados do gráfico", 500


# --- ROTA 6: ENVIAR FEEDBACK DO USUÁRIO ---
@app.route('/api/enviar_feedback', methods=['POST'])
def api_enviar_feedback():
    dados = request.json
    id_noticia = dados.get('id_noticia')
    texto_usuario = dados.get('texto')
    nota_usuario = float(dados.get('nota', 5.0))  # Pega a nota enviada pelo JS

    if not id_noticia or not texto_usuario:
        return jsonify({"erro": "Dados incompletos"}), 400

    # --- A MÁGICA: Sincroniza as estrelas com a Pizza! ---
    if nota_usuario <= 3:
        sentimento_pizza = 'Não Útil (Humano)'
    else:
        sentimento_pizza = 'Útil (Humano)'
    # -----------------------------------------------------

    conn = conectar()
    cursor = conn.cursor()

    try:
        # Agora inserimos o "sentimento_pizza" no banco, em vez do texto fixo
        cursor.execute('''
                       INSERT INTO forum (id_noticia, nome_usuario, categoria_trabalhador, texto_comentario,
                                          nota_impacto, classificacao_ia)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ''', (id_noticia, 'Você (Usuário)', 'Cidadão', texto_usuario, nota_usuario, sentimento_pizza))

        conn.commit()
        conn.close()
        return jsonify({"sucesso": True, "mensagem": "Opinião registrada com sucesso!"})

    except Exception as e:
        print(f"Erro ao salvar feedback: {e}")
        conn.rollback()
        conn.close()
        return jsonify({"erro": "Falha ao salvar no banco"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)