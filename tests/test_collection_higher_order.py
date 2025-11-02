import pytest
from larapy.database.orm.collection import Collection


class TestCollectionTap:
    
    def test_tap_passes_collection_and_returns_self(self):
        collection = Collection([1, 2, 3])
        result = collection.tap(lambda c: c.push(4))
        
        assert result is collection
        assert result.all() == [1, 2, 3, 4]
    
    def test_tap_allows_side_effects_without_breaking_chain(self):
        side_effects = []
        
        result = (Collection([1, 2, 3])
            .tap(lambda c: side_effects.append(c.count()))
            .map(lambda x: x * 2)
            .tap(lambda c: side_effects.append(c.count()))
            .all())
        
        assert result == [2, 4, 6]
        assert side_effects == [3, 3]


class TestCollectionPipe:
    
    def test_pipe_transforms_collection(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.pipe(lambda c: c.sum())
        
        assert result == 15
    
    def test_pipe_can_return_any_type(self):
        collection = Collection([{'name': 'John'}, {'name': 'Jane'}])
        result = collection.pipe(lambda c: ', '.join(c.pluck('name')))
        
        assert result == 'John, Jane'
    
    def test_pipe_through_sequential_transformations(self):
        def double_all(c):
            return c.map(lambda x: x * 2)
        
        def sum_all(c):
            total = 0
            for x in c:
                total += x
            return total
        
        result = Collection([1, 2, 3]).pipe_through([double_all, sum_all])
        
        assert result == 12


class TestCollectionWhen:
    
    def test_when_with_true_condition(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.when(True, lambda c: c.filter(lambda x: x > 2))
        
        assert result.all() == [3, 4, 5]
    
    def test_when_with_false_condition(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.when(False, lambda c: c.filter(lambda x: x > 2))
        
        assert result.all() == [1, 2, 3, 4, 5]
    
    def test_when_with_callable_condition(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.when(
            lambda c: c.count() > 3,
            lambda c: c.take(3)
        )
        
        assert result.all() == [1, 2, 3]
    
    def test_when_with_default_callback(self):
        collection = Collection([1, 2, 3])
        result = collection.when(
            False,
            lambda c: c.map(lambda x: x * 2),
            lambda c: c.map(lambda x: x * 3)
        )
        
        assert result.all() == [3, 6, 9]
    
    def test_when_returns_original_if_callback_doesnt_return_collection(self):
        collection = Collection([1, 2, 3])
        result = collection.when(True, lambda c: c.sum())
        
        assert result is collection


class TestCollectionUnless:
    
    def test_unless_with_false_condition(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.unless(False, lambda c: c.filter(lambda x: x > 2))
        
        assert result.all() == [3, 4, 5]
    
    def test_unless_with_true_condition(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.unless(True, lambda c: c.filter(lambda x: x > 2))
        
        assert result.all() == [1, 2, 3, 4, 5]
    
    def test_unless_with_callable_condition(self):
        collection = Collection([1, 2])
        result = collection.unless(
            lambda c: c.count() > 3,
            lambda c: c.map(lambda x: x * 2)
        )
        
        assert result.all() == [2, 4]


class TestCollectionWhenEmpty:
    
    def test_when_empty_executes_on_empty_collection(self):
        collection = Collection([])
        result = collection.when_empty(lambda c: c.push(1).push(2))
        
        assert result.all() == [1, 2]
    
    def test_when_empty_skips_on_non_empty_collection(self):
        collection = Collection([1, 2, 3])
        result = collection.when_empty(lambda c: c.push(4))
        
        assert result.all() == [1, 2, 3]


class TestCollectionWhenNotEmpty:
    
    def test_when_not_empty_executes_on_non_empty_collection(self):
        collection = Collection([1, 2, 3])
        result = collection.when_not_empty(lambda c: c.map(lambda x: x * 2))
        
        assert result.all() == [2, 4, 6]
    
    def test_when_not_empty_skips_on_empty_collection(self):
        collection = Collection([])
        result = collection.when_not_empty(lambda c: c.push(1))
        
        assert result.all() == []


class TestCollectionSole:
    
    def test_sole_returns_single_item(self):
        collection = Collection([{'id': 1, 'name': 'John'}])
        result = collection.sole()
        
        assert result == {'id': 1, 'name': 'John'}
    
    def test_sole_with_key_value(self):
        collection = Collection([
            {'id': 1, 'role': 'admin'},
            {'id': 2, 'role': 'user'},
            {'id': 3, 'role': 'user'}
        ])
        result = collection.sole('role', 'admin')
        
        assert result['id'] == 1
    
    def test_sole_throws_on_empty_collection(self):
        collection = Collection([])
        
        with pytest.raises(ValueError, match="No items found"):
            collection.sole()
    
    def test_sole_throws_on_multiple_items(self):
        collection = Collection([1, 2, 3])
        
        with pytest.raises(ValueError, match="Multiple items found"):
            collection.sole()


class TestCollectionEnsure:
    
    def test_ensure_validates_single_type(self):
        collection = Collection([1, 2, 3, 4])
        result = collection.ensure(int)
        
        assert result is collection
    
    def test_ensure_validates_multiple_types(self):
        collection = Collection([1, 2.5, 3, 4.0])
        result = collection.ensure((int, float))
        
        assert result is collection
    
    def test_ensure_throws_on_wrong_type(self):
        collection = Collection([1, 2, 'three', 4])
        
        with pytest.raises(TypeError):
            collection.ensure(int)


class TestCollectionDot:
    
    def test_dot_flattens_nested_dict(self):
        collection = Collection([
            {'user': {'name': 'John', 'email': 'john@example.com'}},
            {'user': {'name': 'Jane', 'email': 'jane@example.com'}}
        ])
        result = collection.dot()
        
        assert result.all() == [
            {'user.name': 'John', 'user.email': 'john@example.com'},
            {'user.name': 'Jane', 'user.email': 'jane@example.com'}
        ]
    
    def test_dot_handles_deeply_nested_dict(self):
        collection = Collection([
            {'a': {'b': {'c': 1}}}
        ])
        result = collection.dot()
        
        assert result.first() == {'a.b.c': 1}


class TestCollectionUndot:
    
    def test_undot_expands_dot_notation(self):
        collection = Collection([
            {'user.name': 'John', 'user.email': 'john@example.com'}
        ])
        result = collection.undot()
        
        expected = {'user': {'name': 'John', 'email': 'john@example.com'}}
        assert result.first() == expected


class TestCollectionSliding:
    
    def test_sliding_creates_windows(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.sliding(2)
        
        assert result.all() == [[1, 2], [2, 3], [3, 4], [4, 5]]
    
    def test_sliding_with_custom_size(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.sliding(3)
        
        assert result.all() == [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
    
    def test_sliding_with_step(self):
        collection = Collection([1, 2, 3, 4, 5, 6])
        result = collection.sliding(2, 2)
        
        assert result.all() == [[1, 2], [3, 4], [5, 6]]


class TestCollectionChunkWhile:
    
    def test_chunk_while_groups_consecutive(self):
        collection = Collection([1, 2, 2, 3, 3, 3, 1])
        result = collection.chunk_while(lambda curr, prev: curr == prev)
        
        assert result.all() == [[1], [2, 2], [3, 3, 3], [1]]
    
    def test_chunk_while_with_custom_condition(self):
        collection = Collection([1, 3, 5, 2, 4, 6])
        result = collection.chunk_while(lambda curr, prev: curr % 2 == prev % 2)
        
        assert result.all() == [[1, 3, 5], [2, 4, 6]]


class TestCollectionTakeUntil:
    
    def test_take_until_condition_met(self):
        collection = Collection([1, 2, 3, 4, 5, 6])
        result = collection.take_until(lambda x: x >= 4)
        
        assert result.all() == [1, 2, 3]
    
    def test_take_until_condition_never_met(self):
        collection = Collection([1, 2, 3])
        result = collection.take_until(lambda x: x > 10)
        
        assert result.all() == [1, 2, 3]


class TestCollectionTakeWhile:
    
    def test_take_while_condition_true(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.take_while(lambda x: x < 4)
        
        assert result.all() == [1, 2, 3]


class TestCollectionSkipUntil:
    
    def test_skip_until_condition_met(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.skip_until(lambda x: x >= 4)
        
        assert result.all() == [4, 5]


class TestCollectionSkipWhile:
    
    def test_skip_while_condition_true(self):
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.skip_while(lambda x: x < 4)
        
        assert result.all() == [4, 5]


class TestCollectionLazy:
    
    def test_lazy_converts_to_lazy_collection(self):
        collection = Collection([1, 2, 3, 4, 5])
        lazy = collection.lazy()
        
        from larapy.support.lazy_collection import LazyCollection
        assert isinstance(lazy, LazyCollection)
        assert lazy.all() == [1, 2, 3, 4, 5]


class TestCollectionFlatten:
    
    def test_flatten_nested_lists(self):
        collection = Collection([[1, 2], [3, 4], [5]])
        result = collection.flatten()
        
        assert result.all() == [1, 2, 3, 4, 5]
    
    def test_flatten_with_depth(self):
        collection = Collection([[[1, 2]], [[3, 4]]])
        result = collection.flatten(2)
        
        assert result.all() == [1, 2, 3, 4]


class TestCollectionWhere:
    
    def test_where_with_single_argument(self):
        collection = Collection([
            {'id': 1, 'active': True},
            {'id': 2, 'active': False},
            {'id': 3, 'active': True}
        ])
        result = collection.where('active')
        
        assert result.count() == 2
    
    def test_where_with_two_arguments(self):
        collection = Collection([
            {'id': 1, 'role': 'admin'},
            {'id': 2, 'role': 'user'},
            {'id': 3, 'role': 'admin'}
        ])
        result = collection.where('role', 'admin')
        
        assert result.count() == 2
    
    def test_where_with_operator(self):
        collection = Collection([
            {'id': 1, 'age': 25},
            {'id': 2, 'age': 30},
            {'id': 3, 'age': 35}
        ])
        result = collection.where('age', '>', 28)
        
        assert result.count() == 2
        assert result.first()['age'] == 30


class TestCollectionWhereIn:
    
    def test_where_in_filters_by_list(self):
        collection = Collection([
            {'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}
        ])
        result = collection.where_in('id', [2, 4])
        
        assert result.count() == 2


class TestCollectionWhereNotIn:
    
    def test_where_not_in_excludes_values(self):
        collection = Collection([
            {'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}
        ])
        result = collection.where_not_in('id', [2, 4])
        
        assert result.count() == 2


class TestCollectionWhereNull:
    
    def test_where_null_finds_none_values(self):
        collection = Collection([
            {'id': 1, 'email': 'john@example.com'},
            {'id': 2, 'email': None},
            {'id': 3, 'email': 'jane@example.com'}
        ])
        result = collection.where_null('email')
        
        assert result.count() == 1


class TestCollectionWhereNotNull:
    
    def test_where_not_null_excludes_none_values(self):
        collection = Collection([
            {'id': 1, 'email': 'john@example.com'},
            {'id': 2, 'email': None},
            {'id': 3, 'email': 'jane@example.com'}
        ])
        result = collection.where_not_null('email')
        
        assert result.count() == 2
