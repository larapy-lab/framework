from typing import Any, Dict, List, Optional, Union, Callable
from sqlalchemy import text, select, insert, update, delete, func, and_, or_
from larapy.cache import cache


class QueryBuilder:
    def __init__(self, connection, table_name: str):
        self._connection = connection
        self._table = table_name
        self._select_columns = ["*"]
        self._wheres = []
        self._bindings = []
        self._joins = []
        self._orders = []
        self._group_by_columns = []
        self._having_conditions = []
        self._limit_value = None
        self._offset_value = None
        self._distinct_flag = False
        self._cache_enabled = False
        self._cache_ttl = None
        self._cache_key = None

    def select(self, *columns):
        if columns:
            self._select_columns = list(columns)
        return self

    def where(self, column: Union[str, Callable], operator: Any = None, value: Any = None):
        if callable(column):
            nested_builder = QueryBuilder(self._connection, self._table)
            column(nested_builder)

            if nested_builder._wheres:
                self._wheres.append(("nested", nested_builder._wheres))
                # Add nested bindings to parent bindings
                self._bindings.extend(nested_builder._bindings)
            return self

        if value is None and operator is not None:
            value = operator
            operator = "="

        self._wheres.append(("basic", column, operator, value))
        self._bindings.append(value)
        return self

    def or_where(self, column: str, operator: Any = None, value: Any = None):
        if value is None and operator is not None:
            value = operator
            operator = "="

        self._wheres.append(("or", column, operator, value))
        self._bindings.append(value)
        return self

    def where_in(self, column: str, values: List):
        self._wheres.append(("in", column, values))
        self._bindings.extend(values)
        return self

    def where_not_in(self, column: str, values: List):
        self._wheres.append(("not_in", column, values))
        self._bindings.extend(values)
        return self

    def where_null(self, column: str):
        self._wheres.append(("null", column))
        return self

    def where_not_null(self, column: str):
        self._wheres.append(("not_null", column))
        return self

    def where_between(self, column: str, min_value: Any, max_value: Any):
        self._wheres.append(("between", column, min_value, max_value))
        self._bindings.extend([min_value, max_value])
        return self

    def join(self, table: str, first: str, operator: str, second: str):
        self._joins.append(("inner", table, first, operator, second))
        return self

    def left_join(self, table: str, first: str, operator: str, second: str):
        self._joins.append(("left", table, first, operator, second))
        return self

    def right_join(self, table: str, first: str, operator: str, second: str):
        self._joins.append(("right", table, first, operator, second))
        return self

    def order_by(self, column: str, direction: str = "asc"):
        self._orders.append((column, direction.upper()))
        return self

    def group_by(self, *columns):
        self._group_by_columns.extend(columns)
        return self

    def having(self, column: str, operator: str, value: Any):
        self._having_conditions.append((column, operator, value))
        self._bindings.append(value)
        return self

    def limit(self, count: int):
        self._limit_value = count
        return self

    def offset(self, count: int):
        self._offset_value = count
        return self

    def distinct(self):
        self._distinct_flag = True
        return self

    def remember(self, ttl: int = 3600, key: Optional[str] = None):
        """
        Enable caching for this query.
        
        Args:
            ttl: Time to live in seconds (default: 3600 = 1 hour)
            key: Optional custom cache key (auto-generated if not provided)
            
        Returns:
            self for method chaining
            
        Example:
            # Cache results for 1 hour
            users = db.table('users').where('active', True).remember().get()
            
            # Cache for 5 minutes with custom key
            posts = db.table('posts').remember(300, 'featured_posts').get()
        """
        self._cache_enabled = True
        self._cache_ttl = ttl
        self._cache_key = key
        return self

    def _generate_cache_key(self) -> str:
        """
        Generate a unique cache key for the current query.
        
        Returns:
            A hash string representing the query and its bindings
        """
        if self._cache_key:
            return self._cache_key
        
        # Build a representation of the query
        key_parts = [
            self._table,
            str(self._select_columns),
            str(self._wheres),
            str(self._bindings),
            str(self._joins),
            str(self._orders),
            str(self._group_by_columns),
            str(self._having_conditions),
            str(self._limit_value),
            str(self._offset_value),
            str(self._distinct_flag)
        ]
        
        return cache().generate_key(*key_parts)

    def _build_select_query(self) -> str:
        distinct = "DISTINCT " if self._distinct_flag else ""
        columns = ", ".join(self._select_columns)
        query = f"SELECT {distinct}{columns} FROM {self._table}"

        if self._joins:
            for join_type, table, first, operator, second in self._joins:
                join_keyword = join_type.upper()
                query += f" {join_keyword} JOIN {table} ON {first} {operator} {second}"

        if self._wheres:
            where_clause = self._build_where_clause()
            query += f" WHERE {where_clause}"

        if self._group_by_columns:
            query += f" GROUP BY {', '.join(self._group_by_columns)}"

        if self._having_conditions:
            having_parts = []
            for column, operator, value in self._having_conditions:
                having_parts.append(f"{column} {operator} ?")
            query += f" HAVING {' AND '.join(having_parts)}"

        if self._orders:
            order_parts = [f"{col} {direction}" for col, direction in self._orders]
            query += f" ORDER BY {', '.join(order_parts)}"

        if self._limit_value is not None:
            query += f" LIMIT {self._limit_value}"

        if self._offset_value is not None:
            query += f" OFFSET {self._offset_value}"

        return query

    def _build_where_clause(self) -> str:
        parts = []

        for i, where in enumerate(self._wheres):
            where_type = where[0]

            if where_type == "basic":
                _, column, operator, value = where
                clause = f"{column} {operator} ?"
                if i > 0 and self._wheres[i - 1][0] != "or":
                    parts.append("AND")
                parts.append(clause)

            elif where_type == "or":
                _, column, operator, value = where
                clause = f"{column} {operator} ?"
                if i > 0:
                    parts.append("OR")
                parts.append(clause)

            elif where_type == "in":
                _, column, values = where
                placeholders = ", ".join(["?" for _ in values])
                clause = f"{column} IN ({placeholders})"
                if i > 0 and self._wheres[i - 1][0] != "or":
                    parts.append("AND")
                parts.append(clause)

            elif where_type == "not_in":
                _, column, values = where
                placeholders = ", ".join(["?" for _ in values])
                clause = f"{column} NOT IN ({placeholders})"
                if i > 0 and self._wheres[i - 1][0] != "or":
                    parts.append("AND")
                parts.append(clause)

            elif where_type == "null":
                _, column = where
                clause = f"{column} IS NULL"
                if i > 0 and self._wheres[i - 1][0] != "or":
                    parts.append("AND")
                parts.append(clause)

            elif where_type == "not_null":
                _, column = where
                clause = f"{column} IS NOT NULL"
                if i > 0 and self._wheres[i - 1][0] != "or":
                    parts.append("AND")
                parts.append(clause)

            elif where_type == "between":
                _, column, min_val, max_val = where
                clause = f"{column} BETWEEN ? AND ?"
                if i > 0 and self._wheres[i - 1][0] != "or":
                    parts.append("AND")
                parts.append(clause)

            elif where_type == "nested":
                _, nested_wheres = where
                nested_builder = QueryBuilder(self._connection, self._table)
                nested_builder._wheres = nested_wheres
                nested_clause = nested_builder._build_where_clause()
                clause = f"({nested_clause})"
                if i > 0 and self._wheres[i - 1][0] != "or":
                    parts.append("AND")
                parts.append(clause)

        return " ".join(parts)

    def get(self) -> List[Dict]:
        """
        Execute the query and return all results.
        
        If caching is enabled via remember(), results will be cached/retrieved from cache.
        
        Returns:
            List of result rows as dictionaries
        """
        # Check cache if enabled
        if self._cache_enabled:
            cache_key = self._generate_cache_key()
            
            # Try to get from cache
            cached_result = cache().get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute query
            query = self._build_select_query()
            results = self._connection.select(query, self._bindings)
            
            # Store in cache
            cache().put(cache_key, results, self._cache_ttl)
            
            return results
        
        # No caching, execute normally
        query = self._build_select_query()
        return self._connection.select(query, self._bindings)

    def first(self) -> Optional[Dict]:
        self.limit(1)
        results = self.get()
        return results[0] if results else None

    def find(self, id: Any) -> Optional[Dict]:
        return self.where("id", id).first()

    def pluck(self, column: str) -> List[Any]:
        self.select(column)
        results = self.get()
        return [row[column] for row in results]

    def value(self, column: str) -> Any:
        row = self.first()
        return row[column] if row and column in row else None

    def count(self) -> int:
        original_select = self._select_columns
        self._select_columns = ["COUNT(*) as count"]
        result = self.first()
        self._select_columns = original_select
        return result["count"] if result else 0

    def sum(self, column: str) -> Union[int, float]:
        original_select = self._select_columns
        self._select_columns = [f"SUM({column}) as sum"]
        result = self.first()
        self._select_columns = original_select
        return result["sum"] if result and result["sum"] is not None else 0

    def avg(self, column: str) -> Union[int, float]:
        original_select = self._select_columns
        self._select_columns = [f"AVG({column}) as avg"]
        result = self.first()
        self._select_columns = original_select
        return result["avg"] if result and result["avg"] is not None else 0

    def min(self, column: str) -> Any:
        original_select = self._select_columns
        self._select_columns = [f"MIN({column}) as min"]
        result = self.first()
        self._select_columns = original_select
        return result["min"] if result else None

    def max(self, column: str) -> Any:
        original_select = self._select_columns
        self._select_columns = [f"MAX({column}) as max"]
        result = self.first()
        self._select_columns = original_select
        return result["max"] if result else None

    def exists(self) -> bool:
        return self.count() > 0

    def insert(self, data: Union[Dict, List[Dict]]) -> int:
        if isinstance(data, list):
            last_id = 0
            for row in data:
                last_id = self._insert_single(row)
            return last_id
        return self._insert_single(data)

    def _insert_single(self, data: Dict) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})"
        return self._connection.insert(query, list(data.values()))

    def insert_get_id(self, data: Dict) -> int:
        return self.insert(data)

    def update(self, data: Dict) -> int:
        set_parts = [f"{col} = ?" for col in data.keys()]
        query = f"UPDATE {self._table} SET {', '.join(set_parts)}"

        bindings = list(data.values())

        if self._wheres:
            where_clause = self._build_where_clause()
            query += f" WHERE {where_clause}"
            bindings.extend(self._bindings)

        return self._connection.update(query, bindings)

    def increment(self, column: str, amount: int = 1) -> int:
        query = f"UPDATE {self._table} SET {column} = {column} + ?"
        bindings = [amount]

        if self._wheres:
            where_clause = self._build_where_clause()
            query += f" WHERE {where_clause}"
            bindings.extend(self._bindings)

        return self._connection.update(query, bindings)

    def decrement(self, column: str, amount: int = 1) -> int:
        query = f"UPDATE {self._table} SET {column} = {column} - ?"
        bindings = [amount]

        if self._wheres:
            where_clause = self._build_where_clause()
            query += f" WHERE {where_clause}"
            bindings.extend(self._bindings)

        return self._connection.update(query, bindings)

    def delete(self) -> int:
        query = f"DELETE FROM {self._table}"

        if self._wheres:
            where_clause = self._build_where_clause()
            query += f" WHERE {where_clause}"
            return self._connection.delete(query, self._bindings)

        return self._connection.delete(query)

    def truncate(self) -> bool:
        query = f"DELETE FROM {self._table}"
        return self._connection.statement(query)

    def to_sql(self) -> str:
        return self._build_select_query()
