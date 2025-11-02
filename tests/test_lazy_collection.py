import pytest
from larapy.support.lazy_collection import LazyCollection


class TestLazyCollectionBasics:
    
    def test_create_from_list(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.all() == [1, 2, 3, 4, 5]
    
    def test_create_from_generator(self):
        def gen():
            for i in range(1, 6):
                yield i
        
        lazy = LazyCollection(gen())
        assert lazy.all() == [1, 2, 3, 4, 5]
    
    def test_create_from_callable(self):
        def gen():
            for i in range(1, 6):
                yield i
        
        lazy = LazyCollection(gen)
        assert lazy.all() == [1, 2, 3, 4, 5]
    
    def test_map_transformation(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        result = lazy.map(lambda x: x * 2).all()
        assert result == [2, 4, 6, 8, 10]
    
    def test_filter_items(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        result = lazy.filter(lambda x: x > 2).all()
        assert result == [3, 4, 5]
    
    def test_filter_without_callback(self):
        lazy = LazyCollection([0, 1, False, 2, None, 3])
        result = lazy.filter().all()
        assert result == [1, 2, 3]
    
    def test_take_items(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        result = lazy.take(3).all()
        assert result == [1, 2, 3]
    
    def test_skip_items(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        result = lazy.skip(2).all()
        assert result == [3, 4, 5]
    
    def test_chain_operations(self):
        lazy = LazyCollection([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = lazy.filter(lambda x: x % 2 == 0).map(lambda x: x * 2).take(3).all()
        assert result == [4, 8, 12]


class TestLazyCollectionConditional:
    
    def test_take_while(self):
        lazy = LazyCollection([1, 2, 3, 4, 5, 6])
        result = lazy.take_while(lambda x: x < 4).all()
        assert result == [1, 2, 3]
    
    def test_take_until(self):
        lazy = LazyCollection([1, 2, 3, 4, 5, 6])
        result = lazy.take_until(lambda x: x >= 4).all()
        assert result == [1, 2, 3]
    
    def test_skip_while(self):
        lazy = LazyCollection([1, 2, 3, 4, 5, 6])
        result = lazy.skip_while(lambda x: x < 4).all()
        assert result == [4, 5, 6]
    
    def test_skip_until(self):
        lazy = LazyCollection([1, 2, 3, 4, 5, 6])
        result = lazy.skip_until(lambda x: x >= 4).all()
        assert result == [4, 5, 6]


class TestLazyCollectionChunking:
    
    def test_chunk_items(self):
        lazy = LazyCollection([1, 2, 3, 4, 5, 6, 7])
        result = lazy.chunk(3).all()
        assert result == [[1, 2, 3], [4, 5, 6], [7]]
    
    def test_chunk_while(self):
        lazy = LazyCollection([1, 2, 2, 3, 3, 3, 1])
        result = lazy.chunk_while(lambda curr, prev: curr == prev).all()
        assert result == [[1], [2, 2], [3, 3, 3], [1]]
    
    def test_sliding_window(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        result = lazy.sliding(2).all()
        assert result == [[1, 2], [2, 3], [3, 4], [4, 5]]
    
    def test_sliding_window_with_step(self):
        lazy = LazyCollection([1, 2, 3, 4, 5, 6])
        result = lazy.sliding(3, 2).all()
        assert result == [[1, 2, 3], [3, 4, 5]]


class TestLazyCollectionAggregates:
    
    def test_count(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.count() == 5
    
    def test_first(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.first() == 1
    
    def test_first_with_callback(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.first(lambda x: x > 3) == 4
    
    def test_first_with_default(self):
        lazy = LazyCollection([1, 2, 3])
        assert lazy.first(lambda x: x > 10, default=99) == 99
    
    def test_last(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.last() == 5
    
    def test_last_with_callback(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.last(lambda x: x < 4) == 3
    
    def test_sum(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.sum() == 15
    
    def test_sum_with_key(self):
        lazy = LazyCollection([
            {'price': 10}, 
            {'price': 20}, 
            {'price': 30}
        ])
        assert lazy.sum('price') == 60
    
    def test_avg(self):
        lazy = LazyCollection([10, 20, 30, 40])
        assert lazy.avg() == 25.0
    
    def test_avg_with_key(self):
        lazy = LazyCollection([
            {'score': 80}, 
            {'score': 90}, 
            {'score': 70}
        ])
        assert lazy.avg('score') == 80.0
    
    def test_min(self):
        lazy = LazyCollection([5, 3, 8, 1, 9])
        assert lazy.min() == 1
    
    def test_min_with_key(self):
        lazy = LazyCollection([
            {'age': 25}, 
            {'age': 18}, 
            {'age': 30}
        ])
        assert lazy.min('age') == 18
    
    def test_max(self):
        lazy = LazyCollection([5, 3, 8, 1, 9])
        assert lazy.max() == 9
    
    def test_max_with_key(self):
        lazy = LazyCollection([
            {'age': 25}, 
            {'age': 18}, 
            {'age': 30}
        ])
        assert lazy.max('age') == 30


class TestLazyCollectionUtilities:
    
    def test_tap_does_not_affect_chain(self):
        side_effects = []
        
        lazy = LazyCollection([1, 2, 3, 4, 5])
        result = lazy.tap(lambda x: side_effects.append(x)).map(lambda x: x * 2).all()
        
        assert result == [2, 4, 6, 8, 10]
        assert side_effects == [1, 2, 3, 4, 5]
    
    def test_each_iterates_without_collecting(self):
        side_effects = []
        
        lazy = LazyCollection([1, 2, 3])
        lazy.each(lambda x: side_effects.append(x * 2))
        
        assert side_effects == [2, 4, 6]
    
    def test_contains_with_value(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.contains(3) is True
        assert lazy.contains(10) is False
    
    def test_contains_with_callback(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        assert lazy.contains(lambda x: x > 3) is True
        assert lazy.contains(lambda x: x > 10) is False
    
    def test_is_empty(self):
        assert LazyCollection([]).is_empty() is True
        assert LazyCollection([1]).is_empty() is False
    
    def test_is_not_empty(self):
        assert LazyCollection([]).is_not_empty() is False
        assert LazyCollection([1]).is_not_empty() is True
    
    def test_pluck_dict_items(self):
        lazy = LazyCollection([
            {'name': 'John', 'age': 30},
            {'name': 'Jane', 'age': 25}
        ])
        result = lazy.pluck('name').all()
        assert result == ['John', 'Jane']
    
    def test_flatten(self):
        lazy = LazyCollection([[1, 2], [3, 4], [5]])
        result = lazy.flatten().all()
        assert result == [1, 2, 3, 4, 5]
    
    def test_flatten_with_depth(self):
        lazy = LazyCollection([[[1, 2]], [[3, 4]]])
        result = lazy.flatten(1).all()
        assert result == [[1, 2], [3, 4]]
    
    def test_unique(self):
        lazy = LazyCollection([1, 2, 2, 3, 3, 3, 4])
        result = lazy.unique().all()
        assert result == [1, 2, 3, 4]
    
    def test_unique_with_key(self):
        lazy = LazyCollection([
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'},
            {'id': 1, 'name': 'Jack'}
        ])
        result = lazy.unique(lambda x: x['id']).all()
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[1]['id'] == 2
    
    def test_zip_collections(self):
        lazy = LazyCollection([1, 2, 3])
        result = lazy.zip(['a', 'b', 'c']).all()
        assert result == [(1, 'a'), (2, 'b'), (3, 'c')]


class TestLazyCollectionMemoryEfficiency:
    
    def test_deferred_evaluation(self):
        executed = []
        
        def track_execution(x):
            executed.append(x)
            return x * 2
        
        lazy = LazyCollection([1, 2, 3, 4, 5])
        transformed = lazy.map(track_execution)
        
        assert len(executed) == 0
        
        result = transformed.take(2).all()
        
        assert result == [2, 4]
        assert len(executed) == 2
    
    def test_remember_caches_results(self):
        call_count = [0]
        
        def expensive_operation(x):
            call_count[0] += 1
            return x * 2
        
        lazy = LazyCollection([1, 2, 3])
        remembered = lazy.map(expensive_operation).remember()
        
        first_pass = remembered.all()
        second_pass = remembered.all()
        
        assert first_pass == second_pass
        assert call_count[0] == 3
    
    def test_lazy_does_not_load_all_at_once(self):
        loaded_items = []
        
        def generator():
            for i in range(1000):
                loaded_items.append(i)
                yield i
        
        lazy = LazyCollection(generator)
        result = lazy.take(5).all()
        
        assert result == [0, 1, 2, 3, 4]
        assert len(loaded_items) <= 6


class TestLazyCollectionStaticFactories:
    
    def test_make_factory(self):
        lazy = LazyCollection.make([1, 2, 3])
        assert lazy.all() == [1, 2, 3]
    
    def test_times_factory(self):
        lazy = LazyCollection.times(5)
        assert lazy.all() == [1, 2, 3, 4, 5]
    
    def test_times_with_callback(self):
        lazy = LazyCollection.times(5, lambda i: i * 2)
        assert lazy.all() == [2, 4, 6, 8, 10]
    
    def test_range_factory(self):
        lazy = LazyCollection.range(1, 5)
        assert lazy.all() == [1, 2, 3, 4, 5]
    
    def test_range_with_step(self):
        lazy = LazyCollection.range(0, 10, 2)
        assert lazy.all() == [0, 2, 4, 6, 8, 10]


class TestLazyCollectionEagerConversion:
    
    def test_eager_converts_to_collection(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        eager = lazy.eager()
        
        from larapy.database.orm.collection import Collection
        assert isinstance(eager, Collection)
        assert eager.all() == [1, 2, 3, 4, 5]
    
    def test_to_list(self):
        lazy = LazyCollection([1, 2, 3])
        assert lazy.to_list() == [1, 2, 3]


class TestLazyCollectionIterability:
    
    def test_iteration(self):
        lazy = LazyCollection([1, 2, 3, 4, 5])
        result = []
        for item in lazy:
            result.append(item)
        assert result == [1, 2, 3, 4, 5]
    
    def test_multiple_iterations(self):
        lazy = LazyCollection([1, 2, 3])
        
        first = list(lazy)
        second = list(lazy)
        
        assert first == [1, 2, 3]
        assert second == [1, 2, 3]
