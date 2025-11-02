"""
Tests for Database Exception Hierarchy
"""

import pytest
from larapy.exceptions import (
    DatabaseException,
    QueryException,
    ConnectionException,
    TransactionException,
    MigrationException,
    ModelNotFoundException,
    RecordNotFoundException,
    DuplicateRecordException,
    RelationNotFoundException,
    InvalidRelationException,
    SchemaException,
    DeadlockException,
)


class TestDatabaseException:
    """Test base DatabaseException"""
    
    def test_basic_exception(self):
        """Test basic exception creation"""
        exc = DatabaseException("Database error occurred")
        assert exc.message == "Database error occurred"
        assert exc.query is None
        assert exc.bindings is None
        assert exc.connection_name is None
    
    def test_exception_with_query(self):
        """Test exception with SQL query"""
        exc = DatabaseException(
            "Query failed",
            query="SELECT * FROM users WHERE id = ?",
            bindings={"id": 1}
        )
        assert "SELECT * FROM users" in str(exc)
        assert exc.query is not None
    
    def test_exception_with_connection(self):
        """Test exception with connection name"""
        exc = DatabaseException(
            "Connection error",
            connection_name="mysql"
        )
        assert "Connection: mysql" in str(exc)
    
    def test_long_query_truncation(self):
        """Test that long queries are truncated"""
        long_query = "SELECT * FROM users WHERE " + "x = 1 AND " * 50
        exc = DatabaseException("Error", query=long_query)
        assert "..." in str(exc)
        assert len(str(exc)) < len(long_query)
    
    def test_get_context(self):
        """Test getting exception context"""
        exc = DatabaseException(
            "Error",
            query="SELECT 1",
            bindings={"id": 1},
            connection_name="mysql"
        )
        context = exc.get_context()
        assert context['message'] == "Error"
        assert context['query'] == "SELECT 1"
        assert context['bindings'] == {"id": 1}
        assert context['connection_name'] == "mysql"


class TestQueryException:
    """Test QueryException"""
    
    def test_query_exception_basic(self):
        """Test basic query exception"""
        exc = QueryException("SQL syntax error")
        assert exc.message == "SQL syntax error"
    
    def test_query_exception_with_original(self):
        """Test with original exception"""
        original = ValueError("Invalid value")
        exc = QueryException(
            "Query failed",
            query="INSERT INTO users",
            original_exception=original
        )
        assert "Original error: Invalid value" in str(exc)
        assert exc.original_exception == original
    
    def test_password_sanitization(self):
        """Test that passwords are sanitized in bindings"""
        exc = QueryException(
            "Insert failed",
            query="INSERT INTO users",
            bindings={"password": "secret123", "email": "test@example.com"}
        )
        exc_str = str(exc)
        assert "***" in exc_str
        assert "secret123" not in exc_str
        assert "test@example.com" in exc_str


class TestModelNotFoundException:
    """Test ModelNotFoundException"""
    
    def test_single_id(self):
        """Test with single ID"""
        exc = ModelNotFoundException("User", 123)
        assert "User" in str(exc)
        assert "123" in str(exc)
        assert exc.model == "User"
        assert exc.ids == [123]
    
    def test_multiple_ids(self):
        """Test with multiple IDs"""
        exc = ModelNotFoundException("Post", [1, 2, 3])
        assert "Post" in str(exc)
        assert "1, 2, 3" in str(exc)
        assert exc.ids == [1, 2, 3]
    
    def test_status_code(self):
        """Test HTTP status code"""
        exc = ModelNotFoundException("User", 1)
        assert exc.get_status_code() == 404


class TestRecordNotFoundException:
    """Test RecordNotFoundException"""
    
    def test_basic_record_not_found(self):
        """Test basic record not found"""
        exc = RecordNotFoundException()
        assert "Record not found" in str(exc)
        assert exc.get_status_code() == 404
    
    def test_custom_message(self):
        """Test with custom message"""
        exc = RecordNotFoundException("No records match your criteria")
        assert "No records match" in str(exc)


class TestDuplicateRecordException:
    """Test DuplicateRecordException"""
    
    def test_duplicate_record(self):
        """Test duplicate record exception"""
        exc = DuplicateRecordException(
            "Duplicate entry",
            column="email",
            value="test@example.com"
        )
        assert "Duplicate" in str(exc)
        assert "email" in str(exc)
        assert "test@example.com" in str(exc)
    
    def test_status_code(self):
        """Test HTTP status code"""
        exc = DuplicateRecordException("Duplicate")
        assert exc.get_status_code() == 409
    
    def test_password_sanitization(self):
        """Test password value sanitization"""
        exc = DuplicateRecordException(
            "Duplicate",
            column="password",
            value="secret"
        )
        assert "***" in str(exc)
        assert "secret" not in str(exc)


class TestRelationNotFoundException:
    """Test RelationNotFoundException"""
    
    def test_relation_not_found(self):
        """Test relation not found"""
        exc = RelationNotFoundException("User", "unknownRelation")
        assert "User" in str(exc)
        assert "unknownRelation" in str(exc)
        assert exc.model == "User"
        assert exc.relation_name == "unknownRelation"


class TestInvalidRelationException:
    """Test InvalidRelationException"""
    
    def test_invalid_relation(self):
        """Test invalid relation"""
        exc = InvalidRelationException(
            "Post",
            "comments",
            "Missing foreign_key parameter"
        )
        assert "Post" in str(exc)
        assert "comments" in str(exc)
        assert "Missing foreign_key" in str(exc)
        assert exc.model == "Post"
        assert exc.relation_name == "comments"


class TestTransactionException:
    """Test TransactionException"""
    
    def test_transaction_exception(self):
        """Test transaction exception"""
        exc = TransactionException(
            "Transaction failed",
            transaction_level=2
        )
        assert "Transaction failed" in str(exc)
        assert "Transaction level: 2" in str(exc)
        assert exc.transaction_level == 2


class TestMigrationException:
    """Test MigrationException"""
    
    def test_migration_exception(self):
        """Test migration exception"""
        exc = MigrationException(
            "Migration failed",
            migration_name="2024_01_01_create_users_table"
        )
        assert "Migration failed" in str(exc)
        assert "2024_01_01_create_users_table" in str(exc)
        assert exc.migration_name == "2024_01_01_create_users_table"


class TestSchemaException:
    """Test SchemaException"""
    
    def test_schema_exception(self):
        """Test schema exception"""
        exc = SchemaException(
            "Table creation failed",
            table_name="users"
        )
        assert "Table creation failed" in str(exc)
        assert "Table: users" in str(exc)
        assert exc.table_name == "users"


class TestConnectionException:
    """Test ConnectionException"""
    
    def test_connection_exception(self):
        """Test connection exception"""
        exc = ConnectionException(
            "Connection refused",
            connection_name="mysql"
        )
        assert "Connection refused" in str(exc)
        assert "Connection: mysql" in str(exc)


class TestDeadlockException:
    """Test DeadlockException"""
    
    def test_deadlock_exception(self):
        """Test deadlock exception"""
        exc = DeadlockException(retry_count=2)
        assert "Deadlock detected" in str(exc)
        assert "Retry count: 2" in str(exc)
        assert exc.retry_count == 2
    
    def test_should_retry(self):
        """Test retry logic"""
        exc = DeadlockException(retry_count=1)
        assert exc.should_retry(max_retries=3) is True
        
        exc = DeadlockException(retry_count=3)
        assert exc.should_retry(max_retries=3) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
