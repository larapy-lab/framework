from datetime import datetime
from typing import List, Optional
import hashlib
from larapy.database.orm.model import Model


class PersonalAccessToken(Model):
    
    _table = 'personal_access_tokens'
    
    _fillable = [
        'name',
        'token',
        'abilities',
        'last_used_at',
        'expires_at',
        'tokenable_type',
        'tokenable_id'
    ]
    
    _casts = {
        'abilities': 'json',
        'last_used_at': 'datetime',
        'expires_at': 'datetime'
    }
    
    def tokenable(self):
        return self._morph_to_relation('tokenable')
    
    def _morph_to_relation(self, name: str):
        tokenable_type = self.get_attribute(f'{name}_type')
        tokenable_id = self.get_attribute(f'{name}_id')
        
        if not tokenable_type or not tokenable_id:
            return None
            
        from larapy.support.facades.app import App
        model_class = App.make(tokenable_type)
        
        return model_class.query().where('id', tokenable_id).first()
    
    def can(self, ability: str) -> bool:
        abilities = self.get_attribute('abilities')
        
        if not abilities:
            return False
        
        if isinstance(abilities, str):
            import json
            try:
                abilities = json.loads(abilities)
            except:
                return False
        
        if not isinstance(abilities, list):
            return False
            
        if '*' in abilities:
            return True
            
        return ability in abilities
    
    def cant(self, ability: str) -> bool:
        return not self.can(ability)
    
    def is_expired(self) -> bool:
        expires_at = self.get_attribute('expires_at')
        
        if not expires_at:
            return False
        
        if isinstance(expires_at, str):
            expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
            
        return datetime.now() > expires_at
    
    @classmethod
    def find_token(cls, token: str, connection=None) -> Optional['PersonalAccessToken']:
        # Token format is {id}|{secret}. We need to extract and hash only the secret part.
        if '|' not in token:
            return None
        
        parts = token.split('|', 1)
        if len(parts) != 2:
            return None
        
        token_id, secret = parts
        hashed = hashlib.sha256(secret.encode()).hexdigest()
        
        instance = cls({}, connection) if connection else cls()
        result = instance.get_connection().table(instance.get_table()).where('id', token_id).where('token', hashed).first()
        
        if not result:
            return None
        
        model = cls({}, connection) if connection else cls()
        model._attributes = dict(result)
        model._original = dict(result)
        model._exists = True
        
        return model
