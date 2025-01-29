class Players {
    static async loadPlayerRank(name, tag) {
        try {
            const player = await Api.getPlayerRank(name, tag, Auth.token);
            UI.addPlayerCard(player);
        } catch (error) {
            if (error.message === 'Unauthorized') {
                return; // Não adiciona card de erro quando for unauthorized
            }
            UI.addPlayerCard({name, tag}, error.message);
        }
    }

    static async loadAllPlayers() {
        UI.clearPlayersList();
        UI.showLoadingMessage();

        try {
            const players = await Api.getAllPlayers();
            
            if (!players || players.length === 0) {
                UI.hideLoadingMessage();
                return;
            }

            const BATCH_SIZE = 2;
            const playerBatches = [];
            
            for (let i = 0; i < players.length; i += BATCH_SIZE) {
                playerBatches.push(players.slice(i, i + BATCH_SIZE));
            }

            for (const batch of playerBatches) {
                const promises = batch.map(player => 
                    this.loadPlayerRank(player.name, player.tag)
                );

                await Promise.all(promises);
                // Pequena pausa entre os lotes para não sobrecarregar
                await new Promise(resolve => setTimeout(resolve, 200));
            }
            
            UI.adjustCardWidths();
        } catch (error) {
            console.error('Erro ao carregar jogadores:', error);
            UI.hideLoadingMessage();
            if (error.message.includes('Unauthorized')) {
                Auth.silentLogout();
            }
        } finally {
            UI.hideLoadingMessage();
        }
    }

    static async deletePlayer(id) {
        try {
            await Api.deletePlayer(id);
            UI.removePlayerCard(id);
            UI.showFeedback('Jogador removido com sucesso!');
        } catch (error) {
            UI.showFeedback(`Erro ao deletar jogador: ${error.message}`);
        }
    }

    static async checkPlayerExists(field, value) {
        console.log(`Iniciando verificação de ${field} com valor: ${value}`);

        if (!value) {
            console.log(`${field} vazio, limpando feedback`);
            UI.updateFieldFeedback(field, '', false);
            return false;
        }

        try {
            const result = await Api.checkPlayerExists({ [field]: value });
            const exists = result[`${field}_exists`];
            
            console.log(`Resultado para ${field}: ${exists ? 'Já existe' : 'Disponível'}`);
            
            if (exists) {
                console.log(`${field} já cadastrado no sistema`);
                UI.updateFieldFeedback(field, `Este ${field} já está cadastrado`, true);
                return true;
            } else {
                console.log(`${field} disponível para uso`);
                UI.updateFieldFeedback(field, 'Disponível', false);
                return false;
            }
        } catch (error) {
            console.error(`Erro ao verificar ${field}:`, error);
            UI.showFeedback(`Erro ao verificar ${field}: ${error.message}`);
            UI.updateFieldFeedback(field, 'Erro ao verificar', true);
            return true;
        }
    }

    static async loadSinglePlayer(player) {
        try {
            // Garantindo que temos os campos necessários
            if (!player.name || !player.tag) {
                console.error('Dados do jogador incompletos:', player);
                return;
            }

            const playerData = await Api.getPlayerRank(player.name, player.tag, Auth.token);
            UI.addPlayerCard({ ...player, ...playerData });
        } catch (error) {
            if (error.message === 'Unauthorized') {
                return;
            }
            UI.addPlayerCard(player, error.message);
        }
    }

    static async confirmAndDeletePlayer(id) {
        if (confirm('Tem certeza que deseja deletar este jogador?')) {
            try {
                await Api.deletePlayer(id);
                UI.removePlayerCard(id);
                UI.showFeedback('Jogador removido com sucesso!');
            } catch (error) {
                UI.showFeedback(`Erro ao deletar jogador: ${error.message}`);
            }
        }
    }
}
