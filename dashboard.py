import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from collections import Counter


def tokenizar_comentarios(textos):
    """
    Função de Processamento de Linguagem Natural (NLP).
    Limpa os textos, remove palavras inúteis e conta as mais frequentes.
    """
    # Dicionário de 'Stopwords' (palavras vazias que a IA deve ignorar)
    stopwords = {
        'o', 'a', 'os', 'as', 'um', 'uma', 'e', 'de', 'do', 'da', 'dos', 'das',
        'em', 'no', 'na', 'nos', 'nas', 'para', 'com', 'por', 'que', 'se', 'é',
        'não', 'mais', 'mas', 'como', 'ao', 'aos', 'ou', 'sua', 'seu', 'são',
        'sobre', 'isso', 'muito', 'tem', 'ser'
    }

    todas_palavras = []

    for texto in textos:
        if not texto: continue

        # 1. Limpeza: Transforma tudo em minúsculo e remove pontuações com Regex
        palavras_limpas = re.findall(r'\b[a-zà-ú]+\b', str(texto).lower())

        # 2. Filtro: Mantém apenas palavras que não são stopwords e têm mais de 2 letras
        for palavra in palavras_limpas:
            if palavra not in stopwords and len(palavra) > 2:
                todas_palavras.append(palavra)

    # 3. Contagem: Retorna as 10 palavras mais usadas
    return Counter(todas_palavras).most_common(10)


def gerar_dashboard():
    print("\n📊 Processando dados do banco e executando Tokenização...")

    # 1. Conectar e carregar dados
    conn = sqlite3.connect('banco_politico.db')
    query = '''
            SELECT n.titulo_vitrine, f.categoria_trabalhador, f.nota_impacto, f.classificacao_ia, f.texto_comentario
            FROM forum f
                     JOIN noticias n ON f.id_noticia = n.id_noticia \
            '''
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("❌ Banco de dados vazio. Rode o simulador primeiro!")
        return

    # Configuração de estilo visual
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Painel de Inteligência de Dados - Projeto Turma B', fontsize=22, fontweight='bold', color='#333333')

    # ---------------------------------------------------------
    # GRÁFICO 1: Média de Notas por Lei
    # ---------------------------------------------------------
    sns.barplot(ax=axes[0, 0], data=df, x='nota_impacto', y='titulo_vitrine', hue='titulo_vitrine', palette='viridis', legend=False, errorbar=None)
    axes[0, 0].set_title('Média de Aceitação (0 a 5 estrelas)', fontsize=14)
    axes[0, 0].set_xlabel('Nota Média')
    axes[0, 0].set_ylabel('')

    # ---------------------------------------------------------
    # GRÁFICO 2: Distribuição de Sentimento (Útil vs Não Útil)
    # ---------------------------------------------------------
    sentiment_counts = df['classificacao_ia'].value_counts()
    axes[0, 1].pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%',
                   colors=['#4CAF50', '#FF5252'], startangle=140, textprops={'fontsize': 12})
    axes[0, 1].set_title('Percepção de Utilidade Geral', fontsize=14)

    # ---------------------------------------------------------
    # GRÁFICO 3: Reação por Categoria de Trabalhador
    # ---------------------------------------------------------
    sns.boxplot(ax=axes[1, 0], data=df, x='categoria_trabalhador', y='nota_impacto', hue='categoria_trabalhador', palette='Set2', legend=False)
    axes[1, 0].set_title('Variabilidade de Opinião por Classe Social', fontsize=14)
    axes[1, 0].set_xlabel('Perfil do Cidadão')
    axes[1, 0].set_ylabel('Nota Dada')

    # ---------------------------------------------------------
    # GRÁFICO 4: Tokenização (Palavras-Chave dos Comentários)
    # ---------------------------------------------------------
    # Aplica nossa função de NLP na coluna de textos
    top_palavras = tokenizar_comentarios(df['texto_comentario'])
    # Prepara os dados para o gráfico
    palavras = [item[0] for item in top_palavras]
    frequencias = [item[1] for item in top_palavras]
    sns.barplot(ax=axes[1, 1], x=frequencias, y=palavras, hue=palavras, palette='magma', legend=False)
    axes[1, 1].set_title('Tendências (Termos Mais Falados)', fontsize=14)
    axes[1, 1].set_xlabel('Frequência de Uso')
    axes[1, 1].set_ylabel('Palavras-Chave')

    # ---------------------------------------------------------
    # Finalização e Exportação
    # ---------------------------------------------------------
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('dashboard_final.png', dpi=300)  # Salva em alta resolução
    print("\n✅ Dashboard gerado com sucesso! Arquivo 'dashboard_final.png' salvo na sua pasta.")

    # Abre a janela interativa com os gráficos
    plt.show()


if __name__ == "__main__":
    gerar_dashboard()