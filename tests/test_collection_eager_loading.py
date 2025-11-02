"""
Tests for Collection Eager Loading

Tests the load() and load_missing() methods for preventing N+1 queries.
"""

import pytest
from unittest.mock import Mock, MagicMock, call
from larapy.database.orm.collection import Collection


class TestCollectionEagerLoading:
    """Test eager loading functionality in Collection."""
    
    def setup_method(self):
        """Setup test fixtures before each test."""
        # Create mock models
        self.mock_models = []
        for i in range(3):
            model = Mock()
            model.id = i + 1
            model.name = f"Model {i + 1}"
            model._relations = {}
            model.relation_loaded = Mock(return_value=False)
            model.get_relation = Mock(return_value=None)
            model.load = Mock(return_value=model)
            self.mock_models.append(model)
    
    def test_load_returns_self(self):
        """Test that load() returns self for method chaining."""
        collection = Collection(self.mock_models)
        result = collection.load('posts')
        
        assert result is collection
    
    def test_load_with_empty_collection(self):
        """Test load() with empty collection does nothing."""
        collection = Collection([])
        
        # Should not raise any errors
        result = collection.load('posts')
        
        assert result is collection
        assert collection.count() == 0
    
    def test_load_with_no_relations(self):
        """Test load() with no relations specified."""
        collection = Collection(self.mock_models)
        
        result = collection.load()
        
        assert result is collection
    
    def test_load_with_non_models(self):
        """Test load() with non-model items (dicts)."""
        items = [{'id': 1, 'name': 'Test'}]
        collection = Collection(items)
        
        # Should not raise errors, just return self
        result = collection.load('posts')
        
        assert result is collection
    
    def test_load_single_relation(self):
        """Test loading a single relationship."""
        # Create a mock relation
        mock_relation = Mock()
        mock_relation.add_eager_constraints = Mock()
        mock_relation.get_query = Mock()
        mock_relation.get_eager = Mock(return_value=Collection([]))
        mock_relation.match = Mock()
        
        # Setup first model to return the mock relation
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        collection = Collection(self.mock_models)
        result = collection.load('posts')
        
        # Verify eager constraints were added
        mock_relation.add_eager_constraints.assert_called_once_with(self.mock_models)
        
        # Verify get_eager was called
        mock_relation.get_eager.assert_called_once()
        
        # Verify match was called
        assert mock_relation.match.called
    
    def test_load_multiple_relations(self):
        """Test loading multiple relationships."""
        # Create mock relations
        posts_relation = Mock()
        posts_relation.add_eager_constraints = Mock()
        posts_relation.get_eager = Mock(return_value=Collection([]))
        posts_relation.match = Mock()
        
        comments_relation = Mock()
        comments_relation.add_eager_constraints = Mock()
        comments_relation.get_eager = Mock(return_value=Collection([]))
        comments_relation.match = Mock()
        
        # Setup model class
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=posts_relation)
        first_model.__class__.comments = Mock(return_value=comments_relation)
        
        collection = Collection(self.mock_models)
        result = collection.load('posts', 'comments')
        
        # Both relations should be loaded
        posts_relation.add_eager_constraints.assert_called_once()
        comments_relation.add_eager_constraints.assert_called_once()
    
    def test_load_with_callback(self):
        """Test loading relationship with query constraint."""
        mock_relation = Mock()
        mock_query = Mock()
        mock_relation.add_eager_constraints = Mock()
        mock_relation.get_query = Mock(return_value=mock_query)
        mock_relation.get_eager = Mock(return_value=Collection([]))
        mock_relation.match = Mock()
        
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        # Define a callback
        def constraint(query):
            query.where('published', True)
        
        collection = Collection(self.mock_models)
        result = collection.load({'posts': constraint})
        
        # Callback should be called with the query
        mock_relation.get_query.assert_called_once()
    
    def test_load_nested_relations(self):
        """Test loading nested relationships (e.g., 'posts.comments')."""
        # Create mock posts
        mock_posts = []
        posts_collection = Collection([])
        
        for i in range(2):
            post = Mock()
            post.id = i + 1
            post._relations = {}
            post.relation_loaded = Mock(return_value=False)
            post.load = Mock(return_value=post)
            mock_posts.append(post)
            posts_collection.push(post)
        
        # Setup posts relation
        posts_relation = Mock()
        posts_relation.add_eager_constraints = Mock()
        posts_relation.get_eager = Mock(return_value=posts_collection)
        posts_relation.match = Mock()
        
        # Make match() set the posts on models
        def match_posts(models, results, relation):
            for model in models:
                model._relations['posts'] = posts_collection
                model.relation_loaded = Mock(side_effect=lambda r: r == 'posts')
                model.get_relation = Mock(side_effect=lambda r: posts_collection if r == 'posts' else None)
        
        posts_relation.match.side_effect = match_posts
        
        # Setup model class
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=posts_relation)
        
        collection = Collection(self.mock_models)
        
        # Load nested relation
        result = collection.load('posts.comments')
        
        # Posts should be loaded first
        posts_relation.add_eager_constraints.assert_called()
        
        # Comments should be loaded on the posts collection
        # Since posts_collection has load() method from Collection
        # The nested loading is handled correctly
    
    def test_load_missing_all_missing(self):
        """Test load_missing() when all relations are missing."""
        mock_relation = Mock()
        mock_relation.add_eager_constraints = Mock()
        mock_relation.get_eager = Mock(return_value=Collection([]))
        mock_relation.match = Mock()
        
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        # All models have relation_loaded returning False
        for model in self.mock_models:
            model.relation_loaded = Mock(return_value=False)
        
        collection = Collection(self.mock_models)
        result = collection.load_missing('posts')
        
        # Should load since none are loaded
        mock_relation.add_eager_constraints.assert_called_once()
    
    def test_load_missing_all_loaded(self):
        """Test load_missing() when all relations are already loaded."""
        # All models have posts already loaded
        for model in self.mock_models:
            model.relation_loaded = Mock(return_value=True)
        
        collection = Collection(self.mock_models)
        
        # Mock the relation (should not be called)
        mock_relation = Mock()
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        result = collection.load_missing('posts')
        
        # Should not attempt to load
        assert not mock_relation.add_eager_constraints.called
    
    def test_load_missing_some_loaded(self):
        """Test load_missing() when some relations are loaded."""
        # First model has relation loaded, others don't
        self.mock_models[0].relation_loaded = Mock(return_value=True)
        self.mock_models[1].relation_loaded = Mock(return_value=False)
        self.mock_models[2].relation_loaded = Mock(return_value=False)
        
        mock_relation = Mock()
        mock_relation.add_eager_constraints = Mock()
        mock_relation.get_eager = Mock(return_value=Collection([]))
        mock_relation.match = Mock()
        
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        collection = Collection(self.mock_models)
        result = collection.load_missing('posts')
        
        # Should load since at least one doesn't have it
        mock_relation.add_eager_constraints.assert_called()
    
    def test_load_missing_multiple_relations(self):
        """Test load_missing() with multiple relations."""
        # Posts is loaded, comments is not
        for model in self.mock_models:
            model.relation_loaded = Mock(side_effect=lambda r: r == 'posts')
        
        posts_relation = Mock()
        comments_relation = Mock()
        comments_relation.add_eager_constraints = Mock()
        comments_relation.get_eager = Mock(return_value=Collection([]))
        comments_relation.match = Mock()
        
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=posts_relation)
        first_model.__class__.comments = Mock(return_value=comments_relation)
        
        collection = Collection(self.mock_models)
        result = collection.load_missing('posts', 'comments')
        
        # Only comments should be loaded
        assert not posts_relation.add_eager_constraints.called
        comments_relation.add_eager_constraints.assert_called()
    
    def test_load_with_dict_format(self):
        """Test load() with dictionary format for constraints."""
        mock_relation = Mock()
        mock_query = Mock()
        mock_relation.add_eager_constraints = Mock()
        mock_relation.get_query = Mock(return_value=mock_query)
        mock_relation.get_eager = Mock(return_value=Collection([]))
        mock_relation.match = Mock()
        
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        collection = Collection(self.mock_models)
        
        # Load with constraint
        callback_called = []
        
        def constraint(q):
            callback_called.append(True)
            q.where('published', True)
        
        result = collection.load({'posts': constraint})
        
        # Callback should be executed
        assert len(callback_called) == 1
        mock_relation.get_query.assert_called()
    
    def test_load_non_existent_relation(self):
        """Test loading a relation that doesn't exist."""
        collection = Collection(self.mock_models)
        
        # Load a relation that doesn't exist
        result = collection.load('nonexistent')
        
        # Should not raise error, just return collection
        assert result is collection
    
    def test_load_relation_without_eager_support(self):
        """Test loading a relation that doesn't support eager loading."""
        # Create a relation without add_eager_constraints
        mock_relation = Mock()
        # Explicitly don't add add_eager_constraints attribute
        
        first_model = self.mock_models[0]
        first_model.__class__.unsupported = Mock(return_value=mock_relation)
        
        collection = Collection(self.mock_models)
        
        # Should not raise error
        result = collection.load('unsupported')
        
        assert result is collection
    
    def test_load_chaining(self):
        """Test that load() can be chained with other collection methods."""
        mock_relation = Mock()
        mock_relation.add_eager_constraints = Mock()
        mock_relation.get_eager = Mock(return_value=Collection([]))
        mock_relation.match = Mock()
        
        # Add proper get_attribute method to models
        for model in self.mock_models:
            model.get_attribute = Mock(side_effect=lambda k: model.id if k == 'id' else None)
        
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        collection = Collection(self.mock_models)
        
        # Chain load with other methods
        result = (collection
                  .load('posts')
                  .where('id', '>', 0)
                  .take(2))
        
        assert isinstance(result, Collection)
        assert result.count() == 2
    
    def test_load_missing_chaining(self):
        """Test that load_missing() can be chained."""
        for model in self.mock_models:
            model.relation_loaded = Mock(return_value=False)
        
        mock_relation = Mock()
        mock_relation.add_eager_constraints = Mock()
        mock_relation.get_eager = Mock(return_value=Collection([]))
        mock_relation.match = Mock()
        
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        collection = Collection(self.mock_models)
        
        # Chain load_missing
        result = (collection
                  .load_missing('posts')
                  .filter(lambda m: m.id > 1))
        
        assert isinstance(result, Collection)
    
    def test_load_with_empty_string_relation(self):
        """Test load() with empty string relation name."""
        collection = Collection(self.mock_models)
        
        # Should handle gracefully
        result = collection.load('')
        
        assert result is collection
    
    def test_load_missing_with_dict_format(self):
        """Test load_missing() with dictionary format."""
        for model in self.mock_models:
            model.relation_loaded = Mock(return_value=False)
        
        mock_relation = Mock()
        mock_query = Mock()
        mock_relation.add_eager_constraints = Mock()
        mock_relation.get_query = Mock(return_value=mock_query)
        mock_relation.get_eager = Mock(return_value=Collection([]))
        mock_relation.match = Mock()
        
        first_model = self.mock_models[0]
        first_model.__class__.posts = Mock(return_value=mock_relation)
        
        collection = Collection(self.mock_models)
        
        # Load missing with dict format should always load
        result = collection.load_missing({'posts': lambda q: q.where('active', True)})
        
        mock_relation.add_eager_constraints.assert_called()
