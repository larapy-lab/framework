"""
Tests for Pipeline Exception Handling and Enhancements

Tests the enhanced Pipeline class with exception handling,
terminable middleware, and complex middleware scenarios.
"""

import pytest
from larapy.pipeline.pipeline import Pipeline
from larapy.http.kernel import Kernel
from larapy.http.request import Request
from larapy.http.response import Response, JsonResponse


class TestPipelineExceptionHandling:
    """Test Pipeline exception handling."""
    
    def test_exception_in_middleware_propagates_without_handler(self):
        pipeline = Pipeline()
        
        class FailingMiddleware:
            def handle(self, request, next_handler):
                raise ValueError("Middleware failed")
        
        request = Request('/')
        
        with pytest.raises(ValueError, match="Middleware failed"):
            pipeline.send(request).through([FailingMiddleware()]).then(lambda r: Response('OK'))
    
    def test_exception_caught_by_handler(self):
        pipeline = Pipeline()
        
        class FailingMiddleware:
            def handle(self, request, next_handler):
                raise ValueError("Middleware failed")
        
        handled_exception = None
        
        def exception_handler(passable, exception):
            nonlocal handled_exception
            handled_exception = exception
            return Response('Error handled', 500)
        
        request = Request('/')
        
        response = (pipeline
                   .send(request)
                   .through([FailingMiddleware()])
                   .on_exception(exception_handler)
                   .then(lambda r: Response('OK')))
        
        assert handled_exception is not None
        assert isinstance(handled_exception, ValueError)
        assert response.status() == 500
        assert response.content() == 'Error handled'
    
    def test_exception_in_destination_caught(self):
        pipeline = Pipeline()
        
        handled_exception = None
        
        def exception_handler(passable, exception):
            nonlocal handled_exception
            handled_exception = exception
            return Response('Destination error handled', 500)
        
        def failing_destination(request):
            raise RuntimeError("Destination failed")
        
        request = Request('/')
        
        response = (pipeline
                   .send(request)
                   .on_exception(exception_handler)
                   .then(failing_destination))
        
        assert handled_exception is not None
        assert isinstance(handled_exception, RuntimeError)
        assert response.status() == 500
    
    def test_exception_handler_receives_correct_passable(self):
        pipeline = Pipeline()
        
        class FailingMiddleware:
            def handle(self, request, next_handler):
                request._marker = 'modified'
                raise ValueError("After modification")
        
        received_passable = None
        
        def exception_handler(passable, exception):
            nonlocal received_passable
            received_passable = passable
            return Response('OK')
        
        request = Request('/')
        
        pipeline.send(request).through([FailingMiddleware()]).on_exception(exception_handler).then(lambda r: Response('OK'))
        
        assert received_passable is request
        assert hasattr(received_passable, '_marker')
        assert received_passable._marker == 'modified'
    
    def test_multiple_middleware_exception_in_first(self):
        pipeline = Pipeline()
        
        class FirstMiddleware:
            def handle(self, request, next_handler):
                raise ValueError("First failed")
        
        class SecondMiddleware:
            def handle(self, request, next_handler):
                object.__setattr__(request, '_second_called', True)
                return next_handler(request)
        
        handled = False
        
        def exception_handler(passable, exception):
            nonlocal handled
            handled = True
            return Response('Handled')
        
        request = Request('/')
        
        pipeline.send(request).through([FirstMiddleware(), SecondMiddleware()]).on_exception(exception_handler).then(lambda r: Response('OK'))
        
        assert handled
        try:
            object.__getattribute__(request, '_second_called')
            assert False, "Second middleware should not have been called"
        except AttributeError:
            pass
    
    def test_exception_in_middle_middleware(self):
        pipeline = Pipeline()
        
        class FirstMiddleware:
            def handle(self, request, next_handler):
                object.__setattr__(request, '_first', True)
                return next_handler(request)
        
        class SecondMiddleware:
            def handle(self, request, next_handler):
                raise ValueError("Second failed")
        
        class ThirdMiddleware:
            def handle(self, request, next_handler):
                object.__setattr__(request, '_third', True)
                return next_handler(request)
        
        def exception_handler(passable, exception):
            return Response('Handled')
        
        request = Request('/')
        
        response = (pipeline
                   .send(request)
                   .through([FirstMiddleware(), SecondMiddleware(), ThirdMiddleware()])
                   .on_exception(exception_handler)
                   .then(lambda r: Response('OK')))
        
        assert object.__getattribute__(request, '_first') is True
        try:
            object.__getattribute__(request, '_third')
            assert False, "Third middleware should not have been called"
        except AttributeError:
            pass
        assert response.content() == 'Handled'


class TestTerminableMiddleware:
    """Test terminable middleware support."""
    
    def test_terminable_middleware_called(self):
        class LoggingMiddleware:
            def __init__(self):
                self.logs = []
            
            def handle(self, request, next_handler):
                self.logs.append('handle')
                return next_handler(request)
            
            def terminate(self, request, response):
                self.logs.append('terminate')
        
        kernel = Kernel()
        middleware = LoggingMiddleware()
        kernel.use([middleware])
        
        request = Request('/')
        request._route_middleware = []
        
        def handler(req):
            return Response('OK')
        
        response = kernel.handle(request, handler)
        kernel.terminate(request, response)
        
        assert middleware.logs == ['handle', 'terminate']
    
    def test_multiple_terminable_middleware(self):
        order = []
        
        class FirstMiddleware:
            def handle(self, request, next_handler):
                order.append('first_handle')
                return next_handler(request)
            
            def terminate(self, request, response):
                order.append('first_terminate')
        
        class SecondMiddleware:
            def handle(self, request, next_handler):
                order.append('second_handle')
                return next_handler(request)
            
            def terminate(self, request, response):
                order.append('second_terminate')
        
        kernel = Kernel()
        kernel.use([FirstMiddleware(), SecondMiddleware()])
        
        request = Request('/')
        request._route_middleware = []
        
        def handler(req):
            order.append('handler')
            return Response('OK')
        
        response = kernel.handle(request, handler)
        kernel.terminate(request, response)
        
        assert order == [
            'first_handle',
            'second_handle',
            'handler',
            'first_terminate',
            'second_terminate'
        ]
    
    def test_terminate_receives_response(self):
        received_response = None
        
        class ResponseCheckMiddleware:
            def handle(self, request, next_handler):
                return next_handler(request)
            
            def terminate(self, request, response):
                nonlocal received_response
                received_response = response
        
        kernel = Kernel()
        middleware = ResponseCheckMiddleware()
        kernel.use([middleware])
        
        request = Request('/')
        request._route_middleware = []
        
        def handler(req):
            return Response('Test Content', 201)
        
        response = kernel.handle(request, handler)
        kernel.terminate(request, response)
        
        assert received_response is response
        assert received_response.status() == 201
        assert received_response.content() == 'Test Content'
    
    def test_terminate_without_terminate_method(self):
        class SimpleMiddleware:
            def handle(self, request, next_handler):
                return next_handler(request)
        
        kernel = Kernel()
        kernel.use([SimpleMiddleware()])
        
        request = Request('/')
        request._route_middleware = []
        
        def handler(req):
            return Response('OK')
        
        response = kernel.handle(request, handler)
        
        # Should not raise error
        kernel.terminate(request, response)


class TestComplexMiddlewareScenarios:
    """Test complex middleware scenarios."""
    
    def test_middleware_modifies_request_and_response(self):
        class RequestResponseMiddleware:
            def handle(self, request, next_handler):
                request._processed = True
                response = next_handler(request)
                response.header('X-Processed', 'true')
                return response
        
        pipeline = Pipeline()
        request = Request('/')
        
        def destination(req):
            assert req._processed is True
            return Response('OK')
        
        response = pipeline.send(request).through([RequestResponseMiddleware()]).then(destination)
        
        assert response.getHeaders()['X-Processed'] == 'true'
    
    def test_middleware_short_circuit(self):
        class AuthMiddleware:
            def handle(self, request, next_handler):
                try:
                    object.__getattribute__(request, '_authenticated')
                    return next_handler(request)
                except AttributeError:
                    return Response('Unauthorized', 401)
        
        pipeline = Pipeline()
        request = Request('/')
        
        destination_called = False
        
        def destination(req):
            nonlocal destination_called
            destination_called = True
            return Response('OK')
        
        response = pipeline.send(request).through([AuthMiddleware()]).then(destination)
        
        assert not destination_called
        assert response.status() == 401
    
    def test_conditional_middleware_execution(self):
        class ConditionalMiddleware:
            def handle(self, request, next_handler):
                if request.path().startswith('api'):
                    object.__setattr__(request, '_api', True)
                return next_handler(request)
        
        pipeline = Pipeline()
        
        api_request = Request('/api/users')
        web_request = Request('/dashboard')
        
        def destination(req):
            return Response('OK')
        
        response1 = pipeline.send(api_request).through([ConditionalMiddleware()]).then(destination)
        assert object.__getattribute__(api_request, '_api') is True
        
        response2 = pipeline.send(web_request).through([ConditionalMiddleware()]).then(destination)
        try:
            object.__getattribute__(web_request, '_api')
            assert False, "API flag should not be set for web request"
        except AttributeError:
            pass
    
    def test_middleware_with_container_resolution(self):
        from larapy.container.container import Container
        
        class ServiceMiddleware:
            def __init__(self, service_name='default'):
                self.service_name = service_name
            
            def handle(self, request, next_handler):
                object.__setattr__(request, '_service', self.service_name)
                return next_handler(request)
        
        container = Container()
        container.bind('middleware.service', lambda c: ServiceMiddleware('custom'))
        
        pipeline = Pipeline(container)
        request = Request('/')
        
        def destination(req):
            return Response('OK')
        
        response = pipeline.send(request).through(['middleware.service']).then(destination)
        
        assert object.__getattribute__(request, '_service') == 'custom'
    
    def test_nested_pipeline_execution(self):
        class OuterMiddleware:
            def handle(self, request, next_handler):
                request._outer = True
                return next_handler(request)
        
        class InnerMiddleware:
            def handle(self, request, next_handler):
                request._inner = True
                return next_handler(request)
        
        outer_pipeline = Pipeline()
        request = Request('/')
        
        def inner_destination(req):
            assert req._outer is True
            assert req._inner is True
            return Response('OK')
        
        def outer_destination(req):
            inner_pipeline = Pipeline()
            return inner_pipeline.send(req).through([InnerMiddleware()]).then(inner_destination)
        
        response = outer_pipeline.send(request).through([OuterMiddleware()]).then(outer_destination)
        
        assert response.status() == 200


class TestPipelineEdgeCases:
    """Test Pipeline edge cases."""
    
    def test_empty_middleware_list(self):
        pipeline = Pipeline()
        request = Request('/')
        
        def destination(req):
            return Response('OK')
        
        response = pipeline.send(request).through([]).then(destination)
        
        assert response.status() == 200
    
    def test_none_passable(self):
        pipeline = Pipeline()
        
        class Middleware:
            def handle(self, passable, next_handler):
                return next_handler(passable)
        
        result = pipeline.send(None).through([Middleware()]).then(lambda p: 'result')
        
        assert result == 'result'
    
    def test_pipeline_reuse(self):
        pipeline = Pipeline()
        
        class CounterMiddleware:
            def __init__(self):
                self.count = 0
            
            def handle(self, request, next_handler):
                self.count += 1
                request._count = self.count
                return next_handler(request)
        
        middleware = CounterMiddleware()
        
        request1 = Request('/')
        request2 = Request('/')
        
        def destination(req):
            return Response('OK')
        
        pipeline.send(request1).through([middleware]).then(destination)
        pipeline.send(request2).through([middleware]).then(destination)
        
        assert request1._count == 1
        assert request2._count == 2
    
    def test_middleware_returning_non_response(self):
        class DataMiddleware:
            def handle(self, data, next_handler):
                data['processed'] = True
                return next_handler(data)
        
        pipeline = Pipeline()
        data = {'value': 42}
        
        def destination(d):
            d['completed'] = True
            return d
        
        result = pipeline.send(data).through([DataMiddleware()]).then(destination)
        
        assert result['processed'] is True
        assert result['completed'] is True
        assert result['value'] == 42


class TestMiddlewareWithParameters:
    """Test middleware with parameters."""
    
    def test_middleware_receives_parameters(self):
        class ParameterizedMiddleware:
            def handle(self, request, next_handler, *args):
                request._params = args
                return next_handler(request)
        
        pipeline = Pipeline()
        request = Request('/')
        
        middleware_with_params = 'larapy.http.middleware.ParameterizedMiddleware:admin,moderator'
        
        # Simulate parameter parsing
        from larapy.http.kernel import MiddlewareWithParameters
        middleware = MiddlewareWithParameters(ParameterizedMiddleware(), ['admin', 'moderator'])
        
        def destination(req):
            return Response('OK')
        
        # Manual parameter passing for this test
        class ParameterWrapper:
            def __init__(self, middleware_instance, params):
                self.middleware = middleware_instance
                self.params = params
            
            def handle(self, request, next_handler):
                return self.middleware.handle(request, next_handler, *self.params)
        
        wrapped = ParameterWrapper(ParameterizedMiddleware(), ['admin', 'moderator'])
        response = pipeline.send(request).through([wrapped]).then(destination)
        
        assert request._params == ('admin', 'moderator')


class TestKernelMiddlewarePriority:
    """Test Kernel middleware priority sorting."""
    
    def test_middleware_executes_in_priority_order(self):
        execution_order = []
        
        class FirstPriorityMiddleware:
            def handle(self, request, next_handler):
                execution_order.append('first')
                return next_handler(request)
        
        class SecondPriorityMiddleware:
            def handle(self, request, next_handler):
                execution_order.append('second')
                return next_handler(request)
        
        class ThirdPriorityMiddleware:
            def handle(self, request, next_handler):
                execution_order.append('third')
                return next_handler(request)
        
        kernel = Kernel()
        
        # Set priority (first should execute first)
        kernel.priority([
            FirstPriorityMiddleware,
            SecondPriorityMiddleware,
            ThirdPriorityMiddleware
        ])
        
        # Add in reverse order
        kernel.use([
            ThirdPriorityMiddleware(),
            FirstPriorityMiddleware(),
            SecondPriorityMiddleware()
        ])
        
        request = Request('/')
        request._route_middleware = []
        
        def handler(req):
            execution_order.append('handler')
            return Response('OK')
        
        kernel.handle(request, handler)
        
        assert execution_order == ['first', 'second', 'third', 'handler']
