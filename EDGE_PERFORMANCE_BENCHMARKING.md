# Edge A.I. Performance Benchmarking Guide

## Overview

This guide provides comprehensive methodology for benchmarking Quadra-Matrix A.I. on edge devices, including tools, metrics, and interpretation guidelines.

---

## 1. Benchmarking Framework

### 1.1 Core Metrics

#### Latency Metrics
```python
Latency = Time from input submission to output delivery

Key measurements:
  - Mean Latency: Average inference time
  - P50 (Median): 50th percentile latency
  - P95: 95th percentile latency
  - P99: 99th percentile latency
  - Max Latency: Worst-case inference time
  - Jitter: Std dev of latency (variance)
```

#### Throughput Metrics
```python
Throughput = Inferences per second (RPS)

Calculation:
  RPS = (Number of inferences) / (Total time in seconds)
  
Batch throughput:
  Batch RPS = (Number of batches) / (Total time)
  Sample RPS = (Number of samples) / (Total time)
```

#### Resource Metrics
```python
Memory Usage:
  - Peak: Maximum memory used during inference
  - Average: Mean memory over inference period
  - Working Set: Memory actively used

CPU/Compute:
  - CPU %: Percentage of single core
  - Power (W): Watts consumed
  - Energy (mJ): Joules per inference

Storage:
  - Model size: Quantized weight file
  - Cache size: Symbolic cache storage
  - Total footprint: All files needed
```

#### Quality Metrics
```python
Accuracy:
  - Top-1: Exact match accuracy
  - Top-5: Prediction in top-5 candidates
  - MRR: Mean reciprocal rank
  - NDCG: Normalized discounted cumulative gain

Sparsity:
  - Spike rate: % of active neurons
  - Sparsity: 1 - spike_rate
  - Cache hit rate: % of cache hits
```

### 1.2 Benchmark Categories

#### 1. Latency Benchmark
```
Measure inference time under various loads
- Single sample inference
- Batched inference (batch size 1-32)
- Concurrent requests
- Different input sizes
```

#### 2. Throughput Benchmark
```
Measure requests/second under sustained load
- Steady-state throughput
- Max achievable throughput
- Throughput vs batch size
- Throughput vs input size
```

#### 3. Resource Benchmark
```
Measure hardware resource usage
- Peak memory
- Average memory
- CPU utilization
- Power consumption
- Energy per inference
```

#### 4. Accuracy Benchmark
```
Measure output quality
- Baseline accuracy (cloud model)
- Quantized model accuracy
- Edge device accuracy
- Accuracy vs sparsity trade-off
```

#### 5. Scalability Benchmark
```
Measure performance at scale
- Inference count vs latency degradation
- Cache effectiveness over time
- Field state growth
- Long-running stability
```

---

## 2. Benchmark Tools

### 2.1 Built-in Profiler Usage

```python
from quadra.edge.inference_engine import EdgeInferenceEngine, EdgeConfig
from quadra.edge import EdgeProfiler

# Initialize engine
config = EdgeConfig.for_tier(EdgeTier.STANDARD)
engine = EdgeInferenceEngine(model, config)

# Run inferences (profiler tracks automatically)
for i in range(1000):
    input_data = torch.randn(1, 128)
    result = engine.forward(input_data)

# Get profile summary
stats = engine.get_stats()
print(f"Average latency: {stats['profiler']['avg_latency_ms']:.2f} ms")
print(f"P95 latency: {stats['profiler']['p95_latency_ms']:.2f} ms")
print(f"Memory usage: {stats['profiler']['avg_memory_mb']:.2f} MB")
```

### 2.2 Benchmark Suite Script

```python
#!/usr/bin/env python3
"""Complete benchmarking suite for edge inference"""

import torch
import time
import numpy as np
import json
from quadra.edge.inference_engine import EdgeInferenceEngine, EdgeConfig, EdgeTier

class EdgeBenchmarkSuite:
    def __init__(self, model, tier=EdgeTier.STANDARD):
        self.config = EdgeConfig.for_tier(tier)
        self.engine = EdgeInferenceEngine(model, self.config)
        self.results = {}
    
    def benchmark_latency(self, num_samples=100, input_shape=(1, 128)):
        """Benchmark inference latency"""
        print("\n=== Latency Benchmark ===")
        latencies = []
        
        for i in range(num_samples):
            input_data = torch.randn(input_shape)
            result = self.engine.forward(input_data)
            latencies.append(result['latency_ms'])
        
        latencies = np.array(latencies)
        
        self.results['latency'] = {
            'mean_ms': float(latencies.mean()),
            'median_ms': float(np.median(latencies)),
            'p95_ms': float(np.percentile(latencies, 95)),
            'p99_ms': float(np.percentile(latencies, 99)),
            'max_ms': float(latencies.max()),
            'min_ms': float(latencies.min()),
            'std_ms': float(latencies.std()),
        }
        
        print(f"Mean: {self.results['latency']['mean_ms']:.2f} ms")
        print(f"P95: {self.results['latency']['p95_ms']:.2f} ms")
        print(f"P99: {self.results['latency']['p99_ms']:.2f} ms")
        
        return self.results['latency']
    
    def benchmark_throughput(self, duration_seconds=10):
        """Benchmark sustained throughput"""
        print("\n=== Throughput Benchmark ===")
        
        inference_count = 0
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            input_data = torch.randn(1, 128)
            self.engine.forward(input_data)
            inference_count += 1
        
        elapsed = time.time() - start_time
        throughput_rps = inference_count / elapsed
        
        self.results['throughput'] = {
            'rps': throughput_rps,
            'total_inferences': inference_count,
            'duration_seconds': elapsed,
        }
        
        print(f"Throughput: {throughput_rps:.2f} RPS")
        print(f"Total inferences: {inference_count}")
        
        return self.results['throughput']
    
    def benchmark_memory(self, num_samples=50):
        """Benchmark memory usage"""
        print("\n=== Memory Benchmark ===")
        memories = []
        
        for i in range(num_samples):
            input_data = torch.randn(1, 128)
            result = self.engine.forward(input_data)
            memories.append(result.get('memory_mb', 0))
        
        memories = np.array(memories)
        
        self.results['memory'] = {
            'mean_mb': float(memories.mean()),
            'peak_mb': float(memories.max()),
            'min_mb': float(memories.min()),
            'std_mb': float(memories.std()),
        }
        
        print(f"Average: {self.results['memory']['mean_mb']:.2f} MB")
        print(f"Peak: {self.results['memory']['peak_mb']:.2f} MB")
        
        return self.results['memory']
    
    def benchmark_batch_scaling(self, batch_sizes=[1, 2, 4, 8, 16]):
        """Benchmark throughput vs batch size"""
        print("\n=== Batch Scaling Benchmark ===")
        results = {}
        
        for batch_size in batch_sizes:
            latencies = []
            for _ in range(50):
                input_data = torch.randn(batch_size, 128)
                result = self.engine.forward(input_data)
                latencies.append(result['latency_ms'])
            
            avg_latency = np.mean(latencies)
            latency_per_sample = avg_latency / batch_size
            throughput = 1000 / latency_per_sample
            
            results[batch_size] = {
                'batch_latency_ms': float(avg_latency),
                'latency_per_sample_ms': float(latency_per_sample),
                'throughput_rps': float(throughput),
            }
            
            print(f"Batch {batch_size}: {latency_per_sample:.2f} ms/sample, {throughput:.1f} RPS")
        
        self.results['batch_scaling'] = results
        return results
    
    def benchmark_cache_effectiveness(self, num_inferences=1000):
        """Benchmark cache hit rate"""
        print("\n=== Cache Effectiveness Benchmark ===")
        
        # Repeated pattern inferences
        test_patterns = [torch.randn(1, 128) for _ in range(10)]
        
        for _ in range(num_inferences):
            pattern = test_patterns[_ % len(test_patterns)]
            self.engine.forward(pattern)
        
        if self.engine.symbolic_cache:
            cache_stats = self.engine.symbolic_cache.stats()
            self.results['cache'] = cache_stats
            
            print(f"Cache hit rate: {cache_stats['hit_rate']:.1f}%")
            print(f"Cache size: {cache_stats['size']}/{cache_stats['max_size']}")
        
        return self.results.get('cache', {})
    
    def benchmark_accuracy_vs_sparsity(self, test_data, test_labels):
        """Benchmark accuracy impact of sparsity"""
        print("\n=== Accuracy vs Sparsity Benchmark ===")
        
        sparsity_levels = []
        
        for _ in range(min(100, len(test_data))):
            idx = np.random.randint(0, len(test_data))
            input_data = torch.tensor(test_data[idx]).float()
            result = self.engine.forward(input_data)
            sparsity_levels.append(result.get('spike_rate', 0))
        
        avg_sparsity = np.mean(sparsity_levels)
        
        self.results['sparsity'] = {
            'avg_sparsity': float(avg_sparsity),
            'avg_spike_rate': float(1.0 - avg_sparsity),
        }
        
        print(f"Average sparsity: {avg_sparsity*100:.1f}%")
        
        return self.results['sparsity']
    
    def save_results(self, filepath):
        """Save benchmark results to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to {filepath}")
    
    def print_summary(self):
        """Print summary of all benchmarks"""
        print("\n" + "="*50)
        print("BENCHMARK SUMMARY")
        print("="*50)
        
        if 'latency' in self.results:
            lat = self.results['latency']
            print(f"\nLatency (ms):")
            print(f"  Mean: {lat['mean_ms']:.2f}")
            print(f"  P95: {lat['p95_ms']:.2f}")
            print(f"  P99: {lat['p99_ms']:.2f}")
        
        if 'throughput' in self.results:
            thr = self.results['throughput']
            print(f"\nThroughput: {thr['rps']:.2f} RPS")
        
        if 'memory' in self.results:
            mem = self.results['memory']
            print(f"\nMemory (MB):")
            print(f"  Average: {mem['mean_mb']:.2f}")
            print(f"  Peak: {mem['peak_mb']:.2f}")
        
        if 'cache' in self.results:
            cache = self.results['cache']
            print(f"\nCache Hit Rate: {cache.get('hit_rate', 0):.1f}%")


# Usage example
if __name__ == '__main__':
    # Load model
    model = torch.load('model.pt')
    
    # Run benchmark suite
    suite = EdgeBenchmarkSuite(model, tier=EdgeTier.STANDARD)
    
    suite.benchmark_latency(num_samples=100)
    suite.benchmark_throughput(duration_seconds=10)
    suite.benchmark_memory(num_samples=50)
    suite.benchmark_batch_scaling()
    suite.benchmark_cache_effectiveness(num_inferences=1000)
    
    suite.print_summary()
    suite.save_results('benchmark_results.json')
```

---

## 3. Benchmark Execution

### 3.1 Single Sample Latency Benchmark

```bash
# Test with varying input shapes
for input_size in 32 64 128 256 512; do
    python -c "
    import torch
    from quadra.edge.inference_engine import EdgeInferenceEngine
    
    engine = EdgeInferenceEngine(model, config)
    
    # Warm up
    for _ in range(10):
        engine.forward(torch.randn(1, $input_size))
    
    # Benchmark
    latencies = []
    for _ in range(100):
        input_data = torch.randn(1, $input_size)
        result = engine.forward(input_data)
        latencies.append(result['latency_ms'])
    
    import numpy as np
    print(f'Input size {$input_size}: {np.mean(latencies):.2f} ms')
    "
done
```

### 3.2 Sustained Load Benchmark

```python
import threading
import time
import torch
from collections import deque

def load_test(engine, num_threads=4, duration_seconds=60):
    """Sustained load test with concurrent requests"""
    
    results = deque(maxlen=1000)
    stop_event = threading.Event()
    errors = []
    
    def worker():
        while not stop_event.is_set():
            try:
                input_data = torch.randn(1, 128)
                start = time.time()
                result = engine.forward(input_data)
                elapsed = (time.time() - start) * 1000
                results.append({
                    'latency_ms': elapsed,
                    'confidence': result.get('confidence', 0),
                })
            except Exception as e:
                errors.append(str(e))
    
    # Start worker threads
    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    
    # Run for specified duration
    time.sleep(duration_seconds)
    stop_event.set()
    
    # Wait for threads
    for t in threads:
        t.join()
    
    # Analyze results
    import numpy as np
    latencies = [r['latency_ms'] for r in results]
    
    return {
        'total_requests': len(results),
        'throughput_rps': len(results) / duration_seconds,
        'avg_latency_ms': np.mean(latencies),
        'p95_latency_ms': np.percentile(latencies, 95),
        'p99_latency_ms': np.percentile(latencies, 99),
        'errors': len(errors),
        'error_rate': len(errors) / len(results) if results else 0,
    }
```

---

## 4. Benchmark Interpretation

### 4.1 Latency Analysis

```
Acceptable Latency Thresholds:

Tier 1 (Embedded):
  ✓ < 5000 ms: Acceptable
  ⚠ 5-10 seconds: Marginal
  ✗ > 10 seconds: Unacceptable

Tier 2 (Mobile):
  ✓ < 200 ms: Excellent
  ✓ 200-500 ms: Acceptable
  ⚠ 500-1000 ms: Marginal
  ✗ > 1000 ms: Unacceptable

Tier 3 (Edge Server):
  ✓ < 50 ms: Excellent
  ✓ 50-100 ms: Acceptable
  ⚠ 100-200 ms: Marginal
  ✗ > 200 ms: Investigate
```

### 4.2 Throughput Analysis

```
Expected Throughput (Single CPU Core):

Tier 1 (Embedded):
  Expected: 1-5 RPS
  @ 100 MHz CPU: ~0.2-1 RPS

Tier 2 (Mobile):
  Expected: 10-50 RPS
  @ 2 GHz CPU: ~20-50 RPS

Tier 3 (Edge Server):
  Expected: 100-500 RPS
  @ 4 GHz CPU: ~100-200 RPS
```

### 4.3 Memory Analysis

```
Memory Usage Patterns:

Baseline (no inference):
  Tier 1: < 1 MB
  Tier 2: < 50 MB
  Tier 3: < 200 MB

Peak (during inference):
  Tier 1: < 5 MB
  Tier 2: < 150 MB
  Tier 3: < 500 MB

Growth over time:
  Normal: < 1 MB/hour (cache)
  Warning: 5-10 MB/hour (leak likely)
  Error: > 10 MB/hour (memory leak)
```

### 4.4 Cache Effectiveness

```
Cache Hit Rate Interpretation:

> 80%: Excellent (few unique patterns)
60-80%: Good (some pattern repetition)
40-60%: Moderate (varied workload)
< 40%: Poor (highly varied inputs)

Actions:
- If hit rate too low: Increase cache size
- If memory constrained: Reduce cache size
- If hit rate unstable: Check for data distribution changes
```

---

## 5. Comparative Benchmarking

### 5.1 Quantization Impact

```python
def benchmark_quantization_impact(model, test_data, test_labels):
    """Measure accuracy loss from quantization"""
    
    # Full precision baseline
    baseline_acc = evaluate(model, test_data, test_labels)
    
    # 16-bit quantization
    quantize_weights(model, bits=16)
    acc_16bit = evaluate(model, test_data, test_labels)
    loss_16bit = (baseline_acc - acc_16bit) / baseline_acc * 100
    
    # 8-bit quantization
    quantize_weights(model, bits=8)
    acc_8bit = evaluate(model, test_data, test_labels)
    loss_8bit = (baseline_acc - acc_8bit) / baseline_acc * 100
    
    return {
        'baseline': baseline_acc,
        '16bit': acc_16bit,
        '16bit_loss_percent': loss_16bit,
        '8bit': acc_8bit,
        '8bit_loss_percent': loss_8bit,
    }
```

### 5.2 Tier Comparison

```python
def benchmark_all_tiers(model):
    """Compare performance across all tiers"""
    
    tiers = [EdgeTier.ULTRA_LIGHT, EdgeTier.STANDARD, EdgeTier.HEAVY]
    results = {}
    
    for tier in tiers:
        config = EdgeConfig.for_tier(tier)
        engine = EdgeInferenceEngine(model, config)
        
        # Run latency benchmark
        latencies = []
        for _ in range(100):
            result = engine.forward(torch.randn(1, 128))
            latencies.append(result['latency_ms'])
        
        results[tier.value] = {
            'mean_latency_ms': np.mean(latencies),
            'p95_latency_ms': np.percentile(latencies, 95),
            'memory_mb': engine._estimate_memory_usage(),
            'cache_size': config.cache_size,
        }
    
    return results
```

---

## 6. Benchmark Reporting

### 6.1 Sample Report

```markdown
# Edge A.I. Performance Benchmark Report

**Date**: 2026-01-08
**Device**: Raspberry Pi 4 (4GB RAM, ARM Cortex-A72)
**Tier**: Tier 2 Standard
**Model**: quadra_matrix_edge_int8
**Test Duration**: 30 minutes

## Results

### Latency
- Mean: 87.3 ms
- P95: 145.2 ms
- P99: 201.5 ms
- Max: 512.3 ms

### Throughput
- Sustained: 11.4 RPS
- Peak: 12.1 RPS

### Memory
- Baseline: 45.2 MB
- Peak: 89.4 MB
- Growth rate: 0.2 MB/hour

### Cache
- Hit rate: 78.5%
- Size: 12.4 MB / 20 MB

### Sparsity
- Average spike rate: 22%
- Average sparsity: 78%

## Analysis

The device meets all performance targets for Tier 2:
- Latency well under 500ms budget
- Cache performing effectively (>70% hit rate)
- Memory usage stable

## Recommendations

1. Monitor sustained operation (> 8 hours)
2. Test with realistic input distribution
3. Validate accuracy on target data
```

### 6.2 Comparative Report

```json
{
  "benchmark_date": "2026-01-08",
  "device": "Raspberry Pi 4",
  "tiers": {
    "tier_1_ultra": {
      "config": {
        "field_size": 16,
        "quantization_bits": 8,
        "cache_size": 5
      },
      "metrics": {
        "latency_mean_ms": 12.5,
        "latency_p95_ms": 23.4,
        "throughput_rps": 0.8,
        "memory_peak_mb": 5.2,
        "cache_hit_rate": 0.65
      }
    },
    "tier_2_standard": {
      "config": {
        "field_size": 64,
        "quantization_bits": 8,
        "cache_size": 20
      },
      "metrics": {
        "latency_mean_ms": 87.3,
        "latency_p95_ms": 145.2,
        "throughput_rps": 11.4,
        "memory_peak_mb": 89.4,
        "cache_hit_rate": 0.78
      }
    },
    "tier_3_heavy": {
      "config": {
        "field_size": 128,
        "quantization_bits": 16,
        "cache_size": 100
      },
      "metrics": {
        "latency_mean_ms": 45.1,
        "latency_p95_ms": 78.3,
        "throughput_rps": 22.1,
        "memory_peak_mb": 245.3,
        "cache_hit_rate": 0.85
      }
    }
  }
}
```

---

## 7. Continuous Monitoring

### 7.1 Real-Time Dashboard

```python
from datetime import datetime, timedelta

class PerformanceDashboard:
    def __init__(self, window_size=3600):  # 1 hour window
        self.window_size = window_size
        self.metrics_log = deque()
    
    def record_inference(self, latency_ms, memory_mb, cache_hit):
        self.metrics_log.append({
            'timestamp': time.time(),
            'latency_ms': latency_ms,
            'memory_mb': memory_mb,
            'cache_hit': cache_hit,
        })
    
    def get_window_stats(self):
        now = time.time()
        cutoff = now - self.window_size
        
        recent = [m for m in self.metrics_log 
                 if m['timestamp'] > cutoff]
        
        if not recent:
            return {}
        
        latencies = [m['latency_ms'] for m in recent]
        cache_hits = sum(1 for m in recent if m['cache_hit'])
        
        return {
            'inference_count': len(recent),
            'avg_latency_ms': np.mean(latencies),
            'p95_latency_ms': np.percentile(latencies, 95),
            'cache_hit_rate': cache_hits / len(recent),
        }
```

---

## Conclusion

This benchmarking guide enables comprehensive performance validation of Quadra-Matrix A.I. on edge devices, from micro-optimizations to system-level characteristics. Regular benchmarking ensures deployed systems maintain performance targets and identifies issues early.
