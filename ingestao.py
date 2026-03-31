import database
import ingestao

if __name__ == "__main__":
    database.criar_tabelas()
    dados = ingestao.buscar_leis()
    ingestao.salvar_no_banco(dados)
    print("Sistema rodando de forma organizada!")