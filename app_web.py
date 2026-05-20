import io
import matplotlib

matplotlib.use('Agg')  # <-- OBRIGATÓRIO para o Matplotlib funcionar dentro do Flask
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, render_template, jsonify, request, Response
from database import conectar, obter_engine_pandas
from agentes_ia import gerar_materia_sob_demanda  # Importa o seu agente do Llama 3.1

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


# --- ROTA 4: FÓRUM (PUXA OS COMENTÁRIOS DO BANCO NEON) ---
@app.route('/api/forum')
def api_forum():
    conn = conectar()
    cursor = conn.cursor()

    # CORREÇÃO AQUI: Mudamos de "ORDER BY id_forum DESC" para "ORDER BY id_noticia DESC"
    cursor.execute('''
                   SELECT nome_usuario, categoria_trabalhador, texto_comentario, nota_impacto, classificacao_ia
                   FROM forum
                   ORDER BY id_noticia DESC LIMIT 50
                   ''')

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


# --- ROTA 5: DASHBOARD DINÂMICO (MATPLOTLIB + PANDAS) ---
@app.route('/api/dashboard.png')
def obter_dashboard_dinamico():
    try:
        engine = obter_engine_pandas()

        # Nova query com CASE WHEN para limpar os dados antigos na hora da leitura
        query = """
            SELECT 
                CASE 
                    WHEN classificacao_ia ILIKE '%não%' OR classificacao_ia ILIKE '%inútil%' OR classificacao_ia ILIKE '%pouco%' THEN 'Não Útil'
                    ELSE 'Útil'
                END as sentimento,
                COUNT(*) as total 
            FROM forum 
            GROUP BY sentimento
        """
        df = pd.read_sql(query, engine)

        if df.empty:
            df = pd.DataFrame({'sentimento': ['Sem Dados'], 'total': [1]})

        plt.figure(figsize=(7, 5))

        # Cores: Verde para Útil, Vermelho para Não Útil (ou cinza para outros)
        cores = ['#2ecc71' if s == 'Útil' else '#e74c3c' for s in df['sentimento']]

        # Criando o gráfico de pizza com estilo moderno
        plt.pie(df['total'], labels=df['sentimento'], autopct='%1.1f%%', startangle=140,
                colors=cores, textprops={'fontsize': 12, 'weight': 'bold'},
                wedgeprops={'edgecolor': 'white', 'linewidth': 2})

        plt.title('Sentimento Público Geral sobre as Leis', fontsize=14, fontweight='bold', pad=15)
        plt.tight_layout()

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100)
        img_buffer.seek(0)
        plt.close()

        return Response(img_buffer.getvalue(), mimetype='image/png')

    except Exception as e:
        print(f"Erro ao gerar gráfico de pizza: {e}")
        return "Erro ao processar dados do gráfico", 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)