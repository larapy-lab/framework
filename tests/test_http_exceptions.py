import unittest
from larapy.http.exceptions import (
    HttpException,
    NotFoundHttpException,
    ForbiddenHttpException,
    UnauthorizedHttpException,
    MethodNotAllowedHttpException,
    ServerErrorHttpException,
    ServiceUnavailableHttpException,
)


class TestHttpException(unittest.TestCase):
    
    def test_http_exception_with_custom_message(self):
        exception = HttpException(404, 'Custom not found message')
        
        self.assertEqual(exception.status_code, 404)
        self.assertEqual(str(exception), 'Custom not found message')
        self.assertEqual(exception.get_status_code(), 404)
    
    def test_http_exception_with_default_message(self):
        exception = HttpException(404)
        
        self.assertEqual(str(exception), 'Not Found')
    
    def test_http_exception_with_headers(self):
        headers = {'X-Custom': 'value'}
        exception = HttpException(404, headers=headers)
        
        self.assertEqual(exception.get_headers(), headers)
    
    def test_http_exception_set_headers(self):
        exception = HttpException(404)
        new_headers = {'X-Custom': 'new value'}
        
        result = exception.set_headers(new_headers)
        
        self.assertEqual(exception.get_headers(), new_headers)
        self.assertIs(result, exception)
    
    def test_http_exception_with_code(self):
        exception = HttpException(500, code=42)
        
        self.assertEqual(exception.code, 42)


class TestNotFoundHttpException(unittest.TestCase):
    
    def test_not_found_exception_status_code(self):
        exception = NotFoundHttpException()
        
        self.assertEqual(exception.status_code, 404)
        self.assertEqual(exception.get_status_code(), 404)
    
    def test_not_found_exception_with_message(self):
        exception = NotFoundHttpException('User not found')
        
        self.assertEqual(str(exception), 'User not found')
    
    def test_not_found_exception_default_message(self):
        exception = NotFoundHttpException()
        
        self.assertEqual(str(exception), 'Not Found')
    
    def test_not_found_exception_with_headers(self):
        headers = {'X-Request-ID': '123'}
        exception = NotFoundHttpException(headers=headers)
        
        self.assertEqual(exception.get_headers(), headers)


class TestForbiddenHttpException(unittest.TestCase):
    
    def test_forbidden_exception_status_code(self):
        exception = ForbiddenHttpException()
        
        self.assertEqual(exception.status_code, 403)
    
    def test_forbidden_exception_with_message(self):
        exception = ForbiddenHttpException('Access denied')
        
        self.assertEqual(str(exception), 'Access denied')
    
    def test_forbidden_exception_default_message(self):
        exception = ForbiddenHttpException()
        
        self.assertEqual(str(exception), 'Forbidden')


class TestUnauthorizedHttpException(unittest.TestCase):
    
    def test_unauthorized_exception_status_code(self):
        exception = UnauthorizedHttpException()
        
        self.assertEqual(exception.status_code, 401)
    
    def test_unauthorized_exception_with_message(self):
        exception = UnauthorizedHttpException('Authentication required')
        
        self.assertEqual(str(exception), 'Authentication required')
    
    def test_unauthorized_exception_default_message(self):
        exception = UnauthorizedHttpException()
        
        self.assertEqual(str(exception), 'Unauthorized')


class TestMethodNotAllowedHttpException(unittest.TestCase):
    
    def test_method_not_allowed_status_code(self):
        exception = MethodNotAllowedHttpException()
        
        self.assertEqual(exception.status_code, 405)
    
    def test_method_not_allowed_with_allowed_methods(self):
        exception = MethodNotAllowedHttpException(['GET', 'POST'])
        
        self.assertEqual(exception.allowed_methods, ['GET', 'POST'])
        self.assertEqual(exception.get_headers()['Allow'], 'GET, POST')
    
    def test_method_not_allowed_without_allowed_methods(self):
        exception = MethodNotAllowedHttpException()
        
        self.assertEqual(exception.allowed_methods, [])
        self.assertNotIn('Allow', exception.get_headers())
    
    def test_method_not_allowed_default_message(self):
        exception = MethodNotAllowedHttpException()
        
        self.assertEqual(str(exception), 'Method Not Allowed')


class TestServerErrorHttpException(unittest.TestCase):
    
    def test_server_error_status_code(self):
        exception = ServerErrorHttpException()
        
        self.assertEqual(exception.status_code, 500)
    
    def test_server_error_with_message(self):
        exception = ServerErrorHttpException('Database connection failed')
        
        self.assertEqual(str(exception), 'Database connection failed')
    
    def test_server_error_default_message(self):
        exception = ServerErrorHttpException()
        
        self.assertEqual(str(exception), 'Internal Server Error')


class TestServiceUnavailableHttpException(unittest.TestCase):
    
    def test_service_unavailable_status_code(self):
        exception = ServiceUnavailableHttpException()
        
        self.assertEqual(exception.status_code, 503)
    
    def test_service_unavailable_with_retry_after(self):
        exception = ServiceUnavailableHttpException(retry_after=60)
        
        self.assertEqual(exception.retry_after, 60)
        self.assertEqual(exception.get_headers()['Retry-After'], '60')
    
    def test_service_unavailable_without_retry_after(self):
        exception = ServiceUnavailableHttpException()
        
        self.assertIsNone(exception.retry_after)
        self.assertNotIn('Retry-After', exception.get_headers())
    
    def test_service_unavailable_default_message(self):
        exception = ServiceUnavailableHttpException()
        
        self.assertEqual(str(exception), 'Service Unavailable')


class TestAbortHelpers(unittest.TestCase):
    
    def test_abort_raises_exception(self):
        from larapy.support.helpers_exceptions import abort
        
        with self.assertRaises(HttpException) as context:
            abort(404, 'Not found')
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(str(context.exception), 'Not found')
    
    def test_abort_if_raises_when_true(self):
        from larapy.support.helpers_exceptions import abort_if
        
        with self.assertRaises(HttpException):
            abort_if(True, 403, 'Forbidden')
    
    def test_abort_if_does_not_raise_when_false(self):
        from larapy.support.helpers_exceptions import abort_if
        
        abort_if(False, 403, 'Forbidden')
    
    def test_abort_unless_raises_when_false(self):
        from larapy.support.helpers_exceptions import abort_unless
        
        with self.assertRaises(HttpException):
            abort_unless(False, 403, 'Forbidden')
    
    def test_abort_unless_does_not_raise_when_true(self):
        from larapy.support.helpers_exceptions import abort_unless
        
        abort_unless(True, 403, 'Forbidden')


if __name__ == '__main__':
    unittest.main()
