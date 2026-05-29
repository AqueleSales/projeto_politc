let paginaAtual = 1;
let leiAtualLida = null;
let notaSelecionada = 0;
let carregandoNews = false;
let temMaisNoticias = true;
let termoPesquisaAtual = "";
let filtrosAtivos = [];
let isUserLogged = false;

// ============================================================================
// FUNÇÃO SALVA-VIDAS (MEMÓRIA DO SISTEMA)
// ============================================================================
// Esta função garante que o site nunca esqueça de onde você veio e o que digitou.
window.salvarEstadoEIrPara = function(url, apenasSalvar = false) {
    // 1. Salva a Lei que está sendo lida (se houver)
    if (leiAtualLida) {
        sessionStorage.setItem('leiPendente', leiAtualLida);
    } else {
        sessionStorage.removeItem('leiPendente'); // Limpa se estiver no Feed
    }

    // 2. Salva o texto que foi digitado
    const inputTexto = document.getElementById('feedback-texto'); // Letra minúscula!
    if (inputTexto && inputTexto.value.trim() !== "") {
        sessionStorage.setItem('textoPendente', inputTexto.value.trim());
    }

    // 3. Salva a estrela que foi clicada
    if (notaSelecionada !== 0) {
        sessionStorage.setItem('notaPendente', notaSelecionada);
    }

    // 4. Decide se viaja de página ou se apenas abre o Modal de Convite
    if (!apenasSalvar && url) {
        window.location.href = url;
    } else if (apenasSalvar) {
        const modalConvite = document.getElementById('modal-convite');
        if (modalConvite) {
            modalConvite.style.display = 'flex';
            setTimeout(() => { modalConvite.classList.add('active'); }, 10);
        }
    }
};

document.addEventListener("DOMContentLoaded", () => {
    verificarStatusLogin(true);

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

    const btnVoltarFeed = document.getElementById('btn-voltar-feed');
    if (btnVoltarFeed) {
        btnVoltarFeed.addEventListener('click', () => fecharMateria(true));
    }

    // --- SCROLL INFINITO ---
    const sentinela = document.getElementById('scroll-sentinela');
    if (sentinela) {
        const observer = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && !carregandoNews && temMaisNoticias) {
                paginaAtual++;
                carregarNoticias(paginaAtual);
            }
        });
        observer.observe(sentinela);
    }

    // --- LÓGICA DE FEEDBACK (ESTRELAS) PERMISSIVA ---
    const starBtns = document.querySelectorAll('.star-btn');
    starBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            notaSelecionada = parseInt(btn.getAttribute('data-nota'));
            document.getElementById('nota-selecionada-display').innerText = `Nota: ${notaSelecionada}.0`;
            starBtns.forEach((s, index) => s.classList.toggle('active', index < notaSelecionada));
        });
    });

    // --- LÓGICA DE ENVIAR FEEDBACK (COM GATILHO DE CONVITE) ---
    const btnEnviarFeedback = document.querySelector('.btn-enviar-feedback');
    if (btnEnviarFeedback) {
        btnEnviarFeedback.addEventListener('click', () => {
            const inputTexto = document.getElementById('feedback-texto');
            const texto = inputTexto ? inputTexto.value.trim() : "";

            // REGRA 1: Valida se o usuário preencheu pelo menos UMA coisa
            if (texto === "" && notaSelecionada === 0) {
                // Em vez de alert(), mudamos o placeholder ou a cor para avisar suavemente
                inputTexto.style.borderColor = "red";
                inputTexto.placeholder = "Por favor, deixe um comentário ou selecione uma nota...";
                setTimeout(() => {
                    inputTexto.style.borderColor = "var(--text-main)";
                    inputTexto.placeholder = "O que você achou dessa lei?";
                }, 3000);
                return;
            }

            // REGRA 2: Se não estiver logado, SALVA tudo na memória e mostra o Convite
            if (!isUserLogged) {
                window.salvarEstadoEIrPara(null, true);
                return;
            }

            btnEnviarFeedback.innerText = "A enviar...";
            btnEnviarFeedback.disabled = true;

            // Se o usuário não selecionou nota, mandamos 3 (Neutra) por padrão para não quebrar a pizza
            const notaFinal = notaSelecionada !== 0 ? notaSelecionada : 3.0;
            // Se o usuário não escreveu nada, mandamos um texto padrão
            const textoFinal = texto !== "" ? texto : "Avaliação por estrelas.";

            fetch('/api/enviar_feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id_noticia: leiAtualLida, texto: textoFinal, nota: notaFinal })
            })
            .then(response => response.json())
            .then(data => {
                if (data.sucesso) {
                    inputTexto.value = "";
                    notaSelecionada = 0;
                    document.getElementById('nota-selecionada-display').innerText = "Selecione uma nota";
                    starBtns.forEach(s => s.classList.remove('active'));
                    carregarForumEChart(leiAtualLida);
                }
            })
            .finally(() => {
                btnEnviarFeedback.innerText = "Enviar Análise";
                btnEnviarFeedback.disabled = false;
            });
        });
    }

    // --- LÓGICA DOS FILTROS ---
    const tagsFiltro = document.querySelectorAll('.tag-filtro');
    tagsFiltro.forEach(tag => {
        tag.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    });

    const btnAplicarFiltros = document.querySelector('.btn-aplicar-filtros');
    if (btnAplicarFiltros) {
        btnAplicarFiltros.addEventListener('click', () => {
            const tagsAtivas = document.querySelectorAll('.tag-filtro.active');
            filtrosAtivos = Array.from(tagsAtivas).map(tag => tag.innerText);
            toggleModalFiltro();
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
        document.getElementById('feed-noticias').innerHTML = '';
        carregarNoticias(paginaAtual);
    }

    if (btnPesquisa && inputPesquisa) {
        btnPesquisa.addEventListener('click', executarPesquisa);
        inputPesquisa.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                executarPesquisa();
            }
        });
    }
});

// ============================================================================
// FUNÇÕES GLOBAIS DE CONTEÚDO E API
// ============================================================================

function toggleModalFiltro() {
    const modal = document.getElementById('modal-filtro');
    if (!modal) return;
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

    if (!feed) return; // Segurança para não rodar se estiver na tela de login

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

    let urlDaApi = `/api/noticias?pagina=${pagina}&busca=${encodeURIComponent(termoPesquisaAtual)}`;
    if (filtrosAtivos.length > 0) {
        urlDaApi += `&filtros=${encodeURIComponent(filtrosAtivos.join(','))}`;
    }

    fetch(urlDaApi)
        .then(response => response.json())
        .then(noticias => {
            if (noticias.length === 0) {
                temMaisNoticias = false;
                sentinela.innerHTML = pagina === 1 ? "<p style='grid-column: 1/-1; text-align: center; color: var(--muted-purple); font-weight: bold;'>Nenhum projeto encontrado com estes filtros.</p>" : "Chegou ao fim do feed.";
                if (pagina === 1) feed.innerHTML = '';
                return;
            }

            if (pagina === 1) feed.innerHTML = '';
            sentinela.innerHTML = '';

            // PAYWALL: Corta a lista para 4 se não estiver logado
            let noticiasParaExibir = noticias;
            if (!isUserLogged) {
                noticiasParaExibir = noticias.slice(0, 4);
                temMaisNoticias = false;
            }

            noticiasParaExibir.forEach(noti => {
                const card = document.createElement('div');
                card.className = 'card-noticia';
                const imageUrl = `https://picsum.photos/seed/lei${noti.id}/400/200`;

                card.innerHTML = `
                    <div style="width: 100%; height: 160px; overflow: hidden; border-radius: 8px 8px 0 0; margin-bottom: 12px;">
                        <img src="${imageUrl}" style="width: 100%; height: 100%; object-fit: cover;" alt="Capa da Lei">
                    </div>
                    <h3>${noti.titulo}</h3>
                    <p>Ler Análise Completa ➔</p>
                `;
                card.addEventListener('click', () => abrirMateria(noti.id, noti.titulo, true));
                feed.appendChild(card);
            });

            // Adiciona o banner do Paywall após os 4 cards com REDIRECIONAMENTO INTELIGENTE
            if (!isUserLogged) {
                const paywallBox = document.createElement('div');
                paywallBox.className = 'paywall-feed';
                paywallBox.innerHTML = `
                    <h3>🔒 +50.000 projetos de lei ocultos</h3>
                    <p>O acesso completo ao histórico legislativo e debates é exclusivo para membros.</p>
                    <button class="btn-brutal btn-destaque" style="font-size: 1.2rem; padding: 15px 30px;" onclick="window.salvarEstadoEIrPara('/cadastro')">Criar Conta Gratuita</button>
                    <p style="margin-top: 15px; font-size: 0.9rem;">Já tem conta? <a href="#" onclick="window.salvarEstadoEIrPara('/login')" style="color: var(--text-main);">Entrar</a></p>
                `;
                feed.appendChild(paywallBox);
            }

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

    modalTexto.innerHTML = `
        <div class="spinner-container">
            <div class="retro-spinner"></div>
            <div class="spinner-texto">A traduzir Juridiquês...</div>
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

            // MAGIA: RESTAURA TEXTO E NOTA SE O CARA ACABOU DE LOGAR!
            setTimeout(() => {
                const textoPendente = sessionStorage.getItem('textoPendente');
                const notaPendente = sessionStorage.getItem('notaPendente');

                if (textoPendente) {
                    const box = document.getElementById('feedback-texto');
                    if (box) box.value = textoPendente;
                    sessionStorage.removeItem('textoPendente'); // limpa a memória
                }
                if (notaPendente) {
                    // Clica na estrela automaticamente para o usuário
                    const btnEstrela = document.querySelector(`.star-btn[data-nota="${notaPendente}"]`);
                    if (btnEstrela) btnEstrela.click();
                    sessionStorage.removeItem('notaPendente');
                }

                sessionStorage.removeItem('leiPendente'); // Limpa a lei pendente para não grudar
            }, 500);
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

    chartImg.src = `/api/dashboard/${id_noticia}.png?t=${new Date().getTime()}`;

    forumContainer.innerHTML = '<div class="loading">A carregar debates...</div>';
    fetch(`/api/forum/${id_noticia}`)
        .then(response => response.json())
        .then(comentarios => {
            forumContainer.innerHTML = '';

            // PAYWALL DO FÓRUM: Filtra cidadãos reais se for anónimo
            const comentariosParaExibir = isUserLogged ? comentarios : comentarios.filter(c => c.categoria !== 'Cidadão');

            renderizarBarrasGoogle(comentariosParaExibir);

            if (comentariosParaExibir.length === 0) {
                forumContainer.innerHTML = '<p style="text-align:center; color:#718096; font-size: 0.9em;">Nenhum debate encontrado.</p>';
                return;
            }

            comentariosParaExibir.forEach(c => {
                const card = document.createElement('div');
                card.className = 'comentario-card';

                if(c.nome_usuario !== 'Usuário Real' && !c.nome_usuario.includes('(Usuário)')) {
                    // Mantém a cor padrão para IA
                } else {
                    card.style.backgroundColor = "#fffbcc";
                    card.style.border = "1px solid var(--yellow-hero)";
                }

                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <strong style="font-size: 0.9em;">👤 ${c.nome_usuario}</strong>
                        <span style="background: var(--gray-card); padding: 2px 6px; border-radius: 4px; font-size: 0.75em; color: var(--text-main);">${c.categoria}</span>
                    </div>
                    <p style="font-style: italic; color: #2d3748; font-size: 0.85em;">"${c.texto}"</p>
                    <div style="margin-top: 8px; font-size: 0.8em; color: var(--accent-light-orange);">
                        <span>⭐ ${c.nota}/5</span> | 
                        <strong>${c.classificacao}</strong>
                    </div>
                `;
                forumContainer.appendChild(card);
            });
        });
}

// ============================================================================
// FUNÇÃO DE AUTENTICAÇÃO E ROTEAMENTO
// ============================================================================

function verificarStatusLogin(isInitialLoad = false) {
    fetch('/api/status_login')
        .then(response => response.json())
        .then(data => {
            isUserLogged = data.logado; // Atualiza a variável mestra

            // Atualiza a sidebar se ela existir na tela atual
            const container = document.getElementById('auth-sidebar-container');
            if (container) {
                if (isUserLogged) {
                    container.innerHTML = `
                        <p style="font-family: 'Playfair Display', serif; font-size: 1.1rem; margin: 0 0 10px 0; color: var(--text-main);">Olá, <strong>${data.nome}</strong></p>
                        <button class="btn-brutal btn-sair" style="width: 100%; padding: 6px;" onclick="fazerLogout()">Sair</button>
                    `;
                } else {
                    container.innerHTML = `
                        <button class="btn-brutal" style="width: 100%; margin-bottom: 10px; padding: 8px;" onclick="window.salvarEstadoEIrPara('/login')">Entrar</button>
                        <button class="btn-brutal btn-roxo" style="width: 100%; padding: 8px;" onclick="window.salvarEstadoEIrPara('/cadastro')">Criar Conta</button>
                    `;
                }
            }

            // Se for o carregamento inicial da página principal
            if (isInitialLoad) {
                const urlParams = new URLSearchParams(window.location.search);
                const leiDaUrl = urlParams.get('lei');
                if (leiDaUrl) {
                    abrirMateria(leiDaUrl, "Projeto de Lei", false);
                } else {
                    // Verifica se o feed existe (pra não dar erro se estivermos na página de login)
                    if (document.getElementById('feed-noticias')) {
                        carregarNoticias(paginaAtual);
                    }
                }
            }
        });
}

function fazerLogout() {
    fetch('/api/logout', { method: 'POST' }).then(() => {
        isUserLogged = false;
        // Redireciona para o Início para limpar a visualização inteira
        window.location.href = '/';
    });
}