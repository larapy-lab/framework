import unittest
import time
from larapy.cache.rate_limiter import RateLimiter, Limit
from larapy.ratelimiting import RateLimit


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
        else:
            self.store[key] = {'value': new_value, 'expires': time.time() + 3600}
        
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


class TestRateLimitFacade(unittest.TestCase):
    
    def setUp(self):
        self.cache = MockCache()
        self.limiter = RateLimiter(self.cache)
        RateLimit.set_limiter(self.limiter)
    
    def test_facade_for_registers_named_limiter(self):
        def limiter_callback(request):
            return Limit.per_minute(10)
        
        RateLimit.for_('test', limiter_callback)
        
        registered = self.limiter.limiter('test')
        self.assertIsNotNone(registered)
        self.assertEqual(registered, limiter_callback)
    
    def test_facade_attempt_executes_callback_when_allowed(self):
        executed = []
        
        def callback():
            executed.append(True)
            return True
        
        result = RateLimit.attempt('test-key', 5, callback)
        
        self.assertTrue(result)
        self.assertEqual(len(executed), 1)
    
    def test_facade_attempt_blocks_when_rate_exceeded(self):
        executed = []
        
        def callback():
            executed.append(True)
            return True
        
        for _ in range(5):
            RateLimit.attempt('test-key', 5, callback)
        
        result = RateLimit.attempt('test-key', 5, callback)
        
        self.assertFalse(result)
        self.assertEqual(len(executed), 5)
    
    def test_facade_too_many_attempts_checks_limit(self):
        for _ in range(3):
            RateLimit.hit('test-key')
        
        self.assertFalse(RateLimit.too_many_attempts('test-key', 5))
        self.assertTrue(RateLimit.too_many_attempts('test-key', 3))
    
    def test_facade_hit_increments_attempts(self):
        hits = RateLimit.hit('test-key')
        self.assertEqual(hits, 1)
        
        hits = RateLimit.hit('test-key')
        self.assertEqual(hits, 2)
    
    def test_facade_attempts_returns_current_count(self):
        RateLimit.hit('test-key')
        RateLimit.hit('test-key')
        
        self.assertEqual(RateLimit.attempts('test-key'), 2)
    
    def test_facade_reset_attempts_clears_count(self):
        RateLimit.hit('test-key')
        RateLimit.hit('test-key')
        
        RateLimit.reset_attempts('test-key')
        
        self.assertEqual(RateLimit.attempts('test-key'), 0)
    
    def test_facade_remaining_calculates_correctly(self):
        RateLimit.hit('test-key')
        RateLimit.hit('test-key')
        
        self.assertEqual(RateLimit.remaining('test-key', 5), 3)
    
    def test_facade_available_in_returns_wait_time(self):
        RateLimit.hit('test-key', 60)
        
        available_in = RateLimit.available_in('test-key')
        
        self.assertGreater(available_in, 0)
        self.assertLessEqual(available_in, 60)
    
    def test_facade_clear_removes_all_data(self):
        RateLimit.hit('test-key')
        
        RateLimit.clear('test-key')
        
        self.assertEqual(RateLimit.attempts('test-key'), 0)
        self.assertEqual(RateLimit.available_in('test-key'), 0)


class TestLimitEnhancements(unittest.TestCase):
    
    def test_per_minutes_creates_custom_limit(self):
        limit = Limit.per_minutes(100, 5)
        
        self.assertEqual(limit.max_attempts, 100)
        self.assertEqual(limit.decay_minutes, 5)
    
    def test_limit_chaining_multiple_methods(self):
        def response_callback():
            return {'error': 'Rate limit exceeded'}
        
        limit = Limit.per_minute(60).by('user:123').response(response_callback)
        
        self.assertEqual(limit.max_attempts, 60)
        self.assertEqual(limit.decay_minutes, 1)
        self.assertEqual(limit.key, 'user:123')
        self.assertEqual(limit.response_callback, response_callback)
    
    def test_limit_by_converts_int_to_string(self):
        limit = Limit.per_minute(60).by(12345)
        
        self.assertEqual(limit.key, '12345')
    
    def test_limit_by_handles_none(self):
        limit = Limit.per_minute(60).by(None)
        
        self.assertEqual(limit.key, 'None')


class TestRateLimiterEnhancements(unittest.TestCase):
    
    def setUp(self):
        self.cache = MockCache()
        self.limiter = RateLimiter(self.cache)
    
    def test_remaining_alias_works(self):
        self.limiter.hit('test-key')
        self.limiter.hit('test-key')
        
        remaining = self.limiter.remaining('test-key', 10)
        remaining_attempts = self.limiter.remaining_attempts('test-key', 10)
        
        self.assertEqual(remaining, remaining_attempts)
        self.assertEqual(remaining, 8)
    
    def test_for_alias_works(self):
        def callback(request):
            return Limit.per_minute(10)
        
        result1 = self.limiter.for_('test', callback)
        result2 = self.limiter.for_rate('test2', callback)
        
        self.assertEqual(result1, self.limiter)
        self.assertEqual(result2, self.limiter)
        self.assertIsNotNone(self.limiter.limiter('test'))
        self.assertIsNotNone(self.limiter.limiter('test2'))
    
    def test_concurrent_keys_independent(self):
        for _ in range(3):
            self.limiter.hit('user:1')
        
        for _ in range(5):
            self.limiter.hit('user:2')
        
        self.assertEqual(self.limiter.attempts('user:1'), 3)
        self.assertEqual(self.limiter.attempts('user:2'), 5)
    
    def test_rate_limit_respects_decay(self):
        self.limiter.hit('test-key', 1)
        self.assertEqual(self.limiter.attempts('test-key'), 1)
        
        time.sleep(1.1)
        
        self.assertEqual(self.limiter.attempts('test-key'), 0)
    
    def test_reset_clears_both_attempts_and_timer(self):
        self.limiter.hit('test-key', 60)
        
        self.assertGreater(self.limiter.attempts('test-key'), 0)
        self.assertGreater(self.limiter.available_in('test-key'), 0)
        
        self.limiter.reset_attempts('test-key')
        
        self.assertEqual(self.limiter.attempts('test-key'), 0)
        self.assertEqual(self.limiter.available_in('test-key'), 0)


class TestRateLimitingEdgeCases(unittest.TestCase):
    
    def setUp(self):
        self.cache = MockCache()
        self.limiter = RateLimiter(self.cache)
    
    def test_zero_max_attempts_always_blocks(self):
        self.limiter.hit('test-key')
        self.assertTrue(self.limiter.too_many_attempts('test-key', 0))
    
    def test_negative_max_attempts_always_blocks(self):
        self.limiter.hit('test-key')
        self.assertTrue(self.limiter.too_many_attempts('test-key', -1))
    
    def test_very_large_max_attempts(self):
        max_attempts = 1000000
        
        for _ in range(100):
            self.limiter.hit('test-key')
        
        self.assertFalse(self.limiter.too_many_attempts('test-key', max_attempts))
        self.assertEqual(self.limiter.remaining('test-key', max_attempts), max_attempts - 100)
    
    def test_empty_key_string(self):
        self.limiter.hit('')
        self.assertEqual(self.limiter.attempts(''), 1)
    
    def test_special_characters_in_key(self):
        key = 'user:123@email.com|/api/resource'
        
        self.limiter.hit(key)
        self.assertEqual(self.limiter.attempts(key), 1)
    
    def test_unicode_in_key(self):
        key = 'user:测试用户'
        
        self.limiter.hit(key)
        self.assertEqual(self.limiter.attempts(key), 1)
    
    def test_multiple_limiters_same_key_prefix(self):
        self.limiter.hit('api:user:1')
        self.limiter.hit('api:user:10')
        self.limiter.hit('api:user:100')
        
        self.assertEqual(self.limiter.attempts('api:user:1'), 1)
        self.assertEqual(self.limiter.attempts('api:user:10'), 1)
        self.assertEqual(self.limiter.attempts('api:user:100'), 1)


if __name__ == '__main__':
    unittest.main()
