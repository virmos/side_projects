"""
Unit tests for the auth router and permissions functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import httpx
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError

from api.routers.auth import router
from securities.permissions import (
    get_current_customer_id,
    authorize_order_access,
    _get_casdoor_public_key,
    oauth2_scheme
)


class TestCasdoorPublicKey:
    """Test cases for Casdoor public key handling."""
    
    def test_get_casdoor_public_key_from_file(self):
        """Test getting public key from file."""
        mock_cert_content = "test_certificate_content"
        
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('builtins.open', mock_open(read_data=mock_cert_content)):
                    with patch('securities.permissions.settings') as mock_settings:
                        mock_settings.CASDOOR_CERTIFICATE = "/path/to/cert.pem"
                        
                        result = _get_casdoor_public_key()
                        
                        assert result == f"-----BEGIN CERTIFICATE-----\n{mock_cert_content}\n-----END CERTIFICATE-----\n"
    
    def test_get_casdoor_public_key_from_string(self):
        """Test getting public key from string."""
        cert_string = "test_certificate_content"
        
        with patch('securities.permissions.settings') as mock_settings:
            mock_settings.CASDOOR_CERTIFICATE = cert_string
            
            result = _get_casdoor_public_key()
            
            assert result == f"-----BEGIN CERTIFICATE-----\n{cert_string}\n-----END CERTIFICATE-----\n"
    
    def test_get_casdoor_public_key_already_formatted(self):
        """Test getting public key that's already properly formatted."""
        cert_string = "-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----"
        
        with patch('securities.permissions.settings') as mock_settings:
            mock_settings.CASDOOR_CERTIFICATE = cert_string
            
            result = _get_casdoor_public_key()
            
            assert result == cert_string
    
    def test_get_casdoor_public_key_file_not_found(self):
        """Test getting public key when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            with patch('securities.permissions.settings') as mock_settings:
                mock_settings.CASDOOR_CERTIFICATE = "/nonexistent/path"
                
                result = _get_casdoor_public_key()
                
                assert result is None
    
    def test_get_casdoor_public_key_empty_config(self):
        """Test getting public key when config is empty."""
        with patch('securities.permissions.settings') as mock_settings:
            mock_settings.CASDOOR_CERTIFICATE = ""
            
            result = _get_casdoor_public_key()
            
            assert result is None


class TestPermissions:
    """Test cases for permission functions."""
    
    @pytest.mark.asyncio
    async def test_get_current_customer_id_success(self):
        """Test successful customer ID extraction from JWT."""
        mock_token = "valid.jwt.token"
        mock_claims = {"sub": "test_customer_123", "preferred_username": "test_user"}
        
        with patch('securities.permissions._get_casdoor_public_key', return_value="mock_cert"):
            with patch('jose.jwt.decode', return_value=mock_claims):
                result = await get_current_customer_id(mock_token)
                
                assert result == "test_customer_123"
    
    @pytest.mark.asyncio
    async def test_get_current_customer_id_preferred_username_fallback(self):
        """Test customer ID extraction using preferred_username as fallback."""
        mock_token = "valid.jwt.token"
        mock_claims = {"preferred_username": "test_user", "name": "Test User"}
        
        with patch('securities.permissions._get_casdoor_public_key', return_value="mock_cert"):
            with patch('jose.jwt.decode', return_value=mock_claims):
                result = await get_current_customer_id(mock_token)
                
                assert result == "test_user"
    
    @pytest.mark.asyncio
    async def test_get_current_customer_id_name_fallback(self):
        """Test customer ID extraction using name as fallback."""
        mock_token = "valid.jwt.token"
        mock_claims = {"name": "Test User"}
        
        with patch('securities.permissions._get_casdoor_public_key', return_value="mock_cert"):
            with patch('jose.jwt.decode', return_value=mock_claims):
                result = await get_current_customer_id(mock_token)
                
                assert result == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_current_customer_id_no_certificate(self):
        """Test customer ID extraction when certificate is missing."""
        mock_token = "valid.jwt.token"
        
        with patch('securities.permissions._get_casdoor_public_key', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_customer_id(mock_token)
            
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Casdoor certificate missing"
    
    @pytest.mark.asyncio
    async def test_get_current_customer_id_invalid_token(self):
        """Test customer ID extraction with invalid JWT token."""
        mock_token = "invalid.jwt.token"
        
        with patch('securities.permissions._get_casdoor_public_key', return_value="mock_cert"):
            with patch('jose.jwt.decode', side_effect=JWTError("Invalid token")):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_customer_id(mock_token)
                
                assert exc_info.value.status_code == 401
                assert exc_info.value.detail == "Invalid token"
    
    @pytest.mark.asyncio
    async def test_get_current_customer_id_invalid_payload(self):
        """Test customer ID extraction with invalid token payload."""
        mock_token = "valid.jwt.token"
        mock_claims = {}  # No user identifier
        
        with patch('securities.permissions._get_casdoor_public_key', return_value="mock_cert"):
            with patch('jose.jwt.decode', return_value=mock_claims):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_customer_id(mock_token)
                
                assert exc_info.value.status_code == 401
                assert exc_info.value.detail == "Invalid token payload"
    
    def test_authorize_order_access_success(self):
        """Test successful order access authorization."""
        current_user_id = "test_customer_123"
        order_customer_id = "test_customer_123"
        
        # Should not raise any exception
        authorize_order_access(current_user_id, order_customer_id)
    
    def test_authorize_order_access_forbidden(self):
        """Test order access authorization when user is not authorized."""
        current_user_id = "test_customer_123"
        order_customer_id = "different_customer_456"
        
        with pytest.raises(HTTPException) as exc_info:
            authorize_order_access(current_user_id, order_customer_id)
        
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Not authorized to access this order"


class TestAuthRouter:
    """Test cases for auth router endpoints."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for auth tests."""
        return {
            "CASDOOR_URL": "https://casdoor.example.com",
            "CASDOOR_APP_NAME": "test_app",
            "CASDOOR_CLIENT_ID": "test_client_id",
            "CASDOOR_CLIENT_SECRET": "test_client_secret"
        }
    
    def test_signup_redirect(self, mock_settings):
        """Test signup redirect endpoint."""
        from api.routers.auth import signup_redirect
        
        with patch('api.routers.auth.settings', mock_settings):
            response = signup_redirect()
            
            expected_url = f"{mock_settings['CASDOOR_URL'].rstrip('/')}/signup/{mock_settings['CASDOOR_APP_NAME']}"
            assert response.url == expected_url
            assert response.status_code == 307
    
    def test_signin_redirect(self, mock_settings):
        """Test signin redirect endpoint."""
        from api.routers.auth import signin_redirect
        
        redirect_uri = "https://example.com/callback"
        
        with patch('api.routers.auth.settings', mock_settings):
            response = signin_redirect(redirect_uri)
            
            expected_url = (
                f"{mock_settings['CASDOOR_URL'].rstrip('/')}/login/oauth/authorize"
                f"?client_id={mock_settings['CASDOOR_CLIENT_ID']}"
                f"&response_type=code&redirect_uri={redirect_uri}&scope=read&state=casdoor"
            )
            assert response.url == expected_url
            assert response.status_code == 307
    
    @pytest.mark.asyncio
    async def test_auth_callback_success(self, mock_settings):
        """Test successful auth callback."""
        from api.routers.auth import auth_callback
        
        code = "test_code"
        state = "casdoor"
        redirect_uri = "https://example.com/callback"
        
        mock_token_response = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        with patch('api.routers.auth.settings', mock_settings):
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = AsyncMock()
                mock_response.json.return_value = mock_token_response
                mock_response.raise_for_status = AsyncMock()
                mock_client.post.return_value = mock_response
                
                result = await auth_callback(code, state, redirect_uri)
                
                assert result == mock_token_response
                
                # Verify the request was made correctly
                mock_client.post.assert_called_once()
                call_args = mock_client.post.call_args
                assert call_args[1]["data"]["grant_type"] == "authorization_code"
                assert call_args[1]["data"]["code"] == code
                assert call_args[1]["data"]["redirect_uri"] == redirect_uri
    
    @pytest.mark.asyncio
    async def test_auth_callback_http_error(self, mock_settings):
        """Test auth callback with HTTP error."""
        from api.routers.auth import auth_callback
        
        code = "test_code"
        state = "casdoor"
        redirect_uri = "https://example.com/callback"
        
        with patch('api.routers.auth.settings', mock_settings):
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = AsyncMock()
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Bad Request", request=MagicMock(), response=MagicMock()
                )
                mock_client.post.return_value = mock_response
                
                with pytest.raises(httpx.HTTPStatusError):
                    await auth_callback(code, state, redirect_uri)
    
    @pytest.mark.asyncio
    async def test_login_success(self, mock_settings):
        """Test successful login."""
        from api.routers.auth import login
        
        form_data = OAuth2PasswordRequestForm(
            username="test_user",
            password="test_password"
        )
        
        mock_token_response = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        with patch('api.routers.auth.settings', mock_settings):
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_token_response
                mock_response.raise_for_status = AsyncMock()
                mock_client.post.return_value = mock_response
                
                result = await login(form_data)
                
                assert result == mock_token_response
                
                # Verify the request was made correctly
                mock_client.post.assert_called_once()
                call_args = mock_client.post.call_args
                assert call_args[1]["data"]["grant_type"] == "password"
                assert call_args[1]["data"]["username"] == "test_user"
                assert call_args[1]["data"]["password"] == "test_password"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_settings):
        """Test login with invalid credentials."""
        from api.routers.auth import login
        
        form_data = OAuth2PasswordRequestForm(
            username="test_user",
            password="wrong_password"
        )
        
        with patch('api.routers.auth.settings', mock_settings):
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = AsyncMock()
                mock_response.status_code = 400
                mock_response.raise_for_status = AsyncMock()
                mock_client.post.return_value = mock_response
                
                with pytest.raises(HTTPException) as exc_info:
                    await login(form_data)
                
                assert exc_info.value.status_code == 401
                assert exc_info.value.detail == "Invalid credentials"
    
    @pytest.mark.asyncio
    async def test_login_http_error(self, mock_settings):
        """Test login with HTTP error."""
        from api.routers.auth import login
        
        form_data = OAuth2PasswordRequestForm(
            username="test_user",
            password="test_password"
        )
        
        with patch('api.routers.auth.settings', mock_settings):
            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                mock_response = AsyncMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Internal Server Error", request=MagicMock(), response=MagicMock()
                )
                mock_client.post.return_value = mock_response
                
                with pytest.raises(httpx.HTTPStatusError):
                    await login(form_data)
