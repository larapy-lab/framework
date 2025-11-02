"""
Database Exception Hierarchy

Provides consistent exception classes for database operations with
improved error messages and context.
"""

from typing import Optional, Dict, Any


class DatabaseException(Exception):
    """
    Base exception for all database-related errors.
    
    Attributes:
        message: The error message
        query: Optional SQL query that caused the error
        bindings: Optional query parameter bindings
        connection_name: Optional database connection name
    """
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None,
        connection_name: Optional[str] = None
    ):
        self.message = message
        self.query = query
        self.bindings = bindings
        self.connection_name = connection_name
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message with context"""
        parts = [self.message]
        
        if self.connection_name:
            parts.append(f"Connection: {self.connection_name}")
        
        if self.query:
            # Truncate long queries
            query_display = self.query[:200] + "..." if len(self.query) > 200 else self.query
            parts.append(f"Query: {query_display}")
        
        if self.bindings:
            parts.append(f"Bindings: {self.bindings}")
        
        return "\n".join(parts)
    
    def get_context(self) -> Dict[str, Any]:
        """Get exception context for logging"""
        return {
            'message': self.message,
            'query': self.query,
            'bindings': self.bindings,
            'connection_name': self.connection_name,
        }


class QueryException(DatabaseException):
    """
    Exception raised when a database query fails.
    
    Example:
        ```python
        try:
            User.where('invalid_column', 'value').get()
        except QueryException as e:
            print(f"Query failed: {e.message}")
            print(f"SQL: {e.query}")
        ```
    """
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None,
        connection_name: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        self.original_exception = original_exception
        super().__init__(message, query, bindings, connection_name)
    
    def _format_message(self) -> str:
        """Format with original exception details"""
        parts = [self.message]
        
        if self.original_exception:
            parts.append(f"Original error: {str(self.original_exception)}")
        
        if self.connection_name:
            parts.append(f"Connection: {self.connection_name}")
        
        if self.query:
            query_display = self.query[:200] + "..." if len(self.query) > 200 else self.query
            parts.append(f"SQL: {query_display}")
        
        if self.bindings:
            # Sanitize sensitive data
            safe_bindings = {k: '***' if 'password' in k.lower() else v 
                           for k, v in self.bindings.items()}
            parts.append(f"Bindings: {safe_bindings}")
        
        return "\n".join(parts)


class ConnectionException(DatabaseException):
    """
    Exception raised when database connection fails.
    
    Example:
        ```python
        try:
            connection = DB.connection('invalid')
        except ConnectionException as e:
            print(f"Connection failed: {e.message}")
        ```
    """
    pass


class TransactionException(DatabaseException):
    """
    Exception raised during transaction operations.
    
    Example:
        ```python
        try:
            DB.transaction(lambda: risky_operation())
        except TransactionException as e:
            print(f"Transaction failed: {e.message}")
        ```
    """
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None,
        connection_name: Optional[str] = None,
        transaction_level: int = 0
    ):
        self.transaction_level = transaction_level
        super().__init__(message, query, bindings, connection_name)
    
    def _format_message(self) -> str:
        """Format with transaction level"""
        base_message = super()._format_message()
        return f"{base_message}\nTransaction level: {self.transaction_level}"


class MigrationException(DatabaseException):
    """
    Exception raised during database migrations.
    
    Example:
        ```python
        try:
            migrate.run()
        except MigrationException as e:
            print(f"Migration failed: {e.message}")
            print(f"Migration: {e.migration_name}")
        ```
    """
    
    def __init__(
        self,
        message: str,
        migration_name: Optional[str] = None,
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None,
        connection_name: Optional[str] = None
    ):
        self.migration_name = migration_name
        super().__init__(message, query, bindings, connection_name)
    
    def _format_message(self) -> str:
        """Format with migration details"""
        parts = [self.message]
        
        if self.migration_name:
            parts.append(f"Migration: {self.migration_name}")
        
        if self.connection_name:
            parts.append(f"Connection: {self.connection_name}")
        
        if self.query:
            query_display = self.query[:200] + "..." if len(self.query) > 200 else self.query
            parts.append(f"SQL: {query_display}")
        
        return "\n".join(parts)


class ModelNotFoundException(DatabaseException):
    """
    Exception raised when a model is not found.
    
    Example:
        ```python
        try:
            user = User.find_or_fail(999)
        except ModelNotFoundException as e:
            return {"error": "User not found"}, 404
        ```
    """
    
    def __init__(
        self,
        model: str,
        ids: Any,
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None
    ):
        self.model = model
        self.ids = ids if isinstance(ids, list) else [ids]
        message = self._build_message()
        super().__init__(message, query, bindings)
    
    def _build_message(self) -> str:
        """Build user-friendly message"""
        if len(self.ids) == 1:
            return f"No query results for model [{self.model}] with ID {self.ids[0]}"
        else:
            ids_str = ", ".join(str(id) for id in self.ids)
            return f"No query results for model [{self.model}] with IDs: {ids_str}"
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this exception"""
        return 404


class RecordNotFoundException(DatabaseException):
    """
    Exception raised when a database record is not found.
    
    Similar to ModelNotFoundException but for raw queries.
    """
    
    def __init__(
        self,
        message: str = "Record not found",
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None,
        connection_name: Optional[str] = None
    ):
        super().__init__(message, query, bindings, connection_name)
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this exception"""
        return 404


class DuplicateRecordException(DatabaseException):
    """
    Exception raised when attempting to create a duplicate record.
    
    Example:
        ```python
        try:
            User.create({'email': 'existing@example.com'})
        except DuplicateRecordException as e:
            return {"error": "Email already exists"}, 409
        ```
    """
    
    def __init__(
        self,
        message: str,
        column: Optional[str] = None,
        value: Optional[Any] = None,
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None,
        connection_name: Optional[str] = None
    ):
        self.column = column
        self.value = value
        super().__init__(message, query, bindings, connection_name)
    
    def _format_message(self) -> str:
        """Format with duplicate details"""
        parts = [self.message]
        
        if self.column and self.value:
            # Sanitize sensitive values
            safe_value = '***' if 'password' in self.column.lower() else self.value
            parts.append(f"Duplicate value '{safe_value}' for column '{self.column}'")
        
        if self.connection_name:
            parts.append(f"Connection: {self.connection_name}")
        
        return "\n".join(parts)
    
    def get_status_code(self) -> int:
        """Get HTTP status code for this exception"""
        return 409


class RelationNotFoundException(DatabaseException):
    """
    Exception raised when a relationship is not found on a model.
    
    Example:
        ```python
        try:
            user.unknown_relation
        except RelationNotFoundException as e:
            print(f"Relation not found: {e.relation_name}")
        ```
    """
    
    def __init__(
        self,
        model: str,
        relation_name: str
    ):
        self.model = model
        self.relation_name = relation_name
        message = f"Relation '{relation_name}' not found on model [{model}]"
        super().__init__(message)


class InvalidRelationException(DatabaseException):
    """
    Exception raised when a relationship configuration is invalid.
    
    Example:
        ```python
        # Missing required foreign_key parameter
        try:
            self.has_many(Post)
        except InvalidRelationException as e:
            print(f"Invalid relation: {e.message}")
        ```
    """
    
    def __init__(
        self,
        model: str,
        relation_name: str,
        reason: str
    ):
        self.model = model
        self.relation_name = relation_name
        self.reason = reason
        message = f"Invalid relation '{relation_name}' on model [{model}]: {reason}"
        super().__init__(message)


class SchemaException(DatabaseException):
    """
    Exception raised during schema operations.
    
    Example:
        ```python
        try:
            Schema.drop_if_exists('nonexistent_table')
        except SchemaException as e:
            print(f"Schema error: {e.message}")
        ```
    """
    
    def __init__(
        self,
        message: str,
        table_name: Optional[str] = None,
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None,
        connection_name: Optional[str] = None
    ):
        self.table_name = table_name
        super().__init__(message, query, bindings, connection_name)
    
    def _format_message(self) -> str:
        """Format with table details"""
        parts = [self.message]
        
        if self.table_name:
            parts.append(f"Table: {self.table_name}")
        
        if self.connection_name:
            parts.append(f"Connection: {self.connection_name}")
        
        if self.query:
            query_display = self.query[:200] + "..." if len(self.query) > 200 else self.query
            parts.append(f"SQL: {query_display}")
        
        return "\n".join(parts)


class DeadlockException(DatabaseException):
    """
    Exception raised when a database deadlock is detected.
    
    Example:
        ```python
        try:
            DB.transaction(lambda: concurrent_operation())
        except DeadlockException as e:
            # Retry logic
            time.sleep(0.1)
            retry()
        ```
    """
    
    def __init__(
        self,
        message: str = "Deadlock detected",
        query: Optional[str] = None,
        bindings: Optional[Dict[str, Any]] = None,
        connection_name: Optional[str] = None,
        retry_count: int = 0
    ):
        self.retry_count = retry_count
        super().__init__(message, query, bindings, connection_name)
    
    def _format_message(self) -> str:
        """Format with retry information"""
        base_message = super()._format_message()
        return f"{base_message}\nRetry count: {self.retry_count}"
    
    def should_retry(self, max_retries: int = 3) -> bool:
        """Check if operation should be retried"""
        return self.retry_count < max_retries
