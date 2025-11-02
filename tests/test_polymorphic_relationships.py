import pytest
from larapy.database.orm.model import Model
from larapy.database.orm.morph_map import MorphMap
from larapy.database.connection import Connection


class Post(Model):
    _table = "posts"
    _fillable = ["id", "title", "body"]
    
    def comments(self):
        return self.morph_many(Comment, "commentable")
    
    def image(self):
        return self.morph_one(Image, "imageable")


class Video(Model):
    _table = "videos"
    _fillable = ["id", "title", "url"]
    
    def comments(self):
        return self.morph_many(Comment, "commentable")


class Comment(Model):
    _table = "comments"
    _fillable = ["id", "body", "commentable_id", "commentable_type"]
    
    def commentable(self):
        return self.morph_to()


class Image(Model):
    _table = "images"
    _fillable = ["id", "url", "imageable_id", "imageable_type"]
    
    def imageable(self):
        return self.morph_to()


@pytest.fixture
def connection():
    conn = Connection({'driver': 'sqlite', 'database': ':memory:'})
    conn.connect()
    
    conn.statement("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            body TEXT NOT NULL,
            commentable_id INTEGER,
            commentable_type TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            imageable_id INTEGER NOT NULL,
            imageable_type TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    MorphMap.set({
        "post": "tests.test_polymorphic_relationships.Post",
        "video": "tests.test_polymorphic_relationships.Video",
    })
    
    return conn


def test_morph_to_retrieves_correct_parent_model(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test Post", "body": "Content"})
    
    comment = Comment.create({
        "body": "Great post!",
        "commentable_id": post.get_key(),
        "commentable_type": "post"
    })
    
    loaded_comment = Comment.find(comment.get_key())
    commentable = loaded_comment.commentable().get_results()
    
    assert commentable is not None
    assert isinstance(commentable, Post)
    assert commentable.get_key() == post.get_key()
    assert commentable.get_attribute("title") == "Test Post"


def test_morph_to_returns_none_for_null_morph_type(connection):
    Comment._connection = connection
    
    comment = Comment.create({
        "body": "Orphan comment",
        "commentable_id": 999,
        "commentable_type": ""
    })
    
    loaded_comment = Comment.find(comment.get_key())
    commentable = loaded_comment.commentable().get_results()
    
    assert commentable is None


def test_morph_one_creates_child_with_correct_morph_fields(connection):
    Post._connection = connection
    Image._connection = connection
    
    post = Post.create({"title": "Test Post", "body": "Content"})
    
    image = post.image().create({"url": "https://example.com/image.jpg"})
    
    assert image.get_attribute("imageable_id") == post.get_key()
    assert image.get_attribute("imageable_type") == "post"
    assert image.get_attribute("url") == "https://example.com/image.jpg"


def test_morph_many_returns_collection_of_children(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test Post", "body": "Content"})
    
    post.comments().create({"body": "First comment"})
    post.comments().create({"body": "Second comment"})
    
    comments = post.comments().get_results()
    
    assert len(comments) == 2
    assert comments[0].get_attribute("commentable_id") == post.get_key()
    assert comments[0].get_attribute("commentable_type") == "post"
    assert comments[1].get_attribute("commentable_id") == post.get_key()


def test_morph_relationships_save_parent_type_correctly(connection):
    Video._connection = connection
    Comment._connection = connection
    
    video = Video.create({"title": "Tutorial Video", "url": "https://example.com/video.mp4"})
    
    comment = video.comments().create({"body": "Excellent tutorial!"})
    
    assert comment.get_attribute("commentable_type") == "video"
    assert comment.get_attribute("commentable_id") == video.get_key()


def test_morph_relationships_save_parent_id_correctly(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    comment = Comment.create({
        "body": "Comment",
        "commentable_type": "post",
        "commentable_id": post.get_key()
    })
    
    loaded = Comment.find(comment.get_key())
    assert loaded.get_attribute("commentable_id") == post.get_key()


def test_multiple_morph_relationships_on_single_model(connection):
    Post._connection = connection
    Comment._connection = connection
    Image._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    comment = post.comments().create({"body": "Comment"})
    image = post.image().create({"url": "image.jpg"})
    
    assert comment.get_attribute("commentable_id") == post.get_key()
    assert image.get_attribute("imageable_id") == post.get_key()


def test_morph_to_with_different_parent_types(connection):
    Post._connection = connection
    Video._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Post", "body": "Content"})
    video = Video.create({"title": "Video", "url": "video.mp4"})
    
    post_comment = Comment.create({
        "body": "Post comment",
        "commentable_id": post.get_key(),
        "commentable_type": "post"
    })
    
    video_comment = Comment.create({
        "body": "Video comment",
        "commentable_id": video.get_key(),
        "commentable_type": "video"
    })
    
    loaded_post_comment = Comment.find(post_comment.get_key())
    loaded_video_comment = Comment.find(video_comment.get_key())
    
    post_parent = loaded_post_comment.commentable().get_results()
    video_parent = loaded_video_comment.commentable().get_results()
    
    assert isinstance(post_parent, Post)
    assert isinstance(video_parent, Video)
    assert post_parent.get_key() == post.get_key()
    assert video_parent.get_key() == video.get_key()


def test_morph_many_create_many(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    comments = post.comments().create_many([
        {"body": "First"},
        {"body": "Second"},
        {"body": "Third"}
    ])
    
    assert len(comments) == 3
    for comment in comments:
        assert comment.get_attribute("commentable_id") == post.get_key()
        assert comment.get_attribute("commentable_type") == "post"


def test_morph_to_associate(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    comment = Comment({"body": "Comment"}, connection)
    comment.commentable().associate(post)
    comment.save()
    
    assert comment.get_attribute("commentable_id") == post.get_key()
    assert comment.get_attribute("commentable_type") == "post"


def test_morph_to_dissociate(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    comment = Comment.create({
        "body": "Comment",
        "commentable_id": post.get_key(),
        "commentable_type": "post"
    })
    
    comment.commentable().dissociate()
    comment.save()
    
    loaded = Comment.find(comment.get_key())
    assert loaded.get_attribute("commentable_id") is None
    assert loaded.get_attribute("commentable_type") is None


def test_morph_map_resolves_aliases_to_classes(connection):
    assert MorphMap.resolve_type("post") == "tests.test_polymorphic_relationships.Post"
    assert MorphMap.resolve_type("video") == "tests.test_polymorphic_relationships.Video"


def test_morph_map_resolves_classes_to_aliases(connection):
    assert MorphMap.get_morph_alias("tests.test_polymorphic_relationships.Post") == "post"
    assert MorphMap.get_morph_alias("tests.test_polymorphic_relationships.Video") == "video"


def test_morph_map_handles_unknown_types(connection):
    unknown_class = MorphMap.get_morph_alias("unknown.Class")
    assert unknown_class is None or unknown_class == "unknown.Class"


def test_morph_one_returns_none_when_no_child(connection):
    Post._connection = connection
    Image._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    image = post.image().get_results()
    
    assert image is None


def test_morph_many_returns_empty_collection_when_no_children(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    comments = post.comments().get_results()
    
    assert len(comments) == 0


def test_morph_relationship_with_where_constraint(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    post.comments().create({"body": "First comment"})
    post.comments().create({"body": "Second comment"})
    
    filtered_comments = post.comments().where("body", "LIKE", "%First%").get_results()
    
    assert len(filtered_comments) == 1
    assert filtered_comments[0].get_attribute("body") == "First comment"


def test_morph_to_handles_missing_parent(connection):
    Comment._connection = connection
    
    comment = Comment.create({
        "body": "Comment",
        "commentable_id": 999,
        "commentable_type": "post"
    })
    
    commentable = comment.commentable().get_results()
    
    assert commentable is None
