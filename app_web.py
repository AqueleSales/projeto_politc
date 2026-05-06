from flask import Flask, render_template, jsonify, request
import database
import agentes_ia
import ingestao  # <-- Precisamos importar o motor de ingestão aqui!

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/noticias')
def api_noticias():
    pagina = int(request.args.get('pagina', 1))

    # Tenta puxar do banco local primeiro
    lista_noticias = database.buscar_vitrine_paginada(pagina, limite=5)

    # ---> A MÁGICA ACONTECE AQUI <---
    # Se a lista estiver vazia (primeiro acesso ou chegou no fim das páginas)
    if not lista_noticias:
        print(f"⚠️ Página {pagina} vazia! Acionando os robôs para buscar mais notícias...")
        ingestao.executar_ingestao()
        agentes_ia.gerar_titulos_pendentes(limite=5)

        # Tenta buscar no banco de novo depois que os robôs trabalharam
        lista_noticias = database.buscar_vitrine_paginada(pagina, limite=5)

    noticias_json = [{"id": noti[0], "titulo": noti[1]} for noti in lista_noticias]

    # Adicionando cabeçalho de Cache simples (O navegador salva isso por 1 hora)
    resposta = jsonify(noticias_json)
    resposta.headers["Cache-Control"] = "public, max-age=3600"
    return resposta


@app.route('/api/ler_materia/<int:id_noticia>')
def api_ler_materia(id_noticia):
    materia = agentes_ia.gerar_materia_sob_demanda(id_noticia)

    resposta = jsonify({"id": id_noticia, "texto_materia": materia})
    # Matéria completa também tem cache de 1 hora!
    resposta.headers["Cache-Control"] = "public, max-age=3600"
    return resposta


if __name__ == '__main__':
    print("🚀 Servidor Web iniciado! Acesse: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)