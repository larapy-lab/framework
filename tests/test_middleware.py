import pytest
from larapy.pipeline.pipeline import Pipeline
from larapy.http.kernel import Kernel
from larapy.http.request import Request
from larapy.http.response import Response, JsonResponse


class TestPipeline:
    def test_pipeline_creation(self):
        pipeline = Pipeline()
        assert pipeline is not None
    
    def test_send_passable(self):
        pipeline = Pipeline()
        result = pipeline.send("test").thenReturn()
        assert result == "test"
    
    def test_simple_pipe(self):
        def add_one(value, next_handler):
            return next_handler(value + 1)
        
        result = (Pipeline()
                 .send(1)
                 .through([add_one])
                 .thenReturn())
        
        assert result == 2
    
    def test_multiple_pipes(self):
        def add_one(value, next_handler):
            return next_handler(value + 1)
        
        def multiply_two(value, next_handler):
            return next_handler(value * 2)
        
        result = (Pipeline()
                 .send(5)
                 .through([add_one, multiply_two])
                 .thenReturn())
        
        assert result == 12
    
    def test_pipe_order(self):
        operations = []
        
        def first(value, next_handler):
            operations.append('first-before')
            result = next_handler(value)
            operations.append('first-after')
            return result
        
        def second(value, next_handler):
            operations.append('second-before')
            result = next_handler(value)
            operations.append('second-after')
            return result
        
        (Pipeline()
         .send('test')
         .through([first, second])
         .thenReturn())
        
        assert operations == ['first-before', 'second-before', 'second-after', 'first-after']
    
    def test_then_with_destination(self):
        def add_one(value, next_handler):
            return next_handler(value + 1)
        
        def destination(value):
            return value * 10
        
        result = (Pipeline()
                 .send(5)
                 .through([add_one])
                 .then(destination))
        
        assert result == 60
    
    def test_pipe_method(self):
        def add_one(value, next_handler):
            return next_handler(value + 1)
        
        result = (Pipeline()
                 .send(10)
                 .pipe(add_one)
                 .thenReturn())
        
        assert result == 11
    
    def test_via_method(self):
        class CustomPipe:
            def process(self, value, next_handler):
                return next_handler(value + 5)
        
        result = (Pipeline()
                 .send(10)
                 .via('process')
                 .through([CustomPipe()])
                 .thenReturn())
        
        assert result == 15
    
    def test_class_based_pipe(self):
        class AddTenPipe:
            def handle(self, value, next_handler):
                return next_handler(value + 10)
        
        result = (Pipeline()
                 .send(5)
                 .through([AddTenPipe()])
                 .thenReturn())
        
        assert result == 15
    
    def test_pipe_modifying_passable(self):
        class UppercasePipe:
            def handle(self, text, next_handler):
                return next_handler(text.upper())
        
        result = (Pipeline()
                 .send("hello")
                 .through([UppercasePipe()])
                 .thenReturn())
        
        assert result == "HELLO"
    
    def test_pipe_short_circuit(self):
        def check_value(value, next_handler):
            if value < 0:
                return "negative"
            return next_handler(value)
        
        def add_ten(value, next_handler):
            return next_handler(value + 10)
        
        result = (Pipeline()
                 .send(-5)
                 .through([check_value, add_ten])
                 .thenReturn())
        
        assert result == "negative"


class TestKernel:
    def test_kernel_creation(self):
        kernel = Kernel()
        assert kernel is not None
    
    def test_append_middleware(self):
        kernel = Kernel()
        kernel.append('TestMiddleware')
        
        assert 'TestMiddleware' in kernel.getMiddleware()
    
    def test_prepend_middleware(self):
        kernel = Kernel()
        kernel.append('First')
        kernel.prepend('Second')
        
        middleware = kernel.getMiddleware()
        assert middleware[0] == 'Second'
        assert middleware[1] == 'First'
    
    def test_use_middleware(self):
        kernel = Kernel()
        kernel.use(['First', 'Second', 'Third'])
        
        assert kernel.getMiddleware() == ['First', 'Second', 'Third']
    
    def test_middleware_groups(self):
        kernel = Kernel()
        kernel.appendToGroup('web', ['StartSession', 'VerifyCsrfToken'])
        
        groups = kernel.getMiddlewareGroups()
        assert 'StartSession' in groups['web']
        assert 'VerifyCsrfToken' in groups['web']
    
    def test_prepend_to_group(self):
        kernel = Kernel()
        kernel.appendToGroup('web', ['Second'])
        kernel.prependToGroup('web', ['First'])
        
        groups = kernel.getMiddlewareGroups()
        assert groups['web'][0] == 'First'
        assert groups['web'][1] == 'Second'
    
    def test_create_custom_group(self):
        kernel = Kernel()
        kernel.group('admin', ['Auth', 'IsAdmin'])
        
        groups = kernel.getMiddlewareGroups()
        assert groups['admin'] == ['Auth', 'IsAdmin']
    
    def test_middleware_alias(self):
        kernel = Kernel()
        kernel.alias({'auth': 'AuthMiddleware'})
        
        aliases = kernel.getRouteMiddleware()
        assert aliases['auth'] == 'AuthMiddleware'
    
    def test_alias_middleware_single(self):
        kernel = Kernel()
        kernel.aliasMiddleware('throttle', 'ThrottleMiddleware')
        
        assert kernel.getRouteMiddleware()['throttle'] == 'ThrottleMiddleware'
    
    def test_middleware_priority(self):
        kernel = Kernel()
        kernel.priority(['First', 'Second', 'Third'])
        
        assert kernel._middleware_priority == ['First', 'Second', 'Third']
    
    def test_has_middleware(self):
        kernel = Kernel()
        kernel.append('TestMiddleware')
        
        assert kernel.hasMiddleware('TestMiddleware') is True
        assert kernel.hasMiddleware('MissingMiddleware') is False


class TestMiddlewareExecution:
    def test_middleware_execution_order(self):
        class FirstMiddleware:
            def handle(self, request, next_handler):
                if not hasattr(request, '_log'):
                    request._log = []
                request._log.append('first-before')
                response = next_handler(request)
                request._log.append('first-after')
                return response
        
        class SecondMiddleware:
            def handle(self, request, next_handler):
                if not hasattr(request, '_log'):
                    request._log = []
                request._log.append('second-before')
                response = next_handler(request)
                request._log.append('second-after')
                return response
        
        kernel = Kernel()
        kernel.use([FirstMiddleware(), SecondMiddleware()])
        
        request = Request('/')
        request._route_middleware = []
        request._log = []
        
        def handler(req):
            req._log.append('handler')
            return Response('OK')
        
        kernel.handle(request, handler)
        
        assert request._log == ['first-before', 'second-before', 'handler', 'second-after', 'first-after']
    
    def test_middleware_can_modify_request(self):
        class AddHeaderMiddleware:
            def handle(self, request, next_handler):
                request._custom_header = 'value'
                return next_handler(request)
        
        kernel = Kernel()
        kernel.use([AddHeaderMiddleware()])
        
        request = Request('/')
        request._route_middleware = []
        
        def handler(req):
            assert hasattr(req, '_custom_header')
            assert req._custom_header == 'value'
            return Response('OK')
        
        kernel.handle(request, handler)
    
    def test_middleware_can_modify_response(self):
        class AddResponseHeaderMiddleware:
            def handle(self, request, next_handler):
                response = next_handler(request)
                response.header('X-Custom', 'Modified')
                return response
        
        kernel = Kernel()
        kernel.use([AddResponseHeaderMiddleware()])
        
        request = Request('/')
        request._route_middleware = []
        
        def handler(req):
            return Response('OK')
        
        response = kernel.handle(request, handler)
        
        assert response.getHeaders()['X-Custom'] == 'Modified'
    
    def test_middleware_can_short_circuit(self):
        class AuthMiddleware:
            def handle(self, request, next_handler):
                if not getattr(request, 'authenticated', False):
                    return JsonResponse({'error': 'Unauthorized'}, 401)
                return next_handler(request)
        
        kernel = Kernel()
        kernel.use([AuthMiddleware()])
        
        request = Request('/')
        request._route_middleware = []
        request.authenticated = False
        
        def handler(req):
            return Response('Secret Data')
        
        response = kernel.handle(request, handler)
        
        assert response.status() == 401
        assert response.getData()['error'] == 'Unauthorized'
    
    def test_middleware_with_parameters(self):
        class RoleMiddleware:
            def handle(self, request, next_handler, role):
                request._required_role = role
                return next_handler(request)
        
        kernel = Kernel()
        kernel.aliasMiddleware('role', RoleMiddleware())
        
        request = Request('/')
        request._route_middleware = ['role:admin']
        
        def handler(req):
            assert req._required_role == 'admin'
            return Response('OK')
        
        kernel.handle(request, handler)
    
    def test_terminable_middleware(self):
        class LoggingMiddleware:
            def __init__(self):
                self.terminated = False
            
            def handle(self, request, next_handler):
                return next_handler(request)
            
            def terminate(self, request, response):
                self.terminated = True
        
        middleware = LoggingMiddleware()
        kernel = Kernel()
        kernel.use([middleware])
        
        request = Request('/')
        request._route_middleware = []
        
        def handler(req):
            return Response('OK')
        
        response = kernel.handle(request, handler)
        kernel.terminate(request, response)
        
        assert middleware.terminated is True


class TestMiddlewareGroups:
    def test_expand_middleware_group(self):
        kernel = Kernel()
        kernel.group('web', ['StartSession', 'VerifyCsrfToken'])
        
        request = Request('/')
        request._route_middleware = ['web']
        
        expanded = kernel._expand_middleware(request._route_middleware)
        
        assert 'StartSession' in expanded
        assert 'VerifyCsrfToken' in expanded
    
    def test_expand_middleware_alias(self):
        kernel = Kernel()
        kernel.aliasMiddleware('auth', 'AuthMiddleware')
        
        request = Request('/')
        request._route_middleware = ['auth']
        
        expanded = kernel._expand_middleware(request._route_middleware)
        
        assert 'AuthMiddleware' in expanded
    
    def test_middleware_priority_sorting(self):
        kernel = Kernel()
        kernel.priority(['First', 'Second', 'Third'])
        
        unsorted = ['Third', 'First', 'Second']
        sorted_middleware = kernel._sort_middleware(unsorted)
        
        assert sorted_middleware == ['First', 'Second', 'Third']


class TestComplexScenarios:
    def test_authentication_and_authorization_pipeline(self):
        class AuthenticateMiddleware:
            def handle(self, request, next_handler):
                token = request.bearerToken()
                if not token:
                    return JsonResponse({'error': 'Unauthenticated'}, 401)
                request._user = {'id': 1, 'name': 'John', 'role': 'admin'}
                return next_handler(request)
        
        class AuthorizeMiddleware:
            def handle(self, request, next_handler, required_role):
                user = getattr(request, '_user', None)
                if not user or user.get('role') != required_role:
                    return JsonResponse({'error': 'Forbidden'}, 403)
                return next_handler(request)
        
        kernel = Kernel()
        kernel.aliasMiddleware('auth', AuthenticateMiddleware())
        kernel.aliasMiddleware('can', AuthorizeMiddleware())
        
        request = Request('/admin', headers={'Authorization': 'Bearer token123'})
        request._route_middleware = ['auth', 'can:admin']
        
        def handler(req):
            return JsonResponse({'data': 'Secret admin data'})
        
        response = kernel.handle(request, handler)
        
        assert response.status() == 200
        assert response.getData()['data'] == 'Secret admin data'
    
    def test_api_middleware_stack(self):
        class CorsMiddleware:
            def handle(self, request, next_handler):
                response = next_handler(request)
                response.header('Access-Control-Allow-Origin', '*')
                return response
        
        class ThrottleMiddleware:
            def handle(self, request, next_handler):
                request._rate_limited = True
                return next_handler(request)
        
        class JsonMiddleware:
            def handle(self, request, next_handler):
                response = next_handler(request)
                if not isinstance(response, JsonResponse):
                    response = JsonResponse({'data': response.content()})
                return response
        
        kernel = Kernel()
        kernel.group('api', [CorsMiddleware(), ThrottleMiddleware(), JsonMiddleware()])
        
        request = Request('/api/users')
        request._route_middleware = ['api']
        
        def handler(req):
            assert req._rate_limited is True
            return Response('User list')
        
        response = kernel.handle(request, handler)
        
        assert response.getHeaders()['Access-Control-Allow-Origin'] == '*'
        assert isinstance(response, JsonResponse)
    
    def test_web_middleware_stack_with_session(self):
        class StartSessionMiddleware:
            def handle(self, request, next_handler):
                request.setSession({'user_id': 1})
                return next_handler(request)
        
        class VerifyCsrfMiddleware:
            def handle(self, request, next_handler):
                if request.method() == 'POST':
                    csrf_token = request.input('_token')
                    if not csrf_token:
                        return JsonResponse({'error': 'CSRF token missing'}, 419)
                return next_handler(request)
        
        kernel = Kernel()
        kernel.group('web', [StartSessionMiddleware(), VerifyCsrfMiddleware()])
        
        request = Request('/form', 'POST', post={'_token': 'valid-token'})
        request._route_middleware = ['web']
        
        def handler(req):
            assert req.session('user_id') == 1
            return Response('Form submitted')
        
        response = kernel.handle(request, handler)
        
        assert response.status() == 200
    
    def test_logging_middleware_with_termination(self):
        class RequestLogger:
            def __init__(self):
                self.logs = []
            
            def handle(self, request, next_handler):
                self.logs.append(f"Request: {request.method()} {request.path()}")
                return next_handler(request)
            
            def terminate(self, request, response):
                self.logs.append(f"Response: {response.status()}")
        
        logger = RequestLogger()
        kernel = Kernel()
        kernel.use([logger])
        
        request = Request('/users', 'GET')
        request._route_middleware = []
        
        def handler(req):
            return Response('Users list')
        
        response = kernel.handle(request, handler)
        kernel.terminate(request, response)
        
        assert len(logger.logs) == 2
        assert logger.logs[0] == "Request: GET users"
        assert logger.logs[1] == "Response: 200"
    
    def test_conditional_middleware_based_on_request(self):
        class ConditionalMiddleware:
            def handle(self, request, next_handler):
                if request.is_('api/*'):
                    response = next_handler(request)
                    return JsonResponse({'data': response.content()}) if not isinstance(response, JsonResponse) else response
                return next_handler(request)
        
        kernel = Kernel()
        kernel.use([ConditionalMiddleware()])
        
        api_request = Request('/api/users')
        api_request._route_middleware = []
        
        web_request = Request('/dashboard')
        web_request._route_middleware = []
        
        def handler(req):
            return Response('Content')
        
        api_response = kernel.handle(api_request, handler)
        web_response = kernel.handle(web_request, handler)
        
        assert isinstance(api_response, JsonResponse)
        assert isinstance(web_response, Response) and not isinstance(web_response, JsonResponse)
