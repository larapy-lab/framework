import pytest
from larapy.database.orm.collection import Collection


class TestCollectionMacros:
    
    def test_macro_registers_custom_method(self):
        Collection.macro('to_upper', lambda self: self.map(lambda x: x.upper()))
        
        collection = Collection(['john', 'jane', 'jack'])
        result = collection.to_upper()
        
        assert result.all() == ['JOHN', 'JANE', 'JACK']
    
    def test_macro_with_arguments(self):
        Collection.macro('multiply_by', lambda self, factor: self.map(lambda x: x * factor))
        
        collection = Collection([1, 2, 3])
        result = collection.multiply_by(3)
        
        assert result.all() == [3, 6, 9]
    
    def test_macro_returns_collection_for_chaining(self):
        Collection.macro('double', lambda self: self.map(lambda x: x * 2))
        Collection.macro('add_ten', lambda self: self.map(lambda x: x + 10))
        
        collection = Collection([1, 2, 3])
        result = collection.double().add_ten()
        
        assert result.all() == [12, 14, 16]
    
    def test_has_macro_checks_existence(self):
        Collection.macro('custom_method', lambda self: self)
        
        assert Collection.has_macro('custom_method') is True
        assert Collection.has_macro('nonexistent_method') is False
    
    def test_macro_non_collection_return_value(self):
        Collection.macro('sum_all', lambda self: sum(self.all()))
        
        collection = Collection([1, 2, 3, 4, 5])
        result = collection.sum_all()
        
        assert result == 15
    
    def test_mixin_registers_multiple_methods(self):
        class StatsMixin:
            def average(self):
                items = self.all()
                return sum(items) / len(items) if items else 0
            
            def range_value(self):
                items = self.all()
                if not items:
                    return 0
                return max(items) - min(items)
        
        Collection.mixin(StatsMixin)
        
        collection = Collection([10, 20, 30, 40, 50])
        
        assert collection.average() == 30.0
        assert collection.range_value() == 40
    
    def test_mixin_only_registers_public_methods(self):
        class TestMixin:
            def public_method(self):
                return "public"
            
            def _private_method(self):
                return "private"
        
        Collection.mixin(TestMixin)
        
        collection = Collection([])
        
        assert Collection.has_macro('public_method') is True
        assert Collection.has_macro('_private_method') is False
    
    def test_macro_with_kwargs(self):
        Collection.macro('filter_range', lambda self, min_val=0, max_val=100: 
            self.filter(lambda x: min_val <= x <= max_val))
        
        collection = Collection([5, 15, 25, 35, 45, 55])
        result = collection.filter_range(min_val=20, max_val=50)
        
        assert result.all() == [25, 35, 45]
    
    def test_macro_attribute_error_for_unknown_method(self):
        collection = Collection([1, 2, 3])
        
        with pytest.raises(AttributeError):
            collection.unknown_macro_method()
    
    def test_macro_access_collection_properties(self):
        Collection.macro('is_long', lambda self: self.count() > 5)
        
        short_collection = Collection([1, 2, 3])
        long_collection = Collection([1, 2, 3, 4, 5, 6, 7])
        
        assert short_collection.is_long() is False
        assert long_collection.is_long() is True


class TestMacroableComplexScenarios:
    
    def test_macro_with_nested_collection_operations(self):
        Collection.macro('chunk_and_sum', lambda self, size: 
            self.chunk(size).map(lambda chunk: sum(chunk)))
        
        collection = Collection([1, 2, 3, 4, 5, 6])
        result = collection.chunk_and_sum(2)
        
        assert result.all() == [3, 7, 11]
    
    def test_mixin_with_complex_logic(self):
        class AnalyticsMixin:
            def percentile(self, p):
                sorted_items = sorted(self.all())
                if not sorted_items:
                    return None
                index = int(len(sorted_items) * p / 100)
                return sorted_items[min(index, len(sorted_items) - 1)]
            
            def std_dev(self):
                items = self.all()
                if not items:
                    return 0
                mean = sum(items) / len(items)
                variance = sum((x - mean) ** 2 for x in items) / len(items)
                return variance ** 0.5
        
        Collection.mixin(AnalyticsMixin)
        
        collection = Collection([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        
        assert collection.percentile(50) == 60
        assert round(collection.std_dev(), 2) == 28.72
    
    def test_macro_preserves_collection_type(self):
        Collection.macro('positive_only', lambda self: self.filter(lambda x: x > 0))
        
        collection = Collection([-2, -1, 0, 1, 2, 3])
        result = collection.positive_only()
        
        assert isinstance(result, Collection)
        assert result.all() == [1, 2, 3]
