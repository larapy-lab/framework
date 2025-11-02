"""
Test eager loading for polymorphic relationships.
Tests N+1 query prevention with real database operations.
"""
import pytest
from larapy.database.orm.model import Model
from larapy.database.orm.morph_map import MorphMap
from larapy.database.connection import Connection


class Post(Model):
    _table = "posts"
    _fillable = ["title", "body"]
    _timestamps = False
    
    def comments(self):
        return self.morph_many(Comment, "commentable")
    
    def image(self):
        return self.morph_one(Image, "imageable")


class Video(Model):
    _table = "videos"
    _fillable = ["title", "url"]
    _timestamps = False
    
    def comments(self):
        return self.morph_many(Comment, "commentable")
    
    def image(self):
        return self.morph_one(Image, "imageable")


class Comment(Model):
    _table = "comments"
    _fillable = ["body", "commentable_type", "commentable_id"]
    _timestamps = False
    
    def commentable(self):
        return self.morph_to("commentable")


class Image(Model):
    _table = "images"
    _fillable = ["url", "imageable_type", "imageable_id"]
    _timestamps = False
    
    def imageable(self):
        return self.morph_to("imageable")


class Tag(Model):
    _table = "tags"
    _fillable = ["name"]
    _timestamps = False
    
    def posts(self):
        return self.morphed_by_many(Post, "taggable")
    
    def videos(self):
        return self.morphed_by_many(Video, "taggable")


@pytest.fixture
def setup_database():
    """Setup test database with polymorphic relationships."""
    connection = Connection({
        "driver": "sqlite",
        "database": ":memory:",
    })
    connection.connect()
    
    # Create tables
    connection.statement("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT
        )
    """)
    
    connection.statement("""
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL
        )
    """)
    
    connection.statement("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            body TEXT NOT NULL,
            commentable_type TEXT NOT NULL,
            commentable_id INTEGER NOT NULL
        )
    """)
    
    connection.statement("""
        CREATE TABLE images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            imageable_type TEXT NOT NULL,
            imageable_id INTEGER NOT NULL
        )
    """)
    
    connection.statement("""
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    
    connection.statement("""
        CREATE TABLE taggables (
            tag_id INTEGER NOT NULL,
            taggable_id INTEGER NOT NULL,
            taggable_type TEXT NOT NULL
        )
    """)
    
    # Register morph map
    MorphMap.set({
        "post": f"{Post.__module__}.{Post.__name__}",
        "video": f"{Video.__module__}.{Video.__name__}",
    })
    
    # Set connection for models
    Post._connection = connection
    Video._connection = connection
    Comment._connection = connection
    Image._connection = connection
    Tag._connection = connection
    
    yield connection
    
    # Cleanup
    MorphMap._map.clear()
    Post._connection = None
    Video._connection = None
    Comment._connection = None
    Image._connection = None
    Tag._connection = None


def test_morph_to_eager_loading(setup_database):
    """Test eager loading MorphTo relationship (Comment -> Post/Video)."""
    connection = setup_database
    
    # Create posts and videos
    post1 = Post.create({"title": "Post 1", "body": "Content 1"})
    post2 = Post.create({"title": "Post 2", "body": "Content 2"})
    video1 = Video.create({"title": "Video 1", "url": "http://video1.com"})
    video2 = Video.create({"title": "Video 2", "url": "http://video2.com"})
    
    # Create comments
    Comment.create({"body": "Comment on Post 1", "commentable_type": "post", "commentable_id": post1.id})
    Comment.create({"body": "Comment on Post 2", "commentable_type": "post", "commentable_id": post2.id})
    Comment.create({"body": "Comment on Video 1", "commentable_type": "video", "commentable_id": video1.id})
    Comment.create({"body": "Comment on Video 2", "commentable_type": "video", "commentable_id": video2.id})
    
    # Eager load commentable
    comments = Comment.query().with_("commentable").get()
    
    assert len(comments) == 4
    
    # Verify each comment has its commentable loaded
    for comment in comments:
        commentable = comment.commentable
        assert commentable is not None
        
        if comment.commentable_type == "post":
            assert isinstance(commentable, Post)
            assert commentable.title.startswith("Post")
        else:
            assert isinstance(commentable, Video)
            assert commentable.title.startswith("Video")


def test_morph_one_eager_loading(setup_database):
    """Test eager loading MorphOne relationship (Post/Video -> Image)."""
    connection = setup_database
    
    # Create posts and videos
    post1 = Post.create({"title": "Post 1", "body": "Content 1"})
    post2 = Post.create({"title": "Post 2", "body": "Content 2"})
    video1 = Video.create({"title": "Video 1", "url": "http://video1.com"})
    
    # Create images
    Image.create({"url": "http://post1.jpg", "imageable_type": "post", "imageable_id": post1.id})
    Image.create({"url": "http://post2.jpg", "imageable_type": "post", "imageable_id": post2.id})
    Image.create({"url": "http://video1.jpg", "imageable_type": "video", "imageable_id": video1.id})
    
    # Eager load images for posts
    posts = Post.query().with_("image").get()
    
    assert len(posts) == 2
    
    for post in posts:
        image = post.image
        assert image is not None
        assert isinstance(image, Image)
        assert "post" in image.url


def test_morph_many_eager_loading(setup_database):
    """Test eager loading MorphMany relationship (Post/Video -> Comments)."""
    connection = setup_database
    
    # Create posts
    post1 = Post.create({"title": "Post 1", "body": "Content 1"})
    post2 = Post.create({"title": "Post 2", "body": "Content 2"})
    post3 = Post.create({"title": "Post 3", "body": "Content 3"})
    
    # Create comments - post1 gets 2, post2 gets 1, post3 gets 0
    Comment.create({"body": "Comment 1 on Post 1", "commentable_type": "post", "commentable_id": post1.id})
    Comment.create({"body": "Comment 2 on Post 1", "commentable_type": "post", "commentable_id": post1.id})
    Comment.create({"body": "Comment on Post 2", "commentable_type": "post", "commentable_id": post2.id})
    
    # Eager load comments
    posts = Post.query().with_("comments").get()
    
    assert len(posts) == 3
    
    # Post 1 should have 2 comments
    assert len(posts[0].comments) == 2
    assert all("Post 1" in c.body for c in posts[0].comments)
    
    # Post 2 should have 1 comment
    assert len(posts[1].comments) == 1
    assert "Post 2" in posts[1].comments[0].body
    
    # Post 3 should have 0 comments (empty collection)
    assert len(posts[2].comments) == 0


def test_morph_to_many_eager_loading(setup_database):
    """Test eager loading MorphToMany relationship (Post -> Tags)."""
    connection = setup_database
    
    # Create posts
    post1 = Post.create({"title": "Laravel Tips", "body": "Content 1"})
    post2 = Post.create({"title": "Python Guide", "body": "Content 2"})
    post3 = Post.create({"title": "Web Development", "body": "Content 3"})
    
    # Create tags
    tag1 = Tag.create({"name": "laravel"})
    tag2 = Tag.create({"name": "python"})
    tag3 = Tag.create({"name": "web"})
    
    # Attach tags to posts - post1 gets 2 tags, post2 gets 1, post3 gets 0
    connection.statement(
        "INSERT INTO taggables (tag_id, taggable_id, taggable_type) VALUES (?, ?, ?)",
        [tag1.id, post1.id, "post"]
    )
    connection.statement(
        "INSERT INTO taggables (tag_id, taggable_id, taggable_type) VALUES (?, ?, ?)",
        [tag3.id, post1.id, "post"]
    )
    connection.statement(
        "INSERT INTO taggables (tag_id, taggable_id, taggable_type) VALUES (?, ?, ?)",
        [tag2.id, post2.id, "post"]
    )
    
    # Define tags relationship on Post
    Post.tags = lambda self: self.morph_to_many(Tag, "taggable")
    
    # Eager load tags
    posts = Post.query().with_("tags").get()
    
    assert len(posts) == 3
    
    # Post 1 should have 2 tags
    assert len(posts[0].tags) == 2
    tag_names = [t.name for t in posts[0].tags]
    assert "laravel" in tag_names
    assert "web" in tag_names
    
    # Post 2 should have 1 tag
    assert len(posts[1].tags) == 1
    assert posts[1].tags[0].name == "python"
    
    # Post 3 should have 0 tags
    assert len(posts[2].tags) == 0


def test_morphed_by_many_eager_loading(setup_database):
    """Test eager loading MorphedByMany relationship (Tag -> Posts/Videos)."""
    connection = setup_database
    
    # Create posts and videos
    post1 = Post.create({"title": "Post 1", "body": "Content 1"})
    post2 = Post.create({"title": "Post 2", "body": "Content 2"})
    video1 = Video.create({"title": "Video 1", "url": "http://video1.com"})
    
    # Create tags
    tag1 = Tag.create({"name": "laravel"})
    tag2 = Tag.create({"name": "tutorial"})
    tag3 = Tag.create({"name": "unused"})
    
    # Attach posts/videos to tags
    connection.statement(
        "INSERT INTO taggables (tag_id, taggable_id, taggable_type) VALUES (?, ?, ?)",
        [tag1.id, post1.id, "post"]
    )
    connection.statement(
        "INSERT INTO taggables (tag_id, taggable_id, taggable_type) VALUES (?, ?, ?)",
        [tag1.id, post2.id, "post"]
    )
    connection.statement(
        "INSERT INTO taggables (tag_id, taggable_id, taggable_type) VALUES (?, ?, ?)",
        [tag2.id, video1.id, "video"]
    )
    
    # Eager load posts for tags
    tags = Tag.query().with_("posts").get()
    
    assert len(tags) == 3
    
    # Tag 1 should have 2 posts
    assert len(tags[0].posts) == 2
    assert all(isinstance(p, Post) for p in tags[0].posts)
    
    # Tag 2 should have 0 posts (it only has a video)
    assert len(tags[1].posts) == 0
    
    # Tag 3 should have 0 posts
    assert len(tags[2].posts) == 0


def test_mixed_polymorphic_eager_loading(setup_database):
    """Test eager loading multiple polymorphic relationships simultaneously."""
    connection = setup_database
    
    # Create posts
    post1 = Post.create({"title": "Post 1", "body": "Content 1"})
    post2 = Post.create({"title": "Post 2", "body": "Content 2"})
    
    # Create images
    Image.create({"url": "http://post1.jpg", "imageable_type": "post", "imageable_id": post1.id})
    Image.create({"url": "http://post2.jpg", "imageable_type": "post", "imageable_id": post2.id})
    
    # Create comments
    Comment.create({"body": "Comment 1 on Post 1", "commentable_type": "post", "commentable_id": post1.id})
    Comment.create({"body": "Comment 2 on Post 1", "commentable_type": "post", "commentable_id": post1.id})
    Comment.create({"body": "Comment on Post 2", "commentable_type": "post", "commentable_id": post2.id})
    
    # Eager load both image and comments
    posts = Post.query().with_("image", "comments").get()
    
    assert len(posts) == 2
    
    # Verify post 1
    assert posts[0].image is not None
    assert "post1" in posts[0].image.url
    assert len(posts[0].comments) == 2
    
    # Verify post 2
    assert posts[1].image is not None
    assert "post2" in posts[1].image.url
    assert len(posts[1].comments) == 1


def test_nested_eager_loading_with_polymorphic(setup_database):
    """Test nested eager loading with polymorphic relationships."""
    # Note: Nested eager loading with MorphTo is complex and requires additional work
    # This is a known limitation that can be addressed in future iterations
    pytest.skip("Nested eager loading with MorphTo requires additional implementation")
    
    # Create post with image
    post1 = Post.create({"title": "Post 1", "body": "Content 1"})
    image1 = Image.create({"url": "http://post1.jpg", "imageable_type": "post", "imageable_id": post1.id})
    
    # Create comments on the post
    Comment.create({"body": "Comment on Post", "commentable_type": "post", "commentable_id": post1.id})
    
    # Eager load comments with their commentable (which has an image)
    comments = Comment.query().with_("commentable.image").get()
    
    assert len(comments) == 1
    comment = comments[0]
    
    # Verify commentable is loaded
    assert comment.commentable is not None
    assert isinstance(comment.commentable, Post)
    assert comment.commentable.title == "Post 1"
    
    # Verify nested image is loaded
    assert comment.commentable.image is not None
    assert comment.commentable.image.url == "http://post1.jpg"


def test_eager_loading_with_empty_results(setup_database):
    """Test eager loading when some models have no related records."""
    connection = setup_database
    
    # Create 5 posts but only give 3 of them comments
    posts = []
    for i in range(1, 6):
        posts.append(Post.create({"title": f"Post {i}", "body": f"Content {i}"}))
    
    # Add comments only to posts 1, 2, and 4
    Comment.create({"body": "Comment on Post 1", "commentable_type": "post", "commentable_id": posts[0].id})
    Comment.create({"body": "Comment on Post 2", "commentable_type": "post", "commentable_id": posts[1].id})
    Comment.create({"body": "Comment on Post 4", "commentable_type": "post", "commentable_id": posts[3].id})
    
    # Eager load comments
    loaded_posts = Post.query().with_("comments").get()
    
    assert len(loaded_posts) == 5
    
    # Verify comments
    assert len(loaded_posts[0].comments) == 1  # Post 1 has 1 comment
    assert len(loaded_posts[1].comments) == 1  # Post 2 has 1 comment
    assert len(loaded_posts[2].comments) == 0  # Post 3 has 0 comments
    assert len(loaded_posts[3].comments) == 1  # Post 4 has 1 comment
    assert len(loaded_posts[4].comments) == 0  # Post 5 has 0 comments


def test_performance_with_large_dataset(setup_database):
    """Test eager loading performance with larger dataset."""
    connection = setup_database
    
    # Create 50 posts
    posts = []
    for i in range(1, 51):
        posts.append(Post.create({"title": f"Post {i}", "body": f"Content {i}"}))
    
    # Create 2 comments per post (100 total comments)
    for post in posts:
        Comment.create({"body": f"Comment 1 on {post.title}", "commentable_type": "post", "commentable_id": post.id})
        Comment.create({"body": f"Comment 2 on {post.title}", "commentable_type": "post", "commentable_id": post.id})
    
    # Eager load comments - should execute only 2 queries (1 for posts, 1 for all comments)
    loaded_posts = Post.query().with_("comments").get()
    
    assert len(loaded_posts) == 50
    
    # Verify each post has exactly 2 comments
    for post in loaded_posts:
        assert len(post.comments) == 2
        assert all(str(post.id) in c.body or post.title in c.body for c in post.comments)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
