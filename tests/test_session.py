import pytest
import os
import tempfile
import shutil
from larapy.session.store import Store
from larapy.session.array_session_handler import ArraySessionHandler
from larapy.session.file_session_handler import FileSessionHandler
from larapy.session.session_manager import SessionManager
from larapy.session.start_session import StartSession
from larapy.http.request import Request
from larapy.http.response import Response


class TestStore:
    def test_store_creation(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        assert store.getName() == 'test_session'
    
    def test_start_session(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        assert store.start() is True
        assert store.isStarted() is True
    
    def test_session_token_generation(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        assert store.token() is not None
        assert len(store.token()) == 40
    
    def test_put_and_get(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key', 'value')
        assert store.get('key') == 'value'
    
    def test_get_with_default(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        assert store.get('missing', 'default') == 'default'
    
    def test_get_with_callable_default(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        assert store.get('missing', lambda: 'computed') == 'computed'
    
    def test_has(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('exists', 'value')
        assert store.has('exists') is True
        assert store.has('missing') is False
    
    def test_exists(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key', None)
        assert store.exists('key') is True
        assert store.has('key') is False
    
    def test_missing(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        assert store.missing('nonexistent') is True
        store.put('exists', 'value')
        assert store.missing('exists') is False
    
    def test_all(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key1', 'value1')
        store.put('key2', 'value2')
        
        data = store.all()
        assert 'key1' in data
        assert 'key2' in data
    
    def test_put_multiple(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put({'key1': 'value1', 'key2': 'value2'})
        assert store.get('key1') == 'value1'
        assert store.get('key2') == 'value2'
    
    def test_pull(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key', 'value')
        value = store.pull('key')
        
        assert value == 'value'
        assert store.has('key') is False
    
    def test_push_to_array(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.push('items', 'first')
        store.push('items', 'second')
        
        assert store.get('items') == ['first', 'second']
    
    def test_increment(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('counter', 5)
        new_value = store.increment('counter')
        
        assert new_value == 6
        assert store.get('counter') == 6
    
    def test_increment_with_amount(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('counter', 10)
        store.increment('counter', 5)
        
        assert store.get('counter') == 15
    
    def test_decrement(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('counter', 10)
        new_value = store.decrement('counter')
        
        assert new_value == 9
        assert store.get('counter') == 9
    
    def test_forget(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key', 'value')
        store.forget('key')
        
        assert store.has('key') is False
    
    def test_forget_multiple(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key1', 'value1')
        store.put('key2', 'value2')
        store.forget(['key1', 'key2'])
        
        assert store.has('key1') is False
        assert store.has('key2') is False
    
    def test_flush(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key1', 'value1')
        store.put('key2', 'value2')
        store.flush()
        
        assert len(store.all()) == 0
    
    def test_flash_data(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.flash('message', 'Success!')
        assert store.get('message') == 'Success!'
    
    def test_flash_data_ages(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.flash('message', 'Success!')
        store.save()
        
        store2 = Store('test_session', handler, store.getId())
        store2.start()
        assert store2.get('message') == 'Success!'
        store2.save()
        
        store3 = Store('test_session', handler, store2.getId())
        store3.start()
        assert store3.has('message') is False
    
    def test_reflash(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.flash('message', 'Success!')
        store.save()
        
        store2 = Store('test_session', handler, store.getId())
        store2.start()
        store2.reflash()
        store2.save()
        
        store3 = Store('test_session', handler, store2.getId())
        store3.start()
        assert store3.get('message') == 'Success!'
    
    def test_keep_flash_data(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.flash('message', 'Success!')
        store.flash('status', 'Complete')
        store.save()
        
        store2 = Store('test_session', handler, store.getId())
        store2.start()
        store2.keep(['message'])
        store2.save()
        
        store3 = Store('test_session', handler, store2.getId())
        store3.start()
        assert store3.get('message') == 'Success!'
        assert store3.has('status') is False
    
    def test_now_flash(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.now('temp', 'value')
        assert store.get('temp') == 'value'
        store.save()
        
        store2 = Store('test_session', handler, store.getId())
        store2.start()
        assert store2.has('temp') is False
    
    def test_only(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key1', 'value1')
        store.put('key2', 'value2')
        store.put('key3', 'value3')
        
        data = store.only(['key1', 'key3'])
        assert data == {'key1': 'value1', 'key3': 'value3'}
    
    def test_except(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key1', 'value1')
        store.put('key2', 'value2')
        store.put('key3', 'value3')
        
        data = store.except_(['key2'])
        assert 'key1' in data
        assert 'key3' in data
        assert 'key2' not in data
    
    def test_regenerate_session_id(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        old_id = store.getId()
        store.regenerate()
        new_id = store.getId()
        
        assert old_id != new_id
    
    def test_invalidate_session(self):
        handler = ArraySessionHandler()
        store = Store('test_session', handler)
        store.start()
        
        store.put('key', 'value')
        old_id = store.getId()
        
        store.invalidate()
        
        assert store.getId() != old_id
        assert store.has('key') is False


class TestArraySessionHandler:
    def test_handler_creation(self):
        handler = ArraySessionHandler()
        assert handler is not None
    
    def test_read_write(self):
        handler = ArraySessionHandler()
        
        session_id = 'test_session_123'
        data = 'test_data'
        
        handler.write(session_id, data)
        result = handler.read(session_id)
        
        assert result == data
    
    def test_destroy(self):
        handler = ArraySessionHandler()
        
        session_id = 'test_session_123'
        handler.write(session_id, 'data')
        handler.destroy(session_id)
        
        assert handler.read(session_id) == ''


class TestFileSessionHandler:
    def test_handler_creation(self):
        temp_dir = tempfile.mkdtemp()
        try:
            handler = FileSessionHandler(temp_dir)
            assert handler is not None
        finally:
            shutil.rmtree(temp_dir)
    
    def test_read_write(self):
        temp_dir = tempfile.mkdtemp()
        try:
            handler = FileSessionHandler(temp_dir)
            
            session_id = 'test_session_123'
            data = 'test_data_content'
            
            handler.write(session_id, data)
            result = handler.read(session_id)
            
            assert result == data
        finally:
            shutil.rmtree(temp_dir)
    
    def test_destroy(self):
        temp_dir = tempfile.mkdtemp()
        try:
            handler = FileSessionHandler(temp_dir)
            
            session_id = 'test_session_123'
            handler.write(session_id, 'data')
            handler.destroy(session_id)
            
            assert handler.read(session_id) == ''
        finally:
            shutil.rmtree(temp_dir)
    
    def test_garbage_collection(self):
        temp_dir = tempfile.mkdtemp()
        try:
            handler = FileSessionHandler(temp_dir)
            
            handler.write('session1', 'data1')
            handler.write('session2', 'data2')
            
            deleted = handler.gc(0)
            
            assert deleted == 2
            assert handler.read('session1') == ''
        finally:
            shutil.rmtree(temp_dir)


class TestSessionManager:
    def test_manager_creation(self):
        manager = SessionManager()
        assert manager is not None
    
    def test_default_driver(self):
        manager = SessionManager()
        store = manager.driver()
        
        assert isinstance(store, Store)
    
    def test_array_driver(self):
        manager = SessionManager()
        manager.set_config({'driver': 'array'})
        
        store = manager.driver('array')
        assert isinstance(store, Store)
    
    def test_file_driver(self):
        temp_dir = tempfile.mkdtemp()
        try:
            manager = SessionManager()
            manager.set_config({
                'driver': 'file',
                'files': temp_dir
            })
            
            store = manager.driver('file')
            assert isinstance(store, Store)
        finally:
            shutil.rmtree(temp_dir)
    
    def test_custom_driver(self):
        manager = SessionManager()
        
        def create_custom_driver(container):
            return Store('custom', ArraySessionHandler())
        
        manager.extend('custom', create_custom_driver)
        store = manager.driver('custom')
        
        assert store.getName() == 'custom'


class TestStartSession:
    def test_middleware_creation(self):
        manager = SessionManager()
        middleware = StartSession(manager)
        assert middleware is not None
    
    def test_middleware_starts_session(self):
        manager = SessionManager()
        manager.set_config({'driver': 'array', 'cookie': 'test_session'})
        middleware = StartSession(manager)
        
        request = Request('/')
        
        def handler(req):
            assert req.session('_token') is not None
            return Response('OK')
        
        middleware.handle(request, handler)
    
    def test_middleware_saves_session(self):
        manager = SessionManager()
        manager.set_config({'driver': 'array', 'cookie': 'test_session'})
        middleware = StartSession(manager)
        
        request = Request('/')
        
        def handler(req):
            req._session['user_id'] = 123
            return Response('OK')
        
        response = middleware.handle(request, handler)
        cookies = response.getCookies()
        
        assert len(cookies) > 0


class TestComplexScenarios:
    def test_multi_request_session_persistence(self):
        handler = ArraySessionHandler()
        
        store1 = Store('test', handler)
        store1.start()
        store1.put('user_id', 1)
        store1.put('name', 'John')
        session_id = store1.getId()
        store1.save()
        
        store2 = Store('test', handler, session_id)
        store2.start()
        assert store2.get('user_id') == 1
        assert store2.get('name') == 'John'
    
    def test_flash_message_workflow(self):
        handler = ArraySessionHandler()
        
        store = Store('test', handler)
        store.start()
        store.flash('success', 'Profile updated successfully!')
        store.put('user_id', 1)
        session_id = store.getId()
        store.save()
        
        store2 = Store('test', handler, session_id)
        store2.start()
        assert store2.get('success') == 'Profile updated successfully!'
        assert store2.get('user_id') == 1
        store2.save()
        
        store3 = Store('test', handler, session_id)
        store3.start()
        assert store3.has('success') is False
        assert store3.get('user_id') == 1
    
    def test_old_input_form_repopulation(self):
        handler = ArraySessionHandler()
        
        store = Store('test', handler)
        store.start()
        
        old_input = {'name': 'John', 'email': 'john@example.com'}
        store.put('_old_input', old_input)
        session_id = store.getId()
        store.save()
        
        store2 = Store('test', handler, session_id)
        store2.start()
        assert store2.get('_old_input') == old_input
    
    def test_shopping_cart_session(self):
        handler = ArraySessionHandler()
        
        store = Store('cart', handler)
        store.start()
        
        store.push('cart.items', {'product_id': 1, 'quantity': 2})
        store.push('cart.items', {'product_id': 2, 'quantity': 1})
        store.put('cart.total', 150.00)
        
        session_id = store.getId()
        store.save()
        
        store2 = Store('cart', handler, session_id)
        store2.start()
        items = store2.get('cart.items')
        assert len(items) == 2
        assert store2.get('cart.total') == 150.00
    
    def test_csrf_token_management(self):
        handler = ArraySessionHandler()
        
        store = Store('test', handler)
        store.start()
        
        token = store.token()
        assert token is not None
        
        session_id = store.getId()
        store.save()
        
        store2 = Store('test', handler, session_id)
        store2.start()
        assert store2.token() == token
        
        store2.regenerateToken()
        new_token = store2.token()
        assert new_token != token
    
    def test_authentication_state(self):
        handler = ArraySessionHandler()
        
        store = Store('test', handler)
        store.start()
        
        store.put('authenticated', True)
        store.put('user', {'id': 1, 'name': 'John', 'role': 'admin'})
        store.flash('login_message', 'Welcome back!')
        
        session_id = store.getId()
        store.save()
        
        store2 = Store('test', handler, session_id)
        store2.start()
        
        assert store2.get('authenticated') is True
        user = store2.get('user')
        assert user['role'] == 'admin'
        assert store2.get('login_message') == 'Welcome back!'
    
    def test_session_regeneration_for_security(self):
        handler = ArraySessionHandler()
        
        store = Store('test', handler)
        store.start()
        store.put('user_id', 1)
        
        old_id = store.getId()
        store.regenerate(destroy=True)
        new_id = store.getId()
        
        assert old_id != new_id
        assert store.get('user_id') == 1
        
        old_store = Store('test', handler, old_id)
        old_store.start()
        assert old_store.has('user_id') is False
