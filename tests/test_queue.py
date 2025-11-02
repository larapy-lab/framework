import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import timedelta
import json
import time

from larapy.queue import (
    Job,
    dispatch,
    dispatch_sync,
    set_queue_manager,
    SyncQueue,
    DatabaseQueue,
    RedisQueue,
    QueueManager,
    Worker,
    Batch,
    Bus,
    Chain,
    chain,
    DatabaseFailedJobProvider,
    DatabaseBatchRepository
)


class TestJob(Job):
    def __init__(self, value: int = 0):
        super().__init__()
        self.value = value
        self.executed = False
    
    def handle(self):
        self.executed = True
        return self.value * 2


class FailingJob(Job):
    def __init__(self):
        super().__init__()
    
    def handle(self):
        raise Exception("Job failed intentionally")
    
    def failed(self, exception: Exception):
        self.failed_with = exception


class TestJobBasics:
    
    def test_job_has_unique_id(self):
        job1 = TestJob()
        job2 = TestJob()
        
        assert job1.job_id != job2.job_id
    
    def test_job_can_set_queue(self):
        job = TestJob()
        job.onQueue('high')
        
        assert job.queue == 'high'
    
    def test_job_can_set_connection(self):
        job = TestJob()
        job.onConnection('redis')
        
        assert job.connection == 'redis'
    
    def test_job_can_set_delay(self):
        job = TestJob()
        delay = timedelta(minutes=10)
        job.delay(delay)
        
        assert job.delay_time == delay
    
    def test_job_serialization(self):
        job = TestJob(42)
        job.onQueue('test')
        
        payload = job.serialize()
        
        assert payload['job_id'] == job.job_id
        assert payload['queue'] == 'test'
        assert 'TestJob' in payload['class']
        assert isinstance(payload['data'], str)
    
    def test_job_unserialization(self):
        job = TestJob(42)
        payload = job.serialize()
        
        restored_job = Job.unserialize(payload)
        
        assert restored_job.job_id == job.job_id
        assert restored_job.value == 42
    
    def test_job_fire_executes_handle(self):
        job = TestJob(21)
        
        job.fire()
        
        assert job.executed is True
    
    def test_job_fire_calls_failed_on_exception(self):
        job = FailingJob()
        
        with pytest.raises(Exception, match="Job failed intentionally"):
            job.fire()
        
        assert hasattr(job, 'failed_with')
        assert str(job.failed_with) == "Job failed intentionally"


class TestSyncQueue:
    
    def test_sync_queue_pushes_and_executes_immediately(self):
        queue = SyncQueue()
        job = TestJob(10)
        
        payload = job.serialize()
        result = queue.push('TestJob', payload)
        
        assert result == 0
    
    def test_sync_queue_later_executes_immediately(self):
        queue = SyncQueue()
        job = TestJob(10)
        
        payload = job.serialize()
        result = queue.later(timedelta(minutes=10), 'TestJob', payload)
        
        assert result == 0
    
    def test_sync_queue_pop_returns_none(self):
        queue = SyncQueue()
        
        assert queue.pop() is None
    
    def test_sync_queue_size_returns_zero(self):
        queue = SyncQueue()
        
        assert queue.size() == 0


class TestDatabaseQueue:
    
    def test_database_queue_push(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        mock_table.insert_get_id.return_value = 1
        
        queue = DatabaseQueue(mock_db, 'jobs', 'default', 90)
        job = TestJob(10)
        
        payload = job.serialize()
        payload_json = json.dumps(payload)
        
        result = queue.push('TestJob', payload)
        
        assert mock_db.table.called
        assert mock_table.insert_get_id.called
        assert result == 1
    
    def test_database_queue_later(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        mock_table.insert_get_id.return_value = 1
        
        queue = DatabaseQueue(mock_db, 'jobs', 'default', 90)
        job = TestJob(10)
        
        payload = job.serialize()
        delay = timedelta(minutes=10)
        
        result = queue.later(delay, 'TestJob', payload)
        
        assert mock_db.table.called
        call_args = mock_table.insert_get_id.call_args[0][0]
        assert call_args['available_at'] > int(time.time())
    
    def test_database_queue_pop(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        
        job_record = {
            'id': 1,
            'queue': 'default',
            'payload': json.dumps({'job': 'TestJob', 'data': {}}),
            'attempts': 0,
            'reserved_at': None,
            'available_at': int(time.time()),
            'created_at': int(time.time())
        }
        
        mock_table.where.return_value = mock_table
        mock_table.or_where.return_value = mock_table
        mock_table.order_by.return_value = mock_table
        mock_table.first.return_value = job_record
        mock_table.update.return_value = 1
        
        queue = DatabaseQueue(mock_db, 'jobs', 'default', 90)
        
        job = queue.pop('default')
        
        assert job is not None
        assert mock_table.where.called
    
    def test_database_queue_size(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        mock_table.where.return_value = mock_table
        mock_table.count.return_value = 5
        
        queue = DatabaseQueue(mock_db, 'jobs', 'default', 90)
        
        size = queue.size('default')
        
        assert size == 5
    
    def test_database_queue_clear(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        mock_table.where.return_value = mock_table
        mock_table.delete.return_value = 3
        
        queue = DatabaseQueue(mock_db, 'jobs', 'default', 90)
        
        count = queue.clear('default')
        
        assert count == 3


class TestRedisQueue:
    
    def test_redis_queue_push(self):
        mock_redis = Mock()
        mock_redis.rpush.return_value = 1
        
        queue = RedisQueue(mock_redis, 'default', 90)
        job = TestJob(10)
        
        payload = job.serialize()
        
        result = queue.push('TestJob', payload)
        
        assert mock_redis.rpush.called
    
    def test_redis_queue_later(self):
        mock_redis = Mock()
        mock_redis.zadd.return_value = 1
        
        queue = RedisQueue(mock_redis, 'default', 90)
        job = TestJob(10)
        
        payload = job.serialize()
        delay = timedelta(minutes=10)
        
        result = queue.later(delay, 'TestJob', payload)
        
        assert mock_redis.zadd.called
    
    def test_redis_queue_pop(self):
        mock_redis = Mock()
        mock_redis.zrangebyscore.return_value = []
        
        job_payload = json.dumps({
            'job': 'TestJob',
            'data': {},
            'displayName': 'TestJob'
        })
        
        mock_redis.lpop.return_value = job_payload.encode('utf-8')
        
        queue = RedisQueue(mock_redis, 'default', 90)
        
        job = queue.pop('default')
        
        assert job is not None
        assert mock_redis.lpop.called
    
    def test_redis_queue_size(self):
        mock_redis = Mock()
        mock_redis.llen.return_value = 10
        
        queue = RedisQueue(mock_redis, 'default', 90)
        
        size = queue.size('default')
        
        assert size == 10
    
    def test_redis_queue_clear(self):
        mock_redis = Mock()
        mock_redis.llen.return_value = 5
        mock_redis.delete.return_value = 1
        
        queue = RedisQueue(mock_redis, 'default', 90)
        
        count = queue.clear('default')
        
        assert count == 5


class TestQueueManager:
    
    def test_manager_creates_sync_driver(self):
        config = {
            'default': 'sync',
            'connections': {
                'sync': {'driver': 'sync'}
            }
        }
        
        manager = QueueManager(config)
        connection = manager.connection('sync')
        
        assert isinstance(connection, SyncQueue)
    
    def test_manager_creates_database_driver(self):
        mock_db = Mock()
        mock_container = Mock()
        mock_container.make.return_value = mock_db
        
        config = {
            'default': 'database',
            'connections': {
                'database': {
                    'driver': 'database',
                    'table': 'jobs',
                    'queue': 'default',
                    'retry_after': 90
                }
            }
        }
        
        manager = QueueManager(config, mock_container)
        connection = manager.connection('database')
        
        assert isinstance(connection, DatabaseQueue)
    
    def test_manager_uses_default_connection(self):
        config = {
            'default': 'sync',
            'connections': {
                'sync': {'driver': 'sync'}
            }
        }
        
        manager = QueueManager(config)
        connection = manager.connection()
        
        assert isinstance(connection, SyncQueue)
    
    def test_manager_caches_connections(self):
        config = {
            'default': 'sync',
            'connections': {
                'sync': {'driver': 'sync'}
            }
        }
        
        manager = QueueManager(config)
        connection1 = manager.connection('sync')
        connection2 = manager.connection('sync')
        
        assert connection1 is connection2


class TestWorker:
    
    def test_worker_processes_job(self):
        job = TestJob(10)
        mock_manager = Mock()
        mock_queue = Mock()
        mock_queue.pop.return_value = None
        mock_manager.connection.return_value = mock_queue
        mock_manager.get_default_connection.return_value = 'sync'
        
        worker = Worker(mock_manager)
        
        with patch.object(worker, 'get_next_job', return_value=None):
            with patch.object(worker, 'should_quit', True):
                worker.work('sync', 'default', {'sleep': 1, 'memory': 128})
    
    def test_worker_handles_failed_job(self):
        mock_job = Mock()
        mock_job.max_tries.return_value = 1
        mock_job.attempts.return_value = 1
        mock_job.is_deleted.return_value = False
        mock_job.is_deleted_or_released.return_value = False
        mock_job.fire.side_effect = Exception("Test exception")
        mock_job.get_connection_name.return_value = 'sync'
        mock_job.get_queue.return_value = 'default'
        mock_job.get_raw_body.return_value = '{}'
        mock_job.payload.return_value = {'data': {}}
        
        mock_manager = Mock()
        mock_failed_provider = Mock()
        
        worker = Worker(mock_manager, mock_failed_provider)
        
        worker.handle_job_exception(mock_job, 'sync', Exception("Test"), {'delay': 0})
        
        assert mock_job.mark_as_failed.called


class TestBatch:
    
    def test_batch_creation(self):
        batch = Batch(
            batch_id='test-123',
            name='Test Batch',
            total_jobs=10,
            pending_jobs=10,
            failed_jobs=0,
            failed_job_ids=[]
        )
        
        assert batch.id == 'test-123'
        assert batch.total_jobs == 10
        assert batch.pending_jobs == 10
    
    def test_batch_finished_when_no_pending_jobs(self):
        batch = Batch(
            batch_id='test-123',
            name='Test',
            total_jobs=10,
            pending_jobs=0,
            failed_jobs=0,
            failed_job_ids=[]
        )
        
        assert batch.finished() is True
    
    def test_batch_not_finished_with_pending_jobs(self):
        batch = Batch(
            batch_id='test-123',
            name='Test',
            total_jobs=10,
            pending_jobs=5,
            failed_jobs=0,
            failed_job_ids=[]
        )
        
        assert batch.finished() is False
    
    def test_batch_has_failures(self):
        batch = Batch(
            batch_id='test-123',
            name='Test',
            total_jobs=10,
            pending_jobs=5,
            failed_jobs=2,
            failed_job_ids=['job-1', 'job-2']
        )
        
        assert batch.has_failures() is True


class TestChain:
    
    def test_chain_sets_jobs_correctly(self):
        job1 = TestJob(1)
        job2 = TestJob(2)
        job3 = TestJob(3)
        
        chain_instance = Chain([job1, job2, job3])
        
        assert len(chain_instance.jobs) == 3
    
    def test_chain_with_queue(self):
        job1 = TestJob(1)
        job2 = TestJob(2)
        
        chain_instance = Chain([job1, job2])
        chain_instance.on_queue('high')
        
        assert chain_instance.queue_name == 'high'


class TestFailedJobProvider:
    
    def test_failed_job_provider_logs_job(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        mock_table.insert_get_id.return_value = 1
        
        provider = DatabaseFailedJobProvider(mock_db, 'failed_jobs')
        
        job_id = provider.log('sync', 'default', {'job': 'TestJob'}, Exception("Test"))
        
        assert mock_table.insert_get_id.called
        assert job_id == 1
    
    def test_failed_job_provider_finds_job(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        
        job_record = {
            'id': 1,
            'connection': 'sync',
            'queue': 'default',
            'payload': '{}',
            'exception': 'Test exception'
        }
        
        mock_table.find.return_value = job_record
        
        provider = DatabaseFailedJobProvider(mock_db, 'failed_jobs')
        
        job = provider.find(1)
        
        assert job == job_record
    
    def test_failed_job_provider_forgets_job(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        mock_table.where.return_value = mock_table
        mock_table.delete.return_value = 1
        
        provider = DatabaseFailedJobProvider(mock_db, 'failed_jobs')
        
        result = provider.forget(1)
        
        assert result is True
    
    def test_failed_job_provider_gets_all_jobs(self):
        mock_db = Mock()
        mock_table = Mock()
        mock_db.table.return_value = mock_table
        mock_table.order_by.return_value = mock_table
        mock_table.get.return_value = [
            {'id': 1, 'queue': 'default'},
            {'id': 2, 'queue': 'default'}
        ]
        
        provider = DatabaseFailedJobProvider(mock_db, 'failed_jobs')
        
        jobs = provider.all()
        
        assert len(jobs) == 2


class TestDispatcher:
    
    def test_dispatch_function_with_sync_queue(self):
        config = {
            'default': 'sync',
            'connections': {
                'sync': {'driver': 'sync'}
            }
        }
        
        manager = QueueManager(config)
        set_queue_manager(manager)
        
        job = TestJob(10)
        
        result = dispatch(job)
        
        assert result is not None
    
    def test_dispatch_sync_executes_immediately(self):
        job = TestJob(10)
        
        dispatch_sync(job)
        
        assert job.executed is True
