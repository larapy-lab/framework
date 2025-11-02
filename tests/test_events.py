import pytest
from larapy.events import Dispatcher, Event, Dispatchable, EventSubscriber, event, set_event_dispatcher, EventServiceProvider
from larapy.container import Container
from larapy.foundation import Application


class UserRegistered(Event, Dispatchable):
    def __init__(self, user_id: int, email: str):
        self.user_id = user_id
        self.email = email


class OrderPlaced(Event, Dispatchable):
    def __init__(self, order_id: int, total: float):
        self.order_id = order_id
        self.total = total


class PaymentProcessed(Event, Dispatchable):
    def __init__(self, payment_id: int, amount: float):
        self.payment_id = payment_id
        self.amount = amount


class SendWelcomeEmail:
    def __init__(self):
        self.handled = False
        self.event_data = None
    
    def handle(self, event: UserRegistered):
        self.handled = True
        self.event_data = event
        return f"Welcome email sent to {event.email}"


class UpdateUserStatistics:
    def __init__(self):
        self.handled = False
    
    def handle(self, event: UserRegistered):
        self.handled = True
        return "Statistics updated"


class LogOrderPlaced:
    def handle(self, event: OrderPlaced):
        return f"Order {event.order_id} logged"


class UserEventSubscriber(EventSubscriber):
    def subscribe(self, dispatcher):
        return {
            'tests.test_events.UserRegistered': [
                self.on_user_registered,
                self.send_admin_notification,
            ]
        }
    
    def on_user_registered(self, event: UserRegistered):
        return f"Subscriber: User {event.user_id} registered"
    
    def send_admin_notification(self, event: UserRegistered):
        return "Admin notified"


class TestDispatcher:
    def test_can_create_dispatcher(self):
        dispatcher = Dispatcher()
        assert dispatcher is not None
    
    def test_can_listen_to_event(self):
        dispatcher = Dispatcher()
        calls = []
        
        def listener(event):
            calls.append(event)
        
        dispatcher.listen('user.registered', listener)
        assert dispatcher.has_listeners('user.registered')
    
    def test_can_dispatch_string_event(self):
        dispatcher = Dispatcher()
        results = []
        
        def listener(payload):
            results.append(payload)
            return "handled"
        
        dispatcher.listen('user.registered', listener)
        responses = dispatcher.dispatch('user.registered', {'user_id': 1})
        
        assert len(results) == 1
        assert results[0] == {'user_id': 1}
        assert responses == ["handled"]
    
    def test_can_dispatch_object_event(self):
        dispatcher = Dispatcher()
        results = []
        
        def listener(event):
            results.append(event)
            return f"User {event.user_id} registered"
        
        dispatcher.listen('tests.test_events.UserRegistered', listener)
        
        event_obj = UserRegistered(1, 'john@example.com')
        responses = dispatcher.dispatch(event_obj)
        
        assert len(results) == 1
        assert results[0].user_id == 1
        assert results[0].email == 'john@example.com'
        assert responses[0] == "User 1 registered"
    
    def test_multiple_listeners_for_same_event(self):
        dispatcher = Dispatcher()
        calls = []
        
        def listener1(event):
            calls.append('listener1')
            return 'response1'
        
        def listener2(event):
            calls.append('listener2')
            return 'response2'
        
        dispatcher.listen('user.registered', listener1)
        dispatcher.listen('user.registered', listener2)
        
        responses = dispatcher.dispatch('user.registered', {'user_id': 1})
        
        assert calls == ['listener1', 'listener2']
        assert responses == ['response1', 'response2']
    
    def test_listener_class_with_handle_method(self):
        dispatcher = Dispatcher()
        listener = SendWelcomeEmail()
        
        dispatcher.listen('tests.test_events.UserRegistered', listener)
        
        event_obj = UserRegistered(1, 'john@example.com')
        responses = dispatcher.dispatch(event_obj)
        
        assert listener.handled
        assert listener.event_data.email == 'john@example.com'
        assert responses[0] == "Welcome email sent to john@example.com"
    
    def test_dispatcher_with_container_resolves_listeners(self):
        container = Container()
        container.singleton(SendWelcomeEmail, SendWelcomeEmail)
        
        dispatcher = Dispatcher(container)
        dispatcher.listen('tests.test_events.UserRegistered', SendWelcomeEmail)
        
        event_obj = UserRegistered(1, 'jane@example.com')
        responses = dispatcher.dispatch(event_obj)
        
        assert len(responses) == 1
        assert "Welcome email sent to jane@example.com" in responses[0]
    
    def test_until_stops_on_first_non_null_response(self):
        dispatcher = Dispatcher()
        calls = []
        
        def listener1(event):
            calls.append('listener1')
            return None
        
        def listener2(event):
            calls.append('listener2')
            return 'stop_here'
        
        def listener3(event):
            calls.append('listener3')
            return 'not_reached'
        
        dispatcher.listen('test.event', listener1)
        dispatcher.listen('test.event', listener2)
        dispatcher.listen('test.event', listener3)
        
        result = dispatcher.until('test.event', {})
        
        assert calls == ['listener1', 'listener2']
        assert result == 'stop_here'
    
    def test_wildcard_listeners(self):
        dispatcher = Dispatcher()
        calls = []
        
        def wildcard_listener(event, event_name):
            calls.append(event_name)
            return f"Wildcard handled: {event_name}"
        
        dispatcher.listen('user.*', wildcard_listener)
        
        dispatcher.dispatch('user.registered', {'id': 1})
        dispatcher.dispatch('user.updated', {'id': 2})
        dispatcher.dispatch('user.deleted', {'id': 3})
        dispatcher.dispatch('order.placed', {'id': 4})
        
        assert 'user.registered' in calls
        assert 'user.updated' in calls
        assert 'user.deleted' in calls
        assert 'order.placed' not in calls
        assert len(calls) == 3
    
    def test_has_wildcard_listeners(self):
        dispatcher = Dispatcher()
        
        def listener(event):
            pass
        
        dispatcher.listen('app.*', listener)
        
        assert dispatcher.has_listeners('app.boot')
        assert dispatcher.has_listeners('app.ready')
        assert not dispatcher.has_listeners('user.registered')
    
    def test_forget_event_listeners(self):
        dispatcher = Dispatcher()
        
        def listener(event):
            return "handled"
        
        dispatcher.listen('user.registered', listener)
        assert dispatcher.has_listeners('user.registered')
        
        dispatcher.forget('user.registered')
        assert not dispatcher.has_listeners('user.registered')
    
    def test_flush_is_alias_for_forget(self):
        dispatcher = Dispatcher()
        
        def listener(event):
            return "handled"
        
        dispatcher.listen('user.registered', listener)
        dispatcher.flush('user.registered')
        
        assert not dispatcher.has_listeners('user.registered')
    
    def test_get_listeners_for_event(self):
        dispatcher = Dispatcher()
        
        def listener1(event):
            pass
        
        def listener2(event):
            pass
        
        dispatcher.listen('user.registered', listener1)
        dispatcher.listen('user.registered', listener2)
        
        listeners = dispatcher.get_listeners('user.registered')
        assert len(listeners) == 2
        assert listener1 in listeners
        assert listener2 in listeners
    
    def test_listen_to_multiple_events(self):
        dispatcher = Dispatcher()
        calls = []
        
        def listener(event):
            calls.append(event)
        
        dispatcher.listen(['user.registered', 'user.updated'], listener)
        
        dispatcher.dispatch('user.registered', {'id': 1})
        dispatcher.dispatch('user.updated', {'id': 2})
        
        assert len(calls) == 2
    
    def test_subscriber_registration(self):
        dispatcher = Dispatcher()
        subscriber = UserEventSubscriber()
        
        dispatcher.subscribe(subscriber)
        
        event_obj = UserRegistered(1, 'john@example.com')
        responses = dispatcher.dispatch(event_obj)
        
        assert len(responses) == 2
        assert "Subscriber: User 1 registered" in responses
        assert "Admin notified" in responses
    
    def test_subscriber_with_container(self):
        container = Container()
        dispatcher = Dispatcher(container)
        
        dispatcher.subscribe(UserEventSubscriber)
        
        event_obj = UserRegistered(1, 'jane@example.com')
        responses = dispatcher.dispatch(event_obj)
        
        assert len(responses) == 2


class TestEvent:
    def test_event_can_be_created(self):
        event_obj = UserRegistered(1, 'john@example.com')
        assert event_obj.user_id == 1
        assert event_obj.email == 'john@example.com'
    
    def test_event_inherits_from_event_base(self):
        event_obj = UserRegistered(1, 'john@example.com')
        assert isinstance(event_obj, Event)


class TestDispatchable:
    def test_dispatchable_dispatch_method(self):
        dispatcher = Dispatcher()
        set_event_dispatcher(dispatcher)
        
        results = []
        
        def listener(event):
            results.append(event)
            return "handled"
        
        dispatcher.listen('tests.test_events.UserRegistered', listener)
        
        UserRegistered.dispatch(1, 'john@example.com')
        
        assert len(results) == 1
        assert results[0].user_id == 1
        assert results[0].email == 'john@example.com'
    
    def test_dispatch_if_when_true(self):
        dispatcher = Dispatcher()
        set_event_dispatcher(dispatcher)
        
        results = []
        
        def listener(event):
            results.append(event)
        
        dispatcher.listen('tests.test_events.UserRegistered', listener)
        
        UserRegistered.dispatch_if(True, 1, 'john@example.com')
        
        assert len(results) == 1
    
    def test_dispatch_if_when_false(self):
        dispatcher = Dispatcher()
        set_event_dispatcher(dispatcher)
        
        results = []
        
        def listener(event):
            results.append(event)
        
        dispatcher.listen('tests.test_events.UserRegistered', listener)
        
        UserRegistered.dispatch_if(False, 1, 'john@example.com')
        
        assert len(results) == 0
    
    def test_dispatch_unless_when_true(self):
        dispatcher = Dispatcher()
        set_event_dispatcher(dispatcher)
        
        results = []
        
        def listener(event):
            results.append(event)
        
        dispatcher.listen('tests.test_events.UserRegistered', listener)
        
        UserRegistered.dispatch_unless(True, 1, 'john@example.com')
        
        assert len(results) == 0
    
    def test_dispatch_unless_when_false(self):
        dispatcher = Dispatcher()
        set_event_dispatcher(dispatcher)
        
        results = []
        
        def listener(event):
            results.append(event)
        
        dispatcher.listen('tests.test_events.UserRegistered', listener)
        
        UserRegistered.dispatch_unless(False, 1, 'john@example.com')
        
        assert len(results) == 1


class TestEventHelper:
    def test_event_helper_returns_dispatcher_when_no_args(self):
        dispatcher = Dispatcher()
        set_event_dispatcher(dispatcher)
        
        result = event()
        assert result is dispatcher
    
    def test_event_helper_dispatches_event(self):
        dispatcher = Dispatcher()
        set_event_dispatcher(dispatcher)
        
        results = []
        
        def listener(ev):
            results.append(ev)
            return "handled"
        
        dispatcher.listen('tests.test_events.OrderPlaced', listener)
        
        event_obj = OrderPlaced(1, 99.99)
        responses = event(event_obj)
        
        assert len(results) == 1
        assert results[0].order_id == 1
        assert responses[0] == "handled"
    
    def test_event_helper_with_halt(self):
        dispatcher = Dispatcher()
        set_event_dispatcher(dispatcher)
        
        calls = []
        
        def listener1(ev):
            calls.append('listener1')
            return 'stop'
        
        def listener2(ev):
            calls.append('listener2')
        
        dispatcher.listen('test.event', listener1)
        dispatcher.listen('test.event', listener2)
        
        result = event('test.event', {}, halt=True)
        
        assert calls == ['listener1']
        assert result == 'stop'
    
    def test_event_helper_raises_error_if_dispatcher_not_set(self):
        set_event_dispatcher(None)
        
        with pytest.raises(RuntimeError, match="Event dispatcher not set"):
            event('test.event')


class TestComplexScenarios:
    def test_event_driven_user_registration_flow(self):
        container = Container()
        dispatcher = Dispatcher(container)
        set_event_dispatcher(dispatcher)
        
        welcome_email = SendWelcomeEmail()
        statistics = UpdateUserStatistics()
        
        container.instance(SendWelcomeEmail, welcome_email)
        container.instance(UpdateUserStatistics, statistics)
        
        dispatcher.listen('tests.test_events.UserRegistered', SendWelcomeEmail)
        dispatcher.listen('tests.test_events.UserRegistered', UpdateUserStatistics)
        
        user_event = UserRegistered(100, 'newuser@example.com')
        responses = event(user_event)
        
        assert welcome_email.handled
        assert welcome_email.event_data.user_id == 100
        assert statistics.handled
        assert len(responses) == 2
    
    def test_wildcard_logger_with_specific_handlers(self):
        dispatcher = Dispatcher()
        log_calls = []
        specific_calls = []
        
        def log_all(ev, event_name):
            log_calls.append(event_name)
        
        def handle_user_registered(ev):
            specific_calls.append(ev)
        
        dispatcher.listen('*', log_all)
        dispatcher.listen('tests.test_events.UserRegistered', handle_user_registered)
        
        UserRegistered.dispatch = classmethod(lambda cls, *args, **kwargs: dispatcher.dispatch(cls(*args, **kwargs)))
        
        dispatcher.dispatch(UserRegistered(1, 'john@example.com'))
        dispatcher.dispatch(OrderPlaced(1, 99.99))
        
        assert len(log_calls) == 2
        assert len(specific_calls) == 1
        assert specific_calls[0].user_id == 1
    
    def test_multiple_event_types_with_subscriber(self):
        class MultiEventSubscriber(EventSubscriber):
            def __init__(self):
                self.user_events = []
                self.order_events = []
            
            def subscribe(self, dispatcher):
                return {
                    'tests.test_events.UserRegistered': self.on_user_registered,
                    'tests.test_events.OrderPlaced': self.on_order_placed,
                }
            
            def on_user_registered(self, event):
                self.user_events.append(event)
                return "user_handled"
            
            def on_order_placed(self, event):
                self.order_events.append(event)
                return "order_handled"
        
        dispatcher = Dispatcher()
        subscriber = MultiEventSubscriber()
        dispatcher.subscribe(subscriber)
        
        dispatcher.dispatch(UserRegistered(1, 'john@example.com'))
        dispatcher.dispatch(OrderPlaced(1, 99.99))
        dispatcher.dispatch(UserRegistered(2, 'jane@example.com'))
        
        assert len(subscriber.user_events) == 2
        assert len(subscriber.order_events) == 1
    
    def test_event_with_false_return_is_excluded(self):
        dispatcher = Dispatcher()
        calls = []
        
        def listener1(event):
            calls.append('listener1')
            return False
        
        def listener2(event):
            calls.append('listener2')
            return "response2"
        
        dispatcher.listen('test.event', listener1)
        dispatcher.listen('test.event', listener2)
        
        responses = dispatcher.dispatch('test.event', {})
        
        assert calls == ['listener1', 'listener2']
        assert len(responses) == 1
        assert responses[0] == "response2"
    
    def test_nested_wildcard_patterns(self):
        dispatcher = Dispatcher()
        app_calls = []
        user_calls = []
        
        def app_listener(ev, name):
            app_calls.append(name)
        
        def user_listener(ev, name):
            user_calls.append(name)
        
        dispatcher.listen('app.*', app_listener)
        dispatcher.listen('app.user.*', user_listener)
        
        dispatcher.dispatch('app.boot', {})
        dispatcher.dispatch('app.user.registered', {})
        dispatcher.dispatch('app.user.updated', {})
        dispatcher.dispatch('app.ready', {})
        
        assert len(app_calls) == 4
        assert len(user_calls) == 2
    
    def test_listener_with_no_parameters(self):
        dispatcher = Dispatcher()
        calls = []
        
        def listener_no_params():
            calls.append('called')
            return "handled"
        
        dispatcher.listen('test.event', listener_no_params)
        responses = dispatcher.dispatch('test.event', {})
        
        assert calls == ['called']
        assert responses[0] == "handled"
    
    def test_listener_with_event_and_name_parameters(self):
        dispatcher = Dispatcher()
        results = []
        
        def listener(event, event_name):
            results.append({'event': event, 'name': event_name})
            return "handled"
        
        dispatcher.listen('user.registered', listener)
        dispatcher.dispatch('user.registered', {'user_id': 1})
        
        assert len(results) == 1
        assert results[0]['event'] == {'user_id': 1}
        assert results[0]['name'] == 'user.registered'


class TestEventServiceProvider:
    def test_registers_event_dispatcher_in_container(self):
        app = Application('/tmp/test')
        provider = EventServiceProvider(app)
        
        provider.register()
        
        assert app.bound('events')
        dispatcher = app.make('events')
        assert isinstance(dispatcher, Dispatcher)
    
    def test_boots_dispatcher_with_listeners(self):
        app = Application('/tmp/test')
        
        class TestEventProvider(EventServiceProvider):
            def __init__(self, app):
                super().__init__(app)
                self.listen = {
                    'tests.test_events.UserRegistered': [SendWelcomeEmail, UpdateUserStatistics]
                }
        
        welcome = SendWelcomeEmail()
        stats = UpdateUserStatistics()
        app.instance(SendWelcomeEmail, welcome)
        app.instance(UpdateUserStatistics, stats)
        
        provider = TestEventProvider(app)
        provider.register()
        provider.boot()
        
        user_event = UserRegistered(1, 'test@example.com')
        event(user_event)
        
        assert welcome.handled
        assert stats.handled
    
    def test_boots_dispatcher_with_subscribers(self):
        app = Application('/tmp/test')
        
        class TestEventProvider(EventServiceProvider):
            def __init__(self, app):
                super().__init__(app)
                self.subscribe = [UserEventSubscriber]
        
        provider = TestEventProvider(app)
        provider.register()
        provider.boot()
        
        user_event = UserRegistered(1, 'test@example.com')
        responses = event(user_event)
        
        assert len(responses) == 2
        assert "Subscriber: User 1 registered" in responses
        assert "Admin notified" in responses
    
    def test_single_listener_without_list(self):
        app = Application('/tmp/test')
        
        class TestEventProvider(EventServiceProvider):
            def __init__(self, app):
                super().__init__(app)
                self.listen = {
                    'tests.test_events.UserRegistered': SendWelcomeEmail
                }
        
        welcome = SendWelcomeEmail()
        app.instance(SendWelcomeEmail, welcome)
        
        provider = TestEventProvider(app)
        provider.register()
        provider.boot()
        
        user_event = UserRegistered(1, 'test@example.com')
        event(user_event)
        
        assert welcome.handled
    
    def test_dispatcher_uses_application_container(self):
        app = Application('/tmp/test')
        provider = EventServiceProvider(app)
        
        provider.register()
        
        dispatcher = app.make('events')
        assert dispatcher._container is app
    
    def test_event_helper_set_after_boot(self):
        app = Application('/tmp/test')
        provider = EventServiceProvider(app)
        
        provider.register()
        provider.boot()
        
        dispatcher = event()
        assert dispatcher is not None
        assert isinstance(dispatcher, Dispatcher)
