class UI {
    static async init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeForm());
        } else {
            this.initializeForm();
        }
    }

    static initializeForm() {
        const loginForm = document.getElementById('login-form');
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        const tfaCodeInput = document.getElementById('2fa-code');

        // Verifica se todos os elementos necessários existem
        if (!loginForm || !usernameInput || !passwordInput || !tfaCodeInput) {
            console.error('Elementos do formulário não encontrados:', {
                form: !!loginForm,
                username: !!usernameInput,
                password: !!passwordInput,
                tfaCode: !!tfaCodeInput
            });
            return;
        }

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            UI.handleLogin();
        });
    }

    static async handleLogin() {
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        const tfaCodeInput = document.getElementById('2fa-code');
        
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        const tfaCode = tfaCodeInput.value.trim();
        
        if (!username || !password) {
            UI.showFeedback('Por favor, preencha usuário e senha');
            return;
        }

        try {
            const result = await Auth.login(username, password, tfaCode);
            if (result.needsTwoFactor) {
                UI.show2FAInput();
            } else if (result.success) {
                UI.showMainContent();
                await Players.loadAllPlayers();
            }
        } catch (error) {
            console.error('Erro no login:', error);
            UI.showFeedback(error.message || 'Erro no login');
        }
    }

    static show2FAInput() {
        const tfaInput = document.getElementById('2fa-code');
        tfaInput.style.display = 'block';
        tfaInput.focus();
    }

    static async show2FASetup() {
        try {
            const modal = document.getElementById('setup-2fa-modal');
            const setupSection = document.getElementById('setup-2fa-section');
            const resetSection = document.getElementById('reset-2fa-section');
            const verifySection = document.getElementById('verify-2fa-section');
            
            const setupData = await Api.setup2FA(Auth.token);
            
            if (setupData.is_configured) {
                setupSection.style.display = 'none';
                resetSection.style.display = 'block';
                verifySection.style.display = 'none';
            } else if (setupData.secret) {  // Verificar se secret existe
                setupSection.style.display = 'block';
                resetSection.style.display = 'none';
                verifySection.style.display = 'block';
                
                const qrCode = document.getElementById('qr-code');
                const secretKey = document.getElementById('secret-key');
                
                if (setupData.qr_code_url) {
                    qrCode.src = setupData.qr_code_url;
                }
                if (setupData.secret) {
                    secretKey.textContent = setupData.secret;
                }
            } else {
                throw new Error('Dados de configuração 2FA inválidos');
            }
            
            modal.style.display = 'block';
        } catch (error) {
            console.error('Erro completo:', error);
            UI.showFeedback('Erro ao configurar 2FA: ' + error.message);
            this.closeModal('setup-2fa-modal');
        }
    }

    static async verify2FASetup(event) {
        event.preventDefault();
        const form = event.target;
        const code = form.querySelector('input[name="verification_code"]').value.trim();
        const secretKey = document.getElementById('secret-key').textContent.trim();
        
        console.log('Tentando verificar com:', { secretKey, code });
        
        if (!code || !secretKey) {
            this.showFeedback('Código e chave secreta são obrigatórios');
            return;
        }

        try {
            await Api.verify2FASetup(secretKey, code);
            this.showFeedback('2FA configurado com sucesso!');
            this.closeModal('setup-2fa-modal');
        } catch (error) {
            this.showFeedback(`Erro na verificação: ${error.message}`);
        }
    }

    static closeModal(modalName) {
        const modal = document.getElementById(modalName);
        modal.style.display = 'none';
    }

    static showLoginPage() {
        document.getElementById('login-container').style.display = 'block';
        document.getElementById('content').style.display = 'none';
        this.clearPlayersList();
    }

    static showMainContent() {
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('content').style.display = 'block';
    }

    static clearPlayersList() {
        document.getElementById('players-list').innerHTML = '';
    }

    static showLoadingMessage() {
        const loadingMessage = document.getElementById('loading-message');
        loadingMessage.textContent = 'Carregando ranks...';
        loadingMessage.style.display = 'inline-block';
    }

    static updateLoadingMessage(message) {
        const loadingMessage = document.getElementById('loading-message');
        loadingMessage.textContent = message;
    }

    static hideLoadingMessage() {
        const loadingMessage = document.getElementById('loading-message');
        loadingMessage.style.display = 'none';
        loadingMessage.textContent = '';
    }

    static removePlayerCard(id) {
        const playersList = document.getElementById('players-list');
        const card = playersList.querySelector(`.player-card[data-player-id="${id}"]`);
        if (card) {
            playersList.removeChild(card);
        } else {
            console.warn(`Card do jogador com ID ${id} não encontrado`);
        }
    }

    static addPlayerCard(player, error = null) {
        const playersList = document.getElementById('players-list');
        if (!playersList) {
            console.error('Elemento players-list não encontrado');
            return;
        }

        if (!player || (!player.name && !player.name)) {
            console.error('Dados do jogador inválidos:', player);
            return;
        }

        try {
            const playerCard = document.createElement('div');
            playerCard.className = error ? 'player-card error' : 'player-card';
            playerCard.setAttribute('data-player-id', player.id);
            
            playerCard.innerHTML = error ? 
                this.getErrorCardHTML(player, error) : 
                this.getPlayerCardHTML(player);
            
            playersList.appendChild(playerCard);
            this.adjustCardWidths();
        } catch (e) {
            console.error('Erro ao criar card do jogador:', e);
        }
    }

    static getErrorCardHTML(player, error) {
        return `
            <h3>${player.name}#${player.tag}</h3>
            <p class="error-message">${error}</p>
        `;
    }

    static getPlayerCardHTML(player) {
        console.log('Dados do player para card:', player);
        
        // Prepara o texto do rank baseado no tipo de dados
        let rankDisplay = 'N/A';
        if (player.rank) {
            if (typeof player.rank === 'object' && player.rank.message && player.rank.url) {
                rankDisplay = `<a href="#" onclick="UI.showRankMessage('${player.rank.message}', '${player.rank.url}')">Consultar</a>`;
            } else {
                rankDisplay = player.rank;
            }
        }

        return `
            <h3>${player.name || player.name}#${player.tag || player.tag}</h3>
            <p>Rank: <span class="rank">${rankDisplay}</span></p>
            <div class="sensitive-info">
                ${player.email ? `
                <div class="info-row">
                    <span class="info-label">Email:</span>
                    <span class="info-value hidden-text">${player.email}</span>
                    <div class="info-actions">
                        <span class="action-icon" onclick="UI.copyText('${player.email}', this)">📋</span>
                    </div>
                </div>
                ` : ''}
                ${player.login ? `
                <div class="info-row">
                    <span class="info-label">Login:</span>
                    <span class="info-value hidden-text">${player.login}</span>
                    <div class="info-actions">
                        <span class="action-icon" onclick="UI.copyText('${player.login}', this)">📋</span>
                    </div>
                </div>
                ` : ''}
                ${player.login && player.email ? `
                <div class="info-row" data-login="${player.login}" data-email="${player.email}">
                    <span class="info-label">Senha:</span>
                    <span class="info-value password-value" style="display: none"></span>
                    <span class="info-value password-hidden">********</span>
                    <div class="info-actions">
                        <span class="action-icon" onclick="UI.copyText('', this, 'password')">📋</span>
                        <span class="action-icon toggle-password" id="toggle-password-${player.id}" onclick="UI.togglePassword(this)">👁️</span>
                    </div>
                </div>
                ` : ''}
            </div>
            ${player.id ? `<button onclick="Players.confirmAndDeletePlayer(${player.id})" class="delete-btn">Deletar</button>` : ''}
        `;
    }

    static showRankMessage(message, url) {
        const modal = document.getElementById('rank-message-modal');
        const messageElement = document.getElementById('rank-message-content');
        const linkElement = document.getElementById('rank-message-link');
        
        messageElement.textContent = message;
        linkElement.href = url;
        linkElement.textContent = url;
        
        modal.style.display = 'block';
    }

    static adjustCardWidths() {
        const cards = document.querySelectorAll('.player-card');
        let maxWidth = 250;
        cards.forEach(card => {
            maxWidth = Math.max(maxWidth, card.scrollWidth);
        });
        cards.forEach(card => {
            card.style.width = `${maxWidth}px`;
        });
    }

    static async copyText(text, element, type = 'text') {
        try {
            let contentToCopy = text;

            if (type === 'password') {
                const row = element.closest('.info-row');
                const login = row.getAttribute('data-login');
                const email = row.getAttribute('data-email');
                
                console.log('Buscando senha para:', { login, email });
                
                try {
                    const response = await Api.verifyCredentials(login, email, Auth.token);
                    if (response?.password) {
                        contentToCopy = response.password;
                    } else {
                        throw new Error('Senha não encontrada');
                    }
                } catch (error) {
                    console.error('Erro ao recuperar senha:', error);
                    this.showFeedback('Erro ao recuperar senha');
                    return;
                }
            }

            await navigator.clipboard.writeText(contentToCopy);
            this.showFeedback('Copiado!');
        } catch (err) {
            // Fallback usando elemento temporário
            const textarea = document.createElement('textarea');
            textarea.value = contentToCopy;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            
            try {
                document.execCommand('copy');
                this.showFeedback('Copiado!');
            } catch (e) {
                console.error('Falha ao copiar texto (fallback):', e);
                this.showFeedback('Erro ao copiar');
            } finally {
                document.body.removeChild(textarea);
            }
        }
    }

    static showFeedback(message, duration = 2000) {
        const feedback = document.getElementById('copy-feedback');
        feedback.textContent = message;
        feedback.style.display = 'block';
        setTimeout(() => {
            feedback.style.display = 'none';
        }, duration);
    }

    static async togglePassword(element) {
        const row = element.closest('.info-row');
        const passwordValue = row.querySelector('.password-value');
        const passwordHidden = row.querySelector('.password-hidden');
        const login = row.getAttribute('data-login');
        const email = row.getAttribute('data-email');
        
        if (passwordValue.style.display === 'none') {
            try {
                const data = await Api.verifyCredentials(login, email, Auth.token);
                passwordValue.textContent = data.password;
                passwordValue.style.display = 'inline';
                passwordHidden.style.display = 'none';
                element.innerHTML = '👁️‍🗨️';
            } catch (error) {
                console.error('Erro ao recuperar senha:', error);
            }
        } else {
            passwordValue.style.display = 'none';
            passwordHidden.style.display = 'inline';
            element.innerHTML = '👁️';
        }
    }

    static async reset2FA() {
        if (confirm('Tem certeza que deseja resetar sua configuração de 2FA? Você precisará configurá-lo novamente.')) {
            try {
                await Api.reset2FA(Auth.token);
                this.showFeedback('2FA resetado com sucesso! Configure-o novamente.');
                await this.show2FASetup();
            } catch (error) {
                this.showFeedback(`Erro ao resetar 2FA: ${error.message}`);
            }
        }
    }

    static showAddPlayerModal() {
        const modal = document.getElementById('add-player-modal');
        modal.style.display = 'block';
    }

    static closeAddPlayerModal() {
        const modal = document.getElementById('add-player-modal');
        modal.style.display = 'none';
        document.getElementById('add-player-form').reset();
    }

    static showAddBatchModal() {
        const modal = document.getElementById('add-batch-modal');
        modal.style.display = 'block';
    }

    static closeAddBatchModal() {
        const modal = document.getElementById('add-batch-modal');
        modal.style.display = 'none';
        document.getElementById('add-batch-form').reset();
    }

    static updateFieldFeedback(field, message, isError) {
        const feedback = document.getElementById(`${field}-feedback`);
        if (feedback) {
            feedback.textContent = message;
            feedback.className = `feedback-message ${isError ? 'error' : 'success'}`;
            
            // Atualizar estado do botão de submit
            const submitButton = document.querySelector('#add-player-form button[type="submit"]');
            const allFeedbacks = document.querySelectorAll('.feedback-message.error');
            
            if (submitButton) {
                submitButton.disabled = allFeedbacks.length > 0;
            }
        }
    }

    static async submitAddPlayer(event) {
        event.preventDefault();
        const form = event.target;

        const playerData = {
            name: form.name.value,
            tag: form.tag.value,
            email: form.email.value,
            login: form.login.value,
            password: form.password.value
        };

        try {
            await Api.addPlayer(playerData);
            this.showFeedback('Jogador adicionado com sucesso!');
            this.closeAddPlayerModal();
            
            await Players.loadSinglePlayer({
                name: playerData.name,
                tag: playerData.tag
            });
        } catch (error) {
            this.showFeedback(`Erro ao adicionar jogador: ${error.message}`);
        }
    }

    static async submitAddBatch(event) {
        event.preventDefault();
        const form = event.target;
        
        try {
            const playersData = JSON.parse(form['batch-data'].value);
            if (!Array.isArray(playersData)) {
                throw new Error('O JSON deve conter um array de jogadores');
            }

            await Api.addPlayersBatch(playersData);
            this.showFeedback('Jogadores adicionados com sucesso!');
            this.closeAddBatchModal();
            await Players.loadAllPlayers();
        } catch (error) {
            this.showFeedback(`Erro ao adicionar jogadores em lote: ${error.message}`);
        }
    }
}
