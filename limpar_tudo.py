from database import conectar

def limpar_banco_completo():
    conn = conectar()
    cursor = conn.cursor()
    try:
        # CASCADE: Apaga as notícias e todos os comentários do fórum ligados a elas!
        cursor.execute("TRUNCATE TABLE noticias CASCADE;")
        conn.commit()
        print("💥 BANCO ZERADO! Tabela de notícias e fórum estão completamente limpas.")
    except Exception as e:
        print(f"❌ Erro ao limpar o banco: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    limpar_banco_completo()