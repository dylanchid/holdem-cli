# Performance Guide

Comprehensive guide to performance optimization and monitoring for Holdem CLI.

## Performance Targets

### Core Benchmarks
- **Equity Calculation**: Complete within 2 seconds on modern hardware
- **Quiz Generation**: Generate questions in < 100ms
- **Database Queries**: Execute in < 50ms
- **Memory Usage**: Stay under 100MB for typical usage

### Target Hardware
- **Minimum**: 1GB RAM, Dual-core CPU
- **Recommended**: 2GB RAM, Quad-core CPU
- **CI/Build**: Apple Silicon M1/M2 or equivalent

## Performance Monitoring

### Built-in Profiling
```python
# Enable performance profiling
export HOLDEM_PROFILE=1
holdem equity AKs QQ --iterations 10000
```

### External Profiling Tools
```bash
# Profile with cProfile
python -m cProfile -s time src/holdem_cli/cli.py equity AKs QQ

# Memory profiling
python -m memory_profiler src/holdem_cli/cli.py equity AKs QQ

# Line-by-line profiling
python -m line_profiler src/holdem_cli/engine/equity.py
```

## Optimization Strategies

### 1. Algorithm Optimization

#### Equity Calculation
```python
# Optimized Monte Carlo simulation
def calculate_equity_optimized(hand1, hand2, board=None, iterations=25000):
    # Pre-compute card masks for faster lookup
    hand1_mask = create_card_mask(hand1)
    hand2_mask = create_card_mask(hand2)

    # Use vectorized operations where possible
    equity_samples = np.zeros(iterations)

    for i in range(iterations):
        # Fast deck sampling
        remaining_deck = get_remaining_deck(hand1_mask | hand2_mask | board_mask)
        sample_board = sample_cards(remaining_deck, 5 - len(board or []))

        # Evaluate hands quickly
        hand1_rank = evaluate_hand(hand1 + sample_board)
        hand2_rank = evaluate_hand(hand2 + sample_board)

        equity_samples[i] = hand1_rank > hand2_rank

    return np.mean(equity_samples)
```

### 2. Memory Optimization

#### Object Reuse
```python
# Reuse objects to reduce memory allocation
class CardPool:
    _instances = {}

    @classmethod
    def get_card(cls, rank, suit):
        key = (rank, suit)
        if key not in cls._instances:
            cls._instances[key] = Card(rank, suit)
        return cls._instances[key]
```

#### Generator Usage
```python
# Use generators for large datasets
def generate_hand_combinations(range_notation):
    """Generate hands without storing all in memory."""
    for hand in parse_range_notation(range_notation):
        yield hand

# Instead of:
# all_hands = list(parse_range_notation(range_notation))
```

### 3. Database Optimization

#### Query Optimization
```python
# Use indexed queries
def get_user_stats_optimized(user_id):
    query = """
    SELECT
        COUNT(*) as total_quizzes,
        AVG(score) as avg_score,
        MAX(created_at) as last_quiz
    FROM quiz_sessions
    WHERE user_id = ?
    """
    return db.execute(query, (user_id,)).fetchone()

# Avoid N+1 queries
def get_users_with_stats():
    query = """
    SELECT
        u.name,
        qs.total_quizzes,
        qs.avg_score
    FROM users u
    LEFT JOIN (
        SELECT
            user_id,
            COUNT(*) as total_quizzes,
            AVG(score) as avg_score
        FROM quiz_sessions
        GROUP BY user_id
    ) qs ON u.id = qs.user_id
    """
    return db.execute(query).fetchall()
```

#### Connection Pooling
```python
import sqlite3
from contextlib import contextmanager

class DatabasePool:
    def __init__(self, db_path, max_connections=5):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = []

    @contextmanager
    def get_connection(self):
        if self.connections:
            conn = self.connections.pop()
        else:
            conn = sqlite3.connect(self.db_path)

        try:
            yield conn
        finally:
            if len(self.connections) < self.max_connections:
                self.connections.append(conn)
            else:
                conn.close()
```

## Caching Strategies

### 1. In-Memory Caching
```python
from functools import lru_cache
import time

class CachedEquityCalculator:
    @lru_cache(maxsize=1000)
    def calculate_equity_cached(self, hand1_key, hand2_key, board_key, iterations):
        # Convert hands to hashable keys
        hand1 = decode_hand_key(hand1_key)
        hand2 = decode_hand_key(hand2_key)
        board = decode_board_key(board_key) if board_key else None

        return self._calculate_equity(hand1, hand2, board, iterations)

    def calculate_equity(self, hand1, hand2, board=None, iterations=25000):
        # Create cache keys
        hand1_key = create_hand_key(hand1)
        hand2_key = create_hand_key(hand2)
        board_key = create_board_key(board) if board else None

        return self.calculate_equity_cached(hand1_key, hand2_key, board_key, iterations)
```

### 2. File-Based Caching
```python
import json
import hashlib

class FileCache:
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_key(self, data):
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def get(self, key):
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                cached = json.load(f)
            if time.time() - cached['timestamp'] < 3600:  # 1 hour
                return cached['data']
        return None

    def set(self, key, data):
        cache_file = self.cache_dir / f"{key}.json"
        cached = {
            'timestamp': time.time(),
            'data': data
        }
        with open(cache_file, 'w') as f:
            json.dump(cached, f)
```

## Performance Testing

### Benchmark Suite
```python
import time
import pytest

def benchmark_equity_calculation():
    """Benchmark equity calculation performance."""
    hand1 = [Card('As'), Card('Ks')]
    hand2 = [Card('Ah'), Card('Kh')]

    start_time = time.perf_counter()
    equity = calculate_equity(hand1, hand2, iterations=25000)
    end_time = time.perf_counter()

    execution_time = end_time - start_time
    assert execution_time < 2.0  # Must complete within 2 seconds
    assert 0.4 <= equity <= 0.6  # Should be close to 50%

def benchmark_memory_usage():
    """Test memory usage during equity calculations."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Run multiple calculations
    for _ in range(100):
        hand1 = [Card('As'), Card('Ks')]
        hand2 = [Card('Ah'), Card('Kh')]
        calculate_equity(hand1, hand2, iterations=1000)

    final_memory = process.memory_info().rss
    memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

    assert memory_increase < 50  # Less than 50MB increase
```

### Performance Regression Testing
```bash
# Run performance tests
pytest tests/performance/ -v

# Generate performance report
pytest tests/performance/ --benchmark-save=baseline
pytest tests/performance/ --benchmark-compare=baseline

# Continuous integration
# Compare against baseline performance
```

## Optimization Techniques

### 1. Vectorization
```python
import numpy as np

# Vectorized equity calculation
def calculate_equity_vectorized(hand1, hand2, iterations=25000):
    # Simulate multiple hands at once
    deck = np.arange(52)
    np.random.shuffle(deck)

    # Vectorized hand evaluation
    hand1_values = evaluate_hands_batch(hand1_cards, boards)
    hand2_values = evaluate_hands_batch(hand2_cards, boards)

    wins = np.sum(hand1_values > hand2_values)
    ties = np.sum(hand1_values == hand2_values)

    return wins / iterations, ties / iterations
```

### 2. JIT Compilation
```python
from numba import jit, int32

@jit(nopython=True)
def evaluate_hand_fast(cards):
    """Fast hand evaluation with JIT compilation."""
    # Optimized hand evaluation logic
    # Avoid Python objects and use primitive types
    pass
```

### 3. Async Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncEquityCalculator:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def calculate_equity_async(self, hand1, hand2, iterations=25000):
        loop = asyncio.get_event_loop()
        equity = await loop.run_in_executor(
            self.executor,
            self._calculate_equity,
            hand1, hand2, iterations
        )
        return equity
```

## Monitoring and Alerting

### Performance Metrics
```python
import time
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        start_memory = get_memory_usage()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            end_memory = get_memory_usage()

            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory

            # Log metrics
            log_performance_metric(func.__name__, execution_time, memory_usage)

            # Alert on performance degradation
            if execution_time > get_performance_threshold(func.__name__):
                alert_performance_degradation(func.__name__, execution_time)

    return wrapper
```

### System Resource Monitoring
```python
import psutil

def get_system_metrics():
    """Get current system resource usage."""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'process_memory': psutil.Process().memory_info().rss
    }

def check_resource_limits():
    """Check if system resources are within acceptable limits."""
    metrics = get_system_metrics()

    if metrics['cpu_percent'] > 90:
        alert_high_cpu_usage(metrics['cpu_percent'])

    if metrics['memory_percent'] > 85:
        alert_high_memory_usage(metrics['memory_percent'])
```

## Optimization Checklist

### Code Review Checklist
- [ ] Algorithms have appropriate time/space complexity
- [ ] Database queries are optimized and indexed
- [ ] Memory usage is monitored and bounded
- [ ] Caching is implemented for expensive operations
- [ ] Async processing used for I/O-bound operations
- [ ] Vectorization applied where beneficial
- [ ] Profiling completed and bottlenecks identified

### Performance Testing Checklist
- [ ] Benchmark tests implemented
- [ ] Memory profiling completed
- [ ] Load testing performed
- [ ] Performance regression tests in CI
- [ ] Performance metrics logged
- [ ] Alerting configured for performance degradation

### Production Monitoring Checklist
- [ ] Performance metrics collected
- [ ] Resource usage monitored
- [ ] Error rates tracked
- [ ] Response times measured
- [ ] Memory leaks detected
- [ ] CPU usage optimized

## Best Practices

1. **Measure Before Optimizing**: Use profiling to identify real bottlenecks
2. **Set Performance Budgets**: Define acceptable performance limits
3. **Monitor in Production**: Track performance in real-world usage
4. **Optimize Iteratively**: Make incremental improvements and measure impact
5. **Balance Performance and Maintainability**: Don't sacrifice code quality for speed
6. **Test Performance Changes**: Ensure optimizations don't break functionality
7. **Monitor System Resources**: Keep track of CPU, memory, and disk usage
8. **Plan for Scale**: Design with future growth in mind

## Troubleshooting Performance Issues

### Common Problems and Solutions

#### Slow Equity Calculations
**Symptoms**: Equity calculations taking > 5 seconds

**Solutions**:
1. Reduce default iterations from 25,000 to 10,000
2. Implement caching for repeated calculations
3. Use faster hand evaluation algorithms
4. Optimize deck sampling methods

#### High Memory Usage
**Symptoms**: Memory usage > 200MB

**Solutions**:
1. Implement object pooling for cards
2. Use generators instead of lists for large datasets
3. Clear caches periodically
4. Optimize data structures

#### Slow Database Queries
**Symptoms**: Database queries taking > 100ms

**Solutions**:
1. Add appropriate indexes
2. Optimize query structure
3. Implement query result caching
4. Use connection pooling

#### CPU Bottlenecks
**Symptoms**: High CPU usage during calculations

**Solutions**:
1. Implement parallel processing for independent calculations
2. Use more efficient algorithms
3. Apply JIT compilation to performance-critical functions
4. Optimize inner loops

Remember: Performance optimization is an ongoing process. Regularly profile your code and monitor performance in production to identify and address bottlenecks.
