import pytest
from datetime import datetime, timedelta
from larapy.http.middleware.check_abilities import CheckAbilities, CheckForAnyAbility
from larapy.http.response import JsonResponse


class MockToken:
    def __init__(self, abilities=None):
        self.abilities = abilities or []
        self.name = 'test-token'
        self.created_at = datetime.now()
    
    def can(self, ability):
        return ability in self.abilities


class MockUser:
    def __init__(self, token=None):
        self._token = token
        self.id = 1
        self.email = 'test@example.com'
    
    def current_access_token(self):
        return self._token


class MockRequest:
    def __init__(self, user=None):
        self._user = user
        self.headers = {}
        self.method = 'GET'
        self.path = '/api/test'
    
    def user(self):
        return self._user


def next_middleware_success(request):
    return {'success': True, 'data': 'authorized'}


def next_middleware_custom(request):
    return {'message': 'Request processed successfully'}


class TestCheckAbilities:
    
    def test_middleware_allows_request_with_all_required_abilities(self):
        token = MockToken(abilities=['read', 'write', 'delete'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['read', 'write'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_middleware_blocks_request_missing_one_ability(self):
        token = MockToken(abilities=['read'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['read', 'write'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 403
        assert 'lacks required ability: write' in result.getData()['message']
    
    def test_middleware_blocks_request_with_no_abilities(self):
        token = MockToken(abilities=[])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['read'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 403
        assert 'lacks required ability: read' in result.getData()['message']
    
    def test_middleware_blocks_unauthenticated_request(self):
        request = MockRequest(user=None)
        
        middleware = CheckAbilities(['read'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 401
        assert result.getData()['message'] == 'Unauthenticated'
    
    def test_middleware_blocks_user_without_token(self):
        user = MockUser(token=None)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['read'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 401
        assert result.getData()['message'] == 'Token not found'
    
    def test_middleware_blocks_user_without_current_access_token_method(self):
        class UserWithoutToken:
            pass
        
        user = UserWithoutToken()
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['read'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 401
    
    def test_middleware_with_single_ability(self):
        token = MockToken(abilities=['admin'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['admin'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_middleware_with_multiple_abilities_all_present(self):
        token = MockToken(abilities=['user:read', 'user:write', 'user:delete', 'admin:access'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['user:read', 'user:write', 'user:delete'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_middleware_with_namespaced_abilities(self):
        token = MockToken(abilities=['posts:create', 'posts:update', 'comments:moderate'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['posts:create', 'posts:update'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_middleware_fails_with_partial_namespaced_abilities(self):
        token = MockToken(abilities=['posts:create'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['posts:create', 'posts:delete'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 403
        assert 'posts:delete' in result.getData()['message']


class TestCheckForAnyAbility:
    
    def test_middleware_allows_request_with_any_ability(self):
        token = MockToken(abilities=['read'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckForAnyAbility(['read', 'write', 'delete'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_middleware_allows_request_with_multiple_matching_abilities(self):
        token = MockToken(abilities=['read', 'write'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckForAnyAbility(['read', 'write', 'delete'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_middleware_blocks_request_with_no_matching_abilities(self):
        token = MockToken(abilities=['execute'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckForAnyAbility(['read', 'write', 'delete'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 403
        assert 'lacks any required abilities' in result.getData()['message']
    
    def test_middleware_blocks_empty_abilities_token(self):
        token = MockToken(abilities=[])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckForAnyAbility(['read', 'write'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 403
    
    def test_middleware_allows_with_last_ability_in_list(self):
        token = MockToken(abilities=['delete'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckForAnyAbility(['read', 'write', 'delete'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_middleware_with_single_matching_ability(self):
        token = MockToken(abilities=['admin'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckForAnyAbility(['admin'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_middleware_inherits_authentication_checks(self):
        request = MockRequest(user=None)
        
        middleware = CheckForAnyAbility(['read', 'write'])
        result = middleware.handle(request, next_middleware_success)
        
        assert isinstance(result, JsonResponse)
        assert result.status_code == 401
        assert result.getData()['message'] == 'Unauthenticated'


class TestComplexAbilityScenarios:
    
    def test_api_endpoint_with_tiered_abilities(self):
        token = MockToken(abilities=['api:read', 'api:write', 'reports:generate'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        read_middleware = CheckAbilities(['api:read'])
        write_middleware = CheckAbilities(['api:write'])
        
        read_result = read_middleware.handle(request, next_middleware_success)
        write_result = write_middleware.handle(request, next_middleware_success)
        
        assert read_result == {'success': True, 'data': 'authorized'}
        assert write_result == {'success': True, 'data': 'authorized'}
    
    def test_admin_dashboard_requires_multiple_abilities(self):
        token = MockToken(abilities=['admin:access', 'users:manage', 'settings:edit'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities(['admin:access', 'users:manage', 'settings:edit'])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_read_only_api_token(self):
        token = MockToken(abilities=['read:users', 'read:posts', 'read:comments'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        read_middleware = CheckForAnyAbility(['read:users', 'read:posts'])
        write_middleware = CheckAbilities(['write:users'])
        
        read_result = read_middleware.handle(request, next_middleware_success)
        write_result = write_middleware.handle(request, next_middleware_success)
        
        assert read_result == {'success': True, 'data': 'authorized'}
        assert isinstance(write_result, JsonResponse)
        assert write_result.status_code == 403
    
    def test_moderator_with_selective_permissions(self):
        token = MockToken(abilities=['posts:edit', 'comments:delete', 'users:ban'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        can_moderate_posts = CheckForAnyAbility(['posts:edit', 'posts:delete'])
        can_manage_users = CheckForAnyAbility(['users:ban', 'users:delete'])
        cannot_access_settings = CheckAbilities(['settings:edit'])
        
        posts_result = can_moderate_posts.handle(request, next_middleware_success)
        users_result = can_manage_users.handle(request, next_middleware_success)
        settings_result = cannot_access_settings.handle(request, next_middleware_success)
        
        assert posts_result == {'success': True, 'data': 'authorized'}
        assert users_result == {'success': True, 'data': 'authorized'}
        assert isinstance(settings_result, JsonResponse)
        assert settings_result.status_code == 403
    
    def test_microservice_token_with_service_specific_abilities(self):
        token = MockToken(abilities=[
            'service:payments:process',
            'service:payments:refund',
            'service:notifications:send'
        ])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        payment_middleware = CheckAbilities(['service:payments:process', 'service:payments:refund'])
        notification_middleware = CheckAbilities(['service:notifications:send'])
        billing_middleware = CheckAbilities(['service:billing:invoice'])
        
        payment_result = payment_middleware.handle(request, next_middleware_success)
        notification_result = notification_middleware.handle(request, next_middleware_custom)
        billing_result = billing_middleware.handle(request, next_middleware_success)
        
        assert payment_result == {'success': True, 'data': 'authorized'}
        assert notification_result == {'message': 'Request processed successfully'}
        assert isinstance(billing_result, JsonResponse)
        assert billing_result.status_code == 403
    
    def test_cascading_ability_checks(self):
        basic_token = MockToken(abilities=['user:read'])
        advanced_token = MockToken(abilities=['user:read', 'user:write'])
        admin_token = MockToken(abilities=['user:read', 'user:write', 'user:delete'])
        
        basic_user = MockUser(token=basic_token)
        advanced_user = MockUser(token=advanced_token)
        admin_user = MockUser(token=admin_token)
        
        read_request = MockRequest(user=basic_user)
        write_request = MockRequest(user=advanced_user)
        delete_request = MockRequest(user=admin_user)
        
        read_middleware = CheckAbilities(['user:read'])
        write_middleware = CheckAbilities(['user:write'])
        delete_middleware = CheckAbilities(['user:delete'])
        
        assert read_middleware.handle(read_request, next_middleware_success) == {'success': True, 'data': 'authorized'}
        assert write_middleware.handle(write_request, next_middleware_success) == {'success': True, 'data': 'authorized'}
        assert delete_middleware.handle(delete_request, next_middleware_success) == {'success': True, 'data': 'authorized'}
        
        assert isinstance(write_middleware.handle(read_request, next_middleware_success), JsonResponse)
        assert isinstance(delete_middleware.handle(write_request, next_middleware_success), JsonResponse)
    
    def test_wildcard_style_ability_matching(self):
        token = MockToken(abilities=[
            'products:create',
            'products:read',
            'products:update',
            'orders:read'
        ])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        product_management = CheckAbilities(['products:create', 'products:update'])
        order_management = CheckAbilities(['orders:read', 'orders:write'])
        
        product_result = product_management.handle(request, next_middleware_success)
        order_result = order_management.handle(request, next_middleware_success)
        
        assert product_result == {'success': True, 'data': 'authorized'}
        assert isinstance(order_result, JsonResponse)
        assert order_result.status_code == 403


class TestCheckAbilitiesInitialization:
    
    def test_initialization_with_require_all_true(self):
        middleware = CheckAbilities(['read', 'write'], require_all=True)
        assert middleware._abilities == ['read', 'write']
        assert middleware._require_all is True
    
    def test_initialization_with_require_all_false(self):
        middleware = CheckAbilities(['read', 'write'], require_all=False)
        assert middleware._abilities == ['read', 'write']
        assert middleware._require_all is False
    
    def test_initialization_default_require_all(self):
        middleware = CheckAbilities(['read', 'write'])
        assert middleware._require_all is True
    
    def test_check_for_any_ability_initialization(self):
        middleware = CheckForAnyAbility(['read', 'write', 'delete'])
        assert middleware._abilities == ['read', 'write', 'delete']
        assert middleware._require_all is False
    
    def test_empty_abilities_list(self):
        token = MockToken(abilities=['read'])
        user = MockUser(token=token)
        request = MockRequest(user=user)
        
        middleware = CheckAbilities([])
        result = middleware.handle(request, next_middleware_success)
        
        assert result == {'success': True, 'data': 'authorized'}
    
    def test_single_ability_in_list(self):
        middleware = CheckAbilities(['admin'])
        assert middleware._abilities == ['admin']
        assert len(middleware._abilities) == 1
