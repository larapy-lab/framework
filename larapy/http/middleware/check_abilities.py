from typing import List


class CheckAbilities:
    
    def __init__(self, abilities: List[str], require_all: bool = True):
        self._abilities = abilities
        self._require_all = require_all
    
    def handle(self, request, next_middleware):
        from larapy.http.response import JsonResponse
        
        user = request.user()
        
        if not user:
            return JsonResponse({'message': 'Unauthenticated'}, status=401)
        
        if not hasattr(user, 'current_access_token'):
            return JsonResponse({'message': 'Token not found'}, status=401)
        
        token = user.current_access_token()
        if not token:
            return JsonResponse({'message': 'Token not found'}, status=401)
        
        if self._require_all:
            for ability in self._abilities:
                if not token.can(ability):
                    return JsonResponse(
                        {'message': f'Token lacks required ability: {ability}'},
                        status=403
                    )
        else:
            has_any = any(token.can(ability) for ability in self._abilities)
            if not has_any:
                return JsonResponse(
                    {'message': 'Token lacks any required abilities'},
                    status=403
                )
        
        return next_middleware(request)


class CheckForAnyAbility(CheckAbilities):
    
    def __init__(self, abilities: List[str]):
        super().__init__(abilities, require_all=False)
