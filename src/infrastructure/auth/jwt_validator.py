from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.core.logger import app_logger
from src.configs import get_settings

# ⭐ Configuration JWT (IDENTIQUE à NestJS)
# Chargement lazy pour éviter les problèmes d'import circulaire
def get_jwt_secret() -> str:
    """Récupère le JWT_SECRET depuis la configuration"""
    settings = get_settings()
    if not settings.JWT_SECRET:
        raise ValueError("JWT_SECRET environment variable is required")
    return settings.JWT_SECRET

def get_jwt_algorithm() -> str:
    """Récupère le JWT_ALGORITHM depuis la configuration"""
    settings = get_settings()
    return settings.JWT_ALGORITHM

# Security scheme
# auto_error=False pour gérer l'erreur manuellement avec un meilleur logging
security = HTTPBearer(auto_error=False)

# ==========================================
# Modèles Pydantic
# ==========================================

class TokenPayload(BaseModel):
    """
    Structure du JWT payload
    ⭐ DOIT MATCHER le JwtPayload de NestJS
    
    Structure NestJS :
    {
        "sub": string,
        "userId": string,
        "username": string,  # email
        "roles": [{"organizationId": string, "role": string}]
    }
    """
    sub: str  # providerUserId
    userId: str  # user ID
    username: str  # email
    roles: List[Dict[str, Any]] = []  # [{"organizationId": "...", "role": "..."}]
    iat: Optional[int] = None  # Issued at
    exp: Optional[int] = None  # Expiration
    
    class Config:
        # Permettre des champs supplémentaires dans le payload
        extra = "allow"

class CurrentUser(BaseModel):
    """User extrait du JWT et disponible dans les endpoints"""
    id: str
    email: str
    organization_id: Optional[str] = None
    role: Optional[str] = None

# ==========================================
# Validation JWT
# ==========================================

def decode_jwt(token: str) -> TokenPayload:
    """
    Décode et valide le JWT
    
    Vérifie :
    1. Signature (avec JWT_SECRET)
    2. Expiration
    3. Structure du payload
    
    Raises:
        HTTPException: Si JWT invalide
    """
    try:
        # ⭐ Décoder avec le MÊME secret que NestJS
        jwt_secret = get_jwt_secret()
        jwt_algorithm = get_jwt_algorithm()
        
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=[jwt_algorithm]
        )
        
        app_logger.info(f"JWT decoded successfully for user: {payload.get('sub')}")
        app_logger.info(f"JWT payload keys: {list(payload.keys())}")
        
        # Valider la structure du payload
        try:
        token_data = TokenPayload(**payload)
        except ValidationError as e:
            app_logger.error(f"Pydantic validation error: {e.errors()}")
            app_logger.error(f"Payload received: {payload}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid JWT payload structure: {e.errors()}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Vérifier l'expiration manuellement (optionnel, jose le fait déjà)
        if token_data.exp and token_data.exp < datetime.now().timestamp():
            app_logger.warning(f"Expired JWT for user: {token_data.sub}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return token_data
        
    except JWTError as e:
        app_logger.error(f"JWT validation error: {e}")
        try:
            jwt_secret = get_jwt_secret()
            jwt_algorithm = get_jwt_algorithm()
            app_logger.error(f"JWT_SECRET configured: {bool(jwt_secret)}")
            app_logger.error(f"JWT_ALGORITHM: {jwt_algorithm}")
        except Exception:
            app_logger.error("JWT_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # Re-raise les HTTPException
        raise
    except Exception as e:
        app_logger.error(f"Unexpected error decoding JWT: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> CurrentUser:
    """
    Dependency FastAPI pour extraire l'utilisateur du JWT
    
    Structure JWT NestJS :
    {
        "sub": string,
        "userId": string,
        "username": string,  # email
        "roles": [{"organizationId": string, "role": string}]
    }
    
    Usage dans les endpoints :
        @router.post("/sentiment")
        async def analyze_sentiment(
            request: AnalyzeSentimentRequest,
            current_user: CurrentUser = Depends(get_current_user),
        ):
            # current_user.id, current_user.email disponibles
    """
    # Vérifier que les credentials sont présents
    if not credentials:
        app_logger.error("No Authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extraire le token du header Authorization
    token = credentials.credentials
    
    if not token:
        app_logger.error("No token provided in credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    app_logger.info(f"Validating JWT: {token[:20]}... (length: {len(token)})")
    
    # Décoder et valider
    try:
    payload = decode_jwt(token)
    except HTTPException as e:
        app_logger.error(f"JWT validation failed: {e.detail}")
        raise
    
    # Prendre le premier rôle disponible (l'organizationId sera extrait depuis les query params dans les endpoints si nécessaire)
    organization_id_final = None
    role_final = None
    
    if payload.roles and len(payload.roles) > 0:
        # Accéder aux valeurs du dictionnaire de manière sécurisée
        first_role = payload.roles[0]
        if isinstance(first_role, dict):
            organization_id_final = first_role.get("organizationId")
            role_final = first_role.get("role")
    
    # Créer l'objet CurrentUser
    current_user = CurrentUser(
        id=payload.userId,  # Utiliser userId au lieu de sub
        email=payload.username,  # username contient l'email dans NestJS
        organization_id=organization_id_final,
        role=role_final,
    )
    
    app_logger.info(f"User authenticated: {current_user.email} (ID: {current_user.id}, Org: {current_user.organization_id})")
    
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(
        HTTPBearer(auto_error=False)
    )
) -> Optional[CurrentUser]:
    """
    Version optionnelle : n'échoue pas si pas de JWT
    Utile pour endpoints publics avec features premium si connecté
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None