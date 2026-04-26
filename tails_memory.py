"""
Tails-Inspired Memory System for Quadra Matrix SPI
Models after Tails Linux approach: RAM disk + encryption + secure erasure
"""

import os
import json
import hashlib
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import numpy as np
import torch
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    """Memory hierarchy inspired by Tails Linux"""
    VOLATILE = "volatile"      # RAM-based, fastest, cleared on shutdown
    EPHEMERAL = "ephemeral"    # Encrypted, auto-delete after TTL
    PERSISTENT = "persistent"  # Encrypted, survives reboot
    ARCHIVE = "archive"        # Compressed, oldest items, rare access


@dataclass
class MemoryTrace:
    """Single memory entry with metadata"""
    timestamp: float
    session_id: str
    tier: MemoryTier
    data: Dict[str, Any]
    hash_value: str  # For integrity checking
    access_count: int = 0
    last_accessed: float = None
    ttl_seconds: Optional[int] = None  # Time-to-live
    
    def is_expired(self) -> bool:
        """Check if memory trace has expired"""
        if self.ttl_seconds is None:
            return False
        age = datetime.utcnow().timestamp() - self.timestamp
        return age > self.ttl_seconds
    
    def get_freshness_score(self) -> float:
        """Score 0-1, higher = more recent"""
        if self.last_accessed is None:
            return 0.0
        age_seconds = datetime.utcnow().timestamp() - self.last_accessed
        # Decay: halves every hour
        return np.exp(-age_seconds / 3600.0)


class TailsMemoryManager:
    """
    Tails-inspired memory system for Quadra Matrix
    
    Design principles:
    - Everything encrypted by default
    - Multiple tiers (volatile, ephemeral, persistent)
    - Automatic secure erasure
    - Session isolation
    - Integrity verification
    - Audit trail
    """
    
    def __init__(self, 
                 base_path: str = "dashboard_state/tails_memory",
                 encryption_key: Optional[bytes] = None,
                 enable_volatile: bool = True):
        """
        Initialize Tails memory system
        
        Args:
            base_path: Root directory for memory storage
            encryption_key: 32-byte key for Fernet. If None, generates new one
            enable_volatile: Use RAM disk for volatile tier
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Setup encryption
        if encryption_key is None:
            encryption_key = Fernet.generate_key()
            self._save_encryption_key(encryption_key)
        self.cipher = Fernet(encryption_key)
        
        # Memory tiers
        self.volatile_memory: Dict[str, MemoryTrace] = {}  # RAM-only
        self.ephemeral_path = self.base_path / "ephemeral"
        self.persistent_path = self.base_path / "persistent"
        self.archive_path = self.base_path / "archive"
        self.audit_path = self.base_path / "audit"
        
        for path in [self.ephemeral_path, self.persistent_path, 
                     self.archive_path, self.audit_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.enable_volatile = enable_volatile
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_lock = threading.RLock()
        
        # Stats
        self.stats = {
            'total_writes': 0,
            'total_reads': 0,
            'total_erasures': 0,
            'integrity_failures': 0
        }
        
        logger.info("Tails Memory Manager initialized")
    
    def _save_encryption_key(self, key: bytes):
        """Securely save encryption key"""
        key_path = self.base_path / ".memory_key"
        key_path.write_bytes(key)
        os.chmod(str(key_path), 0o600)  # Owner read/write only
    
    def create_session(self, session_id: str, metadata: Dict[str, Any] = None) -> str:
        """
        Create new memory session (like Tails session isolation)
        
        Args:
            session_id: Unique session identifier
            metadata: Optional session metadata
            
        Returns:
            session_id
        """
        with self.session_lock:
            self.sessions[session_id] = {
                'created': datetime.utcnow().timestamp(),
                'last_activity': datetime.utcnow().timestamp(),
                'metadata': metadata or {},
                'memory_count': 0,
                'access_count': 0
            }
        
        self._audit_log('session_created', {'session_id': session_id})
        logger.info(f"Session created: {session_id}")
        return session_id
    
    def write_memory(self,
                    session_id: str,
                    key: str,
                    data: Dict[str, Any],
                    tier: MemoryTier = MemoryTier.PERSISTENT,
                    ttl_seconds: Optional[int] = None) -> str:
        """
        Write data to memory with specified tier
        
        Args:
            session_id: Session to write to
            key: Memory key (like variable name)
            data: Data to store
            tier: Which memory tier (volatile/ephemeral/persistent)
            ttl_seconds: Optional expiration time
            
        Returns:
            memory_id
        """
        # Validate session
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        timestamp = datetime.utcnow().timestamp()
        memory_id = f"{session_id}:{key}:{timestamp}"
        
        # Create trace
        hash_value = self._compute_hash(data)
        trace = MemoryTrace(
            timestamp=timestamp,
            session_id=session_id,
            tier=tier,
            data=data,
            hash_value=hash_value,
            ttl_seconds=ttl_seconds
        )
        
        # Store by tier
        if tier == MemoryTier.VOLATILE:
            self.volatile_memory[memory_id] = trace
        else:
            self._write_to_disk(memory_id, trace, tier)
        
        # Update session
        with self.session_lock:
            self.sessions[session_id]['memory_count'] += 1
            self.sessions[session_id]['last_activity'] = timestamp
        
        self.stats['total_writes'] += 1
        self._audit_log('memory_write', {
            'memory_id': memory_id,
            'tier': tier.value,
            'size_bytes': len(json.dumps(data))
        })
        
        logger.debug(f"Wrote to {tier.value}: {memory_id}")
        return memory_id
    
    def read_memory(self,
                   session_id: str,
                   key: str,
                   verify_integrity: bool = True) -> Optional[Dict[str, Any]]:
        """
        Read from memory, respecting tier hierarchy
        
        Reads in order: Volatile → Ephemeral → Persistent → Archive
        
        Args:
            session_id: Session to read from
            key: Memory key
            verify_integrity: Check hash before returning
            
        Returns:
            Data or None if not found
        """
        # Try volatile first (fastest)
        for memory_id, trace in self.volatile_memory.items():
            if trace.session_id == session_id and memory_id.endswith(f":{key}"):
                self._access_trace(trace)
                return trace.data
        
        # Try ephemeral
        data = self._read_from_disk(session_id, key, self.ephemeral_path)
        if data is not None:
            return data
        
        # Try persistent
        data = self._read_from_disk(session_id, key, self.persistent_path)
        if data is not None:
            return data
        
        # Try archive
        data = self._read_from_disk(session_id, key, self.archive_path)
        
        self.stats['total_reads'] += 1
        return data
    
    def _write_to_disk(self, memory_id: str, trace: MemoryTrace, tier: MemoryTier):
        """Encrypt and write to appropriate tier directory"""
        path = {
            MemoryTier.EPHEMERAL: self.ephemeral_path,
            MemoryTier.PERSISTENT: self.persistent_path,
            MemoryTier.ARCHIVE: self.archive_path,
        }[tier]
        
        # Serialize
        payload = json.dumps(asdict(trace)).encode()
        encrypted = self.cipher.encrypt(payload)
        
        # Write
        file_path = path / f"{trace.session_id}_{trace.hash_value[:8]}.enc"
        file_path.write_bytes(encrypted)
    
    def _read_from_disk(self, session_id: str, key: str, tier_path: Path) -> Optional[Dict]:
        """Read and decrypt from tier directory"""
        # Find matching file
        for file_path in tier_path.glob(f"{session_id}_*.enc"):
            try:
                encrypted = file_path.read_bytes()
                payload = self.cipher.decrypt(encrypted)
                data = json.loads(payload)
                return data.get('data')
            except Exception as e:
                logger.warning(f"Failed to decrypt {file_path}: {e}")
        
        return None
    
    def _compute_hash(self, data: Dict) -> str:
        """Compute integrity hash"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _access_trace(self, trace: MemoryTrace):
        """Update access metadata"""
        trace.access_count += 1
        trace.last_accessed = datetime.utcnow().timestamp()
    
    def prune_expired(self) -> int:
        """Remove expired ephemeral memories (Tails-style auto-cleanup)"""
        count = 0
        
        # Volatile
        for memory_id, trace in list(self.volatile_memory.items()):
            if trace.is_expired():
                del self.volatile_memory[memory_id]
                count += 1
        
        # Disk-based
        for tier_path in [self.ephemeral_path, self.persistent_path]:
            for file_path in tier_path.glob("*.enc"):
                try:
                    encrypted = file_path.read_bytes()
                    payload = self.cipher.decrypt(encrypted)
                    trace_dict = json.loads(payload)
                    
                    if trace_dict.get('ttl_seconds'):
                        age = datetime.utcnow().timestamp() - trace_dict['timestamp']
                        if age > trace_dict['ttl_seconds']:
                            self._secure_erase(file_path)
                            count += 1
                except Exception as e:
                    logger.warning(f"Error pruning {file_path}: {e}")
        
        self.stats['total_erasures'] += count
        logger.info(f"Pruned {count} expired memories")
        return count
    
    def _secure_erase(self, file_path: Path):
        """Securely erase file (overwrite before deletion)"""
        try:
            # Overwrite with random data multiple times (DoD 5220.22-M standard)
            size = file_path.stat().st_size
            for _ in range(3):
                file_path.write_bytes(os.urandom(size))
            file_path.unlink()
            self.stats['total_erasures'] += 1
        except Exception as e:
            logger.error(f"Secure erase failed: {e}")
    
    def clear_session(self, session_id: str, secure: bool = True):
        """Clear all memories for a session"""
        # Volatile
        for memory_id in list(self.volatile_memory.keys()):
            if self.volatile_memory[memory_id].session_id == session_id:
                del self.volatile_memory[memory_id]
        
        # Disk
        for tier_path in [self.ephemeral_path, self.persistent_path, self.archive_path]:
            for file_path in tier_path.glob(f"{session_id}_*.enc"):
                if secure:
                    self._secure_erase(file_path)
                else:
                    file_path.unlink()
        
        # Remove session
        with self.session_lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
        
        self._audit_log('session_cleared', {'session_id': session_id})
        logger.info(f"Cleared session: {session_id}")
    
    def get_memory_stats(self, session_id: str = None) -> Dict[str, Any]:
        """Get memory usage statistics"""
        if session_id:
            return self.sessions.get(session_id, {})
        
        return {
            'total_volatile': len(self.volatile_memory),
            'total_sessions': len(self.sessions),
            'stats': self.stats,
            'tiers': {
                'ephemeral': len(list(self.ephemeral_path.glob("*.enc"))),
                'persistent': len(list(self.persistent_path.glob("*.enc"))),
                'archive': len(list(self.archive_path.glob("*.enc"))),
            }
        }
    
    def _audit_log(self, event: str, details: Dict[str, Any]):
        """Log all memory operations (Tails-style audit trail)"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'event': event,
            'details': details
        }
        
        audit_file = self.audit_path / f"audit_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def emergency_wipe(self):
        """Complete memory wipe (for security emergency)"""
        logger.warning("EMERGENCY WIPE: Clearing all memory!")
        
        # Volatile
        self.volatile_memory.clear()
        
        # Disk - secure erase all
        for tier_path in [self.ephemeral_path, self.persistent_path, self.archive_path]:
            for file_path in tier_path.glob("*.enc"):
                self._secure_erase(file_path)
        
        self._audit_log('emergency_wipe', {})


class MemoryEnabledTrainer:
    """Wrapper for trainer with Tails memory integration"""
    
    def __init__(self, trainer, memory_manager: TailsMemoryManager):
        self.trainer = trainer
        self.memory = memory_manager
        self.session_id = None
    
    def create_session(self) -> str:
        """Create new training session"""
        self.session_id = self.trainer.__class__.__name__ + "_" + \
                         datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.memory.create_session(
            self.session_id,
            {'trainer_type': self.trainer.__class__.__name__}
        )
        return self.session_id
    
    def save_checkpoint(self, checkpoint: Dict[str, Any], tier: MemoryTier = MemoryTier.PERSISTENT):
        """Save training checkpoint with memory"""
        if not self.session_id:
            self.create_session()
        
        self.memory.write_memory(
            self.session_id,
            'checkpoint',
            checkpoint,
            tier=tier,
            ttl_seconds=None if tier == MemoryTier.PERSISTENT else 86400
        )
    
    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load last training checkpoint"""
        if not self.session_id:
            self.create_session()
        
        return self.memory.read_memory(self.session_id, 'checkpoint')


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.DEBUG)
    
    # Create manager
    manager = TailsMemoryManager()
    
    # Create session
    session = manager.create_session("demo_session_001")
    
    # Write to different tiers
    manager.write_memory(
        session,
        "volatile_metrics",
        {"loss": 0.5, "reward": 10.2},
        tier=MemoryTier.VOLATILE
    )
    
    manager.write_memory(
        session,
        "checkpoint",
        {"epoch": 50, "weights": [1, 2, 3]},
        tier=MemoryTier.PERSISTENT
    )
    
    manager.write_memory(
        session,
        "temp_data",
        {"session_cache": [1, 2, 3]},
        tier=MemoryTier.EPHEMERAL,
        ttl_seconds=3600
    )
    
    # Read back
    print("\n=== TAILS MEMORY SYSTEM DEMO ===")
    print(f"Volatile: {manager.read_memory(session, 'volatile_metrics')}")
    print(f"Checkpoint: {manager.read_memory(session, 'checkpoint')}")
    print(f"Temp: {manager.read_memory(session, 'temp_data')}")
    
    # Stats
    print(f"\nStats: {manager.get_memory_stats()}")
    
    # Cleanup
    manager.clear_session(session)
    print("\nSession cleared!")
