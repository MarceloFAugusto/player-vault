from dotenv import load_dotenv
from unidecode import unidecode

load_dotenv('.env.test', override=True)

from config.settings import get_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import unittest
import time
import pyotp
import os
import subprocess
import socket
import sys
from database.admin_repository import AdminRepository
from selenium.webdriver.remote.webdriver import WebDriver

def check_server_running(host="localhost", port=8000, timeout=1):
    """Verifica se o servidor está rodando na porta especificada"""
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

class SeleniumTestCase(unittest.TestCase):
    def get_browser_logs(self) -> str:
        """Obtém os logs do navegador"""
        if hasattr(self, 'driver') and isinstance(self.driver, WebDriver):
            try:
                logs = []
                for entry in self.driver.get_log('browser'):
                    logs.append(f"{entry['level']}: {entry['message']}")
                return "\n".join(logs)
            except Exception as e:
                return f"Erro ao obter logs do navegador: {str(e)}"
        return "Driver do navegador não disponível"

    def run(self, result=None):
        """Sobrescreve o método run para capturar falhas e incluir logs"""
        if result is None:
            result = self.defaultTestResult()
        result.startTest(self)
        testMethod = getattr(self, self._testMethodName)
        try:
            self.setUp()
            try:
                testMethod()
            except Exception as e:
                # Captura logs do navegador antes de registrar a falha
                browser_logs = self.get_browser_logs()
                # Adiciona os logs à mensagem de erro
                if hasattr(e, 'args') and len(e.args) > 0:
                    e.args = (f"{e.args[0]}\n\nBrowser Logs:\n{browser_logs}",) + e.args[1:]
                else:
                    e.args = (f"Browser Logs:\n{browser_logs}",)
                raise
            finally:
                self.tearDown()
        finally:
            result.stopTest(self)

class TestUserJourney(SeleniumTestCase):
    @staticmethod
    def get_test_player_data(name="TestPlayer", tag="TEST"):
        """Fixture para dados do jogador de teste"""
        # Remove acentos, caracteres especiais e substitui espaços por underscore no email
        email_name = unidecode(name.lower())
        email_name = ''.join(c for c in email_name if c.isalnum() or c.isspace())
        email_name = email_name.replace(' ', '_')
        
        return {
            "name": name,
            "tag": tag,
            "email": f"{email_name}@example.com",
            "login": f"{name.lower()}login",
            "password": f"{name.lower()}pass123"
        }

    def add_player(self, player_data):
        """Método auxiliar para adicionar um jogador"""
        # Abrir modal de adicionar jogador
        add_button = self.wait_for_element(By.CLASS_NAME, "add-player-button")
        add_button.click()
        
        # Preencher formulário
        form = self.wait_for_element(By.ID, "add-player-form")
        form.find_element(By.NAME, "name").send_keys(player_data["name"])
        form.find_element(By.NAME, "tag").send_keys(player_data["tag"])
        form.find_element(By.NAME, "email").send_keys(player_data["email"])
        form.find_element(By.NAME, "login").send_keys(player_data["login"])
        
        password_field = self.wait_for_element(
            By.XPATH,
            "//form[@id='add-player-form']//input[@name='password']"
        )
        password_field.send_keys(player_data["password"])
        
        # Submeter formulário
        submit_button = self.wait_for_element(
            By.XPATH, 
            "//form[@id='add-player-form']//button[contains(text(), 'Adicionar')]"
        )
        submit_button.click()
        
        # Verificar se jogador foi adicionado
        players_list = self.wait_for_element(By.ID, "players-list")
        time.sleep(2)  # Aguardar atualização
        player_identifier = f"{player_data['name']}#{player_data['tag']}"
        self.assertIn(player_identifier, players_list.text)
        return player_identifier

    @classmethod
    def create_test_admin(cls):
        """Cria um usuário admin para testes"""
        print("\n=== Iniciando criação/verificação do admin de teste ===")
        admin_repo = AdminRepository()
        settings = get_settings()
        admin_user = settings.ADMIN_USER
        admin_pass = settings.ADMIN_PASS
        
        print(f"Verificando se admin '{admin_user}' já existe...")
        # Verificar se admin já existe
        if not admin_repo.verify_admin(admin_user, admin_pass):
            print("Admin não encontrado. Criando novo admin...")
            # Inserir admin
            query = "INSERT INTO admin_users (username, password) VALUES (?, ?)"
            admin_repo.execute_query(query, (admin_user, admin_pass))
            print("Admin criado com sucesso!")
            
            # Se tiver 2FA, configurar
            if settings.TEST_2FA_SECRET:
                print("Configurando 2FA para o admin...")
                query = """
                    INSERT INTO google_auth (user_id, secret_key, is_active)
                    VALUES ((SELECT id FROM admin_users WHERE username = ?), ?, 1)
                """
                admin_repo.execute_query(query, (admin_user, settings.TEST_2FA_SECRET))
                print("2FA configurado com sucesso!")
        else:
            print("Admin já existe no banco de dados!")
        
        print("=== Finalização da verificação do admin ===\n")

    @classmethod
    def setUpClass(cls):
        """Inicializa o servidor e limpa o banco de teste antes dos testes"""
        if not check_server_running():
            print("Iniciando servidor...")
            # Ajuste o caminho para o app.py baseado na estrutura do projeto
            app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "app.py")
            
            # Inicia o servidor em um processo separado
            cls.server_process = subprocess.Popen(
                [sys.executable, app_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Aguarda o servidor iniciar (máximo 10 segundos)
            for _ in range(10):
                if check_server_running():
                    print("Servidor iniciado com sucesso!")
                    break
                time.sleep(1)
            else:
                cls.server_process.terminate()
                raise Exception("Servidor não iniciou dentro do tempo esperado")
        
        cls.create_test_admin()

    @classmethod
    def tearDownClass(cls):
        """Encerra o servidor após todos os testes"""
        if hasattr(cls, 'server_process'):
            cls.server_process.terminate()
            cls.server_process.wait()
            print("Servidor encerrado")

    def setUp(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        # Adicionar estas novas opções para suprimir os logs
        chrome_options.add_argument('--log-level=3')  # Apenas logs fatais
        chrome_options.add_argument('--silent')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        # Habilitar captura de logs do navegador
        self.driver.get("about:blank")
        self.driver.execute_cdp_cmd('Network.enable', {})
        self.driver.execute_cdp_cmd('Console.enable', {})
        
        self.driver.implicitly_wait(10)
        self.base_url = "http://localhost:8000"
        self.wait = WebDriverWait(self.driver, 10)
        # Carregar credenciais do ambiente
        settings = get_settings()
        self.admin_user = settings.ADMIN_USER
        self.admin_pass = settings.ADMIN_PASS
        self.test_2fa_secret = settings.TEST_2FA_SECRET

    def tearDown(self):
        if self.driver:
            self.driver.quit()

    def wait_for_element(self, by, value, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.fail(f"Elemento não encontrado: {value}")

    def test_01_login_flow(self):
        """Teste do fluxo de login completo"""
        self.driver.get(self.base_url)
        
        # Verificar título da página
        self.assertIn("Valorant Ranks", self.driver.title)
        
        # Realizar login
        username = self.wait_for_element(By.ID, "username")
        password = self.wait_for_element(By.ID, "password")
        
        username.send_keys(self.admin_user)
        password.send_keys(self.admin_pass)
        
        # Se 2FA estiver configurado
        if self.test_2fa_secret:
            # Gerar código 2FA
            totp = pyotp.TOTP(self.test_2fa_secret)
            code = totp.now()

        login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
        login_button.click()

        # Se 2FA estiver configurado
        if self.test_2fa_secret:
            tfa_input = self.wait_for_element(By.ID, "2fa-code")
            tfa_input.send_keys(code)

            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Entrar')]")
            login_button.click()

        # Verificar se login foi bem sucedido
        content = self.wait_for_element(By.ID, "content", timeout=20)
        time.sleep(2)  # Aguardar carregamento
        self.assertTrue(content.is_displayed())

    def test_02_add_player(self):
        """Teste de adição de novo jogador"""
        self.test_01_login_flow()
        player_data = self.get_test_player_data()
        self.add_player(player_data)

    def test_03_delete_player(self):
        """Teste de remoção de jogador"""
        self.test_01_login_flow()
        
        # Adicionar jogador com dados diferentes
        player_data = self.get_test_player_data("DeleteTest", "DEL")
        player_identifier = self.add_player(player_data)
        
        # Encontrar botão de deletar do jogador específico
        delete_button = self.wait_for_element(
            By.XPATH,
            f"//div[contains(@class, 'player-card') and contains(., '{player_identifier}')]//button[contains(@class, 'delete-btn')]"
        )
        
        # Simular confirmação do alert
        self.driver.execute_script(
            "window.confirm = function(){return true;}"
        )
        
        delete_button.click()
        time.sleep(2)  # Aguardar atualização
        
        # Verificar se jogador foi removido
        players_list = self.driver.find_element(By.ID, "players-list")
        self.assertNotIn(player_identifier, players_list.text)

    def test_04_security_features(self):
        """Teste de funcionalidades de segurança"""
        self.test_01_login_flow()
        
        # Adicionar jogador com dados diferentes
        player_data = self.get_test_player_data("Regina Gashélio", "000")
        self.add_player(player_data)
        
        # Testar botão de copiar informações sensíveis
        copy_buttons = self.driver.find_elements(
            By.CLASS_NAME, "action-icon"
        )
        if copy_buttons:
            copy_buttons[0].click()
            feedback = self.wait_for_element(By.ID, "copy-feedback")
            self.assertTrue(feedback.is_displayed())
        
        # Testar visualização de senha usando o novo ID
        eye_button = self.wait_for_element(
            By.CLASS_NAME, "toggle-password"
        )
        if eye_button:
            eye_button.click()
            password_value = self.wait_for_element(By.CLASS_NAME, "password-value")
            time.sleep(1)  # Pequena pausa para garantir que a animação terminou
            self.assertTrue(password_value.is_displayed())

    def test_05_refresh_functionality(self):
        """Teste da funcionalidade de atualização"""
        self.test_01_login_flow()
        
        refresh_button = self.wait_for_element(
            By.CLASS_NAME, "refresh-button"
        )
        refresh_button.click()
        
        # Verificar se mensagem de carregamento aparece
        loading = self.wait_for_element(By.ID, "loading-message")
        self.assertTrue(loading.is_displayed())
        
        # Aguardar conclusão da atualização
        self.wait.until(
            EC.invisibility_of_element_located((By.ID, "loading-message"))
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)