import pytest
from larapy.database.orm.collection import Collection
from larapy.support.lazy_collection import LazyCollection


class TestCollectionLazyIntegration:
    
    def test_collection_to_lazy_and_back(self):
        original = Collection([1, 2, 3, 4, 5])
        lazy = original.lazy()
        eager = lazy.eager()
        
        assert isinstance(lazy, LazyCollection)
        assert isinstance(eager, Collection)
        assert eager.all() == [1, 2, 3, 4, 5]
    
    def test_complex_pipeline_eager_to_lazy(self):
        result = (Collection([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            .lazy()
            .filter(lambda x: x % 2 == 0)
            .map(lambda x: x * 2)
            .take(3)
            .eager()
            .map(lambda x: x + 10)
            .all())
        
        assert result == [14, 18, 22]
    
    def test_lazy_processing_large_dataset(self):
        def generate_numbers():
            for i in range(1, 1001):
                yield i
        
        result = (LazyCollection(generate_numbers)
            .filter(lambda x: x % 10 == 0)
            .map(lambda x: x // 10)
            .take(5)
            .all())
        
        assert result == [1, 2, 3, 4, 5]


class TestHigherOrderPipelines:
    
    def test_tap_pipe_when_chain(self):
        side_effects = []
        
        result = (Collection([1, 2, 3, 4, 5])
            .tap(lambda c: side_effects.append('start'))
            .when(lambda c: c.count() > 3, lambda c: c.take(3))
            .tap(lambda c: side_effects.append('after_when'))
            .pipe(lambda c: c.map(lambda x: x * 2))
            .tap(lambda c: side_effects.append('end'))
            .all())
        
        assert result == [2, 4, 6]
        assert side_effects == ['start', 'after_when', 'end']
    
    def test_conditional_transformation_pipeline(self):
        def process_users(collection, is_admin):
            return (collection
                .when(is_admin, 
                      lambda c: c.where('role', 'admin'),
                      lambda c: c.where('role', 'user'))
                .map(lambda user: {**user, 'processed': True}))
        
        users = Collection([
            {'id': 1, 'name': 'John', 'role': 'admin'},
            {'id': 2, 'name': 'Jane', 'role': 'user'},
            {'id': 3, 'name': 'Jack', 'role': 'admin'}
        ])
        
        admin_result = process_users(users, True)
        user_result = process_users(users, False)
        
        assert admin_result.count() == 2
        assert user_result.count() == 1
        assert all(u['processed'] for u in admin_result)
    
    def test_sliding_window_aggregation(self):
        prices = Collection([10, 12, 15, 14, 16, 18, 20])
        
        moving_averages = (prices
            .sliding(3)
            .map(lambda window: sum(window) / len(window))
            .all())
        
        expected = [12.33, 13.67, 15.0, 16.0, 18.0]
        
        for i, avg in enumerate(moving_averages):
            assert abs(avg - expected[i]) < 0.1
    
    def test_chunk_while_with_aggregation(self):
        transactions = Collection([
            {'date': '2025-01-01', 'amount': 100},
            {'date': '2025-01-01', 'amount': 50},
            {'date': '2025-01-02', 'amount': 75},
            {'date': '2025-01-02', 'amount': 125},
            {'date': '2025-01-03', 'amount': 200}
        ])
        
        daily_totals = (transactions
            .chunk_while(lambda curr, prev: curr['date'] == prev['date'])
            .map(lambda group: {
                'date': group[0]['date'],
                'total': sum(t['amount'] for t in group)
            })
            .all())
        
        assert len(daily_totals) == 3
        assert daily_totals[0]['total'] == 150
        assert daily_totals[1]['total'] == 200
        assert daily_totals[2]['total'] == 200


class TestMacrosWithRealUseCases:
    
    def test_custom_validation_macro(self):
        Collection.macro('all_valid', lambda self, validator: 
            all(validator(item) for item in self.all()))
        
        numbers = Collection([2, 4, 6, 8, 10])
        
        assert numbers.all_valid(lambda x: x % 2 == 0) is True
        assert numbers.all_valid(lambda x: x > 5) is False
    
    def test_custom_grouping_macro(self):
        Collection.macro('group_by_attribute', lambda self, attr: {
            value: [item for item in self.all() if item.get(attr) == value]
            for value in set(item.get(attr) for item in self.all())
        })
        
        users = Collection([
            {'name': 'John', 'role': 'admin'},
            {'name': 'Jane', 'role': 'user'},
            {'name': 'Jack', 'role': 'admin'},
            {'name': 'Jill', 'role': 'user'}
        ])
        
        grouped = users.group_by_attribute('role')
        
        assert len(grouped['admin']) == 2
        assert len(grouped['user']) == 2
    
    def test_mixin_for_statistics(self):
        class StatsMixin:
            def median(self):
                sorted_items = sorted(self.all())
                n = len(sorted_items)
                if n == 0:
                    return None
                if n % 2 == 0:
                    return (sorted_items[n//2 - 1] + sorted_items[n//2]) / 2
                return sorted_items[n//2]
            
            def mode(self):
                items = self.all()
                if not items:
                    return None
                frequency = {}
                for item in items:
                    frequency[item] = frequency.get(item, 0) + 1
                max_freq = max(frequency.values())
                return [k for k, v in frequency.items() if v == max_freq][0]
        
        Collection.mixin(StatsMixin)
        
        dataset = Collection([1, 2, 2, 3, 3, 3, 4, 5])
        
        assert dataset.median() == 3
        assert dataset.mode() == 3


class TestComplexDataTransformations:
    
    def test_nested_collection_flattening(self):
        nested = Collection([
            [
                {'id': 1, 'tags': ['python', 'web']},
                {'id': 2, 'tags': ['javascript', 'web']}
            ],
            [
                {'id': 3, 'tags': ['python', 'data']}
            ]
        ])
        
        all_tags = (nested
            .flatten()
            .lazy()
            .pluck('tags')
            .flatten()
            .unique()
            .all())
        
        assert set(all_tags) == {'python', 'web', 'javascript', 'data'}
    
    def test_data_pipeline_with_filtering_and_transformation(self):
        products = Collection([
            {'name': 'Laptop', 'price': 1000, 'stock': 5, 'category': 'electronics'},
            {'name': 'Phone', 'price': 500, 'stock': 0, 'category': 'electronics'},
            {'name': 'Desk', 'price': 200, 'stock': 3, 'category': 'furniture'},
            {'name': 'Chair', 'price': 100, 'stock': 10, 'category': 'furniture'},
        ])
        
        result = (products
            .where_not_null('stock')
            .where('stock', '>', 0)
            .where('category', 'electronics')
            .map(lambda p: {
                'name': p['name'],
                'discounted_price': p['price'] * 0.9,
                'available': p['stock'] > 0
            })
            .all())
        
        assert len(result) == 1
        assert result[0]['name'] == 'Laptop'
        assert result[0]['discounted_price'] == 900.0
    
    def test_aggregation_with_grouping(self):
        sales = Collection([
            {'product': 'A', 'region': 'North', 'amount': 100},
            {'product': 'B', 'region': 'North', 'amount': 150},
            {'product': 'A', 'region': 'South', 'amount': 200},
            {'product': 'B', 'region': 'South', 'amount': 175},
            {'product': 'A', 'region': 'North', 'amount': 125},
        ])
        
        north_total = (sales
            .where('region', 'North')
            .lazy()
            .pluck('amount')
            .sum())
        
        assert north_total == 375


class TestMemoryEfficiencyScenarios:
    
    def test_lazy_prevents_full_materialization(self):
        processed_count = [0]
        
        def expensive_operation(x):
            processed_count[0] += 1
            return x * 2
        
        def large_dataset():
            for i in range(10000):
                yield i
        
        result = (LazyCollection(large_dataset)
            .map(expensive_operation)
            .take(10)
            .all())
        
        assert len(result) == 10
        assert processed_count[0] <= 11
    
    def test_chunked_processing_with_lazy(self):
        def data_generator():
            for i in range(1, 101):
                yield i
        
        chunk_sums = (LazyCollection(data_generator)
            .chunk(10)
            .map(lambda chunk: sum(chunk))
            .all())
        
        assert len(chunk_sums) == 10
        assert chunk_sums[0] == sum(range(1, 11))
        assert chunk_sums[-1] == sum(range(91, 101))


class TestEdgeCasesAndBoundaries:
    
    def test_empty_collection_operations(self):
        empty = Collection([])
        
        assert empty.tap(lambda c: None).is_empty()
        assert empty.when_empty(lambda c: c.push(1)).count() == 1
        assert empty.pipe(lambda c: 'empty') == 'empty'
    
    def test_single_item_operations(self):
        single = Collection([42])
        
        assert single.sole() == 42
        assert single.sliding(2).all() == []
        assert single.chunk_while(lambda a, b: True).all() == [[42]]
    
    def test_complex_where_chains(self):
        data = Collection([
            {'id': 1, 'status': 'active', 'score': 85, 'email': 'a@test.com'},
            {'id': 2, 'status': 'inactive', 'score': 92, 'email': None},
            {'id': 3, 'status': 'active', 'score': 78, 'email': 'c@test.com'},
            {'id': 4, 'status': 'active', 'score': 95, 'email': 'd@test.com'},
        ])
        
        result = (data
            .where('status', 'active')
            .where_not_null('email')
            .where('score', '>=', 80)
            .all())
        
        assert len(result) == 2
        assert all(r['score'] >= 80 for r in result)
