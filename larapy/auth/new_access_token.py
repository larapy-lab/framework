from larapy.auth.personal_access_token import PersonalAccessToken


class NewAccessToken:
    
    def __init__(self, access_token: PersonalAccessToken, plain_text_token: str):
        self.access_token = access_token
        self.plain_text_token = plain_text_token
    
    def to_dict(self) -> dict:
        return {
            'access_token': self.plain_text_token,
            'token_type': 'Bearer',
            'token': self.access_token.get_attributes() if self.access_token else {}
        }
    
    def to_array(self) -> dict:
        return self.to_dict()
    
    def __str__(self) -> str:
        return self.plain_text_token
