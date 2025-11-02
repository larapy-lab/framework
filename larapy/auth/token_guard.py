from typing import Optional
from datetime import datetime, timedelta
from larapy.auth.guard import Guard
from larapy.auth.personal_access_token import PersonalAccessToken
from larapy.auth.user_provider import UserProvider
from larapy.auth.authenticatable import Authenticatable


class TokenGuard(Guard):
    
    def __init__(self, provider: UserProvider, request=None, expiration: Optional[int] = None):
        self._provider = provider
        self._request = request
        self._expiration = expiration
        self._user: Optional[Authenticatable] = None
        self._token: Optional[PersonalAccessToken] = None
    
    def check(self) -> bool:
        return self.user() is not None
    
    def guest(self) -> bool:
        return not self.check()
    
    def user(self) -> Optional[Authenticatable]:
        if self._user is not None:
            return self._user
        
        token_string = self._get_token_from_request()
        if not token_string:
            return None
        
        access_token = PersonalAccessToken.find_token(token_string)
        if not access_token:
            return None
        
        if access_token.is_expired():
            return None
        
        if self._expiration:
            created_at = access_token.get_attribute('created_at')
            if isinstance(created_at, str):
                created_at = datetime.strptime(created_at, access_token._date_format)
            
            if created_at:
                minutes_old = (datetime.now() - created_at).total_seconds() / 60
                if minutes_old > self._expiration:
                    return None
        
        tokenable_type = access_token.get_attribute('tokenable_type')
        tokenable_id = access_token.get_attribute('tokenable_id')
        
        if not tokenable_type or not tokenable_id:
            return None
        
        user = self._provider.retrieveById(tokenable_id)
        if not user:
            return None
        
        if hasattr(user, 'with_access_token'):
            user.with_access_token(access_token)
        
        access_token.set_attribute('last_used_at', datetime.now())
        access_token.save()
        
        self._user = user
        self._token = access_token
        
        return user
    
    def id(self):
        user = self.user()
        if user:
            return user.getAuthIdentifier()
        return None
    
    def validate(self, credentials: dict) -> bool:
        raise NotImplementedError('Token guard does not support credential validation')
    
    def attempt(self, credentials: dict, remember: bool = False) -> bool:
        raise NotImplementedError('Token guard does not support attempt method')
    
    def _get_token_from_request(self) -> Optional[str]:
        if not self._request:
            return None
        
        auth_header = self._request.header('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            
            if '|' in token:
                parts = token.split('|', 1)
                if len(parts) == 2:
                    return parts[1]
            
            return token
        
        return None
    
    def setRequest(self, request) -> None:
        self._request = request
