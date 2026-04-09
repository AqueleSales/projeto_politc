import sqlite3


def conectar():
    """Cria e retorna a conexão com o banco de dados principal."""
    return sqlite3.connect('banco_politico.db')


def criar_tabelas():
    """Configura o banco de dados do zero para suportar Front-end e IAs."""
    conn = conectar()
    cursor = conn.cursor()

    # TABELA 1: Notícias e Leis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id_noticia INTEGER PRIMARY KEY,
            numero_lei TEXT,
            ano_lei INTEGER,
            ementa_oficial TEXT,
            titulo_vitrine TEXT,
            resumo_vitrine TEXT,
            materia_completa TEXT
        )
    ''')

    # TABELA 2: Fórum de Discussão
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forum (
            id_comentario INTEGER PRIMARY KEY AUTOINCREMENT,
            id_noticia INTEGER,
            nome_usuario TEXT,
            categoria_trabalhador TEXT,
            texto_comentario TEXT,
            nota_impacto INTEGER,
            classificacao_ia TEXT,
            FOREIGN KEY (id_noticia) REFERENCES noticias (id_noticia)
        )
    ''')

    conn.commit()
    conn.close()


# ==========================================
# FUNÇÕES DE CARROSSEL (PAGINAÇÃO)
# ==========================================

def buscar_vitrine_paginada(pagina=1, limite=3):
    conn = conectar()
    cursor = conn.cursor()
    pulo = (pagina - 1) * limite

    # Usamos ASC. As novas leis vão para o final da fila (Página 2, 3...)
    cursor.execute('''
        SELECT id_noticia, titulo_vitrine
        FROM noticias
        WHERE titulo_vitrine IS NOT NULL
        ORDER BY id_noticia ASC 
        LIMIT ? OFFSET ?
    ''', (limite, pulo))

    resultados = cursor.fetchall()
    conn.close()
    return resultados


def tem_proxima_pagina(pagina_atual, limite=3):
    """Olha uma página para frente para ver se o botão 'proximo' deve funcionar."""
    resultados_futuros = buscar_vitrine_paginada(pagina_atual + 1, limite)
    return len(resultados_futuros) > 0


if __name__ == "__main__":
    criar_tabelas()
    print("Tabelas verificadas e funções de paginação prontas!")