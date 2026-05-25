import psycopg2
from sqlalchemy import create_engine

# COLE A SUA URL DO NEON AQUI DENTRO (Mantenha as aspas)
DATABASE_URL = "x"

def conectar():
    # Cria a conexão direta com a Nuvem
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def obter_engine_pandas():
    # O Pandas precisa desse "engine" especial para salvar os dados na nuvem
    return create_engine(DATABASE_URL)

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # No Postgres, usamos BIGINT para IDs longos e SERIAL para autoincremento
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id_noticia BIGINT PRIMARY KEY,
            numero_lei TEXT,
            ano_lei INTEGER,
            ementa_oficial TEXT,
            titulo_vitrine TEXT,
            resumo_vitrine TEXT,
            materia_completa TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forum (
            id_comentario SERIAL PRIMARY KEY,
            id_noticia BIGINT,
            nome_usuario TEXT,
            categoria_trabalhador TEXT,
            texto_comentario TEXT,
            nota_impacto REAL,
            classificacao_ia TEXT,
            FOREIGN KEY (id_noticia) REFERENCES noticias(id_noticia)
        )
    ''')
    conn.commit()
    conn.close()

def buscar_vitrine_paginada(pagina=1, limite=3):
    conn = conectar()
    cursor = conn.cursor()
    offset = (pagina - 1) * limite

    # No Postgres usamos %s no lugar de ?
    cursor.execute('''
        SELECT id_noticia, titulo_vitrine
        FROM noticias
        WHERE titulo_vitrine IS NOT NULL
          AND titulo_vitrine != 'Título Indisponível'
        ORDER BY id_noticia DESC
        LIMIT %s OFFSET %s
    ''', (limite, offset))

    resultados = cursor.fetchall()
    conn.close()
    return resultados

def tem_proxima_pagina(pagina, limite):
    conn = conectar()
    cursor = conn.cursor()
    offset = pagina * limite

    cursor.execute('''
        SELECT COUNT(*)
        FROM noticias
        WHERE titulo_vitrine IS NOT NULL
          AND titulo_vitrine != 'Título Indisponível'
        OFFSET %s LIMIT 1
    ''', (offset,))

    qtd = cursor.fetchone()[0]
    conn.close()
    return qtd > 0
