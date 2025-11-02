import pytest
from unittest.mock import Mock
from larapy.http.resources import JsonResource


class User:
    def __init__(self, id, name, posts=None):
        self.id = id
        self.name = name
        if posts is not None:
            self.posts = posts


class Post:
    def __init__(self, id, title, author=None, comments=None):
        self.id = id
        self.title = title
        if author is not None:
            self.author = author
        if comments is not None:
            self.comments = comments


class Comment:
    def __init__(self, id, content, author=None):
        self.id = id
        self.content = content
        if author is not None:
            self.author = author


class UserResource(JsonResource):
    def to_array(self, request=None):
        return {
            'id': self.resource.id,
            'name': self.resource.name
        }


class PostResource(JsonResource):
    def to_array(self, request=None):
        result = {
            'id': self.resource.id,
            'title': self.resource.title
        }
        
        if hasattr(self.resource, 'author'):
            result['author'] = UserResource(self.resource.author).to_dict(request)
        
        if hasattr(self.resource, 'comments') and self.resource.comments:
            result['comments'] = [
                CommentResource(comment).to_dict(request)
                for comment in self.resource.comments
            ]
        
        return result


class CommentResource(JsonResource):
    def to_array(self, request=None):
        result = {
            'id': self.resource.id,
            'content': self.resource.content
        }
        
        if hasattr(self.resource, 'author'):
            result['author'] = UserResource(self.resource.author).to_dict(request)
        
        return result


class TestNestedResources:
    def test_single_nested_resource(self):
        author = User(1, 'John Doe')
        post = Post(1, 'My First Post', author=author)
        
        resource = PostResource(post)
        data = resource.to_dict()
        
        assert data['id'] == 1
        assert data['title'] == 'My First Post'
        assert data['author']['id'] == 1
        assert data['author']['name'] == 'John Doe'
    
    def test_multiple_nested_resources(self):
        author = User(1, 'John Doe')
        comments = [
            Comment(1, 'Great post!', author=User(2, 'Jane')),
            Comment(2, 'Thanks for sharing', author=User(3, 'Bob'))
        ]
        post = Post(1, 'My Post', author=author, comments=comments)
        
        resource = PostResource(post)
        data = resource.to_dict()
        
        assert len(data['comments']) == 2
        assert data['comments'][0]['content'] == 'Great post!'
        assert data['comments'][0]['author']['name'] == 'Jane'
        assert data['comments'][1]['author']['name'] == 'Bob'
    
    def test_deeply_nested_resources(self):
        comment_author = User(3, 'Bob')
        comment = Comment(1, 'Nice!', author=comment_author)
        
        post_author = User(1, 'John')
        post = Post(1, 'Title', author=post_author, comments=[comment])
        
        resource = PostResource(post)
        data = resource.to_dict()
        
        assert data['author']['name'] == 'John'
        assert data['comments'][0]['author']['name'] == 'Bob'
    
    def test_nested_collection(self):
        posts = [
            Post(1, 'Post 1', author=User(1, 'John')),
            Post(2, 'Post 2', author=User(2, 'Jane')),
            Post(3, 'Post 3', author=User(3, 'Bob'))
        ]
        
        collection = PostResource.collection(posts)
        data = collection.to_dict()
        
        assert len(data) == 3
        assert data[0]['author']['name'] == 'John'
        assert data[1]['author']['name'] == 'Jane'
        assert data[2]['author']['name'] == 'Bob'
    
    def test_conditional_nested_resources(self):
        post_without_author = Post(1, 'No Author Post')
        resource = PostResource(post_without_author)
        data = resource.to_dict()
        
        assert 'author' not in data
        assert data['id'] == 1
        assert data['title'] == 'No Author Post'
    
    def test_nested_with_when_loaded(self):
        class PostWithWhenLoaded(JsonResource):
            def to_array(self, request=None):
                return {
                    'id': self.resource.id,
                    'title': self.resource.title,
                    'author': UserResource(self.resource.author).to_dict(request) if hasattr(self.resource, 'author') else None,
                    'comments_count': len(self.resource.comments) if hasattr(self.resource, 'comments') and self.resource.comments else 0
                }
        
        author = User(1, 'John')
        comments = [Comment(1, 'C1'), Comment(2, 'C2')]
        post = Post(1, 'Title', author=author, comments=comments)
        
        resource = PostWithWhenLoaded(post)
        data = resource.to_dict()
        
        assert data['author']['id'] == 1
        assert data['comments_count'] == 2
    
    def test_empty_nested_collection(self):
        author = User(1, 'John')
        post = Post(1, 'Title', author=author, comments=[])
        resource = PostResource(post)
        data = resource.to_dict()
        
        assert 'comments' not in data
        assert data['author']['name'] == 'John'
    
    def test_nested_resource_with_none_value(self):
        post = Post(1, 'Title', author=None)
        
        class SafePostResource(JsonResource):
            def to_array(self, request=None):
                return {
                    'id': self.resource.id,
                    'title': self.resource.title,
                    'author': UserResource(self.resource.author).to_dict(request) if hasattr(self.resource, 'author') and self.resource.author else None
                }
        
        resource = SafePostResource(post)
        data = resource.to_dict()
        
        assert data['author'] is None
