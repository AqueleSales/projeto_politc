import database
import ingestao
import agentes_ia


def central_de_comando():
    print("Iniciando o Servidor Central...")
    database.criar_tabelas()

    pagina_atual = 1
    limite_por_pagina = 3

    # ---------------------------------------------------------
    # AUTO-BUSCA NO INÍCIO (Totalmente invisível para o usuário)
    # ---------------------------------------------------------
    noticias_iniciais = database.buscar_vitrine_paginada(1, limite_por_pagina)
    if not noticias_iniciais:
        print("\n[Primeiro acesso detectado. Baixando as leis oficiais automaticamente...]")
        ingestao.executar_ingestao()
        agentes_ia.gerar_titulos_pendentes(limite=limite_por_pagina)

    while True:
        print("\n" + "=" * 55)
        print("🏛️  CENTRAL DE COMANDO - PROJETO TURMA B")
        print(f"               (Página {pagina_atual})")
        print("=" * 55)

        lista_noticias = database.buscar_vitrine_paginada(pagina_atual, limite_por_pagina)

        if not lista_noticias:
            print("A vitrine está vazia nesta página.")
        else:
            for i, (id_noticia, titulo) in enumerate(lista_noticias, start=1):
                print(f"{i}. {titulo}")

        print("-" * 55)
        print("Opções:")
        if lista_noticias:
            print(" [1, 2, 3] -> Ler a matéria completa")
        print(" [proximo] -> Avançar página (Baixa novas leis automaticamente se precisar)")
        if pagina_atual > 1:
            print(" [anterior]-> Voltar página")
        print(" [sair]    -> Desligar o sistema")

        escolha = input("\nO que você deseja fazer? ").strip().lower()

        # ---------------------------------------------------------
        # LÓGICA DE NAVEGAÇÃO INTELIGENTE
        # ---------------------------------------------------------
        if escolha == 'proximo':
            # Verifica se JÁ TEMOS a próxima página salva no banco
            if database.tem_proxima_pagina(pagina_atual, limite_por_pagina):
                pagina_atual += 1
                print("\n[Avançando página...]")
            else:
                # Se NÃO TEMOS, ele faz a busca no governo sozinho!
                print("\n[Chegamos ao fim da lista local. Buscando mais leis no Governo...]")
                ingestao.executar_ingestao()
                agentes_ia.gerar_titulos_pendentes(limite=limite_por_pagina)

                # Verifica de novo se a busca trouxe resultados novos
                if database.tem_proxima_pagina(pagina_atual, limite_por_pagina):
                    pagina_atual += 1
                    print("\n[Novas leis processadas! Avançando página...]")
                else:
                    print("\n⚠️ Não há mais leis novas disponíveis no momento. Tente novamente mais tarde.")

        elif escolha == 'anterior':
            if pagina_atual > 1:
                pagina_atual -= 1
                print("\n[Voltando página...]")
            else:
                print("\n⚠️ Você já está na primeira página.")

        elif escolha in ['1', '2', '3']:
            if not lista_noticias:
                print("\n⚠️ Não há notícias nesta posição.")
                continue

            indice = int(escolha) - 1
            if indice < len(lista_noticias):
                id_escolhido = lista_noticias[indice][0]
                titulo_escolhido = lista_noticias[indice][1]

                print(f"\n" + "=" * 55)
                print(f"📰 {titulo_escolhido.upper()}")
                print("=" * 55)

                # O Lazy Loading da matéria continua funcionando perfeito aqui
                materia = agentes_ia.gerar_materia_sob_demanda(id_escolhido)

                print(f"\n{materia}\n")
                print("=" * 55)
                input("➡️ Pressione ENTER para voltar à vitrine...")
            else:
                print("\n⚠️ Posição vazia. Escolha um número válido.")

        elif escolha in ['sair', 'esc']:
            print("\nDesligando os servidores... Até logo!")
            break

        else:
            print("\n⚠️ Comando não reconhecido. Tente novamente.")


if __name__ == "__main__":
    central_de_comando()