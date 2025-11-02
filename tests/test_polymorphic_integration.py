import pytest
from larapy.database.orm.model import Model
from larapy.database.orm.morph_map import MorphMap
from larapy.database.connection import Connection


class Post(Model):
    _table = "posts"
    _fillable = ["id", "title", "body", "status"]
    
    def comments(self):
        return self.morph_many(Comment, "commentable")
    
    def likes(self):
        return self.morph_many(Like, "likeable")
    
    def tags(self):
        return self.morph_to_many(Tag, "taggable")


class Video(Model):
    _table = "videos"
    _fillable = ["id", "title", "url", "status"]
    
    def comments(self):
        return self.morph_many(Comment, "commentable")
    
    def tags(self):
        return self.morph_to_many(Tag, "taggable")


class Photo(Model):
    _table = "photos"
    _fillable = ["id", "url", "caption"]
    
    def tags(self):
        return self.morph_to_many(Tag, "taggable")


class User(Model):
    _table = "users"
    _fillable = ["id", "name", "email"]
    
    def image(self):
        return self.morph_one(Image, "imageable")
    
    def likes(self):
        return self.morph_many(Like, "likeable")


class Product(Model):
    _table = "products"
    _fillable = ["id", "name", "price"]
    
    def images(self):
        return self.morph_many(Image, "imageable")


class Comment(Model):
    _table = "comments"
    _fillable = ["id", "body", "commentable_id", "commentable_type", "user_id"]
    
    def commentable(self):
        return self.morph_to()
    
    def likes(self):
        return self.morph_many(Like, "likeable")


class Image(Model):
    _table = "images"
    _fillable = ["id", "url", "imageable_id", "imageable_type"]
    
    def imageable(self):
        return self.morph_to()


class Like(Model):
    _table = "likes"
    _fillable = ["id", "user_id", "likeable_id", "likeable_type"]
    
    def likeable(self):
        return self.morph_to()


class Tag(Model):
    _table = "tags"
    _fillable = ["id", "name"]
    
    def posts(self):
        return self.morphed_by_many(Post, "taggable")
    
    def videos(self):
        return self.morphed_by_many(Video, "taggable")


class Notification(Model):
    _table = "notifications"
    _fillable = ["id", "message", "notifiable_id", "notifiable_type", "read_at"]
    
    def notifiable(self):
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
            status TEXT DEFAULT 'draft',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'published',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            caption TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            body TEXT NOT NULL,
            user_id INTEGER,
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
            imageable_id INTEGER,
            imageable_type TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            likeable_id INTEGER,
            likeable_type TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            notifiable_id INTEGER,
            notifiable_type TEXT,
            read_at TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    conn.statement("""
        CREATE TABLE taggables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_id INTEGER NOT NULL,
            taggable_id INTEGER NOT NULL,
            taggable_type TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    MorphMap.set({
        "post": "tests.test_polymorphic_integration.Post",
        "video": "tests.test_polymorphic_integration.Video",
        "photo": "tests.test_polymorphic_integration.Photo",
        "user": "tests.test_polymorphic_integration.User",
        "product": "tests.test_polymorphic_integration.Product",
        "comment": "tests.test_polymorphic_integration.Comment",
    })
    
    return conn


def test_blog_comments_complete_workflow(connection):
    Post._connection = connection
    Video._connection = connection
    Comment._connection = connection
    User._connection = connection
    
    user = User.create({"name": "John Doe", "email": "john@example.com"})
    
    post = Post.create({
        "title": "Larapy Performance Tips",
        "body": "Here are some tips for optimizing your Larapy application...",
        "status": "published"
    })
    
    video = Video.create({
        "title": "Larapy Tutorial Series",
        "url": "https://example.com/larapy-tutorial.mp4",
        "status": "published"
    })
    
    post_comment1 = post.comments().create({
        "body": "Great tips! Very helpful.",
        "user_id": user.get_key()
    })
    
    post_comment2 = post.comments().create({
        "body": "Can you explain more about query optimization?",
        "user_id": user.get_key()
    })
    
    video_comment = video.comments().create({
        "body": "Excellent tutorial! Looking forward to part 2.",
        "user_id": user.get_key()
    })
    
    assert isinstance(post_comment1.commentable().get_results(), Post)
    assert post_comment1.commentable().get_results().get_key() == post.get_key()
    
    assert isinstance(video_comment.commentable().get_results(), Video)
    assert video_comment.commentable().get_results().get_key() == video.get_key()
    
    post_comments = post.comments().get_results()
    assert len(post_comments) == 2
    assert all(c.get_attribute("commentable_type") == "post" for c in post_comments)
    
    video_comments = video.comments().get_results()
    assert len(video_comments) == 1
    assert video_comments[0].get_attribute("commentable_type") == "video"
    
    published_post_comments = post.comments().where("body", "LIKE", "%tips%").get_results()
    assert len(published_post_comments) == 1
    assert "tips" in published_post_comments[0].get_attribute("body")


def test_image_system_users_and_products(connection):
    User._connection = connection
    Product._connection = connection
    Image._connection = connection
    
    user = User.create({"name": "Jane Smith", "email": "jane@example.com"})
    
    avatar = user.image().create({"url": "https://example.com/avatars/jane.jpg"})
    
    assert avatar.get_attribute("imageable_id") == user.get_key()
    assert avatar.get_attribute("imageable_type") == "user"
    
    loaded_avatar = user.image().get_results()
    assert loaded_avatar is not None
    assert loaded_avatar.get_key() == avatar.get_key()
    
    product = Product.create({"name": "Laptop", "price": 999.99})
    
    product_image1 = product.images().create({"url": "https://example.com/products/laptop-1.jpg"})
    product_image2 = product.images().create({"url": "https://example.com/products/laptop-2.jpg"})
    
    product_images = product.images().get_results()
    assert len(product_images) == 2
    assert all(img.get_attribute("imageable_type") == "product" for img in product_images)
    
    loaded_image = Image.find(product_image1.get_key())
    if loaded_image:
        owner = loaded_image.imageable().get_results()
        assert isinstance(owner, Product)
        assert owner.get_key() == product.get_key()


def test_activity_feed_likes_on_multiple_types(connection):
    User._connection = connection
    Post._connection = connection
    Comment._connection = connection
    Like._connection = connection
    
    user = User.create({"name": "Alice", "email": "alice@example.com"})
    
    post = Post.create({"title": "Amazing Post", "body": "Content", "status": "published"})
    
    comment = post.comments().create({"body": "Nice post!", "user_id": user.get_key()})
    
    post_like = Like.create({
        "user_id": user.get_key(),
        "likeable_id": post.get_key(),
        "likeable_type": "post"
    })
    
    comment_like = Like.create({
        "user_id": user.get_key(),
        "likeable_id": comment.get_key(),
        "likeable_type": "comment"
    })
    
    post_like_target = post_like.likeable().get_results()
    comment_like_target = comment_like.likeable().get_results()
    
    assert isinstance(post_like_target, Post)
    assert isinstance(comment_like_target, Comment)
    assert post_like_target.get_key() == post.get_key()
    assert comment_like_target.get_key() == comment.get_key()
    
    post_likes = post.likes().get_results()
    comment_likes = comment.likes().get_results()
    
    assert len(post_likes) == 1
    assert len(comment_likes) == 1


def test_notification_system_for_multiple_events(connection):
    User._connection = connection
    Post._connection = connection
    Comment._connection = connection
    Notification._connection = connection
    
    user1 = User.create({"name": "Bob", "email": "bob@example.com"})
    user2 = User.create({"name": "Carol", "email": "carol@example.com"})
    
    post = Post.create({"title": "Test Post", "body": "Content", "status": "published"})
    
    comment = post.comments().create({"body": "Great post!", "user_id": user2.get_key()})
    
    notif1 = Notification.create({
        "message": "New comment on your post",
        "notifiable_id": post.get_key(),
        "notifiable_type": "post"
    })
    
    notif2 = Notification.create({
        "message": "User followed you",
        "notifiable_id": user1.get_key(),
        "notifiable_type": "user"
    })
    
    notif1_subject = notif1.notifiable().get_results()
    notif2_subject = notif2.notifiable().get_results()
    
    assert isinstance(notif1_subject, Post)
    assert isinstance(notif2_subject, User)
    assert notif1_subject.get_key() == post.get_key()
    assert notif2_subject.get_key() == user1.get_key()


def test_nested_polymorphic_relationships(connection):
    Post._connection = connection
    Comment._connection = connection
    Like._connection = connection
    User._connection = connection
    
    user = User.create({"name": "Dave", "email": "dave@example.com"})
    post = Post.create({"title": "Nested Test", "body": "Content", "status": "published"})
    
    comment = post.comments().create({"body": "First level comment", "user_id": user.get_key()})
    
    comment_like = comment.likes().create({
        "user_id": user.get_key()
    })
    
    assert comment_like.get_attribute("likeable_type") == "comment"
    assert comment_like.get_attribute("likeable_id") == comment.get_key()
    
    liked_comment = comment_like.likeable().get_results()
    assert isinstance(liked_comment, Comment)
    
    commented_post = liked_comment.commentable().get_results()
    assert isinstance(commented_post, Post)
    assert commented_post.get_key() == post.get_key()


def test_polymorphic_constraints_with_status_filter(connection):
    Post._connection = connection
    Video._connection = connection
    Comment._connection = connection
    
    published_post = Post.create({"title": "Published", "body": "Content", "status": "published"})
    draft_post = Post.create({"title": "Draft", "body": "Content", "status": "draft"})
    
    published_post.comments().create({"body": "Comment on published"})
    draft_post.comments().create({"body": "Comment on draft"})
    
    all_comments = Comment.query().where("commentable_type", "post").get()
    assert len(all_comments) == 2


def test_morph_to_associate_and_switch_parent(connection):
    Post._connection = connection
    Video._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Post", "body": "Content"})
    video = Video.create({"title": "Video", "url": "video.mp4"})
    
    comment = Comment.create({"body": "Flexible comment"})
    
    comment.commentable().associate(post)
    comment.save()
    
    assert comment.get_attribute("commentable_type") == "post"
    assert comment.get_attribute("commentable_id") == post.get_key()
    
    comment.commentable().associate(video)
    comment.save()
    
    assert comment.get_attribute("commentable_type") == "video"
    assert comment.get_attribute("commentable_id") == video.get_key()
    
    loaded_parent = comment.commentable().get_results()
    assert isinstance(loaded_parent, Video)


def test_bulk_polymorphic_creation(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Bulk Test", "body": "Content"})
    
    comments = post.comments().create_many([
        {"body": "First comment"},
        {"body": "Second comment"},
        {"body": "Third comment"},
        {"body": "Fourth comment"},
        {"body": "Fifth comment"}
    ])
    
    assert len(comments) == 5
    for comment in comments:
        assert comment.get_attribute("commentable_id") == post.get_key()
        assert comment.get_attribute("commentable_type") == "post"
        assert comment._exists is True


def test_polymorphic_with_multiple_morph_types_on_single_table(connection):
    User._connection = connection
    Product._connection = connection
    Image._connection = connection
    
    user = User.create({"name": "Eve", "email": "eve@example.com"})
    product = Product.create({"name": "Phone", "price": 599.99})
    
    user_image = user.image().create({"url": "user-avatar.jpg"})
    product_image = product.images().create({"url": "phone-1.jpg"})
    
    all_images = Image.query().get()
    assert len(all_images) == 2
    
    user_images_only = Image.query().where("imageable_type", "user").get()
    product_images_only = Image.query().where("imageable_type", "product").get()
    
    assert len(user_images_only) == 1
    assert len(product_images_only) == 1


def test_count_polymorphic_children(connection):
    Post._connection = connection
    Video._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Popular Post", "body": "Content"})
    video = Video.create({"title": "Popular Video", "url": "video.mp4"})
    
    for i in range(5):
        post.comments().create({"body": f"Comment {i}"})
    
    for i in range(3):
        video.comments().create({"body": f"Comment {i}"})
    
    post_comment_count = len(post.comments().get_results())
    video_comment_count = len(video.comments().get_results())
    
    assert post_comment_count == 5
    assert video_comment_count == 3


def test_polymorphic_with_ordering(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    comment1 = post.comments().create({"body": "Alpha"})
    comment2 = post.comments().create({"body": "Zeta"})
    comment3 = post.comments().create({"body": "Beta"})
    
    ordered_comments = post.comments().order_by("body", "asc").get_results()
    
    assert ordered_comments[0].get_attribute("body") == "Alpha"
    assert ordered_comments[1].get_attribute("body") == "Beta"
    assert ordered_comments[2].get_attribute("body") == "Zeta"


def test_morph_relationship_deletion_cascade_behavior(connection):
    Post._connection = connection
    Comment._connection = connection
    
    post = Post.create({"title": "Test", "body": "Content"})
    
    comment1 = post.comments().create({"body": "Comment 1"})
    comment2 = post.comments().create({"body": "Comment 2"})
    
    comment_ids = [comment1.get_key(), comment2.get_key()]
    
    # Delete post - comments remain but are orphaned
    post.delete()
    
    # Comments still exist in database
    for comment_id in comment_ids:
        comment = Comment.find(comment_id)
        assert comment is not None
        assert comment.get_attribute("commentable_id") == post.get_key()


def test_polymorphic_null_handling(connection):
    Comment._connection = connection
    
    orphan_comment = Comment.create({
        "body": "Orphan comment",
        "commentable_id": None,
        "commentable_type": None
    })
    
    parent = orphan_comment.commentable().get_results()
    assert parent is None


def test_multiple_polymorphic_relationships_different_names(connection):
    User._connection = connection
    Image._connection = connection
    Like._connection = connection
    
    user = User.create({"name": "Frank", "email": "frank@example.com"})
    
    avatar = user.image().create({"url": "avatar.jpg"})
    like = user.likes().create({"user_id": user.get_key()})
    
    assert avatar.get_attribute("imageable_type") == "user"
    assert avatar.get_attribute("imageable_id") == user.get_key()
    
    assert like.get_attribute("likeable_type") == "user"
    assert like.get_attribute("likeable_id") == user.get_key()


def test_polymorphic_query_performance_single_query_per_type(connection):
    Post._connection = connection
    Comment._connection = connection
    
    posts = [Post.create({"title": f"Post {i}", "body": "Content"}) for i in range(10)]
    
    for post in posts:
        post.comments().create({"body": f"Comment on {post.get_attribute('title')}"})
    
    all_comments = Comment.query().get()
    
    assert len(all_comments) == 10
    for comment in all_comments:
        parent = comment.commentable().get_results()
        assert parent is not None
        assert isinstance(parent, Post)


def test_morph_to_many_tag_system(connection):
    Post._connection = connection
    Video._connection = connection
    Tag._connection = connection
    
    post = Post.create({"title": "Tagged Post", "body": "Content"})
    video = Video.create({"title": "Tagged Video", "url": "video.mp4"})
    
    tag1 = Tag.create({"name": "python"})
    tag2 = Tag.create({"name": "laravel"})
    tag3 = Tag.create({"name": "tutorial"})
    
    post.tags().attach([tag1.get_key(), tag2.get_key()])
    video.tags().attach([tag2.get_key(), tag3.get_key()])
    
    post_tags = post.tags().get_results()
    assert len(post_tags) == 2
    assert set(t.get_attribute("name") for t in post_tags) == {"python", "laravel"}
    
    video_tags = video.tags().get_results()
    assert len(video_tags) == 2
    assert set(t.get_attribute("name") for t in video_tags) == {"laravel", "tutorial"}


def test_morphed_by_many_retrieve_posts_and_videos(connection):
    Post._connection = connection
    Video._connection = connection
    Tag._connection = connection
    
    post1 = Post.create({"title": "Post 1", "body": "Content"})
    post2 = Post.create({"title": "Post 2", "body": "Content"})
    video = Video.create({"title": "Video 1", "url": "video.mp4"})
    
    tag = Tag.create({"name": "featured"})
    
    post1.tags().attach(tag.get_key())
    post2.tags().attach(tag.get_key())
    video.tags().attach(tag.get_key())
    
    featured_posts = tag.posts().get_results()
    assert len(featured_posts) == 2
    
    featured_videos = tag.videos().get_results()
    assert len(featured_videos) == 1


def test_morph_to_many_detach(connection):
    Post._connection = connection
    Tag._connection = connection
    
    post = Post.create({"title": "Post", "body": "Content"})
    
    tag1 = Tag.create({"name": "tag1"})
    tag2 = Tag.create({"name": "tag2"})
    tag3 = Tag.create({"name": "tag3"})
    
    post.tags().attach([tag1.get_key(), tag2.get_key(), tag3.get_key()])
    
    tags = post.tags().get_results()
    assert len(tags) == 3
    
    post.tags().detach([tag2.get_key()])
    
    tags = post.tags().get_results()
    assert len(tags) == 2
    assert set(t.get_attribute("name") for t in tags) == {"tag1", "tag3"}


def test_morph_to_many_sync(connection):
    Post._connection = connection
    Tag._connection = connection
    
    post = Post.create({"title": "Post", "body": "Content"})
    
    tag1 = Tag.create({"name": "tag1"})
    tag2 = Tag.create({"name": "tag2"})
    tag3 = Tag.create({"name": "tag3"})
    tag4 = Tag.create({"name": "tag4"})
    
    post.tags().attach([tag1.get_key(), tag2.get_key()])
    
    result = post.tags().sync([tag2.get_key(), tag3.get_key(), tag4.get_key()])
    
    assert tag1.get_key() in result["detached"]
    assert tag3.get_key() in result["attached"]
    assert tag4.get_key() in result["attached"]
    
    tags = post.tags().get_results()
    assert len(tags) == 3
    assert set(t.get_attribute("name") for t in tags) == {"tag2", "tag3", "tag4"}


def test_morph_to_many_toggle(connection):
    Post._connection = connection
    Tag._connection = connection
    
    post = Post.create({"title": "Post", "body": "Content"})
    
    tag1 = Tag.create({"name": "tag1"})
    tag2 = Tag.create({"name": "tag2"})
    
    post.tags().attach(tag1.get_key())
    
    result = post.tags().toggle([tag1.get_key(), tag2.get_key()])
    
    assert tag1.get_key() in result["detached"]
    assert tag2.get_key() in result["attached"]
    
    tags = post.tags().get_results()
    assert len(tags) == 1
    assert tags[0].get_attribute("name") == "tag2"


def test_morph_to_many_with_pivot_attributes(connection):
    Post._connection = connection
    Tag._connection = connection
    
    post = Post.create({"title": "Post", "body": "Content"})
    tag = Tag.create({"name": "featured"})
    
    post.tags().attach(tag.get_key())
    
    tags = post.tags().get_results()
    assert len(tags) == 1
    assert hasattr(tags[0], "pivot")
    assert tags[0].pivot.taggable_id == post.get_key()
    assert tags[0].pivot.taggable_type == "post"


def test_bidirectional_morph_many_to_many(connection):
    Post._connection = connection
    Video._connection = connection
    Tag._connection = connection
    
    post = Post.create({"title": "Laravel Tips", "body": "Content"})
    video = Video.create({"title": "Laravel Tutorial", "url": "tutorial.mp4"})
    
    tag = Tag.create({"name": "laravel"})
    
    post.tags().attach(tag.get_key())
    video.tags().attach(tag.get_key())
    
    laravel_posts = tag.posts().get_results()
    laravel_videos = tag.videos().get_results()
    
    assert len(laravel_posts) == 1
    assert laravel_posts[0].get_attribute("title") == "Laravel Tips"
    
    assert len(laravel_videos) == 1
    assert laravel_videos[0].get_attribute("title") == "Laravel Tutorial"
