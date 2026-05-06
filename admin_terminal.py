import database
import ingestao
import agentes_ia
import dashboard  # <-- IMPORTAMOS O SEU NOVO ARQUIVO DE GRÁFICOS AQUI!


# ---------------------------------------------------------
# COLETAR FEEDBACK
# ---------------------------------------------------------

def coletar_feedback_usuario(id_noticia):
    print("\n" + "=" * 40)
    print("💬 ESPAÇO DO LEITOR - DEIXE SUA OPINIÃO")
    print("=" * 40)
    print("(Pressione ENTER vazio em qualquer campo para pular)")

    try:
        # 1. Avaliação em Estrelas (0 a 5)
        nota_input = input("\n⭐ Que nota você dá para esta lei? (0 a 5): ").strip()
        if not nota_input:
            print("Feedback cancelado.")
            return

        nota = float(nota_input.replace(',', '.'))
        if not (0 <= nota <= 5):
            print("❌ Nota inválida. Feedback cancelado.")
            return

        # 2. Útil ou Não Útil
        util_input = input("👍 Essa notícia foi útil para você? (S/N): ").strip().upper()
        if not util_input: return
        classificacao = "Útil" if util_input == 'S' else "Não Útil"

        # 3. Comentário
        comentario = input("📝 O que você achou do impacto dessa lei? \n-> ").strip()
        if not comentario: comentario = "Sem comentário textual."

        # SALVAR NO BANCO
        from database import conectar
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('''
                       INSERT INTO forum (id_noticia, nome_usuario, categoria_trabalhador, texto_comentario,
                                          nota_impacto, classificacao_ia)
                       VALUES (?, ?, ?, ?, ?, ?)
                       ''', (id_noticia, "Usuário Real", "Leitor", comentario, nota, classificacao))
        conn.commit()
        conn.close()

        print("\n✅ Feedback salvo com sucesso! Obrigado por participar.")

    except ValueError:
        print("❌ Erro: Digite um número válido para a nota (ex: 4.5).")


def central_de_comando():
    print("Iniciando o Servidor Central...")
    database.criar_tabelas()

    pagina_atual = 1
    limite_por_pagina = 3

    # ---------------------------------------------------------
    # AUTO-BUSCA NO INÍCIO
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

        # ---> NOVA OPÇÃO DO MENU AQUI <---
        print(" [painel]  -> 📊 Abrir Dashboard de Análise de Dados")
        print(" [sair]    -> Desligar o sistema")

        escolha = input("\nO que você deseja fazer? ").strip().lower()

        # ---------------------------------------------------------
        # NAVEGAÇÃO
        # ---------------------------------------------------------

        if escolha == 'proximo':
            if database.tem_proxima_pagina(pagina_atual, limite_por_pagina):
                pagina_atual += 1
                print("\n[Avançando página...]")
            else:
                print("\n[Chegamos ao fim da lista local. Buscando mais leis no Governo...]")
                ingestao.executar_ingestao()
                agentes_ia.gerar_titulos_pendentes(limite=limite_por_pagina)
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

                materia = agentes_ia.gerar_materia_sob_demanda(id_escolhido)

                print("\n" + materia + "\n")
                print("-" * 55)

                # Chama a coleta de feedback perfeitamente alinhada
                coletar_feedback_usuario(id_escolhido)

                print("=" * 55)
                input("➡️ Pressione ENTER para voltar à vitrine...")
            else:
                print("\n⚠️ Posição vazia. Escolha um número válido.")

        # ---> LÓGICA DO NOVO BOTÃO AQUI <---
        elif escolha == 'painel':
            dashboard.gerar_dashboard()
            print("=" * 55)
            input("➡️ Pressione ENTER para voltar ao menu principal...")

        elif escolha in ['sair', 'esc']:
            print("\nDesligando os servidores... Até logo!")
            break

        else:
            print("\n⚠️ Comando não reconhecido. Tente novamente.")


if __name__ == "__main__":
    central_de_comando()