"""
LLM Analysis Engine
===================

Async-safe LLM engine for semantic code analysis.
Offloads inference to thread pool to prevent blocking.
"""

import asyncio
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from pathlib import Path
from ark_tools.utils.debug_logger import debug_log


class LLMAnalysisEngine:
    """
    Async-safe LLM engine for semantic code analysis.
    Offloads inference to thread pool to prevent blocking.
    """
    
    def __init__(self, model_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM engine.
        
        Args:
            model_path: Path to the LLM model file
            config: Configuration dictionary
        """
        self.config = config or {}
        self.model_path = model_path or self._get_default_model_path()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._model = None  # Lazy load to save memory
        self.cache = {}  # Simple in-memory cache
        
        # Model parameters
        self.context_size = self.config.get('context_size', 8192)
        self.max_tokens = self.config.get('max_tokens', 2048)
        self.temperature = self.config.get('temperature', 0.1)
        self.n_threads = self.config.get('threads', 8)
        
    def _get_default_model_path(self) -> str:
        """Get default model path from config or environment."""
        import os
        from pathlib import Path
        
        # Check config
        if 'model_path' in self.config:
            return self.config['model_path']
        
        # Check environment
        if 'ARK_LLM_MODEL_PATH' in os.environ:
            return os.environ['ARK_LLM_MODEL_PATH']
        
        # Default location
        home = Path.home()
        default_path = home / '.ark_tools' / 'models' / 'codellama-7b-instruct.gguf'
        return str(default_path)
    
    def _get_model(self):
        """Lazy load model only when needed."""
        if not self._model:
            try:
                from llama_cpp import Llama
                debug_log.agent("Loading LLM model for semantic analysis...")
                
                self._model = Llama(
                    model_path=self.model_path,
                    n_ctx=self.context_size,
                    n_threads=self.n_threads,
                    n_gpu_layers=35 if self._has_gpu() else 0,
                    verbose=False,
                    seed=42  # For reproducible results
                )
                
                debug_log.agent(f"Model loaded successfully: {Path(self.model_path).name}")
            except ImportError:
                debug_log.error_trace("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
                raise ImportError("LLM engine requires llama-cpp-python. Install with: pip install llama-cpp-python")
            except Exception as e:
                debug_log.error_trace(f"Failed to load model from {self.model_path}", exception=e)
                raise
                
        return self._model
    
    async def analyze_domain_semantics(self, code_skeleton: str) -> Dict[str, Any]:
        """
        Analyze compressed code skeleton asynchronously.
        Returns domain analysis without blocking event loop.
        
        Args:
            code_skeleton: Compressed code skeleton from CodeCompressor
            
        Returns:
            Dictionary with domain analysis results
        """
        # Check cache
        cache_key = self._generate_cache_key(code_skeleton)
        if cache_key in self.cache:
            debug_log.agent("Using cached LLM analysis")
            return self.cache[cache_key]
        
        def _run_inference():
            """Blocking inference in thread pool."""
            llm = self._get_model()
            prompt = self._build_semantic_prompt(code_skeleton)
            
            response = llm(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=0.95,
                stop=["</json>", "\n\n\n"],
                stream=False
            )
            
            return response['choices'][0]['text']
        
        # Run in thread pool to avoid blocking
        debug_log.agent("Starting async LLM inference for domain analysis...")
        try:
            loop = asyncio.get_event_loop()
            result_text = await loop.run_in_executor(
                self._executor,
                _run_inference
            )
            
            result = self._parse_json_response(result_text)
            
            # Cache successful results
            if result.get('domains'):
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            debug_log.error_trace("LLM inference failed", exception=e)
            return {
                "error": str(e),
                "domains": [],
                "confidence": 0,
                "fallback": True
            }
    
    async def analyze_code_intent(self, code_skeleton: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the intent and purpose of code.
        
        Args:
            code_skeleton: Compressed code skeleton
            context: Additional context for analysis
            
        Returns:
            Dictionary with intent analysis
        """
        def _run_inference():
            llm = self._get_model()
            prompt = self._build_intent_prompt(code_skeleton, context)
            
            response = llm(
                prompt,
                max_tokens=1024,
                temperature=0.2,
                stop=["</analysis>"],
                stream=False
            )
            
            return response['choices'][0]['text']
        
        try:
            loop = asyncio.get_event_loop()
            result_text = await loop.run_in_executor(
                self._executor,
                _run_inference
            )
            
            return self._parse_intent_response(result_text)
            
        except Exception as e:
            debug_log.error_trace("Intent analysis failed", exception=e)
            return {"error": str(e), "intent": "unknown"}
    
    def _build_semantic_prompt(self, skeleton: str) -> str:
        """Build prompt for domain analysis."""
        return f"""[INST] You are a Senior Software Architect analyzing code structure.
Your task is to identify business domains and their relationships.

Analyze the following code skeleton (implementation details removed for clarity):

{skeleton}

Identify:
1. Business domains present in this code
2. The primary responsibility of each domain
3. Relationships between domains
4. Confidence level for each identification

Respond with ONLY valid JSON in this format:
{{
  "domains": [
    {{
      "name": "Authentication",
      "description": "User login and session management",
      "confidence": 0.95,
      "primary_components": ["UserService", "SessionManager", "TokenValidator"],
      "relationships": ["UserManagement", "Security"]
    }}
  ],
  "domain_relationships": [
    {{
      "from": "Authentication",
      "to": "UserManagement",
      "type": "depends_on",
      "strength": 0.8
    }}
  ],
  "overall_confidence": 0.85
}}
[/INST]
<json>"""
    
    def _build_intent_prompt(self, skeleton: str, context: Optional[str]) -> str:
        """Build prompt for intent analysis."""
        context_str = f"\nContext: {context}\n" if context else ""
        
        return f"""[INST] Analyze the following code and explain its intent and purpose.
{context_str}
Code Structure:
{skeleton}

Provide a brief analysis covering:
1. Primary purpose of this code
2. Key architectural patterns used
3. Main business logic implemented
4. Potential improvements or concerns

Keep the analysis concise and actionable.
[/INST]
<analysis>"""
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse and clean LLM JSON output."""
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0]
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0]
        
        # Find JSON object
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                debug_log.error_trace(f"Failed to parse LLM JSON response: {e}")
                # Attempt to fix common issues
                json_str = json_str.replace("'", '"')  # Replace single quotes
                json_str = json_str.replace("True", "true").replace("False", "false")
                try:
                    return json.loads(json_str)
                except:
                    pass
        
        # Fallback
        return {
            "domains": [],
            "error": "Failed to parse LLM response",
            "raw_response": text[:500]
        }
    
    def _parse_intent_response(self, text: str) -> Dict[str, Any]:
        """Parse intent analysis response."""
        return {
            "intent": text.strip(),
            "success": True
        }
    
    def _generate_cache_key(self, content: str) -> str:
        """Generate cache key from content."""
        # Use first 1000 chars for key to avoid huge hashes
        key_content = content[:1000]
        return hashlib.md5(key_content.encode()).hexdigest()
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            # Try to detect via nvidia-smi
            import subprocess
            try:
                subprocess.run(['nvidia-smi'], capture_output=True, check=True)
                return True
            except:
                return False
    
    async def analyze_batch(self, code_skeletons: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze multiple code skeletons in batch.
        
        Args:
            code_skeletons: Dictionary mapping identifiers to code skeletons
            
        Returns:
            Dictionary mapping identifiers to analysis results
        """
        results = {}
        
        # Create tasks for parallel processing
        tasks = []
        for identifier, skeleton in code_skeletons.items():
            task = self.analyze_domain_semantics(skeleton)
            tasks.append((identifier, task))
        
        # Execute in parallel
        for identifier, task in tasks:
            try:
                result = await task
                results[identifier] = result
            except Exception as e:
                debug_log.error_trace(f"Batch analysis failed for {identifier}", exception=e)
                results[identifier] = {"error": str(e), "domains": []}
        
        return results
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self.cache.clear()
        debug_log.agent("LLM analysis cache cleared")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_path": self.model_path,
            "context_size": self.context_size,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "threads": self.n_threads,
            "gpu_enabled": self._has_gpu(),
            "cache_size": len(self.cache),
            "model_loaded": self._model is not None
        }