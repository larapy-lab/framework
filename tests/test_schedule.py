import pytest
from datetime import datetime, timedelta
from larapy.console.scheduling.schedule import Schedule
from larapy.console.scheduling.event import Event
from larapy.console.scheduling.command_event import CommandEvent
from larapy.console.scheduling.callback_event import CallbackEvent
from larapy.console.scheduling.job_event import JobEvent
from larapy.console.scheduling.exec_event import ExecEvent
from larapy.console.scheduling.event_mutex import EventMutex
from larapy.console.scheduling.schedule_runner import ScheduleRunner
from larapy.console.scheduling.cron_expression_parser import CronExpressionParser


class MockContainer:
    def __init__(self):
        self.bindings = {}
    
    def make(self, abstract):
        return self.bindings.get(abstract)


class MockCache:
    def __init__(self):
        self.data = {}
    
    def add(self, key, value, ttl=None):
        if key not in self.data:
            self.data[key] = value
            return True
        return False
    
    def has(self, key):
        return key in self.data
    
    def forget(self, key):
        if key in self.data:
            del self.data[key]


class TestSchedule:
    def test_schedule_can_register_command_event(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        event = schedule.command('test:command')
        
        assert len(schedule.all_events()) == 1
        assert isinstance(event, CommandEvent)
    
    def test_schedule_can_register_callback_event(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        def test_callback():
            pass
        
        event = schedule.call(test_callback)
        
        assert len(schedule.all_events()) == 1
        assert isinstance(event, CallbackEvent)
    
    def test_schedule_can_register_job_event(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        class TestJob:
            pass
        
        job = TestJob()
        event = schedule.job(job)
        
        assert len(schedule.all_events()) == 1
        assert isinstance(event, JobEvent)
    
    def test_schedule_can_register_exec_event(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        event = schedule.exec('echo "test"')
        
        assert len(schedule.all_events()) == 1
        assert isinstance(event, ExecEvent)
    
    def test_schedule_can_set_timezone(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        schedule.use_timezone('America/New_York')
        
        assert schedule.timezone == 'America/New_York'
    
    def test_schedule_applies_timezone_to_new_events(self):
        container = MockContainer()
        schedule = Schedule(container)
        schedule.use_timezone('America/New_York')
        
        event = schedule.command('test:command')
        
        assert event.timezone == 'America/New_York'


class TestEvent:
    def test_event_default_expression_is_every_minute(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        assert event.get_expression() == '* * * * *'
    
    def test_event_can_set_cron_expression(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.cron('0 0 * * *')
        
        assert event.get_expression() == '0 0 * * *'
    
    def test_event_every_minute(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.every_minute()
        
        assert event.get_expression() == '* * * * *'
    
    def test_event_every_five_minutes(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.every_five_minutes()
        
        assert event.get_expression() == '*/5 * * * *'
    
    def test_event_hourly(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.hourly()
        
        assert event.get_expression() == '0 * * * *'
    
    def test_event_hourly_at(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.hourly_at(15)
        
        assert event.get_expression() == '15 * * * *'
    
    def test_event_daily(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.daily()
        
        assert event.get_expression() == '0 0 * * *'
    
    def test_event_daily_at(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.daily_at('13:30')
        
        assert event.get_expression() == '30 13 * * *'
    
    def test_event_weekly(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.weekly()
        
        assert event.get_expression() == '0 0 * * 0'
    
    def test_event_weekly_on(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.weekly_on(1, '08:00')
        
        assert event.get_expression() == '0 8 * * 1'
    
    def test_event_monthly(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.monthly()
        
        assert event.get_expression() == '0 0 1 * *'
    
    def test_event_at_sets_time(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.daily().at('15:30')
        
        expression = event.get_expression()
        parts = expression.split()
        assert parts[0] == '30'
        assert parts[1] == '15'
    
    def test_event_can_add_filter(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.when(lambda: True)
        
        assert len(event.filters) == 1
    
    def test_event_can_add_reject(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.skip(lambda: False)
        
        assert len(event.rejects) == 1
    
    def test_event_can_add_before_callback(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.before(lambda: None)
        
        assert len(event.before_callbacks) == 1
    
    def test_event_can_add_after_callback(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.after(lambda: None)
        
        assert len(event.after_callbacks) == 1
    
    def test_event_can_set_description(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.description('Test task')
        
        assert event.get_description() == 'Test task'
    
    def test_event_without_overlapping(self):
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        
        event.without_overlapping()
        
        assert event.without_overlapping_enabled is True
        assert event.overlapping_expires_at == 1440


class TestCronExpressionParser:
    def test_parser_matches_every_minute(self):
        parser = CronExpressionParser('* * * * *')
        now = datetime(2025, 10, 24, 10, 30)
        
        assert parser.is_due(now) is True
    
    def test_parser_matches_specific_minute(self):
        parser = CronExpressionParser('30 * * * *')
        
        now_match = datetime(2025, 10, 24, 10, 30)
        now_no_match = datetime(2025, 10, 24, 10, 31)
        
        assert parser.is_due(now_match) is True
        assert parser.is_due(now_no_match) is False
    
    def test_parser_matches_specific_hour(self):
        parser = CronExpressionParser('0 10 * * *')
        
        now_match = datetime(2025, 10, 24, 10, 0)
        now_no_match = datetime(2025, 10, 24, 11, 0)
        
        assert parser.is_due(now_match) is True
        assert parser.is_due(now_no_match) is False
    
    def test_parser_matches_step_values(self):
        parser = CronExpressionParser('*/5 * * * *')
        
        now_match1 = datetime(2025, 10, 24, 10, 0)
        now_match2 = datetime(2025, 10, 24, 10, 5)
        now_match3 = datetime(2025, 10, 24, 10, 10)
        now_no_match = datetime(2025, 10, 24, 10, 3)
        
        assert parser.is_due(now_match1) is True
        assert parser.is_due(now_match2) is True
        assert parser.is_due(now_match3) is True
        assert parser.is_due(now_no_match) is False
    
    def test_parser_matches_range(self):
        parser = CronExpressionParser('0 9-17 * * *')
        
        now_match1 = datetime(2025, 10, 24, 9, 0)
        now_match2 = datetime(2025, 10, 24, 12, 0)
        now_match3 = datetime(2025, 10, 24, 17, 0)
        now_no_match1 = datetime(2025, 10, 24, 8, 0)
        now_no_match2 = datetime(2025, 10, 24, 18, 0)
        
        assert parser.is_due(now_match1) is True
        assert parser.is_due(now_match2) is True
        assert parser.is_due(now_match3) is True
        assert parser.is_due(now_no_match1) is False
        assert parser.is_due(now_no_match2) is False
    
    def test_parser_matches_list(self):
        parser = CronExpressionParser('0 9,12,17 * * *')
        
        now_match1 = datetime(2025, 10, 24, 9, 0)
        now_match2 = datetime(2025, 10, 24, 12, 0)
        now_match3 = datetime(2025, 10, 24, 17, 0)
        now_no_match = datetime(2025, 10, 24, 10, 0)
        
        assert parser.is_due(now_match1) is True
        assert parser.is_due(now_match2) is True
        assert parser.is_due(now_match3) is True
        assert parser.is_due(now_no_match) is False


class TestEventMutex:
    def test_mutex_can_create_lock(self):
        cache = MockCache()
        mutex = EventMutex(cache)
        
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        event.description('test task')
        
        result = mutex.create(event)
        
        assert result is True
        assert mutex.exists(event) is True
    
    def test_mutex_cannot_create_duplicate_lock(self):
        cache = MockCache()
        mutex = EventMutex(cache)
        
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        event.description('test task')
        
        mutex.create(event)
        result = mutex.create(event)
        
        assert result is False
    
    def test_mutex_can_forget_lock(self):
        cache = MockCache()
        mutex = EventMutex(cache)
        
        container = MockContainer()
        event = CommandEvent(container, 'test', [])
        event.description('test task')
        
        mutex.create(event)
        mutex.forget(event)
        
        assert mutex.exists(event) is False


class TestCallbackEvent:
    @pytest.mark.asyncio
    async def test_callback_event_runs_sync_callback(self):
        container = MockContainer()
        called = []
        
        def test_callback():
            called.append(True)
        
        event = CallbackEvent(container, test_callback, [])
        result = await event.run()
        
        assert result is True
        assert called == [True]
    
    @pytest.mark.asyncio
    async def test_callback_event_runs_async_callback(self):
        container = MockContainer()
        called = []
        
        async def test_callback():
            called.append(True)
        
        event = CallbackEvent(container, test_callback, [])
        result = await event.run()
        
        assert result is True
        assert called == [True]
    
    @pytest.mark.asyncio
    async def test_callback_event_passes_parameters(self):
        container = MockContainer()
        received = []
        
        def test_callback(arg1, arg2):
            received.append((arg1, arg2))
        
        event = CallbackEvent(container, test_callback, ['hello', 'world'])
        await event.run()
        
        assert received == [('hello', 'world')]
    
    @pytest.mark.asyncio
    async def test_callback_event_handles_exceptions(self):
        container = MockContainer()
        
        def test_callback():
            raise Exception('Test error')
        
        event = CallbackEvent(container, test_callback, [])
        result = await event.run()
        
        assert result is False


class TestScheduleRunner:
    @pytest.mark.asyncio
    async def test_runner_runs_due_events(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        called = []
        schedule.call(lambda: called.append(1))
        
        cache = MockCache()
        mutex = EventMutex(cache)
        runner = ScheduleRunner(schedule, mutex)
        
        results = await runner.run()
        
        assert results['total'] == 1
        assert results['ran'] == 1
        assert called == [1]
    
    @pytest.mark.asyncio
    async def test_runner_skips_overlapping_events(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        called = []
        schedule.call(lambda: called.append(1)).without_overlapping()
        
        cache = MockCache()
        mutex = EventMutex(cache)
        runner = ScheduleRunner(schedule, mutex)
        
        await runner.run()
        results = await runner.run()
        
        assert results['total'] == 1
        assert results['skipped'] == 1
        assert called == [1]
    
    @pytest.mark.asyncio
    async def test_runner_executes_before_callbacks(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        execution_order = []
        
        event = schedule.call(lambda: execution_order.append('main'))
        event.before(lambda: execution_order.append('before'))
        
        cache = MockCache()
        mutex = EventMutex(cache)
        runner = ScheduleRunner(schedule, mutex)
        
        await runner.run()
        
        assert execution_order == ['before', 'main']
    
    @pytest.mark.asyncio
    async def test_runner_executes_after_callbacks(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        execution_order = []
        
        event = schedule.call(lambda: execution_order.append('main'))
        event.after(lambda: execution_order.append('after'))
        
        cache = MockCache()
        mutex = EventMutex(cache)
        runner = ScheduleRunner(schedule, mutex)
        
        await runner.run()
        
        assert execution_order == ['main', 'after']
    
    @pytest.mark.asyncio
    async def test_runner_executes_success_callbacks(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        success_called = []
        
        event = schedule.call(lambda: True)
        event.on_success(lambda: success_called.append(True))
        
        cache = MockCache()
        mutex = EventMutex(cache)
        runner = ScheduleRunner(schedule, mutex)
        
        await runner.run()
        
        assert success_called == [True]


class TestScheduleIntegration:
    def test_schedule_with_multiple_events(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        schedule.command('test:command')
        schedule.call(lambda: None)
        schedule.exec('echo "test"')
        
        assert len(schedule.all_events()) == 3
    
    def test_schedule_filters_due_events(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        event1 = schedule.command('test1')
        event1.every_minute()
        
        event2 = schedule.command('test2')
        event2.hourly()
        
        now = datetime(2025, 10, 24, 10, 30)
        due = schedule.due_events(now)
        
        assert len(due) >= 1
    
    def test_schedule_applies_environment_filter(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        event = schedule.command('test')
        event.environments('testing', 'staging')
        
        assert len(event.filters) == 1
    
    def test_schedule_applies_time_constraints(self):
        container = MockContainer()
        schedule = Schedule(container)
        
        event = schedule.command('test')
        event.hourly().between('09:00', '17:00')
        
        assert len(event.filters) == 1
