#!/usr/bin/env python3
"""
Quadra Matrix Training with WikiText Dataset
Trains the Symbolic Predictive Interpreter on Wikipedia text data
"""

import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run training with WikiText dataset"""
    
    print("\n" + "="*80)
    print("🚀 QUADRA MATRIX - WIKITEXT TRAINING SESSION")
    print("="*80)
    print("\n📊 Configuration:")
    print("  • Dataset: WikiText-2 (raw)")
    print("  • Field size: 150")
    print("  • Training batches: 50")
    print("  • Batch size: 10 samples")
    print("  • Device: CPU")
    print("\n⏱️  Estimated time: 5-10 minutes")
    print("🎯 Expected: Neuroscience-based learning with oscillatory optimization\n")
    print("="*80 + "\n")
    
    try:
        # Import trainer
        from train_quadra_matrix import QuadraMatrixTrainer
        
        # Initialize trainer with moderate configuration for WikiText
        logger.info("Initializing QuadraMatrixTrainer with field_size=150...")
        trainer = QuadraMatrixTrainer(field_size=150, device='cpu', enable_noise=True)
        
        # Start training on WikiText-2 dataset
        logger.info("Starting training on WikiText-2 dataset...")
        print("\n📚 Loading WikiText-2 dataset...")
        
        metrics = await trainer.train(
            dataset_name='wikitext',
            dataset_config='wikitext-2-raw-v1',
            num_batches=50,
            batch_size=10
        )
        
        # Print results
        print("\n" + "="*80)
        print("✅ TRAINING COMPLETE!")
        print("="*80)
        print(f"\n📈 Final Metrics:")
        print(f"  • Peak Speedup Factor: {max(metrics['speedup_factors']):.2f}x")
        print(f"  • Final Reward: {metrics['rewards'][-1]:.4f}")
        print(f"  • Cache Efficiency: {metrics['cache_efficiency'][-1]:.2%}")
        print(f"  • Field Resonance: {metrics['field_resonance'][-1]:.4f}")
        print(f"  • Adaptive K-Clusters: {int(metrics['k_values'][-1])}")
        print(f"  • Total Training Batches: {len(metrics['rewards'])}")
        
        # Save trained model
        save_path = "quadra_matrix_wikitext.pth"
        logger.info(f"Saving model weights to {save_path}...")
        trainer.oscillator.save_weights(save_path)
        print(f"\n💾 Model saved to: {save_path}")
        
        # Save metrics
        import json
        metrics_file = "training_metrics_wikitext.json"
        with open(metrics_file, 'w') as f:
            # Convert tensors/numpy to serializable format
            metrics_serializable = {
                'speedup_factors': [float(x) for x in metrics['speedup_factors']],
                'rewards': [float(x) for x in metrics['rewards']],
                'learning_rates': [float(x) for x in metrics['learning_rates']],
                'k_values': [float(x) for x in metrics['k_values']],
                'cache_efficiency': [float(x) for x in metrics['cache_efficiency']],
                'field_resonance': [float(x) for x in metrics['field_resonance']],
            }
            json.dump(metrics_serializable, f, indent=2)
        print(f"📊 Metrics saved to: {metrics_file}")
        
        print("\n" + "="*80)
        print("✨ WikiText training session finished successfully!")
        print("="*80 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
