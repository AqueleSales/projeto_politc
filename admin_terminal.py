import time
from ingestao import popular_banco
from agentes_ia import gerar_titulos_pendentes
from simulador_forum import executar_simulador


def exibir_menu():
    print("\n" + "=" * 50)
    print("🏛️  PAINEL DE ADMINISTRAÇÃO - eREDO".center(50))
    print("=" * 50)
    print("Escolha a etapa do pipeline para executar:")
    print("  [1] 📡 Ingestão: Buscar Projetos da Câmara")
    print("  [2] ✍️  IA Editora: Gerar Títulos e Resumos")
    print("  [3] 🗣️  IA Fórum: Simular População (Comentários)")
    print("  [4] 🚀 RODAR PIPELINE COMPLETO (1, 2 e 3)")
    print("  [0] ❌ Sair")
    print("=" * 50)


def main():
    while True:
        exibir_menu()
        opcao = input("\n👉 Digite o número da opção desejada: ")

        if opcao == '1':
            popular_banco()

        elif opcao == '2':
            print("\n[Admin] Iniciando o Agente Editor...")
            # Puxando até 15 leis sem título para processar
            sucesso = gerar_titulos_pendentes(limite=15)
            if not sucesso:
                print("   ✅ Todas as leis do banco já possuem títulos gerados!")

        elif opcao == '3':
            executar_simulador()

        elif opcao == '4':
            print("\n🚀 INICIANDO PIPELINE DE DADOS COMPLETO...")
            time.sleep(1)

            print("\n--- PASSO 1: INGESTÃO ---")
            popular_banco()
            time.sleep(2)

            print("\n--- PASSO 2: AGENTE EDITOR ---")
            gerar_titulos_pendentes(limite=10)
            time.sleep(2)

            print("\n--- PASSO 3: SIMULADOR DE FÓRUM ---")
            executar_simulador()

            print("\n✅ PIPELINE FINALIZADO! O seu portal está 100% atualizado.")

        elif opcao == '0':
            print("\nDesligando terminal admin... Até logo!")
            break

        else:
            print("\n⚠️ Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()