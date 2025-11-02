import pytest
from unittest.mock import Mock
from larapy.http.resources import JsonResource, ConditionalValue, MergeValue, MissingValue


class User:
    def __init__(self, id, name, email, posts=None):
        self.id = id
        self.name = name
        self.email = email
        if posts is not None:
            self.posts = posts


class TestConditionalAttributes:
    def test_when_returns_value_if_true(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = JsonResource(user)
        
        value = resource.when(True, 'secret-value')
        
        assert value == 'secret-value'
    
    def test_when_returns_missing_if_false(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = JsonResource(user)
        
        value = resource.when(False, 'secret-value')
        
        assert isinstance(value, MissingValue)
    
    def test_when_returns_default_if_false(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = JsonResource(user)
        
        value = resource.when(False, 'secret-value', 'default-value')
        
        assert value == 'default-value'
    
    def test_when_loaded_checks_relationship(self):
        user = User(1, 'John Doe', 'john@example.com', posts=[Mock(), Mock()])
        resource = JsonResource(user)
        
        posts = resource.when_loaded('posts')
        
        assert posts is not None
        assert len(posts) == 2
    
    def test_when_loaded_returns_missing_if_not_loaded(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = JsonResource(user)
        
        posts = resource.when_loaded('posts')
        
        assert isinstance(posts, MissingValue)
    
    def test_when_loaded_returns_default_if_not_loaded(self):
        user = User(1, 'John Doe', 'john@example.com')
        resource = JsonResource(user)
        
        posts = resource.when_loaded('posts', default=[])
        
        assert posts == []
    
    def test_conditional_value_lazy_evaluation(self):
        call_count = [0]
        
        def condition():
            call_count[0] += 1
            return True
        
        def value():
            call_count[0] += 10
            return 'value'
        
        conditional = ConditionalValue(condition, value)
        
        assert call_count[0] == 0
        
        result = conditional.resolve()
        
        assert result == 'value'
        assert call_count[0] == 11
    
    def test_conditional_value_with_false_condition(self):
        conditional = ConditionalValue(False, 'value')
        result = conditional.resolve()
        
        assert isinstance(result, MissingValue)
    
    def test_merge_value_returns_data(self):
        merge = MergeValue({'key1': 'value1', 'key2': 'value2'})
        result = merge.resolve()
        
        assert result == {'key1': 'value1', 'key2': 'value2'}
    
    def test_missing_value_representation(self):
        missing = MissingValue()
        
        assert repr(missing) == '<MissingValue>'
        assert not missing
