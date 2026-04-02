import sqlite3

def conectar():
    """Cria e retorna a conexão com o banco de dados principal."""
    return sqlite3.connect('banco_politico.db')

def criar_tabelas():
    """Configura o banco de dados do zero para suportar Front-end e IAs."""
    conn = conectar()
    cursor = conn.cursor()

    # TABELA 1: Notícias e Leis (Alimenta a Página 1 e a Página 2)
    # Aqui guardamos o dado bruto do governo e os textos gerados pelas IAs 1 e 2
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id_noticia INTEGER PRIMARY KEY,
            numero_lei TEXT,
            ano_lei INTEGER,
            ementa_oficial TEXT,          -- Texto original (difícil)
            titulo_vitrine TEXT,          -- Gerado pela IA 1 (Para Página 1)
            resumo_vitrine TEXT,          -- Gerado pela IA 1 (Para Página 1)
            materia_completa TEXT         -- Gerado pela IA 2 (Para Página 2)
        )
    ''')

    # TABELA 2: Fórum de Discussão (Alimenta a Página 3 e a Página 4)
    # Recebe os dados do usuário e guarda o espaço para a IA 3 (Análise de Sentimento)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forum (
            id_comentario INTEGER PRIMARY KEY AUTOINCREMENT,
            id_noticia INTEGER,           -- Conecta o comentário à notícia correta
            nome_usuario TEXT,            -- Simulação de login
            categoria_trabalhador TEXT,   -- Ex: CLT, Autônomo
            texto_comentario TEXT,        -- O que a pessoa escreveu
            nota_impacto INTEGER,         -- Nota de 1 a 5
            classificacao_ia TEXT,        -- IA 3 vai preencher com: Positivo, Negativo ou Neutro
            FOREIGN KEY (id_noticia) REFERENCES noticias (id_noticia)
        )
    ''')

    conn.commit()
    conn.close()
    print("Sucesso: Alicerce do banco de dados criado com sucesso! Tabelas 'noticias' e 'forum' prontas.")

# Se você rodar este arquivo direto, ele cria o banco.
if __name__ == "__main__":
    criar_tabelas()