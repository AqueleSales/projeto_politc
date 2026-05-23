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


# --- ROTA 2: FEED DE NOTÍCIAS COM PAGINAÇÃO ---
@app.route('/api/noticias')
def api_noticias():
    pagina = int(request.args.get('pagina', 1))
    limite = 5
    offset = (pagina - 1) * limite

    conn = conectar()
    cursor = conn.cursor()

    # Busca apenas as leis que já passaram pelo Agente 1 (têm título)
    cursor.execute('''
        SELECT id_noticia, titulo_vitrine 
        FROM noticias 
        WHERE titulo_vitrine IS NOT NULL 
        ORDER BY id_noticia DESC 
        LIMIT %s OFFSET %s
    ''', (limite, offset))

    resultados = cursor.fetchall()
    conn.close()

    # Formata para JSON para o JavaScript ler
    noticias = [{"id": linha[0], "titulo": linha[1]} for linha in resultados]
    return jsonify(noticias)


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
            SELECT 
                CASE 
                    WHEN classificacao_ia ILIKE '%%não%%' OR classificacao_ia ILIKE '%%inútil%%' OR classificacao_ia ILIKE '%%pouco%%' THEN 'Não Útil'
                    ELSE 'Útil'
                END as sentimento,
                COUNT(*) as total 
            FROM forum 
            WHERE id_noticia = %s
            GROUP BY sentimento
        """
        # Atenção: Ajustamos os % da query ILIKE para %% para não dar conflito com o %s no psycopg2
        df = pd.read_sql(query, engine, params=(id_noticia,))

        # Se df for uma tupla ao invés de dataframe, converte (proteção extra contra bugs do sqlalchemy)
        if isinstance(df, tuple):
            df = df[0]

        plt.figure(figsize=(4, 4)) # Tamanho menor para caber bonito na barra lateral

        if df.empty:
            # Se a lei não tiver comentários ainda, mostra um gráfico de espera elegante
            plt.pie([1], labels=['Sem Dados'], colors=['#cbd5e0'], 
                    textprops={'fontsize': 10, 'color': '#718096'})
        else:
            cores = ['#2ecc71' if s == 'Útil' else '#e74c3c' for s in df['sentimento']]
            # Aumentei a fonte do percentual e tirei o título
            plt.pie(df['total'], labels=df['sentimento'], autopct='%1.1f%%', startangle=140,
                    colors=cores, textprops={'fontsize': 12, 'weight': 'bold'},
                    wedgeprops={'edgecolor': 'white', 'linewidth': 2})

        # 👇 APAGUE (OU COMENTE) A LINHA DO plt.title 👇
        # plt.title('Sentimento Público', fontsize=12, fontweight='bold', pad=10)
        
        # Ajusta as margens para a pizza ocupar o espaço todo sem cortar
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1) 
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, transparent=True)

        plt.title('Sentimento Público', fontsize=12, fontweight='bold', pad=10)
        plt.tight_layout()

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, transparent=True) # Fundo transparente
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
    
    if not id_noticia or not texto_usuario:
        return jsonify({"erro": "Dados incompletos"}), 400

    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # Insere a sua opinião no banco de dados. 
        # Como é um comentário humano sem nota, colocamos nota 5.0 e classificação 'Útil' provisória
        cursor.execute('''
            INSERT INTO forum (id_noticia, nome_usuario, categoria_trabalhador, texto_comentario, nota_impacto, classificacao_ia)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (id_noticia, 'Você (Usuário)', 'Cidadão', texto_usuario, 5.0, 'Útil (Feedback Real)'))
        
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