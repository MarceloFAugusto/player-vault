from fastapi import APIRouter, HTTPException, Depends, Header, Request
from models.auth import AdminLogin, Setup2FARequest, Verify2FACode, Reset2FARequest
from services.auth_service import auth_service
from services.google_auth_service import GoogleAuthService
from services.admin_service import AdminService
import logging
import qrcode
import base64
from io import BytesIO
from slowapi import Limiter
from slowapi.util import get_remote_address
from models.responses import (
    TokenResponse,
    Setup2FAResponse,
    Verify2FAResponse,
    ErrorResponse,
)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()
google_auth = GoogleAuthService()

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def verify_token(authorization: str = Header(None)):
    if not authorization:
        logger.warning("Tentativa de acesso sem token")
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization.split(" ")[1] if "Bearer" in authorization else authorization
    if not auth_service.verify_token(token):
        logger.warning(f"Tentativa de acesso com token inválido: {token}")
        raise HTTPException(status_code=401, detail="Token inválido")
    logger.info("Token verificado com sucesso")
    return token


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
@limiter.limit("5/minute")
async def login(request: Request, credentials: AdminLogin):
    try:
        logger.info(f"Tentativa de login para usuário: {credentials.username}")
        admin_service = AdminService()
        if admin_service.verify_admin(credentials.username, credentials.password):
            # Verificar 2FA se configurado
            user_secret = google_auth.get_user_secret(
                1
            )  # Assumindo user_id = 1 para admin
            if user_secret:
                if not credentials.code:
                    logger.warning(
                        f"Tentativa de login sem código 2FA: {credentials.username}"
                    )
                    raise HTTPException(status_code=403, detail="Código 2FA necessário")
                if not google_auth.verify_code(user_secret, credentials.code):
                    logger.warning(
                        f"Código 2FA inválido para usuário: {credentials.username}"
                    )
                    raise HTTPException(status_code=401, detail="Código 2FA inválido")

            token = auth_service.generate_token()
            expiry_time = auth_service.get_expiry_time()
            logger.info(f"Login bem-sucedido para usuário: {credentials.username}")
            return {"token": token, "expiry_time": expiry_time}
        logger.warning(
            f"Tentativa de login com credenciais inválidas: {credentials.username}"
        )
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/setup-2fa",
    response_model=Setup2FAResponse,
    responses={400: {"model": ErrorResponse}},
)
@limiter.limit("5/minute")
async def setup_2fa(request: Request, setup_request: Setup2FARequest):
    try:
        logger.info(f"Configurando 2FA para usuário ID: {setup_request.user_id}")
        result = google_auth.check_2fa_status(setup_request.user_id)

        if "secret" in result:
            qr_url = google_auth.get_qr_url("admin", result["secret"])

            # Gerar QR code como imagem base64
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Converter para base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()

            result["qr_code_url"] = f"data:image/png;base64,{qr_base64}"

        return result

    except Exception as e:
        logger.error(f"Erro na configuração do 2FA: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/verify-2fa-setup",
    response_model=Verify2FAResponse,
    responses={400: {"model": ErrorResponse}},
)
@limiter.limit("5/minute")
async def verify_2fa_setup(request: Request, verify_request: Verify2FACode):
    try:
        logger.info("Verificando código 2FA durante setup")
        if google_auth.verify_code(verify_request.secret, verify_request.code):
            google_auth.activate_2fa(1, verify_request.secret)
            logger.info("2FA ativado com sucesso")
            return {"success": True}
        logger.warning("Código 2FA inválido durante setup")
        raise HTTPException(status_code=400, detail="Código inválido")
    except Exception as e:
        logger.error(f"Erro na verificação do código 2FA: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-2fa", dependencies=[Depends(verify_token)])
@limiter.limit("5/minute")
async def reset_2fa(request: Request, reset_request: Reset2FARequest):
    try:
        logger.info(f"Resetando 2FA para usuário ID: {reset_request.user_id}")
        result = google_auth.reset_2fa(reset_request.user_id)
        return {"success": result}
    except Exception as e:
        logger.error(f"Erro ao resetar 2FA: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
