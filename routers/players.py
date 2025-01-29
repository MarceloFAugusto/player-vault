from fastapi import APIRouter, HTTPException, Depends, Header, Request, Response
from services.player_service import PlayerService
from services.auth_service import auth_service
from models.player import Player, CredentialRequest
from models.responses import (
    PlayerRankResponse,
    BasicPlayerResponse,
    DeletePlayerResponse,
    CredentialResponse,
    PlayerExistsResponse,
    ErrorResponse,
)
from typing import List
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/players", tags=["players"])


async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization.split(" ")[1] if "Bearer" in authorization else authorization
    if not auth_service.verify_token(token):
        raise HTTPException(status_code=401, detail="Token inválido")
    return token


@router.post(
    "/", response_model=BasicPlayerResponse, dependencies=[Depends(verify_token)]
)
@limiter.limit("10/minute")
async def add_player(request: Request, player: Player):
    try:
        logger.info(f"Tentando adicionar jogador: {player.name}#{player.tag}")
        player_service = PlayerService()
        result = player_service.add_player(player.model_dump())
        logger.info(f"Jogador adicionado com sucesso: {player.name}#{player.tag}")
        return result
    except Exception as e:
        logger.error(f"Erro ao adicionar jogador {player.name}#{player.tag}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/batch",
    response_model=List[BasicPlayerResponse],
    dependencies=[Depends(verify_token)],
)
@limiter.limit("5/minute")
async def add_players(request: Request, players: List[Player]):
    try:
        logger.info(f"Tentando adicionar {len(players)} jogadores em lote")
        player_service = PlayerService()
        result = player_service.add_players([p.model_dump() for p in players])
        logger.info("Jogadores adicionados com sucesso em lote")
        return result
    except Exception as e:
        logger.error(f"Erro ao adicionar jogadores em lote: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/", response_model=List[BasicPlayerResponse], dependencies=[Depends(verify_token)]
)
@limiter.limit("30/minute")
async def get_all_players(request: Request, token: str = Depends(verify_token)):
    """Lista todos os jogadores sem informações sensíveis"""
    try:
        logger.info("Buscando lista básica de jogadores")
        player_service = PlayerService()
        players = player_service.get_all_players()
        if not players:
            return []
        logger.info(f"Encontrados {len(players)} jogadores")
        return players
    except Exception as e:
        logger.error(f"Erro ao listar jogadores: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{name}/{tag}",
    response_model=PlayerRankResponse,
    responses={
        400: {"model": ErrorResponse},
        429: {"description": "Rate limit exceeded"}
    },
)
@limiter.limit("15/minute")
async def get_player_rank(
    request: Request,
    response: Response,
    name: str,
    tag: str,
    token: str = Depends(verify_token)
):
    logger.info(f"Buscando rank do jogador: {name}#{tag}")
    try:
        player_service = PlayerService()
        result = player_service.get_player_rank(name, tag)
        logger.info(f"Rank do jogador {name}#{tag} recuperado com sucesso")
        return result
    except RateLimitExceeded:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded: 15 per 1 minute"
        )
    except ValueError as e:
        logger.error(f"Erro ao buscar rank do jogador {name}#{tag}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Erro inesperado ao buscar rank do jogador {name}#{tag}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.delete("/{id}", response_model=DeletePlayerResponse)
@limiter.limit("10/minute")
async def delete_player(request: Request, id: int, token: str = Depends(verify_token)):
    try:
        if id <= 0:
            raise HTTPException(status_code=400, detail="ID do jogador inválido")

        logger.info(f"Deletando jogador com ID: {id}")
        player_service = PlayerService()
        result = player_service.delete_player(id)

        if not result:
            raise HTTPException(status_code=404, detail="Jogador não encontrado")

        logger.info(f"Jogador {id} deletado com sucesso")
        return {"status": "success", "message": "Jogador deletado com sucesso"}
    except ValueError as e:
        logger.error(f"Erro ao deletar jogador {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro inesperado ao deletar jogador {id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post(
    "/verify-credentials",
    response_model=CredentialResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
@limiter.limit("10/minute")
async def verify_credentials(request: Request, cred: CredentialRequest):
    try:
        logger.info(f"Verificando credenciais para login: {cred.login}")
        player_service = PlayerService()
        result = player_service.verify_credentials(cred.login, cred.email)
        if result and result.get("password"):
            logger.info(f"Credenciais verificadas com sucesso para login: {cred.login}")
            return {"status": "success", "password": result["password"]}
        logger.warning(f"Credenciais não encontradas para login: {cred.login}")
        raise HTTPException(status_code=404, detail="Credenciais não encontradas")
    except Exception as e:
        logger.error(f"Erro ao verificar credenciais para login {cred.login}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/check-exists",
    response_model=PlayerExistsResponse,
    responses={400: {"model": ErrorResponse}},
)
@limiter.limit("20/minute")
async def check_player_exists(request: Request, data: dict):
    try:
        email = data.get("email")
        login = data.get("login")
        logger.info(
            f"Verificando existência de jogador - Email: {email}, Login: {login}"
        )

        player_service = PlayerService()
        result = player_service.check_player_exists(email, login)

        logger.info(
            f"Resultado da verificação - Email existe: {result.get('email_exists')}, "
            f"Login existe: {result.get('login_exists')}"
        )
        return result
    except Exception as e:
        logger.error(
            f"Erro ao verificar existência do jogador - Email: {email}, "
            f"Login: {login}. Erro: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
