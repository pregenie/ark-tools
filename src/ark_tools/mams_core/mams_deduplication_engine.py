#!/usr/bin/env python3
"""
MAMS Deduplication Engine
Handles multiple discovery runs and resolves conflicts intelligently
"""

import os
import sys
import json
import hashlib
import asyncio
import asyncpg
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from arkyvus.services.unified_logger import UnifiedLogger
    logger = UnifiedLogger.getLogger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

@dataclass
class DeduplicationResult:
    """Result of deduplication analysis"""
    action: str  # 'skip', 'update', 'create', 'conflict'
    reason: str
    existing_id: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None

class MAMSDeduplicationEngine:
    """
    Intelligent deduplication engine for MAMS discoveries
    Handles multiple discovery runs and resolves conflicts
    """
    
    def __init__(self):
        self.fingerprint_cache = {}
        self.conflict_rules = self._load_conflict_resolution_rules()
        
    def _load_conflict_resolution_rules(self) -> Dict[str, Any]:
        """Load conflict resolution rules"""
        return {
            'source_type_priority': {
                'service': 10,
                'class': 8,
                'method': 6,
                'function': 4,
                'utility': 2
            },
            'update_threshold_hours': 24,  # Consider updates if older than 24h
            'confidence_threshold': 0.85,  # Auto-resolve if confidence > 85%
            'signature_change_tolerance': 0.1  # 10% signature change tolerance
        }
    
    async def analyze_discovery_run(self, 
                                  mams_component: str,
                                  discovered_items: List[Dict[str, Any]],
                                  execution_scope: str = None) -> Dict[str, Any]:
        """
        Analyze a discovery run for duplicates and conflicts
        Returns deduplication strategy and actions
        """
        logger.info(f"🔍 Analyzing discovery run for {mams_component}")
        
        conn = await asyncpg.connect("postgresql://admin:chooters@db:5432/arkyvus_db")
        try:
            # Generate fingerprint for this discovery run
            run_fingerprint = self._generate_run_fingerprint(discovered_items)
            
            # Check if identical run already exists
            previous_run = await self._check_previous_run(conn, mams_component, run_fingerprint)
            
            if previous_run:
                return {
                    'action': 'skip_identical',
                    'reason': f'Identical run detected from {previous_run["start_time"]}',
                    'previous_execution_id': previous_run['id'],
                    'items_analyzed': len(discovered_items),
                    'deduplication_actions': []
                }
            
            # Analyze each discovered item
            dedup_actions = []
            stats = {
                'create': 0,
                'update': 0, 
                'skip': 0,
                'conflict': 0
            }
            
            for item in discovered_items:
                result = await self._analyze_item(conn, item)
                dedup_actions.append({
                    'item': item,
                    'result': result
                })
                stats[result.action] += 1
            
            return {
                'action': 'process',
                'run_fingerprint': run_fingerprint,
                'items_analyzed': len(discovered_items),
                'statistics': stats,
                'deduplication_actions': dedup_actions,
                'conflicts_requiring_resolution': [
                    action for action in dedup_actions 
                    if action['result'].action == 'conflict'
                ]
            }
            
        finally:
            await conn.close()
    
    async def _check_previous_run(self, conn, mams_component: str, fingerprint: str) -> Optional[Dict]:
        """Check if identical run already exists"""
        result = await conn.fetchrow("""
            SELECT id, start_time, execution_results
            FROM mams_execution_log 
            WHERE mams_component = $1 
                AND source_fingerprint = $2
                AND status = 'completed'
            ORDER BY start_time DESC 
            LIMIT 1
        """, mams_component, fingerprint)
        
        return dict(result) if result else None
    
    async def _analyze_item(self, conn, item: Dict[str, Any]) -> DeduplicationResult:
        """Analyze individual discovered item for deduplication"""
        full_qualified_name = item.get('full_qualified_name', '')
        service_name = item.get('service_name', '')
        method_signature = item.get('method_signature', {})
        
        # Check if item already exists
        existing = await conn.fetchrow("""
            SELECT id, full_qualified_name, method_signature, last_seen, 
                   discovery_metadata, created_at
            FROM migration_source_catalog 
            WHERE full_qualified_name = $1
        """, full_qualified_name)
        
        if not existing:
            return DeduplicationResult(
                action='create',
                reason='New item not found in catalog',
                confidence=1.0
            )
        
        # Item exists - determine if update is needed
        existing_sig = existing['method_signature'] or {}
        current_sig = method_signature or {}
        
        # Calculate signature similarity
        similarity = self._calculate_signature_similarity(existing_sig, current_sig)
        
        # Check age of existing item
        hours_old = (datetime.utcnow() - existing['created_at']).total_seconds() / 3600
        
        # Decision logic
        if similarity > (1 - self.conflict_rules['signature_change_tolerance']):
            if hours_old > self.conflict_rules['update_threshold_hours']:
                return DeduplicationResult(
                    action='update',
                    reason=f'Item exists but is {hours_old:.1f}h old, updating last_seen',
                    existing_id=str(existing['id']),
                    confidence=0.9
                )
            else:
                return DeduplicationResult(
                    action='skip',
                    reason=f'Recent identical item exists ({hours_old:.1f}h old)',
                    existing_id=str(existing['id']),
                    confidence=1.0
                )
        else:
            return DeduplicationResult(
                action='conflict',
                reason=f'Signature change detected (similarity: {similarity:.2f})',
                existing_id=str(existing['id']),
                confidence=similarity,
                metadata={
                    'existing_signature': existing_sig,
                    'new_signature': current_sig,
                    'similarity_score': similarity
                }
            )
    
    def _calculate_signature_similarity(self, sig1: Dict, sig2: Dict) -> float:
        """Calculate similarity between two method signatures"""
        if not sig1 and not sig2:
            return 1.0
        if not sig1 or not sig2:
            return 0.0
        
        # Compare key signature elements
        similarity_factors = []
        
        # Compare method names
        name1 = sig1.get('method_name', '')
        name2 = sig2.get('method_name', '')
        similarity_factors.append(1.0 if name1 == name2 else 0.0)
        
        # Compare parameter counts
        params1 = sig1.get('parameters', [])
        params2 = sig2.get('parameters', [])
        if len(params1) == len(params2):
            similarity_factors.append(1.0)
        else:
            max_params = max(len(params1), len(params2))
            if max_params > 0:
                similarity_factors.append(1.0 - abs(len(params1) - len(params2)) / max_params)
            else:
                similarity_factors.append(1.0)
        
        # Compare return types
        return1 = sig1.get('return_type', '')
        return2 = sig2.get('return_type', '')
        similarity_factors.append(1.0 if return1 == return2 else 0.5)
        
        return sum(similarity_factors) / len(similarity_factors)
    
    def _generate_run_fingerprint(self, discovered_items: List[Dict[str, Any]]) -> str:
        """Generate fingerprint for discovery run to detect identical runs"""
        # Sort items by qualified name for consistent hashing
        sorted_items = sorted(discovered_items, key=lambda x: x.get('full_qualified_name', ''))
        
        # Create fingerprint from key item attributes
        fingerprint_data = []
        for item in sorted_items:
            fingerprint_data.append({
                'fqn': item.get('full_qualified_name', ''),
                'type': item.get('source_type', ''),
                'service': item.get('service_name', ''),
                'method': item.get('method_name', '')
            })
        
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_json.encode()).hexdigest()
    
    async def execute_deduplication_actions(self, 
                                          conn,
                                          dedup_analysis: Dict[str, Any],
                                          execution_id: str) -> Dict[str, Any]:
        """Execute the deduplication actions determined by analysis"""
        results = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'conflicts_logged': 0,
            'errors': []
        }
        
        for action_item in dedup_analysis.get('deduplication_actions', []):
            item = action_item['item']
            result = action_item['result']
            
            try:
                if result.action == 'create':
                    await self._create_item(conn, item, execution_id)
                    results['created'] += 1
                    
                elif result.action == 'update':
                    await self._update_item(conn, item, result.existing_id)
                    results['updated'] += 1
                    
                elif result.action == 'skip':
                    results['skipped'] += 1
                    
                elif result.action == 'conflict':
                    await self._log_conflict(conn, item, result, execution_id)
                    results['conflicts_logged'] += 1
                    
            except Exception as e:
                error_msg = f"Error processing {item.get('full_qualified_name', 'unknown')}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    async def _create_item(self, conn, item: Dict[str, Any], execution_id: str):
        """Create new item in migration_source_catalog"""
        await conn.execute('''
            INSERT INTO migration_source_catalog 
            (source_type, full_qualified_name, service_name, method_name, 
             method_signature, current_state, discovery_metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''',
        item.get('source_type'),
        item.get('full_qualified_name'),
        item.get('service_name'),
        item.get('method_name'),
        json.dumps(item.get('method_signature', {})),
        item.get('current_state', 'discovered'),
        json.dumps({
            **item.get('discovery_metadata', {}),
            'mams_execution_id': execution_id,
            'deduplication_action': 'create'
        }))
    
    async def _update_item(self, conn, item: Dict[str, Any], existing_id: str):
        """Update existing item's last_seen timestamp"""
        await conn.execute('''
            UPDATE migration_source_catalog 
            SET last_seen = CURRENT_TIMESTAMP,
                discovery_metadata = jsonb_set(
                    discovery_metadata, 
                    '{last_dedup_update}', 
                    to_jsonb(CURRENT_TIMESTAMP::text)
                )
            WHERE id = $1
        ''', existing_id)
    
    async def _log_conflict(self, conn, item: Dict[str, Any], result: DeduplicationResult, execution_id: str):
        """Log conflict for manual resolution"""
        # This would insert into a conflicts table for manual review
        logger.warning(f"⚠️ Conflict detected: {item.get('full_qualified_name')} - {result.reason}")

async def main():
    """Test the deduplication engine"""
    engine = MAMSDeduplicationEngine()
    
    # Simulate discovered items
    test_items = [
        {
            'full_qualified_name': 'test.service.TestService',
            'source_type': 'service',
            'service_name': 'TestService',
            'method_name': 'test_method',
            'method_signature': {'method_name': 'test_method', 'parameters': []},
            'current_state': 'discovered'
        }
    ]
    
    analysis = await engine.analyze_discovery_run('MAMS-002', test_items, 'backend')
    print(f"Deduplication Analysis: {json.dumps(analysis, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())