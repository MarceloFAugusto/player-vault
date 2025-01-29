class Api {
    static async login(username, password, code = null) {
        const response = await fetch('http://localhost:8000/login', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ username, password, code })
        });

        if (!response.ok) {
            const error = await response.json();
            throw {
                status: response.status,
                message: error.detail
            };
        }
        return response.json(); // Agora retornará { token: string, expiry_time: number }
    }

    static async setup2FA(token) {
        const response = await fetch('http://localhost:8000/setup-2fa', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: 1 }) // Assumindo que o admin tem user_id = 1
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        return response.json();
    }

    static async verify2FASetup(secret, code) {
        console.log('Enviando:', { secret, code });

        const response = await fetch('http://localhost:8000/verify-2fa-setup', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Auth.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                secret: secret,  // Mudando de secret_key para secret
                code: code
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Erro detalhado:', errorData);
            
            // Tratamento específico para erros de validação
            if (response.status === 422) {
                const errorDetail = errorData.detail?.[0];
                const errorMessage = errorDetail?.msg || 'Erro de validação';
                throw new Error(errorMessage);
            }

            throw new Error(errorData.detail || 'Erro na verificação do 2FA');
        }

        return response.json();
    }

    static async getPlayerRank(name, tag, token) {
        const response = await fetch(`http://localhost:8000/players/${name}/${tag}`, {
            headers: { 
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json'
            }
        });
        
        if (response.status === 401) {
            Auth.silentLogout();
            throw new Error('Unauthorized');
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Servidor retornou erro ' + response.status);
        }
        return await response.json();
    }

    static async verifyCredentials(login, email, token) {
        console.log('Verificando credenciais:', { login, email });
        
        try {
            const response = await fetch('http://localhost:8000/players/verify-credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    login: login,
                    email: email
                })
            });

            if (response.status === 401) {
                Auth.silentLogout();
                throw new Error('Unauthorized');
            }

            if (!response.ok) {
                const error = await response.json();
                console.error('Erro na verificação de credenciais:', error);
                throw new Error(error.detail || 'Credenciais inválidas');
            }

            const result = await response.json();
            console.log('Credenciais verificadas com sucesso');
            return result;
        } catch (error) {
            console.error('Erro ao verificar credenciais:', error);
            throw error;
        }
    }

    static async reset2FA(token) {
        console.log('Solicitando reset do 2FA...');
        const response = await fetch('http://localhost:8000/reset-2fa', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: 1 })  // Admin user_id
        });

        if (!response.ok) {
            const error = await response.json();
            console.error('Erro no reset 2FA:', error);
            throw new Error(error.detail || 'Erro ao resetar 2FA');
        }

        return response.json();
    }

    static async addPlayer(playerData) {
        const response = await fetch('http://localhost:8000/players/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${Auth.token}`
            },
            body: JSON.stringify(playerData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        return response.json();
    }

    static async addPlayersBatch(playersData) {
        const response = await fetch('http://localhost:8000/players/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${Auth.token}`
            },
            body: JSON.stringify(playersData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        return response.json();
    }

    static async getAllPlayers() {
        try {
            const response = await fetch('http://localhost:8000/players/', {
                headers: {
                    'Authorization': `Bearer ${Auth.token}`,
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erro ao buscar jogadores');
            }

            const data = await response.json();
            return Array.isArray(data) ? data : [];
        } catch (error) {
            console.error('Erro na requisição:', error);
            throw new Error(error.message || 'Erro ao buscar jogadores');
        }
    }

    static async deletePlayer(id) {
        const response = await fetch(`http://localhost:8000/players/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${Auth.token}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }
        return response.json();
    }

    static async checkPlayerExists(data) {
        const fieldType = Object.keys(data)[0]; // email ou login
        const value = data[fieldType];
        
        console.log(`Verificando existência de ${fieldType}: ${value}`);
        
        try {
            const response = await fetch('http://localhost:8000/players/check-exists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                console.error(`Erro ao verificar ${fieldType}:`, error);
                throw new Error(error.detail);
            }

            const result = await response.json();
            console.log(`Resultado da verificação para ${fieldType}:`, result);
            return result;
        } catch (error) {
            console.error(`Erro ao verificar ${fieldType} '${value}':`, error);
            throw error;
        }
    }
}