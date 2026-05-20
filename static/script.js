let paginaAtual = 1;

// Quando o site carrega, ele configura tudo
document.addEventListener("DOMContentLoaded", () => {

    // --- 1. NAVEGAÇÃO LATERAL (ABAS) ---
    const navLinks = document.querySelectorAll('.nav-link');
    const tabContents = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault(); // Evita que a página recarregue

            // Remove a classe 'active' de todos os links e abas
            navLinks.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));

            // Adiciona a classe 'active' apenas no link clicado
            link.classList.add('active');

            // Descobre qual é a tela alvo e mostra ela
            const targetId = link.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');

            // Se o usuário abriu a aba do Fórum, dispara a busca no banco!
            if (targetId === 'forum-section') {
                carregarForum();
            }
        });
    });

    // --- 2. CONFIGURAÇÃO DAS NOTÍCIAS ---
    carregarNoticias(paginaAtual);

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

// --- FUNÇÕES DE BUSCA NO BACK-END ---

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
                card.style.cursor = "pointer";

                // Formata o título da lei para a IA de imagens entender o contexto
                const termoBusca = encodeURIComponent("brazil politics law congress " + noti.titulo);

                // Pollinations AI gera uma imagem na hora baseada no título da notícia!
                const imageUrl = `https://image.pollinations.ai/prompt/${termoBusca}?width=400&height=200&nologo=true`;

                // Os estilos inline de texto foram removidos para o style.css agir
                card.innerHTML = `
                    <div style="width: 100%; height: 160px; overflow: hidden; border-radius: 8px 8px 0 0; margin-bottom: 12px;">
                        <img src="${imageUrl}" style="width: 100%; height: 100%; object-fit: cover;" alt="Capa da Lei">
                    </div>
                    <h3>🏛️ ${noti.titulo}</h3>
                    <p>Ler Análise de Impacto Completa ➔</p>
                `;

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

// Busca os comentários gerados pelo Llama 3.1 no banco Neon
function carregarForum() {
    const container = document.getElementById('container-comentarios-forum');
    container.innerHTML = '<div class="loading">Carregando debates simulados...</div>';

    fetch('/api/forum')
        .then(response => response.json())
        .then(comentarios => {
            container.innerHTML = '';

            if (comentarios.length === 0) {
                container.innerHTML = '<p>Nenhum comentário gerado ainda. Rode o simulador de fórum!</p>';
                return;
            }

            // Cria um card para cada comentário da IA
            comentarios.forEach(c => {
                const card = document.createElement('div');
                card.className = 'comentario-card';
                card.style.border = "1px solid #ddd";
                card.style.padding = "15px";
                card.style.margin = "10px 0";
                card.style.borderRadius = "8px";
                card.style.backgroundColor = "#fff";

                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <strong>👤 ${c.nome_usuario}</strong>
                        <span style="background: #e2e8f0; padding: 3px 8px; border-radius: 4px; font-size: 0.8em;">${c.categoria}</span>
                    </div>
                    <p style="font-style: italic; color: #4a5568;">"${c.texto}"</p>
                    <div style="margin-top: 10px; font-size: 0.9em; color: #2b6cb0;">
                        <span>⭐ Nota de Impacto: ${c.nota}/5</span> | 
                        <strong>IA classificou como: ${c.classificacao}</strong>
                    </div>
                `;
                container.appendChild(card);
            });
        })
        .catch(error => {
            container.innerHTML = '<p style="color:red;">Erro ao carregar o fórum.</p>';
        });
}