let paginaAtual = 1;

// Quando o site carrega, ele busca a página 1
document.addEventListener("DOMContentLoaded", () => {
    carregarNoticias(paginaAtual);

    // Configura os botões de próxima/anterior
    document.getElementById('btn-proximo').addEventListener('click', () => {
        paginaAtual++;
        carregarNoticias(paginaAtual);
    });

    document.getElementById('btn-anterior').addEventListener('click', () => {
        if (paginaAtual > 1) {
            paginaAtual--;
            carregarNoticias(paginaAtual);
        }
    });

    // Configura o botão de fechar a matéria
    document.querySelector('.close-btn').addEventListener('click', () => {
        document.getElementById('modal-materia').style.display = "none";
    });
});

// Busca as notícias no Python (Flask)
function carregarNoticias(pagina) {
    const feed = document.getElementById('feed-noticias');
    feed.innerHTML = '<div class="loading">Buscando atualizações na Câmara...</div>';

    document.getElementById('pagina-atual').innerText = `Página ${pagina}`;
    document.getElementById('btn-anterior').disabled = (pagina === 1);

    fetch(`/api/noticias?pagina=${pagina}`)
        .then(response => response.json())
        .then(noticias => {
            feed.innerHTML = ''; // Limpa o "carregando"

            if (noticias.length === 0) {
                feed.innerHTML = '<p style="text-align:center;">Nenhuma notícia encontrada nesta página.</p>';
                return;
            }

            // Cria um card para cada notícia
            noticias.forEach(noti => {
                const card = document.createElement('div');
                card.className = 'card-noticia';
                card.innerHTML = `<h3>📰 ${noti.titulo}</h3><p style="font-size:0.9em; color:#718096;">Clique para ler a matéria completa gerada pela IA</p>`;

                // Se clicar no card, abre a matéria
                card.addEventListener('click', () => abrirMateria(noti.id, noti.titulo));
                feed.appendChild(card);
            });
        })
        .catch(error => console.error('Erro ao carregar notícias:', error));
}

// Pede para o Python/IA gerar a matéria e mostra na tela
function abrirMateria(id_noticia, titulo) {
    const modal = document.getElementById('modal-materia');
    const modalTitulo = document.getElementById('modal-titulo');
    const modalTexto = document.getElementById('modal-texto');

    modalTitulo.innerText = titulo;
    modalTexto.innerHTML = '<div class="loading">🤖 Agente IA lendo o documento oficial e redigindo a matéria. Aguarde...</div>';
    modal.style.display = "block"; // Mostra a janela

    fetch(`/api/ler_materia/${id_noticia}`)
        .then(response => response.json())
        .then(dados => {
            // Converte quebras de linha em parágrafos do HTML
            const textoFormatado = dados.texto_materia.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
            modalTexto.innerHTML = `<p>${textoFormatado}</p>`;
        })
        .catch(error => {
            modalTexto.innerHTML = '<p style="color:red;">Erro ao gerar a matéria.</p>';
        });
}