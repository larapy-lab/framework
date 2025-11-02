import time
import pytest
from larapy.cache.rate_limiter import RateLimiter, Limit


class MockCache:
    
    def __init__(self):
        self.store = {}
    
    def add(self, key: str, value, seconds: int) -> bool:
        if key not in self.store:
            self.store[key] = {'value': value, 'expires': time.time() + seconds}
            return True
        return False
    
    def get(self, key: str, default=None):
        if key in self.store:
            item = self.store[key]
            if item['expires'] > time.time():
                return item['value']
            del self.store[key]
        return default
    
    def put(self, key: str, value, seconds: int):
        self.store[key] = {'value': value, 'expires': time.time() + seconds}
    
    def increment(self, key: str, amount: int = 1):
        current = self.get(key, 0)
        current_value = 0 if current is None else int(current)
        new_value = current_value + amount
        
        if key in self.store:
            self.store[key]['value'] = new_value
        
        return new_value
    
    def forget(self, key: str):
        if key in self.store:
            del self.store[key]
    
    def has(self, key: str) -> bool:
        if key in self.store:
            item = self.store[key]
            if item['expires'] > time.time():
                return True
            del self.store[key]
        return False
    
    def flush(self):
        self.store = {}


class TestRateLimiter:
    
    def setup_method(self):
        self.cache = MockCache()
        self.limiter = RateLimiter(self.cache)
    
    def test_attempt_allows_requests_within_limit(self):
        key = 'test_key'
        max_attempts = 5
        
        for i in range(max_attempts):
            assert self.limiter.attempt(key, max_attempts, 60) is True
        
        assert self.limiter.attempt(key, max_attempts, 60) is False
    
    def test_too_many_attempts_blocks_requests(self):
        key = 'test_key'
        max_attempts = 3
        
        for i in range(max_attempts):
            self.limiter.hit(key, 60)
        
        assert self.limiter.too_many_attempts(key, max_attempts) is True
    
    def test_hit_increments_attempts(self):
        key = 'test_key'
        
        assert self.limiter.attempts(key) == 0
        
        self.limiter.hit(key, 60)
        assert self.limiter.attempts(key) == 1
        
        self.limiter.hit(key, 60)
        assert self.limiter.attempts(key) == 2
        
        self.limiter.hit(key, 60)
        assert self.limiter.attempts(key) == 3
    
    def test_attempts_returns_zero_for_new_key(self):
        key = 'new_key'
        assert self.limiter.attempts(key) == 0
    
    def test_reset_attempts_clears_counter(self):
        key = 'test_key'
        
        for i in range(5):
            self.limiter.hit(key, 60)
        
        assert self.limiter.attempts(key) == 5
        
        self.limiter.reset_attempts(key)
        
        assert self.limiter.attempts(key) == 0
    
    def test_remaining_attempts_calculation(self):
        key = 'test_key'
        max_attempts = 10
        
        assert self.limiter.remaining_attempts(key, max_attempts) == 10
        
        self.limiter.hit(key, 60)
        assert self.limiter.remaining_attempts(key, max_attempts) == 9
        
        for i in range(4):
            self.limiter.hit(key, 60)
        
        assert self.limiter.remaining_attempts(key, max_attempts) == 5
    
    def test_remaining_attempts_never_negative(self):
        key = 'test_key'
        max_attempts = 3
        
        for i in range(10):
            self.limiter.hit(key, 60)
        
        assert self.limiter.remaining_attempts(key, max_attempts) == 0
    
    def test_available_in_returns_wait_time(self):
        key = 'test_key'
        max_attempts = 1
        decay_seconds = 60
        
        self.limiter.hit(key, decay_seconds)
        self.limiter.hit(key, decay_seconds)
        
        available_in = self.limiter.available_in(key)
        
        assert available_in > 0
        assert available_in <= decay_seconds
    
    def test_available_in_returns_zero_when_not_locked(self):
        key = 'unlocked_key'
        
        assert self.limiter.available_in(key) == 0
    
    def test_clear_is_alias_for_reset_attempts(self):
        key = 'test_key'
        
        for i in range(5):
            self.limiter.hit(key, 60)
        
        assert self.limiter.attempts(key) == 5
        
        self.limiter.clear(key)
        
        assert self.limiter.attempts(key) == 0
    
    def test_decay_expires_rate_limit(self):
        key = 'test_key'
        max_attempts = 2
        decay_seconds = 1
        
        self.limiter.hit(key, decay_seconds)
        self.limiter.hit(key, decay_seconds)
        
        assert self.limiter.too_many_attempts(key, max_attempts) is True
        
        time.sleep(1.1)
        
        assert self.limiter.too_many_attempts(key, max_attempts) is False
    
    def test_multiple_keys_isolated(self):
        key1 = 'user_1'
        key2 = 'user_2'
        max_attempts = 3
        
        for i in range(max_attempts):
            self.limiter.hit(key1, 60)
        
        assert self.limiter.too_many_attempts(key1, max_attempts) is True
        assert self.limiter.too_many_attempts(key2, max_attempts) is False
        
        assert self.limiter.attempts(key1) == 3
        assert self.limiter.attempts(key2) == 0
    
    def test_named_limiter_registration(self):
        def limiter_callback(request):
            return Limit.per_minute(10)
        
        self.limiter.for_rate('api', limiter_callback)
        
        registered = self.limiter.limiter('api')
        
        assert registered is not None
        assert callable(registered)
    
    def test_named_limiter_returns_none_if_not_found(self):
        result = self.limiter.limiter('nonexistent')
        
        assert result is None
    
    def test_for_rate_returns_limiter_instance(self):
        def callback(request):
            return Limit.per_minute(5)
        
        result = self.limiter.for_rate('test', callback)
        
        assert result is self.limiter


class TestLimit:
    
    def test_per_minute_creates_limit(self):
        limit = Limit.per_minute(60)
        
        assert limit.max_attempts == 60
        assert limit.decay_minutes == 1
    
    def test_per_hour_creates_limit(self):
        limit = Limit.per_hour(1000)
        
        assert limit.max_attempts == 1000
        assert limit.decay_minutes == 60
    
    def test_per_day_creates_limit(self):
        limit = Limit.per_day(10000)
        
        assert limit.max_attempts == 10000
        assert limit.decay_minutes == 1440
    
    def test_per_second_creates_limit(self):
        limit = Limit.per_second(10)
        
        assert limit.max_attempts == 10
        assert limit.decay_minutes < 1
    
    def test_none_creates_unlimited_limit(self):
        limit = Limit.none()
        
        assert limit.max_attempts == 999999999
    
    def test_by_sets_custom_key(self):
        limit = Limit.per_minute(60).by('user_123')
        
        assert limit.key == 'user_123'
    
    def test_by_converts_to_string(self):
        limit = Limit.per_minute(60).by(456)
        
        assert limit.key == '456'
    
    def test_response_sets_callback(self):
        def custom_response(request):
            return {'error': 'Rate limit exceeded'}
        
        limit = Limit.per_minute(60).response(custom_response)
        
        assert limit.response_callback is custom_response
    
    def test_limit_chaining(self):
        def custom_response(request):
            return {'error': 'Too many requests'}
        
        limit = Limit.per_minute(100).by('user_789').response(custom_response)
        
        assert limit.max_attempts == 100
        assert limit.decay_minutes == 1
        assert limit.key == 'user_789'
        assert limit.response_callback is custom_response
