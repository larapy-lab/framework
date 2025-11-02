from typing import Optional
from larapy.database.orm.relationships.has_many_through import HasManyThrough


class HasOneThrough(HasManyThrough):
    
    def get_results(self):
        if not self._constraints_applied:
            self.add_constraints()
            
        results = self._query.limit(1).get()
        
        if not results:
            return None
            
        return self._hydrate_model(results[0])
    
    def get_eager(self):
        results = self._query.get()
        
        if not results:
            return []
            
        return [self._hydrate_model(row) for row in results]
    
    def match(self, models, results, relation: str):
        dictionary = self._build_dictionary(results)
        
        for model in models:
            key = model.get_attribute(self._get_local_key())
            if key in dictionary:
                model.set_relation(relation, dictionary[key])
            else:
                model.set_relation(relation, None)
                
        return models
    
    def _build_dictionary(self, results):
        dictionary = {}
        first_key = self._get_first_key()
        
        for result in results:
            pivot_data = getattr(result, '_pivot_data', {})
            key = pivot_data.get(first_key)
            
            if key is not None and key not in dictionary:
                dictionary[key] = result
        
        return dictionary
