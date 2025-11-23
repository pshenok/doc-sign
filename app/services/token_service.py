import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from app.config import settings


class TokenService:
    """Service for JWT token generation and validation."""
    
    @staticmethod
    def generate_token(document_id: str, recipient_id: str) -> str:
        """
        Generate a JWT token for a recipient.
        
        Args:
            document_id: The document ID
            recipient_id: The recipient ID
            
        Returns:
            JWT token string
        """
        expiration = datetime.utcnow() + timedelta(days=settings.token_expiration_days)
        
        payload = {
            "document_id": document_id,
            "recipient_id": recipient_id,
            "exp": expiration,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
        return token
    
    @staticmethod
    def validate_token(token: str) -> Dict[str, Any]:
        """
        Validate and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
