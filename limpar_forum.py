from database import conectar


def limpar_tabela_forum():
    print("🧹 Conectando ao banco Neon...")
    conn = conectar()
    cursor = conn.cursor()

    try:
        # O comando TRUNCATE apaga todas as linhas da tabela de uma vez e zera os IDs
        cursor.execute("TRUNCATE TABLE forum;")
        conn.commit()
        print("✅ Sucesso! O Fórum foi completamente zerado.")
    except Exception as e:
        print(f"❌ Erro ao limpar o banco: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    limpar_tabela_forum()