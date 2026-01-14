#!/usr/bin/env python3
"""
MAMS-018: Interactive Review UI Generator
Generates interactive HTML UI for reviewing low-confidence classifications
"""

import json
from pathlib import Path
from typing import List, Any, Dict
from datetime import datetime
from dataclasses import dataclass

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from arkyvus.utils.debug_logger import debug_log


class ReviewUIGenerator:
    """
    Generates interactive HTML UI for manual review of classifications
    """
    
    def __init__(self):
        self.output_dir = Path('/app/.migration/review_ui')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_review_interface(self, classifications: List[Any], 
                                       validation_report: Any) -> str:
        """Generate interactive review UI"""
        debug_log.api("Generating review UI", level="INFO")
        
        # Filter for low-confidence items
        review_items = [c for c in classifications if c.requires_review]
        
        # Generate HTML
        html_content = self._generate_html(review_items, validation_report)
        
        # Save to file
        output_file = self.output_dir / f'review_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        output_file.write_text(html_content)
        
        debug_log.api(f"Review UI generated: {output_file}", level="INFO")
        return str(output_file)
    
    def _generate_html(self, review_items: List[Any], validation_report: Any) -> str:
        """Generate HTML content for review UI"""
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAMS Frontend Classification Review</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #2d3748;
            margin-bottom: 10px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #718096;
            margin-top: 5px;
        }}
        
        .filters {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .filter-group {{
            display: inline-block;
            margin-right: 20px;
        }}
        
        .filter-group label {{
            display: block;
            color: #4a5568;
            margin-bottom: 5px;
            font-weight: 600;
        }}
        
        .filter-group select,
        .filter-group input {{
            padding: 8px 12px;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
            background: white;
        }}
        
        .review-items {{
            display: grid;
            gap: 20px;
        }}
        
        .review-card {{
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .review-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}
        
        .review-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .file-path {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
            word-break: break-all;
        }}
        
        .confidence-badge {{
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
        }}
        
        .confidence-low {{ background: #f56565; }}
        .confidence-medium {{ background: #ed8936; }}
        .confidence-high {{ background: #48bb78; }}
        
        .review-body {{
            padding: 20px;
        }}
        
        .domain-section {{
            margin-bottom: 20px;
        }}
        
        .domain-label {{
            color: #718096;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .domain-options {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .domain-option {{
            padding: 8px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .domain-option:hover {{
            border-color: #667eea;
            background: #f7fafc;
        }}
        
        .domain-option.selected {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .domain-option.current {{
            background: #edf2f7;
            border-color: #cbd5e0;
        }}
        
        .evidence-section {{
            background: #f7fafc;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        
        .evidence-title {{
            font-weight: 600;
            color: #4a5568;
            margin-bottom: 10px;
        }}
        
        .evidence-item {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .evidence-item:last-child {{
            border-bottom: none;
        }}
        
        .evidence-type {{
            color: #718096;
            font-size: 0.9em;
        }}
        
        .evidence-value {{
            color: #2d3748;
            font-weight: 500;
        }}
        
        .review-actions {{
            display: flex;
            gap: 10px;
            padding: 15px 20px;
            background: #f7fafc;
            border-top: 1px solid #e2e8f0;
        }}
        
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5a67d8;
        }}
        
        .btn-secondary {{
            background: #e2e8f0;
            color: #4a5568;
        }}
        
        .btn-secondary:hover {{
            background: #cbd5e0;
        }}
        
        .btn-danger {{
            background: #f56565;
            color: white;
        }}
        
        .btn-danger:hover {{
            background: #e53e3e;
        }}
        
        .bulk-actions {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: none;
        }}
        
        .bulk-actions.show {{
            display: block;
        }}
        
        .review-reasons {{
            background: #fff5f5;
            border: 1px solid #feb2b2;
            border-radius: 6px;
            padding: 10px 15px;
            margin-bottom: 15px;
        }}
        
        .review-reason {{
            color: #c53030;
            margin: 5px 0;
        }}
        
        .dependencies-list {{
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            border-radius: 6px;
            padding: 10px 15px;
            margin-bottom: 15px;
        }}
        
        .dependency-item {{
            color: #22543d;
            font-family: monospace;
            font-size: 0.9em;
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MAMS Frontend Classification Review</h1>
            <p style="color: #718096; margin-top: 10px;">
                Review and correct low-confidence domain classifications
            </p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(review_items)}</div>
                <div class="stat-label">Items to Review</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([i for i in review_items if i.confidence < 0.5])}</div>
                <div class="stat-label">Low Confidence</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len([i for i in review_items if 0.5 <= i.confidence < 0.7])}</div>
                <div class="stat-label">Medium Confidence</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(validation_report.domain_violations)}</div>
                <div class="stat-label">Domain Violations</div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <label>Filter by Domain</label>
                <select id="domainFilter">
                    <option value="">All Domains</option>
                    {self._generate_domain_options(review_items)}
                </select>
            </div>
            <div class="filter-group">
                <label>Filter by Confidence</label>
                <select id="confidenceFilter">
                    <option value="">All</option>
                    <option value="low">Low (&lt; 0.5)</option>
                    <option value="medium">Medium (0.5 - 0.7)</option>
                    <option value="high">High (&gt; 0.7)</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Search Files</label>
                <input type="text" id="searchFilter" placeholder="Search file paths...">
            </div>
        </div>
        
        <div class="review-items">
            {self._generate_review_cards(review_items)}
        </div>
        
        <div class="bulk-actions" id="bulkActions">
            <h3 style="margin-bottom: 15px;">Bulk Actions</h3>
            <p id="selectedCount">0 items selected</p>
            <div style="margin-top: 15px;">
                <button class="btn btn-primary" onclick="applyBulkChanges()">Apply Changes</button>
                <button class="btn btn-secondary" onclick="clearSelection()">Clear Selection</button>
            </div>
        </div>
    </div>
    
    <script>
        let selectedItems = new Set();
        let changes = {{}};
        
        function selectDomain(cardId, domain) {{
            const card = document.getElementById(cardId);
            const options = card.querySelectorAll('.domain-option');
            
            options.forEach(opt => {{
                opt.classList.remove('selected');
                if (opt.dataset.domain === domain) {{
                    opt.classList.add('selected');
                }}
            }});
            
            changes[cardId] = {{ domain: domain }};
            updateBulkActions();
        }}
        
        function approveClassification(cardId) {{
            const card = document.getElementById(cardId);
            const currentDomain = card.dataset.currentDomain;
            
            changes[cardId] = {{ 
                domain: currentDomain, 
                approved: true 
            }};
            
            card.style.opacity = '0.7';
            card.style.background = '#f0fff4';
            updateBulkActions();
        }}
        
        function skipClassification(cardId) {{
            const card = document.getElementById(cardId);
            card.style.opacity = '0.5';
            
            if (changes[cardId]) {{
                delete changes[cardId];
            }}
            updateBulkActions();
        }}
        
        function flagForManual(cardId) {{
            const card = document.getElementById(cardId);
            
            changes[cardId] = {{ 
                flagged: true,
                reason: prompt('Reason for flagging:')
            }};
            
            card.style.borderLeft = '5px solid #f56565';
            updateBulkActions();
        }}
        
        function updateBulkActions() {{
            const count = Object.keys(changes).length;
            const bulkActions = document.getElementById('bulkActions');
            const selectedCount = document.getElementById('selectedCount');
            
            if (count > 0) {{
                bulkActions.classList.add('show');
                selectedCount.textContent = `${{count}} items with changes`;
            }} else {{
                bulkActions.classList.remove('show');
            }}
        }}
        
        function applyBulkChanges() {{
            const result = {{
                timestamp: new Date().toISOString(),
                changes: changes
            }};
            
            // Save to localStorage for persistence
            localStorage.setItem('mams_review_changes', JSON.stringify(result));
            
            // Generate download
            const blob = new Blob([JSON.stringify(result, null, 2)], 
                                 {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mams_review_${{Date.now()}}.json`;
            a.click();
            
            alert(`Changes saved for ${{Object.keys(changes).length}} items`);
        }}
        
        function clearSelection() {{
            changes = {{}};
            document.querySelectorAll('.review-card').forEach(card => {{
                card.style.opacity = '1';
                card.style.background = 'white';
                card.style.borderLeft = 'none';
            }});
            updateBulkActions();
        }}
        
        // Filtering
        document.getElementById('domainFilter').addEventListener('change', filterCards);
        document.getElementById('confidenceFilter').addEventListener('change', filterCards);
        document.getElementById('searchFilter').addEventListener('input', filterCards);
        
        function filterCards() {{
            const domainFilter = document.getElementById('domainFilter').value;
            const confidenceFilter = document.getElementById('confidenceFilter').value;
            const searchFilter = document.getElementById('searchFilter').value.toLowerCase();
            
            document.querySelectorAll('.review-card').forEach(card => {{
                let show = true;
                
                if (domainFilter && card.dataset.currentDomain !== domainFilter) {{
                    show = false;
                }}
                
                if (confidenceFilter) {{
                    const confidence = parseFloat(card.dataset.confidence);
                    if (confidenceFilter === 'low' && confidence >= 0.5) show = false;
                    if (confidenceFilter === 'medium' && (confidence < 0.5 || confidence >= 0.7)) show = false;
                    if (confidenceFilter === 'high' && confidence < 0.7) show = false;
                }}
                
                if (searchFilter && !card.dataset.filepath.toLowerCase().includes(searchFilter)) {{
                    show = false;
                }}
                
                card.style.display = show ? 'block' : 'none';
            }});
        }}
        
        // Load previous changes if any
        const savedChanges = localStorage.getItem('mams_review_changes');
        if (savedChanges) {{
            const saved = JSON.parse(savedChanges);
            if (confirm('Previous review session found. Load changes?')) {{
                changes = saved.changes;
                updateBulkActions();
            }}
        }}
    </script>
</body>
</html>
"""
        return html
    
    def _generate_domain_options(self, review_items: List[Any]) -> str:
        """Generate domain filter options"""
        domains = set()
        for item in review_items:
            domains.add(item.primary_domain)
            domains.update(item.secondary_domains)
        
        options = []
        for domain in sorted(domains):
            options.append(f'<option value="{domain}">{domain}</option>')
        
        return '\n'.join(options)
    
    def _generate_review_cards(self, review_items: List[Any]) -> str:
        """Generate individual review cards"""
        cards = []
        
        for i, item in enumerate(review_items):
            card_id = f"card_{i}"
            
            # Determine confidence level
            if item.confidence < 0.5:
                confidence_class = 'confidence-low'
            elif item.confidence < 0.7:
                confidence_class = 'confidence-medium'
            else:
                confidence_class = 'confidence-high'
            
            # Get top evidence
            top_evidence = []
            for ev in item.evidence[:5]:
                top_evidence.append(f"""
                    <div class="evidence-item">
                        <span class="evidence-type">{ev.type}</span>
                        <span class="evidence-value">{ev.value[:50]}</span>
                    </div>
                """)
            
            # Get domain options
            all_domains = ['auth', 'ai', 'brand', 'content', 'messaging', 'analytics', 
                          'business', 'storage', 'workflow', 'ui', 'shared', 'platform']
            
            domain_buttons = []
            for domain in all_domains:
                is_current = domain == item.primary_domain
                is_secondary = domain in item.secondary_domains
                
                class_name = 'domain-option'
                if is_current:
                    class_name += ' current'
                elif is_secondary:
                    class_name += ' secondary'
                
                domain_buttons.append(f"""
                    <div class="{class_name}" 
                         data-domain="{domain}"
                         onclick="selectDomain('{card_id}', '{domain}')">
                        {domain}
                    </div>
                """)
            
            # Generate card HTML
            card = f"""
            <div class="review-card" id="{card_id}" 
                 data-filepath="{item.file_path}"
                 data-current-domain="{item.primary_domain}"
                 data-confidence="{item.confidence}">
                <div class="review-header">
                    <div class="file-path">{Path(item.file_path).name}</div>
                    <div class="confidence-badge {confidence_class}">
                        {item.confidence:.2f}
                    </div>
                </div>
                
                <div class="review-body">
                    {'<div class="review-reasons">' + 
                     ''.join([f'<div class="review-reason">• {r}</div>' for r in item.review_reasons]) + 
                     '</div>' if item.review_reasons else ''}
                    
                    <div class="domain-section">
                        <div class="domain-label">Current: {item.primary_domain}</div>
                        <div class="domain-options">
                            {''.join(domain_buttons)}
                        </div>
                    </div>
                    
                    <div class="evidence-section">
                        <div class="evidence-title">Evidence</div>
                        {''.join(top_evidence)}
                    </div>
                    
                    {f'<div class="dependencies-list">' +
                     '<div class="evidence-title">Dependencies</div>' +
                     ''.join([f'<div class="dependency-item">• {d}</div>' 
                             for d in list(item.dependencies)[:5]]) +
                     '</div>' if item.dependencies else ''}
                </div>
                
                <div class="review-actions">
                    <button class="btn btn-primary" onclick="approveClassification('{card_id}')">
                        Approve
                    </button>
                    <button class="btn btn-secondary" onclick="skipClassification('{card_id}')">
                        Skip
                    </button>
                    <button class="btn btn-danger" onclick="flagForManual('{card_id}')">
                        Flag
                    </button>
                </div>
            </div>
            """
            
            cards.append(card)
        
        return '\n'.join(cards)


if __name__ == "__main__":
    import asyncio
    
    async def test_generator():
        generator = ReviewUIGenerator()
        
        # Create mock data
        mock_classifications = [
            type('Classification', (), {
                'file_path': '/app/client/src/components/auth/Login.tsx',
                'primary_domain': 'auth',
                'secondary_domains': ['ui'],
                'confidence': 0.45,
                'requires_review': True,
                'review_reasons': ['Low confidence score', 'Multiple domain indicators'],
                'evidence': [
                    type('Evidence', (), {
                        'type': 'import',
                        'value': 'Imports @/services/auth'
                    })(),
                    type('Evidence', (), {
                        'type': 'component',
                        'value': 'Component name: LoginForm'
                    })()
                ],
                'dependencies': ['@/services/auth', '@/components/ui/Button']
            })()
        ]
        
        mock_validation = type('ValidationReport', (), {
            'is_valid': True,
            'domain_violations': []
        })()
        
        # Generate UI
        ui_path = await generator.generate_review_interface(
            mock_classifications, 
            mock_validation
        )
        
        print(f"Review UI generated: {ui_path}")
    
    # Run test
    asyncio.run(test_generator())