from larapy.validation.form_request import FormRequest
from larapy.validation.exceptions import AuthorizationException, ValidationException422
from larapy.http.request import Request
from larapy.http.response import Response, JsonResponse, RedirectResponse
from larapy.routing.router import Router
from larapy.routing.controller import Controller
from larapy.http.middleware import Middleware


class StorePostRequest(FormRequest):
    
    def authorize(self):
        user = self.user()
        return user is not None and user.get('is_author', False)
    
    def rules(self):
        return {
            'title': ['required', 'min:3', 'max:100'],
            'content': ['required', 'min:10'],
            'category_id': ['required', 'integer'],
            'tags': ['array'],
        }
    
    def messages(self):
        return {
            'title.required': 'Post title is required',
            'title.min': 'Title must be at least 3 characters',
            'content.required': 'Post content cannot be empty',
        }
    
    def prepareForValidation(self):
        # Transform category to category_id before validation
        if self.has('category'):
            self.merge({'category_id': self.input('category')})
        
        # Transform tags from CSV string to array before validation
        if self.has('tags') and isinstance(self.input('tags'), str):
            tags_list = [tag.strip() for tag in self.input('tags').split(',')]
            self.merge({'tags': tags_list})
    
    def passedValidation(self):
        # Additional transformations after validation passes
        pass


class PostsController(Controller):
    
    def store(self, request: StorePostRequest):
        validated = request.validated()
        return JsonResponse({'success': True, 'data': validated}, 201)


class TestFormRequestIntegration:
    
    def test_form_request_with_controller(self):
        request = Request()
        request.set_method('POST')
        request.merge({
            'title': 'My First Post',
            'content': 'This is the post content that is long enough',
            'category': 5,
            'tags': 'python, web, framework',
        })
        request.set_header('Accept', 'application/json')
        
        user_resolver = lambda: {'id': 1, 'is_author': True}
        
        form_request = StorePostRequest()
        form_request.merge(request.all())
        form_request.set_request(request)
        form_request.setUserResolver(user_resolver)
        
        form_request.validateResolved()
        
        controller = PostsController()
        response = controller.store(form_request)
        
        assert isinstance(response, JsonResponse)
        assert response.status_code == 201
        assert response.get_json()['success'] is True
        
        validated = response.get_json()['data']
        assert validated['title'] == 'My First Post'
        assert validated['category_id'] == 5
        assert validated['tags'] == ['python', 'web', 'framework']
    
    def test_form_request_authorization_failure(self):
        request = Request()
        request.set_method('POST')
        request.merge({
            'title': 'My First Post',
            'content': 'This is the post content',
            'category_id': 5,
        })
        
        user_resolver = lambda: {'id': 1, 'is_author': False}
        
        form_request = StorePostRequest()
        form_request.merge(request.all())
        form_request.set_request(request)
        form_request.setUserResolver(user_resolver)
        
        try:
            form_request.validateResolved()
            assert False, "Should have raised AuthorizationException"
        except AuthorizationException as e:
            assert e.status_code == 403
    
    def test_form_request_validation_failure(self):
        request = Request()
        request.set_method('POST')
        request.merge({
            'title': 'AB',
            'content': 'Short',
        })
        request.set_header('Accept', 'application/json')
        
        user_resolver = lambda: {'id': 1, 'is_author': True}
        
        form_request = StorePostRequest()
        form_request.merge(request.all())
        form_request.set_request(request)
        form_request.setUserResolver(user_resolver)
        
        try:
            form_request.validateResolved()
            assert False, "Should have raised ValidationException422"
        except ValidationException422 as e:
            assert e.status_code == 422
            errors = e.to_dict()
            assert 'title' in errors['errors']
            assert 'content' in errors['errors']
            assert 'category_id' in errors['errors']
    
    def test_form_request_with_middleware(self):
        class AuthMiddleware(Middleware):
            def handle(self, request, next_handler):
                # Use object.__setattr__ to bypass __getattr__ magic method
                object.__setattr__(request, '_middleware_user', {'id': 1, 'is_author': True})
                return next_handler(request)
        
        request = Request()
        request.set_method('POST')
        request.merge({
            'title': 'My First Post',
            'content': 'This is the post content that is long enough',
            'category_id': 5,
        })
        request.set_header('Accept', 'application/json')
        
        middleware = AuthMiddleware()
        middleware.handle(request, lambda req: req)
        
        user_resolver = lambda: object.__getattribute__(request, '_middleware_user') if hasattr(type(request), '__dict__') and '_middleware_user' in object.__getattribute__(request, '__dict__') else None
        
        form_request = StorePostRequest()
        form_request.merge(request.all())
        form_request.set_request(request)
        form_request.setUserResolver(user_resolver)
        
        form_request.validateResolved()
        
        validated = form_request.validated()
        assert validated['title'] == 'My First Post'
    
    def test_form_request_prepare_transforms_data(self):
        request = Request()
        request.set_method('POST')
        request.merge({
            'title': 'My First Post',
            'content': 'This is the post content that is long enough',
            'category': 5,
            'tags': 'python, web, framework',
        })
        request.set_header('Accept', 'application/json')
        
        user_resolver = lambda: {'id': 1, 'is_author': True}
        
        form_request = StorePostRequest()
        form_request.merge(request.all())
        form_request.set_request(request)
        form_request.setUserResolver(user_resolver)
        
        form_request.validateResolved()
        
        validated = form_request.validated()
        
        assert validated['category_id'] == 5
        assert isinstance(validated['tags'], list)
        assert validated['tags'] == ['python', 'web', 'framework']
    
    def test_multiple_form_requests_isolated(self):
        request1 = Request()
        request1.set_method('POST')
        request1.merge({
            'title': 'First Post',
            'content': 'This is the first post content',
            'category_id': 1,
        })
        request1.set_header('Accept', 'application/json')
        
        request2 = Request()
        request2.set_method('POST')
        request2.merge({
            'title': 'Second Post',
            'content': 'This is the second post content',
            'category_id': 2,
        })
        request2.set_header('Accept', 'application/json')
        
        user_resolver = lambda: {'id': 1, 'is_author': True}
        
        form_request1 = StorePostRequest()
        form_request1.merge(request1.all())
        form_request1.set_request(request1)
        form_request1.setUserResolver(user_resolver)
        form_request1.validateResolved()
        
        form_request2 = StorePostRequest()
        form_request2.merge(request2.all())
        form_request2.set_request(request2)
        form_request2.setUserResolver(user_resolver)
        form_request2.validateResolved()
        
        validated1 = form_request1.validated()
        validated2 = form_request2.validated()
        
        assert validated1['title'] == 'First Post'
        assert validated1['category_id'] == 1
        
        assert validated2['title'] == 'Second Post'
        assert validated2['category_id'] == 2
    
    def test_form_request_with_file_upload(self):
        class UploadFileRequest(FormRequest):
            def authorize(self):
                return True
            
            def rules(self):
                return {
                    'title': ['required'],
                    'file': ['required', 'file'],
                }
        
        request = Request()
        request.set_method('POST')
        request.merge({
            'title': 'My Document',
            'file': {'name': 'document.pdf', 'size': 1024, 'type': 'application/pdf'},
        })
        
        form_request = UploadFileRequest()
        form_request.merge(request.all())
        form_request.set_request(request)
        
        form_request.validateResolved()
        
        validated = form_request.validated()
        assert validated['title'] == 'My Document'
        assert validated['file']['name'] == 'document.pdf'
