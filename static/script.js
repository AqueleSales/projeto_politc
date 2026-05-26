let paginaAtual = 1;
let leiAtualLida = null;
let notaSelecionada = 0;
let carregandoNews = false;
let temMaisNoticias = true;
let termoPesquisaAtual = ""; // Variável para guardar o que o usuário está pesquisando
let filtrosAtivos = []; // Variável para guardar os filtros selecionados no modal

document.addEventListener("DOMContentLoaded", () => {
    // --- LÓGICA DE URL E NAVEGAÇÃO ---
    const urlParams = new URLSearchParams(window.location.search);
    const leiDaUrl = urlParams.get('lei');
    if (leiDaUrl) {
        abrirMateria(leiDaUrl, "Projeto de Lei", false);
    } else {
        carregarNoticias(paginaAtual);
    }

    window.addEventListener('popstate', (e) => {
        const params = new URLSearchParams(window.location.search);
        if (params.get('lei')) {
            abrirMateria(params.get('lei'), "Projeto de Lei", false);
        } else {
            fecharMateria(false);
        }
    });

    // --- MENU LATERAL (ABAS) ---
    const navLinks = document.querySelectorAll('.nav-link');
    const tabContents = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            fecharMateria(true);

            navLinks.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));

            link.classList.add('active');
            const targetId = link.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });

    document.getElementById('btn-voltar-feed').addEventListener('click', () => fecharMateria(true));

    // --- SCROLL INFINITO ---
    const sentinela = document.getElementById('scroll-sentinela');
    const observer = new IntersectionObserver(entries => {
        if (entries[0].isIntersecting && !carregandoNews && temMaisNoticias) {
            paginaAtual++;
            carregarNoticias(paginaAtual);
        }
    });
    observer.observe(sentinela);

    // --- LÓGICA DE FEEDBACK (ESTRELAS) ---
    const starBtns = document.querySelectorAll('.star-btn');
    starBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            notaSelecionada = parseInt(btn.getAttribute('data-nota'));
            document.getElementById('nota-selecionada-display').innerText = `Nota: ${notaSelecionada}.0`;
            starBtns.forEach((s, index) => s.classList.toggle('active', index < notaSelecionada));
        });
    });

    document.querySelector('.btn-enviar-feedback').addEventListener('click', () => {
        const inputTexto = document.getElementById('feedback-texto');
        const texto = inputTexto.value.trim();

        if (texto === "" || notaSelecionada === 0) {
            alert("Por favor, selecione uma nota e digite sua opinião."); return;
        }

        const btn = document.querySelector('.btn-enviar-feedback');
        btn.innerText = "Enviando..."; btn.disabled = true;

        fetch('/api/enviar_feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_noticia: leiAtualLida, texto: texto, nota: notaSelecionada })
        })
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                inputTexto.value = ""; notaSelecionada = 0;
                document.getElementById('nota-selecionada-display').innerText = "Selecione uma nota";
                starBtns.forEach(s => s.classList.remove('active'));
                carregarForumEChart(leiAtualLida);
            }
        })
        .finally(() => { btn.innerText = "Enviar Análise"; btn.disabled = false; });
    });

    // --- LÓGICA DOS FILTROS (TAGS CLICÁVEIS) ---
    const tagsFiltro = document.querySelectorAll('.tag-filtro');
    tagsFiltro.forEach(tag => {
        tag.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    });

    // --- LÓGICA DO BOTÃO APLICAR FILTROS ---
    const btnAplicarFiltros = document.querySelector('.btn-aplicar-filtros');
    if (btnAplicarFiltros) {
        btnAplicarFiltros.addEventListener('click', () => {
            // Pega todas as tags que estão com a classe 'active'
            const tagsAtivas = document.querySelectorAll('.tag-filtro.active');

            // Transforma em uma lista de textos e salva na variável global
            filtrosAtivos = Array.from(tagsAtivas).map(tag => tag.innerText);

            toggleModalFiltro(); // Fecha a janela do modal

            // Reseta o feed e busca as notícias filtradas
            paginaAtual = 1;
            temMaisNoticias = true;
            document.getElementById('feed-noticias').innerHTML = '';
            carregarNoticias(paginaAtual);
        });
    }

    // --- LÓGICA DA BARRA DE PESQUISA ---
    const btnPesquisa = document.querySelector('.search-btn');
    const inputPesquisa = document.getElementById('input-pesquisa');

    function executarPesquisa() {
        if (!inputPesquisa) return;
        termoPesquisaAtual = inputPesquisa.value.trim();
        paginaAtual = 1;
        temMaisNoticias = true;

        // Limpa o feed atual antes de carregar os resultados da pesquisa
        document.getElementById('feed-noticias').innerHTML = '';
        carregarNoticias(paginaAtual);
    }

    if (btnPesquisa && inputPesquisa) {
        // Pesquisa ao clicar na lupa
        btnPesquisa.addEventListener('click', executarPesquisa);

        // Pesquisa ao apertar "Enter" no teclado
        inputPesquisa.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                executarPesquisa();
            }
        });
    }
});

// ============================================================================
// FUNÇÕES GLOBAIS
// ============================================================================

// --- LÓGICA DO MODAL DE FILTROS ---
function toggleModalFiltro() {
    const modal = document.getElementById('modal-filtro');
    if (modal.classList.contains('active')) {
        modal.classList.remove('active');
        setTimeout(() => { modal.style.display = 'none'; }, 300);
    } else {
        modal.style.display = 'flex';
        setTimeout(() => { modal.classList.add('active'); }, 10);
    }
}

function fecharMateria(atualizarUrl = true) {
    if (atualizarUrl) {
        window.history.pushState({}, '', '/');
    }
    document.getElementById('view-leitura').style.display = 'none';
    document.getElementById('view-normal').style.display = 'block';
    leiAtualLida = null;

    document.querySelectorAll('.nav-link').forEach(nav => nav.classList.remove('active'));
    document.querySelector('[data-target="feed-noticias-section"]').classList.add('active');
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById('feed-noticias-section').classList.add('active');
}

function carregarNoticias(pagina) {
    carregandoNews = true;
    const feed = document.getElementById('feed-noticias');
    const sentinela = document.getElementById('scroll-sentinela');

    if (pagina === 1) {
        feed.innerHTML = `
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
            <div class="skeleton-card"></div>
        `;
    } else {
        sentinela.innerHTML = '<div class="skeleton-text" style="width: 200px; margin: 0 auto;"></div>';
    }

    // AQUI: Monta a URL com a Pesquisa E os Filtros
    let urlDaApi = `/api/noticias?pagina=${pagina}&busca=${encodeURIComponent(termoPesquisaAtual)}`;
    if (filtrosAtivos.length > 0) {
        urlDaApi += `&filtros=${encodeURIComponent(filtrosAtivos.join(','))}`;
    }

    fetch(urlDaApi)
        .then(response => response.json())
        .then(noticias => {
            if (noticias.length === 0) {
                temMaisNoticias = false;
                if (pagina === 1) {
                    sentinela.innerHTML = "<p style='grid-column: 1/-1; text-align: center; color: var(--muted-purple); font-weight: bold;'>Nenhuma lei encontrada com estes filtros.</p>";
                } else {
                    sentinela.innerText = "Você chegou ao fim do feed.";
                }
                if (pagina === 1) feed.innerHTML = '';
                return;
            }

            if (pagina === 1) feed.innerHTML = '';
            sentinela.innerHTML = '';

            noticias.forEach(noti => {
                const card = document.createElement('div');
                card.className = 'card-noticia';
                const imageUrl = `https://picsum.photos/seed/lei${noti.id}/400/200`;

                card.innerHTML = `
                    <div style="width: 100%; height: 160px; overflow: hidden; border-radius: 8px 8px 0 0; margin-bottom: 12px;">
                        <img src="${imageUrl}" style="width: 100%; height: 100%; object-fit: cover;" alt="Capa da Lei">
                    </div>
                    <h3>${noti.titulo}</h3>
                    <p>Ler Análise de Impacto Completa ➔</p>
                `;
                card.addEventListener('click', () => abrirMateria(noti.id, noti.titulo, true));
                feed.appendChild(card);
            });
            carregandoNews = false;
        });
}

function abrirMateria(id_noticia, titulo, atualizarUrl = true) {
    leiAtualLida = id_noticia;

    if (atualizarUrl) {
        window.history.pushState({id: id_noticia}, '', `?lei=${id_noticia}`);
    }

    document.getElementById('feedback-texto').value = "";
    notaSelecionada = 0;
    document.getElementById('nota-selecionada-display').innerText = "Selecione uma nota";
    document.querySelectorAll('.star-btn').forEach(s => s.classList.remove('active'));

    document.getElementById('view-normal').style.display = 'none';
    document.getElementById('view-leitura').style.display = 'block';
    window.scrollTo(0, 0);

    document.getElementById('materia-banner').src = `https://picsum.photos/seed/lei${id_noticia}/1200/400`;

    const modalTitulo = document.getElementById('materia-titulo');
    const modalTexto = document.getElementById('materia-texto');

    modalTitulo.innerText = titulo.replace(/TÍTULO:\s*/gi, '').replace(/\*\*(.*?)\*\*/g, '$1');

    // SPINNER DANDADAN
    modalTexto.innerHTML = `
        <div class="spinner-container">
            <div class="retro-spinner"></div>
            <div class="spinner-texto">Traduzindo Juridiquês...</div>
        </div>
    `;

    fetch(`/api/ler_materia/${id_noticia}`)
        .then(response => response.json())
        .then(dados => {
            let textoLimpo = dados.texto_materia;
            textoLimpo = textoLimpo.replace(/TÍTULO:\s*/gi, '');
            textoLimpo = textoLimpo.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            const textoFormatado = textoLimpo.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');

            modalTexto.innerHTML = `<p>${textoFormatado}</p>`;
        });

    carregarForumEChart(id_noticia);
}

function renderizarBarrasGoogle(comentarios) {
    const container = document.getElementById('ranking-barras-google');
    let contagem = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0};
    let total = comentarios.length;

    comentarios.forEach(c => {
        let n = Math.floor(c.nota);
        if (n < 1) n = 1;
        if (n > 5) n = 5;
        contagem[n]++;
    });

    container.innerHTML = "";

    for (let i = 5; i >= 1; i--) {
        let porc = total > 0 ? (contagem[i] / total) * 100 : 0;
        container.innerHTML += `
            <div class="nota-linha">
                <span class="nota-numero">${i}</span>
                <div class="nota-barra-fundo">
                    <div class="nota-barra-fill" style="width: ${porc}%"></div>
                </div>
            </div>
        `;
    }
}

function carregarForumEChart(id_noticia) {
    const chartImg = document.getElementById('dashboard-chart');
    const forumContainer = document.getElementById('container-comentarios-forum');

    chartImg.src = "";
    chartImg.src = `/api/dashboard/${id_noticia}.png?t=${new Date().getTime()}`;

    forumContainer.innerHTML = '<div class="loading">Carregando debates...</div>';
    fetch(`/api/forum/${id_noticia}`)
        .then(response => response.json())
        .then(comentarios => {
            forumContainer.innerHTML = '';
            renderizarBarrasGoogle(comentarios);

            if (comentarios.length === 0) {
                forumContainer.innerHTML = '<p style="text-align:center; color:#718096; font-size: 0.9em;">Seja o primeiro a comentar!</p>';
                return;
            }

            comentarios.forEach(c => {
                const card = document.createElement('div');
                card.className = 'comentario-card';

                if(c.nome_usuario === 'Você (Usuário)') {
                    card.style.backgroundColor = "#ebf8ff";
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