# Player Vault

Sistema de gerenciamento de contas e consulta de ranks de jogadores (Inicialmente, somente de Valorant), com interface web e recursos de segurança.

## 🚀 Funcionalidades

### Autenticação e Segurança
- Sistema de login com autenticação em duas etapas (2FA)
- Tokens JWT para gerenciamento de sessão
- Criptografia de dados sensíveis (client-side e server-side)
- Proteção contra ataques comuns (XSS, CSRF)

### Gerenciamento de Jogadores
- CRUD completo de jogadores
- Consulta automática de ranks via web scraping
- Suporte para adição em lote via JSON
- Sistema de verificação de duplicidade

### Interface Web
- Dashboard responsivo
- Feedback visual em tempo real
- Proteção visual de dados sensíveis
- Sistema de cópia segura de credenciais
- Gerenciamento de 2FA com QR Code

## 🛠️ Tecnologias Utilizadas

### Backend
- FastAPI para API REST
- SQLite para persistência de dados
- PyOTP para autenticação 2FA
- Cryptography para criptografia
- Beautiful Soup para web scraping

### Frontend
- HTML5 + CSS3 moderno
- JavaScript puro (Vanilla JS)
- Web Crypto API para criptografia
- Sistema modular de componentes

### DevOps
- PyInstaller para geração de executável
- Scripts de build automatizados
- Minificação de assets
- Gerenciamento de dependências com pip

## 📦 Instalação

### Desenvolvimento
1. Clone o repositório
```bash
git clone <repository-url>
cd valorant-ranks
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

### Produção
1. Execute o script de build:
```bash
./build.ps1  # Windows PowerShell
```

2. O executável será gerado em dist/valorant-ranks.exe

## 🚀 Uso

### Desenvolvimento

1. Inicie o servidor:
```bash
python run.py
```
2. Acesse http://localhost:8000

### Produção
1. Execute o arquivo valorant-ranks.exe
2. O sistema abrirá automaticamente no navegador padrão

### Testes

Para testar rapidamente o sistema:

1. Inicie no modo teste:
```bash
python app.py -test
```

2. Testes Automatizados

Execute os testes usando:
```bash
pytest                    # Todos os testes
pytest tests/unit/        # Apenas testes unitários
pytest tests/integration/ # Apenas testes de integração
pytest tests/e2e/         # Apenas testes end-to-end
```

## 🔒 Segurança
- Todas as senhas são criptografadas
- 2FA via Google Authenticator
- Proteção contra força bruta
- Tokens com expiração automática
- Validação de dados em tempo real

## 📝 API Documentation

### Autenticação

```text
POST /login
POST /setup-2fa
POST /verify-2fa-setup
```

### Jogadores

```text
GET /players
POST /players
POST /players/batch
DELETE /players/{id}
GET /players/{name}/{tag}
```

## 🤝 Contribuição
1. Faça um fork do projeto
2. Crie sua feature branch (git checkout -b feature/AmazingFeature)
3. Commit suas mudanças (git commit -m 'Add some AmazingFeature')
4. Push para a branch (git push origin feature/AmazingFeature)
5. Abra um Pull Request

## 📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## ✨ Próximos Passos
Confira nosso TODO.md para ver os próximos desenvolvimentos planejados.