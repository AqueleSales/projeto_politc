import sqlite3

def conectar():
    return sqlite3.connect('banco_politico.db')

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    # Tabela de Leis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leis (
            id INTEGER PRIMARY KEY,
            numero TEXT,
            ano INTEGER,
            ementa TEXT
        )
    ''')
    # Tabela de Comentários (O Fórum)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comentarios (
            id_comentario INTEGER PRIMARY KEY AUTOINCREMENT,
            id_lei INTEGER,
            texto TEXT,
            nota_impacto INTEGER,
            categoria_trabalhador TEXT,
            FOREIGN KEY (id_lei) REFERENCES leis (id)
        )
    ''')
    conn.commit()
    conn.close()