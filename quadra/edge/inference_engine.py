"""
Edge A.I. Optimized Inference Engine
Lightweight inference with minimal memory and compute requirements.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Tuple, Optional, Any
import time
import logging
from dataclasses import dataclass
import json
import os

from quadra.edge import (
    EdgeConfig, EdgeTier, SparseSpiking, QuantizationUtil,
    SymbolicCache, SparseFieldState, EnergyAwareOptimizer,
    InferenceProfile, EdgeProfiler
)

logger = logging.getLogger(__name__)


@dataclass
class InferenceContext:
    """Context for a single inference request"""
    input_data: torch.Tensor
    batch_size: int = 1
    deadline_ms: Optional[float] = None
    cache_enabled: bool = True
    require_confidence: bool = False
    low_power_mode: bool = False


class EdgeInferenceEngine:
    """Lightweight inference engine optimized for edge devices
    
    Features:
    - Sparse spiking field computation
    - Symbolic result caching
    - Memory-efficient state management
    - Energy-aware adaptation
    """
    
    def __init__(self, model: nn.Module, config: EdgeConfig):
        """Initialize edge inference engine
        
        Args:
            model: Quantized model for edge
            config: Edge deployment configuration
        """
        self.model = model
        self.config = config
        self.device = torch.device('cpu')  # Edge devices use CPU
        self.model.to(self.device)
        self.model.eval()
        
        # Initialize components
        self.field_state = SparseFieldState(size=config.field_size)
        self.symbolic_cache = SymbolicCache(
            max_size=config.cache_size,
            ttl_seconds=config.cache_ttl_seconds
        ) if config.enable_symbolic_cache else None
        
        self.energy_optimizer = EnergyAwareOptimizer(config)
        self.profiler = EdgeProfiler()
        
        # Performance tracking
        self.inference_count = 0
        self.start_time = time.time()
        
        logger.info(f"Initialized EdgeInferenceEngine for tier {config.tier.value}")
        logger.info(f"Field size: {config.field_size}, "
                   f"Quantization: {config.quantization_bits}-bit, "
                   f"Cache size: {config.cache_size}")
    
    def forward(self, input_data: torch.Tensor, 
               context: Optional[InferenceContext] = None) -> Dict[str, Any]:
        """Perform inference with all optimizations
        
        Args:
            input_data: Input tensor
            context: Optional inference context
        
        Returns:
            Dictionary with output and metadata
        """
        context = context or InferenceContext(input_data=input_data)
        
        inference_start = time.time()
        profile = InferenceProfile()
        
        try:
            with torch.no_grad():
                # Check symbolic cache first
                cache_hit = False
                if self.symbolic_cache and context.cache_enabled:
                    cache_key = input_data.cpu().numpy()
                    cached_result = self.symbolic_cache.get(cache_key)
                    if cached_result is not None:
                        profile.cache_hit = True
                        cache_hit = True
                        output = cached_result
                
                # Perform inference if not cached
                if not cache_hit:
                    output = self._inference_pass(input_data, context, profile)
                    
                    # Cache result
                    if self.symbolic_cache and context.cache_enabled:
                        self.symbolic_cache.put(
                            input_data.cpu().numpy(),
                            output
                        )
            
            # Compute confidence
            if isinstance(output, torch.Tensor):
                confidence = self._compute_confidence(output)
            else:
                confidence = 0.95
            
            # Record profiling info
            profile.latency_ms = (time.time() - inference_start) * 1000
            profile.memory_peak_mb = self._estimate_memory_usage()
            profile.spike_rate = self._get_spike_rate()
            
            self.profiler.record(profile)
            self.inference_count += 1
            
            return {
                'output': output,
                'confidence': confidence,
                'cache_hit': profile.cache_hit,
                'latency_ms': profile.latency_ms,
                'memory_mb': profile.memory_peak_mb,
                'spike_rate': profile.spike_rate,
            }
        
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {
                'output': None,
                'confidence': 0.0,
                'error': str(e),
            }
    
    def _inference_pass(self, input_data: torch.Tensor,
                       context: InferenceContext,
                       profile: InferenceProfile) -> torch.Tensor:
        """Single inference pass through model
        
        Args:
            input_data: Input tensor
            context: Inference context
            profile: Profile to update with compute stats
        
        Returns:
            Model output
        """
        # Ensure correct shape
        if input_data.dim() == 1:
            input_data = input_data.unsqueeze(0)
        
        # Model forward pass
        output = self.model(input_data)
        
        # Apply sparse field dynamics if enabled
        if self.config.enable_neuroplasticity:
            output = self._apply_field_dynamics(output, profile)
        
        return output
    
    def _apply_field_dynamics(self, activation: torch.Tensor,
                             profile: InferenceProfile) -> torch.Tensor:
        """Apply sparse spiking field dynamics
        
        Args:
            activation: Neural activation
            profile: Profile to update spike rate
        
        Returns:
            Updated activation with spikes
        """
        # Convert to numpy for field update
        act_np = activation.cpu().detach().numpy()
        
        # Compute spikes
        spikes = (act_np > self.config.spike_threshold).astype(np.float32)
        
        # Update field
        self.field_state.update(act_np, sparsity_mask=spikes)
        
        # Sparse gating
        output = act_np * spikes
        
        # Track sparsity
        spike_count = np.sum(spikes)
        total_count = spikes.size
        profile.spike_rate = (1.0 - spike_count / total_count)  # Sparsity = 1 - spike_rate
        
        return torch.from_numpy(output).float()
    
    def _compute_confidence(self, output: torch.Tensor) -> float:
        """Compute output confidence score
        
        Args:
            output: Model output
        
        Returns:
            Confidence score [0, 1]
        """
        if output.dim() == 1:
            return float(output.max().item())
        else:
            # For batches, average max confidence
            return float(output.max(dim=1)[0].mean().item())
    
    def _estimate_memory_usage(self) -> float:
        """Estimate current memory usage in MB"""
        # Model parameters
        model_params = sum(p.numel() * 4 for p in self.model.parameters()) / (1024 * 1024)
        
        # Field state
        field_memory = self.field_state.memory_usage_bytes() / (1024 * 1024)
        
        # Cache
        cache_memory = 0
        if self.symbolic_cache:
            cache_memory = len(self.symbolic_cache.cache) * 0.05  # ~50KB per entry
        
        return model_params + field_memory + cache_memory
    
    def _get_spike_rate(self) -> float:
        """Get current spike rate from field state"""
        active_count = len(self.field_state.last_active)
        total_count = self.field_state.size
        return active_count / total_count if total_count > 0 else 0.0
    
    def adapt_to_battery(self, battery_percent: int) -> None:
        """Adapt inference for battery level
        
        Args:
            battery_percent: Current battery percentage
        """
        adjusted_config = self.energy_optimizer.adjust_for_battery(battery_percent)
        self.config = adjusted_config
        logger.info(f"Adapted to battery {battery_percent}%")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get inference statistics
        
        Returns:
            Dictionary with performance metrics
        """
        stats = {
            'total_inferences': self.inference_count,
            'uptime_seconds': time.time() - self.start_time,
            'profiler': self.profiler.summary(),
        }
        
        if self.symbolic_cache:
            stats['cache'] = self.symbolic_cache.stats()
        
        return stats
    
    def benchmark(self, num_samples: int = 100,
                 input_shape: Tuple[int, ...] = (1, 128)) -> Dict[str, float]:
        """Run inference benchmark
        
        Args:
            num_samples: Number of inference samples
            input_shape: Shape of input tensors
        
        Returns:
            Benchmark results
        """
        logger.info(f"Running benchmark with {num_samples} samples...")
        
        latencies = []
        memories = []
        
        for _ in range(num_samples):
            # Random input
            input_data = torch.randn(input_shape).to(self.device)
            
            # Inference
            result = self.forward(input_data)
            
            latencies.append(result.get('latency_ms', 0))
            memories.append(result.get('memory_mb', 0))
        
        latencies = np.array(latencies)
        memories = np.array(memories)
        
        return {
            'avg_latency_ms': float(latencies.mean()),
            'p50_latency_ms': float(np.percentile(latencies, 50)),
            'p95_latency_ms': float(np.percentile(latencies, 95)),
            'p99_latency_ms': float(np.percentile(latencies, 99)),
            'max_latency_ms': float(latencies.max()),
            'avg_memory_mb': float(memories.mean()),
            'max_memory_mb': float(memories.max()),
            'throughput_rps': 1000.0 / latencies.mean(),
        }


class EdgeModelDeployer:
    """Deploy and manage models on edge devices"""
    
    @staticmethod
    def prepare_model(model: nn.Module, 
                     quantization_bits: int = 8,
                     optimize_for_inference: bool = True) -> nn.Module:
        """Prepare model for edge deployment
        
        Args:
            model: Full precision model
            quantization_bits: Target quantization (8 or 16)
            optimize_for_inference: Enable inference optimizations
        
        Returns:
            Optimized model
        """
        # Move to CPU
        model = model.cpu()
        model.eval()
        
        # Quantize weights
        logger.info(f"Quantizing model to {quantization_bits}-bit...")
        QuantizationUtil.quantize_weights(model, bits=quantization_bits)
        
        # Estimate model size
        model_size = QuantizationUtil.estimate_model_size(model, bits=quantization_bits)
        logger.info(f"Quantized model size: {model_size:.2f} MB")
        
        # Optional: freeze batch norm statistics
        if optimize_for_inference:
            for module in model.modules():
                if isinstance(module, nn.BatchNorm2d):
                    module.eval()
        
        return model
    
    @staticmethod
    def save_for_edge(model: nn.Module, 
                     config: EdgeConfig,
                     path: str) -> None:
        """Save model and config for edge deployment
        
        Args:
            model: Model to save
            config: Edge configuration
            path: Directory to save to
        """
        os.makedirs(path, exist_ok=True)
        
        # Save model
        model_path = os.path.join(path, 'model.pt')
        torch.save(model.state_dict(), model_path)
        logger.info(f"Saved model to {model_path}")
        
        # Save config
        config_path = os.path.join(path, 'config.json')
        config_dict = {
            'tier': config.tier.value,
            'field_size': config.field_size,
            'quantization_bits': config.quantization_bits,
            'spike_threshold': config.spike_threshold,
            'cache_size': config.cache_size,
            'batch_size': config.batch_size,
        }
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        logger.info(f"Saved config to {config_path}")
    
    @staticmethod
    def load_for_edge(model_class: type,
                     path: str) -> Tuple[nn.Module, EdgeConfig]:
        """Load model and config from edge deployment
        
        Args:
            model_class: Model class to instantiate
            path: Directory to load from
        
        Returns:
            Tuple of (model, config)
        """
        # Load config
        config_path = os.path.join(path, 'config.json')
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # Reconstruct config
        tier = EdgeTier(config_dict['tier'])
        config = EdgeConfig.for_tier(tier)
        config.field_size = config_dict.get('field_size', config.field_size)
        config.quantization_bits = config_dict.get('quantization_bits', config.quantization_bits)
        
        # Load model
        model = model_class()
        model_path = os.path.join(path, 'model.pt')
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        
        logger.info(f"Loaded model from {path} (tier: {tier.value})")
        
        return model, config


class EdgeBatchProcessor:
    """Process inference requests in batches on edge devices"""
    
    def __init__(self, engine: EdgeInferenceEngine,
                 batch_timeout_ms: float = 100):
        """Initialize batch processor
        
        Args:
            engine: Edge inference engine
            batch_timeout_ms: Max time to wait for batch
        """
        self.engine = engine
        self.batch_timeout_ms = batch_timeout_ms
        self.queue = []
        self.batch_start_time = None
    
    def add_request(self, input_data: torch.Tensor,
                   request_id: str = None) -> Optional[Dict[str, Any]]:
        """Add request to batch
        
        Args:
            input_data: Input tensor
            request_id: Optional request identifier
        
        Returns:
            Result if batch complete, None otherwise
        """
        self.queue.append((input_data, request_id))
        
        # Check if batch should process
        if len(self.queue) >= self.engine.config.batch_size:
            return self.process_batch()
        
        # Check timeout
        if self.batch_start_time is None:
            self.batch_start_time = time.time()
        elif (time.time() - self.batch_start_time) * 1000 > self.batch_timeout_ms:
            return self.process_batch()
        
        return None
    
    def process_batch(self) -> Dict[str, Any]:
        """Process accumulated batch
        
        Returns:
            Batch results
        """
        if not self.queue:
            return {}
        
        # Stack inputs
        inputs = [item[0] for item in self.queue]
        request_ids = [item[1] for item in self.queue]
        
        # Batch inference
        batch_data = torch.stack(inputs) if len(inputs) > 1 else inputs[0].unsqueeze(0)
        
        context = InferenceContext(
            input_data=batch_data,
            batch_size=len(inputs)
        )
        
        result = self.engine.forward(batch_data, context)
        
        # Reset queue
        self.queue = []
        self.batch_start_time = None
        
        return {
            'result': result,
            'request_ids': request_ids,
            'batch_size': len(inputs),
        }
