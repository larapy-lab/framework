from typing import List, Optional
from datetime import datetime
import secrets
import hashlib
from larapy.auth.personal_access_token import PersonalAccessToken
from larapy.auth.new_access_token import NewAccessToken


class HasApiTokens:
    
    def tokens(self):
        instance = PersonalAccessToken()
        query = self.get_connection().table(instance.get_table())
        
        query.where('tokenable_type', self.__class__.__name__)
        query.where('tokenable_id', self.get_key())
        
        return TokenRelation(query, self)
    
    def create_token(
        self,
        name: str,
        abilities: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> NewAccessToken:
        if abilities is None:
            abilities = ['*']
        
        plain_text_token = secrets.token_urlsafe(40)
        hashed_token = hashlib.sha256(plain_text_token.encode()).hexdigest()
        
        # Convert expires_at to string without microseconds if it's a datetime object
        if expires_at and isinstance(expires_at, datetime):
            expires_at = expires_at.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        
        token_data = {
            'tokenable_type': self.__class__.__name__,
            'tokenable_id': self.get_key(),
            'name': name,
            'token': hashed_token,
            'abilities': abilities,
            'expires_at': expires_at
        }
        
        token = PersonalAccessToken(token_data, self.get_connection())
        token.save()
        
        token_id = token.get_key()
        plain_token_with_id = f"{token_id}|{plain_text_token}"
        
        return NewAccessToken(token, plain_token_with_id)
    
    def current_access_token(self) -> Optional[PersonalAccessToken]:
        return getattr(self, '_access_token', None)
    
    def with_access_token(self, token: PersonalAccessToken):
        self._access_token = token
        return self
    
    def token_can(self, ability: str) -> bool:
        token = self.current_access_token()
        return token.can(ability) if token else False
    
    def token_cant(self, ability: str) -> bool:
        return not self.token_can(ability)


class TokenRelation:
    
    def __init__(self, query, parent):
        self._query = query
        self._parent = parent
    
    def get(self):
        from larapy.database.orm.collection import Collection
        
        results = self._query.get()
        models = []
        
        for row in results:
            token = PersonalAccessToken({}, self._parent.get_connection())
            token._attributes = dict(row)
            token._original = dict(row)
            token._exists = True
            models.append(token)
        
        return Collection(models)
    
    def first(self):
        result = self._query.first()
        if not result:
            return None
        
        token = PersonalAccessToken({}, self._parent.get_connection())
        token._attributes = dict(result)
        token._original = dict(result)
        token._exists = True
        
        return token
    
    def where(self, column, operator=None, value=None):
        if value is None and operator is not None:
            value = operator
            operator = '='
        
        self._query.where(column, operator, value)
        return self
    
    def create(self, attributes: dict):
        attributes['tokenable_type'] = self._parent.__class__.__name__
        attributes['tokenable_id'] = self._parent.get_key()
        
        token = PersonalAccessToken(attributes, self._parent.get_connection())
        token.save()
        
        return token
