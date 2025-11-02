import pytest
from larapy.http.resources.anonymous_resource import AnonymousResourceCollection


class MockResource:
    def __init__(self, data):
        self._data = data
    
    def __getattr__(self, key):
        return self._data.get(key)
    
    def to_dict(self):
        return self._data


class MockRequest:
    def __init__(self, user_id=None, include_fields=None):
        self.user_id = user_id
        self.include_fields = include_fields or []
        self.headers = {}


class TestAnonymousResourceCollection:
    
    def test_collection_with_simple_callback(self):
        resources = [
            MockResource({'id': 1, 'name': 'Item 1'}),
            MockResource({'id': 2, 'name': 'Item 2'}),
        ]
        
        def callback(resource, request):
            return {'id': resource.id, 'title': resource.name}
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert len(result) == 2
        assert result[0] == {'id': 1, 'title': 'Item 1'}
        assert result[1] == {'id': 2, 'title': 'Item 2'}
    
    def test_collection_with_request_aware_callback(self):
        resources = [
            MockResource({'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}),
            MockResource({'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}),
        ]
        
        def callback(resource, request):
            data = {'id': resource.id, 'name': resource.name}
            if request and hasattr(request, 'include_fields') and 'email' in request.include_fields:
                data['email'] = resource.email
            return data
        
        request = MockRequest(include_fields=['email'])
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict(request)
        
        assert len(result) == 2
        assert result[0] == {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}
        assert result[1] == {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
    
    def test_collection_without_request(self):
        resources = [
            MockResource({'id': 1, 'price': 100}),
            MockResource({'id': 2, 'price': 200}),
        ]
        
        def callback(resource, request):
            return {
                'id': resource.id,
                'price': resource.price,
                'currency': 'USD'
            }
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert len(result) == 2
        assert result[0] == {'id': 1, 'price': 100, 'currency': 'USD'}
        assert result[1] == {'id': 2, 'price': 200, 'currency': 'USD'}
    
    def test_empty_collection(self):
        resources = []
        
        def callback(resource, request):
            return {'id': resource.id}
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert result == []
    
    def test_collection_with_single_resource(self):
        resources = [MockResource({'id': 1, 'status': 'active'})]
        
        def callback(resource, request):
            return {'resource_id': resource.id, 'is_active': resource.status == 'active'}
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert len(result) == 1
        assert result[0] == {'resource_id': 1, 'is_active': True}


class TestAnonymousResourceCollectionComplexTransformations:
    
    def test_collection_with_nested_data_transformation(self):
        resources = [
            MockResource({
                'id': 1,
                'user': {'name': 'John', 'age': 30},
                'posts': [{'title': 'Post 1'}, {'title': 'Post 2'}]
            }),
            MockResource({
                'id': 2,
                'user': {'name': 'Jane', 'age': 25},
                'posts': [{'title': 'Post 3'}]
            }),
        ]
        
        def callback(resource, request):
            return {
                'id': resource.id,
                'author': resource.user['name'],
                'post_count': len(resource.posts)
            }
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert result[0] == {'id': 1, 'author': 'John', 'post_count': 2}
        assert result[1] == {'id': 2, 'author': 'Jane', 'post_count': 1}
    
    def test_collection_with_conditional_field_inclusion(self):
        resources = [
            MockResource({'id': 1, 'name': 'Product A', 'price': 100, 'is_premium': True}),
            MockResource({'id': 2, 'name': 'Product B', 'price': 50, 'is_premium': False}),
            MockResource({'id': 3, 'name': 'Product C', 'price': 200, 'is_premium': True}),
        ]
        
        def callback(resource, request):
            data = {
                'id': resource.id,
                'name': resource.name,
            }
            if resource.is_premium:
                data['price'] = resource.price
                data['badge'] = 'Premium'
            return data
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert result[0] == {'id': 1, 'name': 'Product A', 'price': 100, 'badge': 'Premium'}
        assert result[1] == {'id': 2, 'name': 'Product B'}
        assert result[2] == {'id': 3, 'name': 'Product C', 'price': 200, 'badge': 'Premium'}
    
    def test_collection_with_data_filtering(self):
        resources = [
            MockResource({'id': 1, 'status': 'active', 'value': 100}),
            MockResource({'id': 2, 'status': 'inactive', 'value': 50}),
            MockResource({'id': 3, 'status': 'active', 'value': 200}),
        ]
        
        def callback(resource, request):
            if resource.status != 'active':
                return None
            return {'id': resource.id, 'value': resource.value}
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert result == [
            {'id': 1, 'value': 100},
            None,
            {'id': 3, 'value': 200}
        ]
    
    def test_collection_with_aggregated_calculations(self):
        resources = [
            MockResource({'id': 1, 'price': 100, 'quantity': 2, 'tax_rate': 0.1}),
            MockResource({'id': 2, 'price': 50, 'quantity': 5, 'tax_rate': 0.1}),
            MockResource({'id': 3, 'price': 200, 'quantity': 1, 'tax_rate': 0.15}),
        ]
        
        def callback(resource, request):
            subtotal = resource.price * resource.quantity
            tax = subtotal * resource.tax_rate
            total = subtotal + tax
            
            return {
                'id': resource.id,
                'subtotal': subtotal,
                'tax': round(tax, 2),
                'total': round(total, 2)
            }
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert result[0] == {'id': 1, 'subtotal': 200, 'tax': 20.0, 'total': 220.0}
        assert result[1] == {'id': 2, 'subtotal': 250, 'tax': 25.0, 'total': 275.0}
        assert result[2] == {'id': 3, 'subtotal': 200, 'tax': 30.0, 'total': 230.0}
    
    def test_collection_with_user_specific_visibility(self):
        resources = [
            MockResource({'id': 1, 'title': 'Public Post', 'content': 'Content 1', 'is_public': True, 'author_id': 1}),
            MockResource({'id': 2, 'title': 'Private Post', 'content': 'Secret', 'is_public': False, 'author_id': 1}),
            MockResource({'id': 3, 'title': 'Another Post', 'content': 'Content 3', 'is_public': True, 'author_id': 2}),
        ]
        
        def callback(resource, request):
            data = {'id': resource.id, 'title': resource.title}
            
            if resource.is_public or (request and request.user_id == resource.author_id):
                data['content'] = resource.content
            else:
                data['content'] = '[Hidden]'
            
            return data
        
        public_request = MockRequest(user_id=None)
        author_request = MockRequest(user_id=1)
        other_user_request = MockRequest(user_id=2)
        
        collection = AnonymousResourceCollection(resources, callback)
        
        public_result = collection.to_dict(public_request)
        author_result = collection.to_dict(author_request)
        other_result = collection.to_dict(other_user_request)
        
        assert public_result[1]['content'] == '[Hidden]'
        assert author_result[1]['content'] == 'Secret'
        assert other_result[1]['content'] == '[Hidden]'
    
    def test_collection_with_lambda_callback(self):
        resources = [
            MockResource({'id': 1, 'value': 10}),
            MockResource({'id': 2, 'value': 20}),
        ]
        
        collection = AnonymousResourceCollection(
            resources,
            lambda resource, request: {'id': resource.id, 'doubled': resource.value * 2}
        )
        result = collection.to_dict()
        
        assert result[0] == {'id': 1, 'doubled': 20}
        assert result[1] == {'id': 2, 'doubled': 40}


class TestAnonymousResourceCollectionRealWorldScenarios:
    
    def test_api_response_pagination_metadata(self):
        resources = [
            MockResource({'id': 1, 'name': 'Item 1'}),
            MockResource({'id': 2, 'name': 'Item 2'}),
            MockResource({'id': 3, 'name': 'Item 3'}),
        ]
        
        page = 1
        per_page = 3
        total = 10
        
        def callback(resource, request):
            return {
                'id': resource.id,
                'name': resource.name,
                'links': {
                    'self': f'/api/items/{resource.id}'
                }
            }
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert len(result) == 3
        assert all('links' in item for item in result)
        assert result[0]['links']['self'] == '/api/items/1'
    
    def test_e_commerce_product_catalog_with_pricing(self):
        resources = [
            MockResource({
                'id': 1,
                'name': 'Laptop',
                'base_price': 1000,
                'discount_percent': 10,
                'in_stock': True,
                'category': 'Electronics'
            }),
            MockResource({
                'id': 2,
                'name': 'Mouse',
                'base_price': 25,
                'discount_percent': 0,
                'in_stock': True,
                'category': 'Accessories'
            }),
            MockResource({
                'id': 3,
                'name': 'Keyboard',
                'base_price': 75,
                'discount_percent': 15,
                'in_stock': False,
                'category': 'Accessories'
            }),
        ]
        
        def callback(resource, request):
            discount_amount = resource.base_price * (resource.discount_percent / 100)
            final_price = resource.base_price - discount_amount
            
            return {
                'id': resource.id,
                'name': resource.name,
                'category': resource.category,
                'pricing': {
                    'original': resource.base_price,
                    'discount': discount_amount,
                    'final': final_price,
                },
                'availability': 'In Stock' if resource.in_stock else 'Out of Stock',
                'has_discount': resource.discount_percent > 0
            }
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert result[0]['pricing']['final'] == 900
        assert result[0]['has_discount'] is True
        assert result[1]['pricing']['final'] == 25
        assert result[1]['has_discount'] is False
        assert result[2]['availability'] == 'Out of Stock'
    
    def test_social_media_feed_with_engagement_metrics(self):
        resources = [
            MockResource({
                'id': 1,
                'author': 'user123',
                'content': 'Great day!',
                'likes': 150,
                'comments': 23,
                'shares': 5,
                'timestamp': '2024-01-15T10:30:00'
            }),
            MockResource({
                'id': 2,
                'author': 'user456',
                'content': 'Check this out',
                'likes': 89,
                'comments': 12,
                'shares': 2,
                'timestamp': '2024-01-15T11:00:00'
            }),
        ]
        
        def callback(resource, request):
            total_engagement = resource.likes + resource.comments + resource.shares
            engagement_rate = (total_engagement / max(resource.likes, 1)) * 100
            
            return {
                'id': resource.id,
                'author': resource.author,
                'content': resource.content[:50] + '...' if len(resource.content) > 50 else resource.content,
                'engagement': {
                    'likes': resource.likes,
                    'comments': resource.comments,
                    'shares': resource.shares,
                    'total': total_engagement,
                    'rate': round(engagement_rate, 2)
                },
                'posted_at': resource.timestamp
            }
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert result[0]['engagement']['total'] == 178
        assert result[0]['engagement']['rate'] == 118.67
        assert result[1]['engagement']['total'] == 103
    
    def test_multi_language_translation_transformation(self):
        resources = [
            MockResource({
                'id': 1,
                'title_en': 'Hello',
                'title_es': 'Hola',
                'title_fr': 'Bonjour',
                'description_en': 'Welcome',
                'description_es': 'Bienvenido',
                'description_fr': 'Bienvenue'
            }),
            MockResource({
                'id': 2,
                'title_en': 'Goodbye',
                'title_es': 'Adiós',
                'title_fr': 'Au revoir',
                'description_en': 'See you',
                'description_es': 'Hasta luego',
                'description_fr': 'À bientôt'
            }),
        ]
        
        def callback(resource, request):
            lang = request.headers.get('Accept-Language', 'en') if request else 'en'
            lang_suffix = f'_{lang}'
            
            return {
                'id': resource.id,
                'title': getattr(resource, f'title{lang_suffix}', resource.title_en),
                'description': getattr(resource, f'description{lang_suffix}', resource.description_en),
                'language': lang
            }
        
        en_request = MockRequest()
        en_request.headers = {'Accept-Language': 'en'}
        
        es_request = MockRequest()
        es_request.headers = {'Accept-Language': 'es'}
        
        collection = AnonymousResourceCollection(resources, callback)
        
        en_result = collection.to_dict(en_request)
        es_result = collection.to_dict(es_request)
        
        assert en_result[0]['title'] == 'Hello'
        assert es_result[0]['title'] == 'Hola'
        assert en_result[1]['description'] == 'See you'
        assert es_result[1]['description'] == 'Hasta luego'
    
    def test_analytics_dashboard_data_aggregation(self):
        resources = [
            MockResource({
                'id': 1,
                'date': '2024-01-01',
                'page_views': 1500,
                'unique_visitors': 800,
                'bounce_rate': 0.35,
                'avg_session_duration': 180
            }),
            MockResource({
                'id': 2,
                'date': '2024-01-02',
                'page_views': 1800,
                'unique_visitors': 950,
                'bounce_rate': 0.28,
                'avg_session_duration': 210
            }),
            MockResource({
                'id': 3,
                'date': '2024-01-03',
                'page_views': 2100,
                'unique_visitors': 1100,
                'bounce_rate': 0.22,
                'avg_session_duration': 240
            }),
        ]
        
        def callback(resource, request):
            engagement_score = (
                (resource.page_views / resource.unique_visitors) * 0.3 +
                ((1 - resource.bounce_rate) * 100) * 0.4 +
                (resource.avg_session_duration / 60) * 0.3
            )
            
            return {
                'date': resource.date,
                'metrics': {
                    'page_views': resource.page_views,
                    'unique_visitors': resource.unique_visitors,
                    'pages_per_visitor': round(resource.page_views / resource.unique_visitors, 2),
                    'bounce_rate_percent': round(resource.bounce_rate * 100, 2),
                    'avg_session_minutes': round(resource.avg_session_duration / 60, 2),
                },
                'engagement_score': round(engagement_score, 2),
                'performance': 'Excellent' if engagement_score > 30 else 'Good' if engagement_score > 20 else 'Fair'
            }
        
        collection = AnonymousResourceCollection(resources, callback)
        result = collection.to_dict()
        
        assert result[0]['metrics']['pages_per_visitor'] == 1.88
        assert result[1]['metrics']['bounce_rate_percent'] == 28.0
        assert result[2]['engagement_score'] > result[0]['engagement_score']
        assert result[2]['performance'] == 'Excellent'
    
    def test_permission_based_field_masking(self):
        resources = [
            MockResource({
                'id': 1,
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '555-1234',
                'ssn': '123-45-6789',
                'salary': 75000
            }),
            MockResource({
                'id': 2,
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': '555-5678',
                'ssn': '987-65-4321',
                'salary': 85000
            }),
        ]
        
        class PermissionRequest:
            def __init__(self, permissions):
                self.permissions = permissions
        
        def callback(resource, request):
            permissions = request.permissions if request else []
            
            data = {
                'id': resource.id,
                'name': resource.name,
            }
            
            if 'view_contact' in permissions:
                data['email'] = resource.email
                data['phone'] = resource.phone
            
            if 'view_sensitive' in permissions:
                data['ssn'] = resource.ssn
            else:
                data['ssn'] = '***-**-****'
            
            if 'view_salary' in permissions:
                data['salary'] = resource.salary
            
            return data
        
        collection = AnonymousResourceCollection(resources, callback)
        
        basic_request = PermissionRequest([])
        contact_request = PermissionRequest(['view_contact'])
        full_request = PermissionRequest(['view_contact', 'view_sensitive', 'view_salary'])
        
        basic_result = collection.to_dict(basic_request)
        contact_result = collection.to_dict(contact_request)
        full_result = collection.to_dict(full_request)
        
        assert 'email' not in basic_result[0]
        assert 'email' in contact_result[0]
        assert basic_result[0]['ssn'] == '***-**-****'
        assert full_result[0]['ssn'] == '123-45-6789'
        assert 'salary' not in contact_result[0]
        assert full_result[0]['salary'] == 75000
