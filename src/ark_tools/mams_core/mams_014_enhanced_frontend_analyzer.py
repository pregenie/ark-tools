#!/usr/bin/env python3
"""
MAMS-014: Enhanced Frontend Analyzer with Confidence Scoring
Production-grade analyzer that extends existing MAMS-003 with AST parsing and confidence metrics
"""

import os
import json
import math
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from arkyvus.utils.debug_logger import debug_log
from arkyvus.migrations.mams_003_frontend_classification import (
    FrontendClassificationEngine, ClassificationResult
)
from arkyvus.migrations.mams_013_typescript_ast_parser import (
    TypeScriptASTParser, TypeScriptAST
)

# Load existing MAMS master mapping
def load_master_mapping() -> Dict[str, Any]:
    """Load MAMS master mapping for existing classifications"""
    mapping_path = Path('/app/MAMS_MASTER_MAPPING.json')
    if not mapping_path.exists():
        mapping_path = Path('/Users/pregenie/Development/arkyvus_project/MAMS_MASTER_MAPPING.json')
    
    if mapping_path.exists():
        with open(mapping_path) as f:
            return json.load(f)
    return {'mappings': {}, 'metadata': {}}

@dataclass
class Evidence:
    """Evidence for domain classification"""
    type: str  # 'import', 'export', 'keyword', 'api_call', 'jsx_element', 'hook', 'file_path'
    value: str
    weight: float
    source_line: Optional[int] = None
    confidence: float = 1.0

@dataclass
class DomainScore:
    """Score for a specific domain"""
    domain: str
    raw_score: float
    log_odds: float
    probability: float
    evidence: List[Evidence]
    confidence: float

@dataclass
class EnhancedClassificationResult:
    """Enhanced classification with confidence and evidence"""
    file_path: str
    base_classification: Dict[str, Any]  # From MAMS mapping
    primary_domain: str
    secondary_domains: List[str]
    confidence: float
    domain_scores: List[DomainScore]
    evidence: List[Evidence]
    dependencies: Set[str]
    requires_review: bool
    review_reasons: List[str]
    ast_errors: List[str]
    classification_timestamp: str

class DomainOntology:
    """
    Domain ontology with rules and relationships
    Based on MAMS_FULL_PLATFORM_DESIGN.md domains
    """
    
    def __init__(self):
        self.domains = self._load_domain_ontology()
        self.evidence_weights = self._load_evidence_weights()
        
    def _load_domain_ontology(self) -> Dict[str, Any]:
        """Load comprehensive domain ontology"""
        return {
            'auth': {
                'keywords': ['auth', 'login', 'logout', 'session', 'token', 'permission', 'role', 'user', 'jwt', 'credential'],
                'imports': ['@/services/auth', 'jsonwebtoken', 'bcrypt', '@/contexts/AuthContext'],
                'api_patterns': ['/auth/', '/users/', '/permissions/', '/login', '/logout'],
                'components': ['Login', 'Signup', 'Auth', 'Permission', 'Role'],
                'hooks': ['useAuth', 'useUser', 'usePermissions'],
                'confidence_threshold': 0.85,
                'risk_level': 'high',
                'allowed_dependencies': ['shared', 'platform', 'messaging'],
                'backend_service': 'unified_auth_service'
            },
            'ai': {
                'keywords': ['ai', 'ml', 'llm', 'gpt', 'openai', 'model', 'prompt', 'embedding', 'maia', 'completion'],
                'imports': ['openai', '@/services/ai', 'langchain', '@/services/maia'],
                'api_patterns': ['/ai/', '/models/', '/completions/', '/embeddings/'],
                'components': ['AI', 'Model', 'Prompt', 'MAIA', 'Completion'],
                'hooks': ['useAI', 'useModel', 'useCompletion'],
                'confidence_threshold': 0.70,
                'risk_level': 'medium',
                'allowed_dependencies': ['shared', 'platform', 'data', 'content'],
                'backend_service': 'unified_ai_service'
            },
            'brand': {
                'keywords': ['brand', 'brand_kit', 'branding', 'logo', 'style', 'theme', 'identity'],
                'imports': ['@/services/brand', '@/contexts/BrandContext'],
                'api_patterns': ['/brands/', '/brand-kits/', '/themes/'],
                'components': ['Brand', 'BrandKit', 'Theme', 'Style'],
                'hooks': ['useBrand', 'useBrandKit', 'useTheme'],
                'confidence_threshold': 0.75,
                'risk_level': 'low',
                'allowed_dependencies': ['shared', 'platform', 'content', 'storage'],
                'backend_service': 'unified_brand_service'
            },
            'content': {
                'keywords': ['content', 'article', 'post', 'blog', 'text', 'editor', 'wysiwyg', 'markdown'],
                'imports': ['@/services/content', 'draft-js', 'quill', 'slate'],
                'api_patterns': ['/content/', '/articles/', '/posts/'],
                'components': ['Content', 'Editor', 'Article', 'Post', 'WYSIWYG'],
                'hooks': ['useContent', 'useEditor', 'useArticle'],
                'confidence_threshold': 0.70,
                'risk_level': 'low',
                'allowed_dependencies': ['shared', 'platform', 'storage', 'ai'],
                'backend_service': 'unified_content_service'
            },
            'messaging': {
                'keywords': ['message', 'email', 'sms', 'notification', 'alert', 'chat', 'inbox'],
                'imports': ['@/services/messaging', 'nodemailer', 'twilio', 'socket.io-client'],
                'api_patterns': ['/messages/', '/notifications/', '/emails/'],
                'components': ['Message', 'Notification', 'Email', 'Chat', 'Alert'],
                'hooks': ['useMessages', 'useNotifications', 'useChat'],
                'confidence_threshold': 0.75,
                'risk_level': 'medium',
                'allowed_dependencies': ['shared', 'platform', 'auth', 'realtime'],
                'backend_service': 'unified_messaging_service'
            },
            'analytics': {
                'keywords': ['analytics', 'metrics', 'tracking', 'stats', 'report', 'dashboard', 'chart', 'graph'],
                'imports': ['@/services/analytics', 'mixpanel', 'google-analytics', 'chart.js', 'd3'],
                'api_patterns': ['/analytics/', '/metrics/', '/reports/', '/stats/'],
                'components': ['Analytics', 'Dashboard', 'Chart', 'Report', 'Metrics'],
                'hooks': ['useAnalytics', 'useMetrics', 'useTracking'],
                'confidence_threshold': 0.70,
                'risk_level': 'low',
                'allowed_dependencies': ['shared', 'platform', 'visualization', 'data'],
                'backend_service': 'unified_analytics_service'
            },
            'business': {
                'keywords': ['billing', 'payment', 'invoice', 'subscription', 'pricing', 'stripe', 'checkout'],
                'imports': ['stripe', '@/services/billing', '@/services/payments'],
                'api_patterns': ['/billing/', '/payments/', '/subscriptions/', '/invoices/'],
                'components': ['Billing', 'Payment', 'Subscription', 'Invoice', 'Checkout'],
                'hooks': ['useBilling', 'usePayments', 'useSubscription'],
                'confidence_threshold': 0.85,
                'risk_level': 'high',
                'allowed_dependencies': ['shared', 'platform', 'auth'],
                'backend_service': 'unified_business_service'
            },
            'storage': {
                'keywords': ['storage', 'upload', 'file', 'blob', 's3', 'media', 'image', 'asset', 'download'],
                'imports': ['@/services/storage', 'aws-sdk', '@aws-sdk/client-s3', 'multer'],
                'api_patterns': ['/storage/', '/uploads/', '/files/', '/media/'],
                'components': ['Upload', 'FileManager', 'MediaLibrary', 'Asset'],
                'hooks': ['useStorage', 'useUpload', 'useFiles'],
                'confidence_threshold': 0.70,
                'risk_level': 'medium',
                'allowed_dependencies': ['shared', 'platform', 'content'],
                'backend_service': 'unified_storage_service'
            },
            'workflow': {
                'keywords': ['workflow', 'process', 'pipeline', 'task', 'job', 'queue', 'schedule', 'automation'],
                'imports': ['@/services/workflow', 'bull', 'agenda', 'node-cron'],
                'api_patterns': ['/workflows/', '/tasks/', '/jobs/', '/schedules/'],
                'components': ['Workflow', 'Pipeline', 'Task', 'Schedule', 'Automation'],
                'hooks': ['useWorkflow', 'useTasks', 'useSchedule'],
                'confidence_threshold': 0.75,
                'risk_level': 'medium',
                'allowed_dependencies': ['shared', 'platform', 'messaging', 'ai'],
                'backend_service': 'unified_workflow_service'
            },
            'ui': {
                'keywords': ['button', 'modal', 'dialog', 'layout', 'component', 'widget', 'form', 'input'],
                'imports': ['@/components/ui', '@mui/material', 'antd', '@/components/base'],
                'api_patterns': [],  # UI components typically don't make API calls
                'components': ['Button', 'Modal', 'Dialog', 'Layout', 'Form', 'Input'],
                'hooks': ['useModal', 'useDialog', 'useForm'],
                'confidence_threshold': 0.65,
                'risk_level': 'low',
                'allowed_dependencies': ['shared', 'platform'],
                'backend_service': None  # UI is frontend-only
            },
            'shared': {
                'keywords': ['util', 'helper', 'common', 'shared', 'constants', 'types', 'interface'],
                'imports': ['@/utils', '@/helpers', '@/constants', '@/types'],
                'api_patterns': [],
                'components': [],
                'hooks': [],
                'confidence_threshold': 0.60,
                'risk_level': 'low',
                'allowed_dependencies': [],  # Shared can be used by all
                'backend_service': None
            },
            'platform': {
                'keywords': ['config', 'env', 'settings', 'initialization', 'bootstrap', 'setup'],
                'imports': ['@/config', '@/platform', 'dotenv'],
                'api_patterns': ['/config/', '/settings/'],
                'components': ['Settings', 'Config', 'Setup'],
                'hooks': ['useConfig', 'useSettings'],
                'confidence_threshold': 0.65,
                'risk_level': 'medium',
                'allowed_dependencies': ['shared'],
                'backend_service': 'unified_platform_service'
            }
        }
    
    def _load_evidence_weights(self) -> Dict[str, float]:
        """Load evidence type weights for confidence calculation"""
        return {
            'import_exact': 2.0,      # Exact import match
            'import_partial': 1.0,    # Partial import match
            'api_exact': 1.8,         # Exact API pattern match
            'api_partial': 0.9,       # Partial API pattern match
            'component_name': 1.5,    # Component name match
            'hook_exact': 1.6,        # Exact hook match
            'keyword_strong': 1.2,    # Strong keyword match
            'keyword_weak': 0.6,      # Weak keyword match
            'file_path': 0.8,         # File path indicator
            'jsx_element': 0.7,       # JSX element usage
            'export_type': 0.5       # Export type indicator
        }

class EnhancedFrontendAnalyzer:
    """
    Production-grade frontend analyzer with AST parsing and confidence scoring
    Extends existing MAMS-003 classification with advanced capabilities
    """
    
    def __init__(self):
        # Use existing classification engine as base
        self.base_classifier = FrontendClassificationEngine()
        
        # Add enhanced capabilities
        self.ts_parser = TypeScriptASTParser()
        self.ontology = DomainOntology()
        self.master_mapping = load_master_mapping()
        
    async def analyze_file(self, file_path: Path) -> EnhancedClassificationResult:
        """
        Analyze a single frontend file with confidence scoring
        """
        file_path = Path(file_path)
        debug_log.api(f"Analyzing {file_path.name}", level="DEBUG")
        
        # Get base classification from MAMS mapping
        relative_path = self._get_relative_path(file_path)
        base_classification = self.master_mapping['mappings'].get(relative_path, {})
        
        # Parse TypeScript AST
        ast = await self.ts_parser.parse(file_path)
        
        # Extract evidence from multiple sources
        evidence = self._extract_evidence(file_path, ast, base_classification)
        
        # Calculate domain scores using log-odds
        domain_scores = self._calculate_domain_scores(evidence)
        
        # Select primary and secondary domains
        primary_domain, secondary_domains = self._select_domains(domain_scores)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(domain_scores, primary_domain)
        
        # Determine if review is needed
        requires_review, review_reasons = self._check_review_requirements(
            confidence, primary_domain, ast.errors
        )
        
        return EnhancedClassificationResult(
            file_path=str(file_path),
            base_classification=base_classification,
            primary_domain=primary_domain,
            secondary_domains=secondary_domains,
            confidence=confidence,
            domain_scores=domain_scores,
            evidence=evidence,
            dependencies=ast.dependencies,
            requires_review=requires_review,
            review_reasons=review_reasons,
            ast_errors=ast.errors,
            classification_timestamp=datetime.now().isoformat()
        )
    
    def _get_relative_path(self, file_path: Path) -> str:
        """Get relative path matching MAMS mapping format"""
        path_str = str(file_path)
        
        # Handle different path formats
        if '/client/src/' in path_str:
            return 'src/' + path_str.split('/client/src/')[-1]
        elif 'client/src/' in path_str:
            return 'src/' + path_str.split('client/src/')[-1]
        elif '/src/' in path_str:
            return 'src/' + path_str.split('/src/')[-1]
        
        return str(file_path.name)
    
    def _extract_evidence(self, file_path: Path, ast: TypeScriptAST, 
                         base_classification: Dict) -> List[Evidence]:
        """Extract evidence from multiple sources"""
        evidence = []
        
        # 1. File path evidence
        path_str = str(file_path).lower()
        for domain, config in self.ontology.domains.items():
            for keyword in config['keywords']:
                if keyword in path_str:
                    evidence.append(Evidence(
                        type='file_path',
                        value=f"Path contains '{keyword}'",
                        weight=self.ontology.evidence_weights['file_path']
                    ))
        
        # 2. Import evidence
        for imp in ast.imports:
            evidence.extend(self._analyze_import(imp.source, imp.is_type_only))
        
        # 3. API call evidence
        for api_call in ast.api_calls:
            evidence.extend(self._analyze_api_call(api_call))
        
        # 4. Component name evidence
        for component in ast.components:
            evidence.extend(self._analyze_component_name(component.name))
        
        # 5. Hook usage evidence
        for hook in ast.hooks:
            evidence.extend(self._analyze_hook(hook))
        
        # 6. JSX element evidence
        jsx_elements = set()
        for component in ast.components:
            jsx_elements.update(component.jsx_elements)
        
        for element in jsx_elements:
            evidence.extend(self._analyze_jsx_element(element))
        
        # 7. State management evidence
        if ast.state_management:
            evidence.extend(self._analyze_state_management(ast.state_management))
        
        # 8. Export evidence
        for export in ast.exports:
            if export.name != 'default':
                evidence.extend(self._analyze_export(export.name))
        
        return evidence
    
    def _analyze_import(self, source: str, is_type_only: bool) -> List[Evidence]:
        """Analyze import statement for domain evidence"""
        evidence = []
        source_lower = source.lower()
        
        for domain, config in self.ontology.domains.items():
            # Check exact import matches
            for imp_pattern in config['imports']:
                if imp_pattern in source or source in imp_pattern:
                    weight = self.ontology.evidence_weights['import_exact']
                    if is_type_only:
                        weight *= 0.7  # Type-only imports are weaker evidence
                    
                    evidence.append(Evidence(
                        type='import',
                        value=f"Imports {source}",
                        weight=weight,
                        confidence=0.9 if not is_type_only else 0.6
                    ))
                    break
            
            # Check partial matches
            for keyword in config['keywords']:
                if keyword in source_lower:
                    weight = self.ontology.evidence_weights['import_partial']
                    if is_type_only:
                        weight *= 0.7
                    
                    evidence.append(Evidence(
                        type='import',
                        value=f"Import contains '{keyword}'",
                        weight=weight,
                        confidence=0.6
                    ))
        
        return evidence
    
    def _analyze_api_call(self, api_call: Dict) -> List[Evidence]:
        """Analyze API call for domain evidence"""
        evidence = []
        endpoint = api_call.get('endpoint', '')
        
        for domain, config in self.ontology.domains.items():
            for pattern in config['api_patterns']:
                if pattern in endpoint:
                    evidence.append(Evidence(
                        type='api_call',
                        value=f"Calls {endpoint}",
                        weight=self.ontology.evidence_weights['api_exact'],
                        source_line=api_call.get('lineNumber'),
                        confidence=0.95
                    ))
                elif any(keyword in endpoint for keyword in config['keywords']):
                    evidence.append(Evidence(
                        type='api_call',
                        value=f"API call to {endpoint}",
                        weight=self.ontology.evidence_weights['api_partial'],
                        source_line=api_call.get('lineNumber'),
                        confidence=0.7
                    ))
        
        return evidence
    
    def _analyze_component_name(self, name: str) -> List[Evidence]:
        """Analyze component name for domain evidence"""
        evidence = []
        name_lower = name.lower()
        
        for domain, config in self.ontology.domains.items():
            for component_pattern in config['components']:
                if component_pattern.lower() in name_lower:
                    evidence.append(Evidence(
                        type='component',
                        value=f"Component '{name}'",
                        weight=self.ontology.evidence_weights['component_name'],
                        confidence=0.85
                    ))
        
        return evidence
    
    def _analyze_hook(self, hook: str) -> List[Evidence]:
        """Analyze React hook for domain evidence"""
        evidence = []
        
        for domain, config in self.ontology.domains.items():
            if hook in config['hooks']:
                evidence.append(Evidence(
                    type='hook',
                    value=f"Uses {hook}",
                    weight=self.ontology.evidence_weights['hook_exact'],
                    confidence=0.9
                ))
        
        return evidence
    
    def _analyze_jsx_element(self, element: str) -> List[Evidence]:
        """Analyze JSX element for domain evidence"""
        evidence = []
        element_lower = element.lower()
        
        for domain, config in self.ontology.domains.items():
            for component in config['components']:
                if component.lower() in element_lower:
                    evidence.append(Evidence(
                        type='jsx_element',
                        value=f"Renders <{element}>",
                        weight=self.ontology.evidence_weights['jsx_element'],
                        confidence=0.7
                    ))
        
        return evidence
    
    def _analyze_state_management(self, state_mgmt: Dict) -> List[Evidence]:
        """Analyze state management patterns for evidence"""
        evidence = []
        
        # Complex state management suggests business logic
        if state_mgmt.get('useReducer', 0) > 2:
            evidence.append(Evidence(
                type='state_management',
                value='Complex state with useReducer',
                weight=0.8,
                confidence=0.7
            ))
        
        # Global state suggests cross-cutting concerns
        if state_mgmt.get('useContext', 0) > 3:
            evidence.append(Evidence(
                type='state_management',
                value='Heavy context usage',
                weight=0.7,
                confidence=0.6
            ))
        
        # Redux/Zustand suggests app-level state
        if state_mgmt.get('redux') or state_mgmt.get('zustand'):
            evidence.append(Evidence(
                type='state_management',
                value='Global state management',
                weight=0.9,
                confidence=0.8
            ))
        
        return evidence
    
    def _analyze_export(self, name: str) -> List[Evidence]:
        """Analyze export name for domain evidence"""
        evidence = []
        name_lower = name.lower()
        
        for domain, config in self.ontology.domains.items():
            for keyword in config['keywords']:
                if keyword in name_lower:
                    evidence.append(Evidence(
                        type='export',
                        value=f"Exports '{name}'",
                        weight=self.ontology.evidence_weights['export_type'],
                        confidence=0.6
                    ))
        
        return evidence
    
    def _calculate_domain_scores(self, evidence: List[Evidence]) -> List[DomainScore]:
        """
        Calculate domain scores using log-odds model
        Mathematically correct implementation as per v3.0 requirements
        """
        domain_evidence = defaultdict(list)
        
        # Group evidence by potential domains
        for ev in evidence:
            # Determine which domains this evidence supports
            for domain, config in self.ontology.domains.items():
                if self._evidence_supports_domain(ev, domain, config):
                    domain_evidence[domain].append(ev)
        
        # Calculate log-odds for each domain
        domain_scores = []
        
        for domain, config in self.ontology.domains.items():
            domain_ev = domain_evidence.get(domain, [])
            
            # Calculate log-odds
            log_odds = 0.0
            
            # Positive evidence
            for ev in domain_ev:
                log_odds += math.log(ev.weight * ev.confidence + 1e-10)
            
            # Negative evidence (lack of expected evidence)
            expected_evidence_types = self._get_expected_evidence_types(config)
            actual_evidence_types = set(ev.type for ev in domain_ev)
            
            for expected in expected_evidence_types:
                if expected not in actual_evidence_types:
                    log_odds -= math.log(2.0)  # Penalty for missing expected evidence
            
            # Convert log-odds to probability using sigmoid
            probability = 1 / (1 + math.exp(-log_odds))
            
            # Calculate confidence based on evidence quantity and quality
            confidence = self._calculate_evidence_confidence(domain_ev)
            
            domain_scores.append(DomainScore(
                domain=domain,
                raw_score=sum(ev.weight * ev.confidence for ev in domain_ev),
                log_odds=log_odds,
                probability=probability,
                evidence=domain_ev,
                confidence=confidence
            ))
        
        # Sort by probability
        domain_scores.sort(key=lambda x: x.probability, reverse=True)
        
        return domain_scores
    
    def _evidence_supports_domain(self, evidence: Evidence, domain: str, 
                                 config: Dict) -> bool:
        """Check if evidence supports a specific domain"""
        ev_value_lower = evidence.value.lower()
        
        # Check keywords
        for keyword in config['keywords']:
            if keyword in ev_value_lower:
                return True
        
        # Check specific patterns based on evidence type
        if evidence.type == 'import':
            for imp in config['imports']:
                if imp in ev_value_lower or ev_value_lower in imp:
                    return True
        
        elif evidence.type == 'api_call':
            for pattern in config['api_patterns']:
                if pattern in ev_value_lower:
                    return True
        
        elif evidence.type == 'component':
            for comp in config['components']:
                if comp.lower() in ev_value_lower:
                    return True
        
        elif evidence.type == 'hook':
            for hook in config['hooks']:
                if hook in ev_value_lower:
                    return True
        
        return False
    
    def _get_expected_evidence_types(self, config: Dict) -> Set[str]:
        """Get expected evidence types for a domain"""
        expected = set()
        
        if config['imports']:
            expected.add('import')
        if config['api_patterns']:
            expected.add('api_call')
        if config['components']:
            expected.add('component')
        if config['hooks']:
            expected.add('hook')
        
        return expected
    
    def _calculate_evidence_confidence(self, evidence: List[Evidence]) -> float:
        """Calculate confidence based on evidence quantity and quality"""
        if not evidence:
            return 0.0
        
        # Calculate weighted average confidence
        total_weight = sum(ev.weight for ev in evidence)
        if total_weight == 0:
            return 0.0
        
        weighted_confidence = sum(ev.weight * ev.confidence for ev in evidence)
        avg_confidence = weighted_confidence / total_weight
        
        # Boost confidence for multiple evidence types
        evidence_types = set(ev.type for ev in evidence)
        type_diversity_boost = min(0.2, len(evidence_types) * 0.05)
        
        # Boost confidence for strong evidence
        strong_evidence_count = sum(1 for ev in evidence if ev.weight > 1.5)
        strength_boost = min(0.15, strong_evidence_count * 0.05)
        
        return min(1.0, avg_confidence + type_diversity_boost + strength_boost)
    
    def _select_domains(self, domain_scores: List[DomainScore]) -> Tuple[str, List[str]]:
        """Select primary and secondary domains based on scores"""
        if not domain_scores:
            return 'misc', []
        
        # Primary domain is highest probability
        primary = domain_scores[0].domain
        
        # Secondary domains are those with probability > 0.3 and within 20% of primary
        secondary = []
        primary_prob = domain_scores[0].probability
        
        for score in domain_scores[1:]:
            if score.probability > 0.3 and score.probability > (primary_prob * 0.8):
                secondary.append(score.domain)
                if len(secondary) >= 2:  # Limit to 2 secondary domains
                    break
        
        return primary, secondary
    
    def _calculate_confidence(self, domain_scores: List[DomainScore], 
                             primary_domain: str) -> float:
        """Calculate overall classification confidence"""
        if not domain_scores:
            return 0.0
        
        # Find primary domain score
        primary_score = next((s for s in domain_scores if s.domain == primary_domain), None)
        if not primary_score:
            return 0.0
        
        # Base confidence is the primary domain's confidence
        confidence = primary_score.confidence
        
        # Adjust based on separation from other domains
        if len(domain_scores) > 1:
            separation = primary_score.probability - domain_scores[1].probability
            separation_boost = min(0.2, separation)
            confidence = min(1.0, confidence + separation_boost)
        
        return confidence
    
    def _check_review_requirements(self, confidence: float, primary_domain: str, 
                                  ast_errors: List[str]) -> Tuple[bool, List[str]]:
        """Determine if manual review is required"""
        review_reasons = []
        
        # Check confidence threshold
        domain_config = self.ontology.domains.get(primary_domain, {})
        threshold = domain_config.get('confidence_threshold', 0.7)
        
        if confidence < threshold:
            review_reasons.append(f"Confidence ({confidence:.2f}) below threshold ({threshold})")
        
        # Check for AST parsing errors
        if ast_errors:
            review_reasons.append(f"AST parsing errors: {', '.join(ast_errors[:3])}")
        
        # Check for high-risk domains
        if domain_config.get('risk_level') == 'high' and confidence < 0.9:
            review_reasons.append(f"High-risk domain '{primary_domain}' requires high confidence")
        
        # Check for domain uncertainty
        if primary_domain == 'misc' or primary_domain == 'unknown':
            review_reasons.append("Unable to determine specific domain")
        
        requires_review = len(review_reasons) > 0
        
        return requires_review, review_reasons
    
    async def analyze_batch(self, file_paths: List[Path], 
                           progress_callback: Optional[callable] = None) -> List[EnhancedClassificationResult]:
        """Analyze multiple files with progress tracking"""
        results = []
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                result = await self.analyze_file(file_path)
                results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, total, file_path)
                    
            except Exception as e:
                debug_log.error_trace(f"Failed to analyze {file_path}", exception=e)
                # Create error result
                results.append(EnhancedClassificationResult(
                    file_path=str(file_path),
                    base_classification={},
                    primary_domain='error',
                    secondary_domains=[],
                    confidence=0.0,
                    domain_scores=[],
                    evidence=[],
                    dependencies=set(),
                    requires_review=True,
                    review_reasons=[f"Analysis failed: {str(e)}"],
                    ast_errors=[str(e)],
                    classification_timestamp=datetime.now().isoformat()
                ))
        
        return results


# Test functionality
if __name__ == "__main__":
    async def test_analyzer():
        analyzer = EnhancedFrontendAnalyzer()
        
        # Test on a sample file
        test_file = Path("/app/client/src/components/auth/LoginPage.tsx")
        if not test_file.exists():
            test_file = Path("/Users/pregenie/Development/arkyvus_project/client/src/components/auth/LoginPage.tsx")
        
        if test_file.exists():
            result = await analyzer.analyze_file(test_file)
            
            print(f"File: {result.file_path}")
            print(f"Primary Domain: {result.primary_domain}")
            print(f"Secondary Domains: {result.secondary_domains}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Requires Review: {result.requires_review}")
            
            if result.review_reasons:
                print(f"Review Reasons: {', '.join(result.review_reasons)}")
            
            print(f"\nTop Domain Scores:")
            for score in result.domain_scores[:3]:
                print(f"  {score.domain}: {score.probability:.3f} (confidence: {score.confidence:.2f})")
            
            print(f"\nEvidence Summary:")
            evidence_types = defaultdict(int)
            for ev in result.evidence:
                evidence_types[ev.type] += 1
            
            for ev_type, count in evidence_types.items():
                print(f"  {ev_type}: {count} pieces")
        else:
            print(f"Test file not found: {test_file}")
    
    # Run test
    asyncio.run(test_analyzer())