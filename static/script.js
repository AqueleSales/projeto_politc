let paginaAtual = 1;
// Variável global para sabermos qual notícia estamos lendo agora
let leiAtualLida = null; 

document.addEventListener("DOMContentLoaded", () => {
    const navLinks = document.querySelectorAll('.nav-link');
    const tabContents = document.querySelectorAll('.tab-content');
    const viewNormal = document.getElementById('view-normal');
    const viewLeitura = document.getElementById('view-leitura');

    // 1. CLIQUE NO MENU LATERAL ESQUERDO
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            viewLeitura.style.display = 'none';
            viewNormal.style.display = 'block';

            navLinks.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            link.classList.add('active');
            const targetId = link.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // 2. CONFIGURAÇÃO DAS NOTÍCIAS
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

    // 3. BOTÃO "VOLTAR" DA TELA DE LEITURA
    document.getElementById('btn-voltar-feed').addEventListener('click', () => {
        viewLeitura.style.display = 'none';
        viewNormal.style.display = 'block';
        leiAtualLida = null; // Limpa a memória
        
        navLinks.forEach(nav => nav.classList.remove('active'));
        document.querySelector('[data-target="feed-noticias-section"]').classList.add('active');
        tabContents.forEach(tab => tab.classList.remove('active'));
        document.getElementById('feed-noticias-section').classList.add('active');
    });

    // 4. A MÁGICA: BOTÃO DE ENVIAR FEEDBACK
    document.querySelector('.btn-enviar-feedback').addEventListener('click', () => {
        const inputTexto = document.querySelector('.feedback-input');
        const texto = inputTexto.value.trim();

        if (texto === "") {
            alert("Por favor, digite sua opinião antes de enviar.");
            return;
        }

        if (leiAtualLida === null) {
            alert("Erro: Não foi possível identificar a lei atual.");
            return;
        }

        // Muda o botão para "Enviando..."
        const btn = document.querySelector('.btn-enviar-feedback');
        btn.innerText = "Enviando...";
        btn.disabled = true;

        // Manda pro Python salvar no banco Neon
        fetch('/api/enviar_feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id_noticia: leiAtualLida,
                texto: texto
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                inputTexto.value = ""; // Limpa a caixinha
                alert("Opinião enviada com sucesso!");
                
                // --- ATUALIZA TUDO DINAMICAMENTE! ---
                carregarForumEChart(leiAtualLida); 
            } else {
                alert("Erro ao enviar: " + data.erro);
            }
        })
        .catch(error => {
            alert("Erro de conexão ao enviar feedback.");
        })
        .finally(() => {
            // Volta o botão ao normal
            btn.innerText = "Enviar";
            btn.disabled = false;
        });
    });
});

function carregarNoticias(pagina) {
    const feed = document.getElementById('feed-noticias');
    feed.innerHTML = '<div class="loading">Buscando atualizações na Câmara...</div>';
    document.getElementById('pagina-atual').innerText = `Página ${pagina}`;
    document.getElementById('btn-anterior').disabled = (pagina === 1);

    fetch(`/api/noticias?pagina=${pagina}`)
        .then(response => response.json())
        .then(noticias => {
            feed.innerHTML = '';
            if (noticias.length === 0) {
                feed.innerHTML = '<p style="text-align:center;">Nenhuma notícia encontrada nesta página.</p>';
                return;
            }

            noticias.forEach(noti => {
                const card = document.createElement('div');
                card.className = 'card-noticia';
                const imageUrl = `https://picsum.photos/seed/${noti.id}/400/200`;

                card.innerHTML = `
                    <div style="width: 100%; height: 160px; overflow: hidden; border-radius: 8px 8px 0 0; margin-bottom: 12px;">
                        <img src="${imageUrl}" style="width: 100%; height: 100%; object-fit: cover;" alt="Capa da Lei">
                    </div>
                    <h3>🏛️ ${noti.titulo}</h3>
                    <p>Ler Análise de Impacto Completa ➔</p>
                `;
                card.addEventListener('click', () => abrirMateria(noti.id, noti.titulo));
                feed.appendChild(card);
            });
        })
        .catch(error => console.error('Erro ao carregar notícias:', error));
}


function abrirMateria(id_noticia, titulo) {
    leiAtualLida = id_noticia; // Salva o ID globalmente para o feedback usar

    document.getElementById('view-normal').style.display = 'none';
    document.getElementById('view-leitura').style.display = 'block';
    window.scrollTo(0, 0); 

    const banner = document.getElementById('materia-banner');
    const modalTitulo = document.getElementById('materia-titulo');
    const modalTexto = document.getElementById('materia-texto');
    
    banner.src = `https://picsum.photos/seed/${id_noticia}/1200/400`; 
    modalTitulo.innerText = titulo;
    modalTexto.innerHTML = '<div class="loading">🤖 Agente IA lendo o documento oficial e redigindo a matéria. Aguarde...</div>';
    
    // Busca a Matéria Textual
    fetch(`/api/ler_materia/${id_noticia}`)
        .then(response => response.json())
        .then(dados => {
            const textoFormatado = dados.texto_materia.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
            modalTexto.innerHTML = `<p>${textoFormatado}</p>`;
        });

    // Chama a função isolada que carrega só a barra da direita
    carregarForumEChart(id_noticia);
}

// Essa função isolada atualiza a lateral. Ela é chamada quando abre a matéria E quando você envia um feedback.
function carregarForumEChart(id_noticia) {
    const chartImg = document.getElementById('dashboard-chart');
    const forumContainer = document.getElementById('container-comentarios-forum');

    // Atualiza a Imagem (força não usar cache)
    chartImg.src = "";
    chartImg.src = `/api/dashboard/${id_noticia}.png?t=${new Date().getTime()}`;

    // Atualiza a lista do Fórum
    forumContainer.innerHTML = '<div class="loading">Carregando debates da população...</div>';
    fetch(`/api/forum/${id_noticia}`)
        .then(response => response.json())
        .then(comentarios => {
            forumContainer.innerHTML = '';
            
            if (comentarios.length === 0) {
                forumContainer.innerHTML = '<p style="text-align:center; color:#718096; font-size: 0.9em;">Seja o primeiro a comentar!</p>';
                return;
            }

            comentarios.forEach(c => {
                const card = document.createElement('div');
                card.className = 'comentario-card';
                // Se for você, pinta o card de um azul clarinho pra destacar
                if(c.nome_usuario === 'Você (Usuário)') {
                    card.style.backgroundColor = "#eebff";
                    card.style.border = "1px solid #3182ce";
                }
                
                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <strong style="font-size: 0.9em;">👤 ${c.nome_usuario}</strong>
                        <span style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; color: #4a5568;">${c.categoria}</span>
                    </div>
                    <p style="font-style: italic; color: #2d3748; font-size: 0.85em;">"${c.texto}"</p>
                    <div style="margin-top: 8px; font-size: 0.8em; color: #3182ce;">
                        <span>⭐ ${c.nota}/5</span> | 
                        <strong>${c.classificacao}</strong>
                    </div>
                `;
                forumContainer.appendChild(card);
            });
        });
}