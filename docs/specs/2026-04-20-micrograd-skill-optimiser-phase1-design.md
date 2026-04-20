# MicroGrad Skill Optimiser — Phase 1 Design Spec

## Goal

Build a platform for systematically improving AI skill files through iterative weight-based evaluation and refinement. Phase 1 delivers: network creation with AI auto-population, a training lab with a real micrograd engine using optimised nudge-testing, learning config dashboard, chat interface (learn + command modes), activity feed, and skill.md export. Deployed on Railway (FastAPI + React + PostgreSQL).

---

## Current State Audit

**Repo:** Empty — single `README.md` with `# skill-tester`. No existing code, no database, no configuration. Greenfield build.

---

## Architecture

### Monorepo Structure

```
skill-tester/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, lifespan, CORS, router registration
│   │   ├── config.py                # Pydantic Settings (env vars)
│   │   ├── database.py              # SQLAlchemy async engine + session factory
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── company.py           # Company, CompanyBrain
│   │   │   ├── network.py           # Network
│   │   │   ├── component.py         # Component
│   │   │   ├── training.py          # TrainingRun, Evaluation
│   │   │   ├── output.py            # OutputTemplate, GeneratedOutput
│   │   │   ├── feedback.py          # Feedback
│   │   │   └── activity.py          # ActivityLog
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── company.py
│   │   │   ├── network.py
│   │   │   ├── component.py
│   │   │   ├── training.py
│   │   │   ├── output.py
│   │   │   ├── feedback.py
│   │   │   └── chat.py
│   │   ├── routers/                 # FastAPI route handlers
│   │   │   ├── __init__.py
│   │   │   ├── companies.py
│   │   │   ├── networks.py
│   │   │   ├── components.py
│   │   │   ├── training.py
│   │   │   ├── outputs.py
│   │   │   ├── chat.py
│   │   │   ├── activity.py
│   │   │   └── websocket.py
│   │   ├── services/                # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── research_agent.py    # Brave search + page fetch + LLM synthesis
│   │   │   ├── evaluator.py         # LLM-as-judge batch scoring
│   │   │   ├── generator.py         # Output generation from weights
│   │   │   ├── training_engine.py   # Micrograd integration + optimised nudge loop
│   │   │   └── chat_service.py      # Chat interface logic (learn + command modes)
│   │   ├── engine/                  # Micrograd core
│   │   │   ├── __init__.py
│   │   │   ├── value.py             # Karpathy's Value class (adapted)
│   │   │   └── optimizer.py         # SGD with finite-difference gradients
│   │   └── integrations/
│   │       ├── __init__.py
│   │       ├── openrouter.py        # OpenAI SDK wrapper pointed at OpenRouter
│   │       └── brave_search.py      # Brave Search API + page content extraction
│   ├── alembic/                     # Database migrations
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── NetworkCreator.tsx    # Goal input + component auto-population
│   │   │   ├── TrainingLab.tsx       # Main training view
│   │   │   ├── LearningConfig.tsx    # Config dashboard
│   │   │   ├── CommandMode.tsx       # Output generation + download
│   │   │   └── NetworkManager.tsx    # Overview of all networks
│   │   ├── components/
│   │   │   ├── ComponentTable.tsx    # Weight/score table with drag-reorder
│   │   │   ├── LossChart.tsx         # Real-time loss curve (Recharts)
│   │   │   ├── ActivityFeed.tsx      # WebSocket-driven event log
│   │   │   ├── ChatPanel.tsx         # Chat interface (learn + command)
│   │   │   ├── NetworkCard.tsx       # Summary card for network manager
│   │   │   └── Layout.tsx            # App shell: sidebar + top bar + content
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts       # WebSocket connection + reconnect
│   │   │   └── useApi.ts             # Fetch wrapper
│   │   ├── api/
│   │   │   └── client.ts             # Typed API client
│   │   └── stores/
│   │       ├── networkStore.ts       # Zustand store for active network state
│   │       └── activityStore.ts      # Zustand store for activity feed
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   └── Dockerfile
├── docker-compose.yml               # Local dev: postgres + backend + frontend
└── railway.toml                     # Railway deployment config
```

### Tech Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Backend | Python + FastAPI | 3.12+ / 0.115+ | Async, OpenAPI docs, WebSocket support |
| ORM | SQLAlchemy (async) | 2.0+ | Best Python async ORM, Alembic migrations |
| Database | PostgreSQL | 16 | Railway plugin, JSONB for flexible fields |
| Migrations | Alembic | 1.13+ | Standard for SQLAlchemy |
| AI Client | openai Python SDK | 1.50+ | OpenAI-compatible, works with OpenRouter |
| Search | Brave Search API | v1 | Web research for component discovery |
| Content extraction | trafilatura | 1.12+ | Extract article text from HTML |
| Frontend | React + TypeScript | 19 / 5.6+ | Component-driven, type-safe |
| Build tool | Vite | 6+ | Fast dev server, optimised builds |
| Styling | Tailwind CSS | 4+ | Utility-first, dark theme support |
| State | Zustand | 5+ | Lightweight, good for real-time updates |
| Charts | Recharts | 2+ | React-native charting for loss curves |
| Drag-reorder | dnd-kit | 6+ | Modern React DnD, accessible |
| Deployment | Railway | — | Postgres plugin + backend + frontend services |

---

## Data Model

### PostgreSQL Schema

All tables use UUID primary keys, `created_at` / `updated_at` timestamps.

#### company

```sql
CREATE TABLE company (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    paperclip_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### company_brain

```sql
CREATE TABLE company_brain (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    knowledge_base JSONB DEFAULT '{}',
    cross_references JSONB DEFAULT '{}',
    last_synthesis TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(company_id)
);
```

#### network

```sql
CREATE TABLE network (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    purpose TEXT,
    ultimate_end_goal TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'training', 'converged', 'archived')),
    mode VARCHAR(10) NOT NULL DEFAULT 'learn'
        CHECK (mode IN ('learn', 'command')),
    readiness_pct FLOAT DEFAULT 0.0,
    current_loss FLOAT,
    total_steps INTEGER DEFAULT 0,
    network_config JSONB DEFAULT '{}',
    how_it_works TEXT,
    reference_files JSONB DEFAULT '[]',
    learning_config JSONB DEFAULT '{}',
    command_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

`network_config` JSONB structure:
```json
{
    "learning_rate": 0.01,
    "research_depth": 3,
    "components_per_step": 5,
    "full_regen_frequency": 10,
    "weight_to_content_mapping": true,
    "weight_content_ratio": 1.0,
    "evaluation_criteria": ["accuracy", "depth", "actionability", "creativity"],
    "priority_multipliers": {
        "critical": 2.0,
        "high": 1.5,
        "medium": 1.0,
        "low": 0.5
    },
    "model_config": {
        "research_model": "moonshotai/kimi-k2",
        "evaluator_model": "moonshotai/kimi-k2",
        "generator_model": "moonshotai/kimi-k2"
    }
}
```

#### component

```sql
CREATE TABLE component (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_id UUID NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(10) NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    weight FLOAT NOT NULL DEFAULT 0.5,
    initial_weight FLOAT NOT NULL DEFAULT 0.5,
    score_pct FLOAT DEFAULT 0.0,
    status VARCHAR(15) NOT NULL DEFAULT 'developing'
        CHECK (status IN ('strong', 'developing', 'weak')),
    sort_order INTEGER NOT NULL DEFAULT 0,
    sub_components JSONB DEFAULT '[]',
    research_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_component_network ON component(network_id);
CREATE INDEX idx_component_sort ON component(network_id, sort_order);
```

#### training_run

```sql
CREATE TABLE training_run (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_id UUID NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(10) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'complete', 'failed', 'paused')),
    total_steps INTEGER DEFAULT 0,
    loss_start FLOAT,
    loss_end FLOAT,
    loss_history JSONB DEFAULT '[]',
    improvements JSONB DEFAULT '{}',
    config_snapshot JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER
);

CREATE INDEX idx_training_run_network ON training_run(network_id);
```

#### evaluation

```sql
CREATE TABLE evaluation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    training_run_id UUID NOT NULL REFERENCES training_run(id) ON DELETE CASCADE,
    component_id UUID NOT NULL REFERENCES component(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    nudge_direction VARCHAR(8) NOT NULL
        CHECK (nudge_direction IN ('baseline', 'up', 'down')),
    nudge_delta FLOAT,
    score_before FLOAT,
    score_after FLOAT,
    evaluator_notes TEXT,
    research_performed JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_evaluation_run ON evaluation(training_run_id);
CREATE INDEX idx_evaluation_component ON evaluation(component_id);
```

#### output_template

```sql
CREATE TABLE output_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_id UUID REFERENCES network(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    output_type VARCHAR(30) NOT NULL DEFAULT 'skill_md'
        CHECK (output_type IN (
            'skill_md', 'agent_config', 'python_script',
            'process_doc', 'architecture_diagram',
            'email_outreach', 'ad_copy', 'custom'
        )),
    master_rule TEXT,
    prompt_template TEXT,
    format_rules JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### generated_output

```sql
CREATE TABLE generated_output (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_id UUID NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    template_id UUID REFERENCES output_template(id) ON DELETE SET NULL,
    version INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    weights_snapshot JSONB DEFAULT '{}',
    quality_score FLOAT,
    human_score FLOAT,
    pushed_to VARCHAR(500),
    pushed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_generated_output_network ON generated_output(network_id);
```

#### feedback

```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_id UUID NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    output_id UUID REFERENCES generated_output(id) ON DELETE SET NULL,
    source VARCHAR(15) NOT NULL DEFAULT 'manual'
        CHECK (source IN ('manual', 'webhook', 'metric', 'agent_report')),
    feedback_type VARCHAR(10) NOT NULL DEFAULT 'neutral'
        CHECK (feedback_type IN ('positive', 'negative', 'neutral', 'metric')),
    metric_name VARCHAR(255),
    metric_value FLOAT,
    notes TEXT,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_network ON feedback(network_id);
```

#### activity_log

```sql
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_id UUID NOT NULL REFERENCES network(id) ON DELETE CASCADE,
    event_type VARCHAR(20) NOT NULL
        CHECK (event_type IN (
            'training_step', 'research', 'evaluation',
            'output_generated', 'feedback_received',
            'weight_adjusted', 'error'
        )),
    message TEXT NOT NULL,
    detail JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activity_network ON activity_log(network_id);
CREATE INDEX idx_activity_created ON activity_log(network_id, created_at DESC);
```

---

## Core Engine Design

### Micrograd Value Class

Adapted from Karpathy's micrograd. Used as a weight container with gradient storage. Since our loss function is non-differentiable (LLM-as-judge), we compute gradients via finite differences and write them directly to `.grad`.

```python
# engine/value.py
class Value:
    """Scalar value with gradient storage. Adapted from Karpathy's micrograd."""
    
    def __init__(self, data: float, label: str = ''):
        self.data = data
        self.grad = 0.0
        self.label = label
    
    def __repr__(self):
        return f"Value(data={self.data:.4f}, grad={self.grad:.4f}, label='{self.label}')"
```

We keep micrograd's `Value` for weight storage, gradient accumulation, and the SGD update loop. The full autograd (`_backward`, `_prev`, topological sort) is not used because our loss is a black-box LLM score — there's no computational graph to differentiate through. The finite-difference approach is mathematically equivalent to numerical gradient estimation, which is a standard technique when analytic gradients are unavailable.

### SGD Optimizer

```python
# engine/optimizer.py
class SGD:
    """Stochastic Gradient Descent for Value parameters."""
    
    def __init__(self, parameters: list[Value], lr: float = 0.01):
        self.parameters = parameters
        self.lr = lr
    
    def step(self):
        for p in self.parameters:
            p.data -= self.lr * p.grad
    
    def zero_grad(self):
        for p in self.parameters:
            p.grad = 0.0
```

### Optimised Training Loop

The training engine uses the cost-optimised approach: **generate once, evaluate-only nudging, batch scoring, round-robin component selection.**

```python
# services/training_engine.py (pseudocode for design clarity)

class TrainingEngine:
    def __init__(self, network, components, evaluator, generator, config):
        self.network = network
        self.components = components
        self.evaluator = evaluator
        self.generator = generator
        
        # Each component's weight becomes a micrograd Value
        self.weights = {
            comp.id: Value(comp.weight, label=comp.name)
            for comp in components
        }
        
        self.optimizer = SGD(
            list(self.weights.values()),
            lr=config.learning_rate
        )
        
        self.components_per_step = config.components_per_step  # default 5
        self.full_regen_frequency = config.full_regen_frequency  # default 10
        self.nudge_delta = config.learning_rate  # h for finite differences
        self.step_index = 0  # tracks round-robin position
    
    async def training_step(self, step_number: int) -> dict:
        """One optimised training step. Returns step metrics."""
        
        # 1. Select components for this step (round-robin)
        selected = self.select_components()
        
        # 2. Generate output (or reuse cached if not a full-regen step)
        if step_number % self.full_regen_frequency == 0:
            output = await self.generator.generate(self.weights_dict())
            self.cached_output = output  # cache for evaluate-only nudges
        else:
            output = self.cached_output
        
        # 3. Batch-evaluate baseline scores for selected components
        baseline_scores = await self.evaluator.batch_score(
            output, selected, self.weights_dict()
        )
        baseline_loss = self.compute_loss(baseline_scores)
        
        # 4. For each selected component, nudge and re-evaluate
        self.optimizer.zero_grad()
        
        for comp in selected:
            weight = self.weights[comp.id]
            original = weight.data
            
            # Nudge UP — re-evaluate with adjusted weight emphasis
            weight.data = original + self.nudge_delta
            scores_up = await self.evaluator.batch_score(
                output, [comp], self.weights_dict()
            )
            loss_up = self.compute_component_loss(comp, scores_up)
            
            # Nudge DOWN
            weight.data = original - self.nudge_delta
            scores_down = await self.evaluator.batch_score(
                output, [comp], self.weights_dict()
            )
            loss_down = self.compute_component_loss(comp, scores_down)
            
            # Restore and set gradient
            weight.data = original
            weight.grad = (loss_up - loss_down) / (2 * self.nudge_delta)
        
        # 5. SGD update
        self.optimizer.step()
        
        # 6. Clamp weights to [0.0, 1.0]
        for w in self.weights.values():
            w.data = max(0.0, min(1.0, w.data))
        
        # 7. Compute total loss
        total_loss = self.compute_loss(baseline_scores)
        
        return {
            "step": step_number,
            "loss": total_loss,
            "components_trained": [c.name for c in selected],
            "weight_updates": {
                c.name: {"before": prev, "after": self.weights[c.id].data}
                for c, prev in zip(selected, [...])
            }
        }
    
    def select_components(self) -> list:
        """Round-robin selection of N components per step."""
        n = self.components_per_step
        start = self.step_index % len(self.components)
        selected = []
        for i in range(n):
            idx = (start + i) % len(self.components)
            selected.append(self.components[idx])
        self.step_index += n
        return selected
    
    def compute_loss(self, scores: dict) -> float:
        """Weighted MSE loss across all scored components."""
        priority_map = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5}
        total = 0.0
        for comp in self.components:
            if comp.id in scores:
                score = scores[comp.id]
                priority_weight = priority_map.get(comp.priority, 1.0)
                total += priority_weight * (1.0 - score) ** 2
        return total
    
    def weights_dict(self) -> dict:
        """Current weights as {component_id: float}."""
        return {cid: v.data for cid, v in self.weights.items()}
```

### API Call Budget Per Step

| Action | Calls | Notes |
|--------|-------|-------|
| Generate output | 0 or 1 | Only on full-regen steps (every 10th) |
| Baseline batch eval | 1 | All selected components scored in one call |
| Nudge-up eval | 1 per selected component | 5 calls for 5 components |
| Nudge-down eval | 1 per selected component | 5 calls for 5 components |
| **Total per step** | **11-12** | |
| **50-step run** | **~550-600** | vs 5,700 naive |

---

## Research Agent Pipeline

### Component Auto-Population Flow

```
1. User enters Ultimate End Goal + title + purpose
2. Backend derives 3-5 search queries from the goal
   → Kimi call: "Generate 3-5 search queries to research: {goal}"
3. For each query:
   a. Brave Search API → top 5 results (title, url, description, extra_snippets)
   b. Fetch top 3 URLs with httpx
   c. Extract content with trafilatura
4. Feed all extracted content + goal to Kimi:
   "Given this research and the goal '{goal}', decompose into 15-40 weighted
    components. For each: name, description, priority, initial_weight, rationale,
    sub_components (if applicable). Return as JSON."
5. Parse response → create Component rows in DB
6. Return components to frontend for review/editing
```

### Research During Training

When `research_depth > 0` in config, the evaluator can perform web research per component during evaluation steps:

```
For each component being evaluated:
1. Brave Search: "{component.name} best practices {network.purpose}"
2. Fetch top N URLs (N = research_depth)
3. Extract content
4. Include in evaluator prompt as reference context
5. Store findings in component.research_notes
```

---

## Evaluator Design

### Batch Scoring

The evaluator scores multiple components in a single LLM call, returning structured JSON.

```python
# services/evaluator.py (interface design)

class Evaluator:
    async def batch_score(
        self,
        output: str,
        components: list[Component],
        weights: dict[UUID, float]
    ) -> dict[UUID, float]:
        """
        Score the output on each component. Returns {component_id: score}.
        Score is 0.0 to 1.0.
        """
        prompt = f"""You are an expert evaluator. Score the following output on each
component listed below. Each score should be 0.0 (completely absent/wrong)
to 1.0 (perfect execution).

The current weight emphasis for each component is shown. Higher-weighted
components should have proportionally more depth and coverage in the output.

OUTPUT TO EVALUATE:
{output}

COMPONENTS TO SCORE:
{self._format_components(components, weights)}

Return ONLY a JSON object mapping component names to scores:
{{"component_name": score, ...}}
"""
        response = await self.llm.chat(prompt)
        return self._parse_scores(response, components)
```

### Nudge Evaluation

For nudge testing, the evaluator re-scores with an adjusted weight instruction — telling the judge "this component should now have X% emphasis" and asking if the output meets that level.

---

## Generator Design

### Output Generation from Weights

```python
# services/generator.py (interface design)

class Generator:
    async def generate(self, weights: dict, network: Network) -> str:
        """Generate a skill.md using current trained weights."""
        
        # Build weight-proportional instruction
        component_instructions = []
        for comp in network.components:
            w = weights[comp.id]
            emphasis = "CRITICAL" if w > 0.8 else "HIGH" if w > 0.6 else "MODERATE" if w > 0.4 else "LIGHT"
            component_instructions.append(
                f"- {comp.name} (weight: {w:.2f}, emphasis: {emphasis}): {comp.description}"
            )
        
        prompt = f"""Generate a comprehensive skill.md file for the following purpose:

GOAL: {network.ultimate_end_goal}

The skill should cover these components with depth proportional to their weight:

{chr(10).join(component_instructions)}

{network.how_it_works or ''}

Output the complete skill.md content, ready to use.
"""
        return await self.llm.chat(prompt)
```

---

## Chat Service Design

### Dual-Mode Chat

The chat service handles both learn and command mode conversations. It has access to the network's current state, training history, and config.

```python
# services/chat_service.py (interface design)

class ChatService:
    async def handle_message(
        self,
        network_id: UUID,
        mode: str,  # "learn" or "command"
        message: str,
        db: AsyncSession
    ) -> ChatResponse:
        """
        Process a chat message. Can read/modify network config,
        answer questions about training state, trigger actions.
        """
        # Build context from current network state
        network = await self.get_network_with_state(network_id, db)
        
        system_prompt = self._build_system_prompt(network, mode)
        
        # Detect intent: query, config_change, action_trigger
        response = await self.llm.chat(
            system=system_prompt,
            user=message,
            tools=self._get_tools(mode)  # tools for config changes, etc.
        )
        
        # If config was changed, persist to DB
        if response.config_changes:
            await self.apply_config_changes(network, response.config_changes, db)
        
        return ChatResponse(
            message=response.text,
            config_changed=bool(response.config_changes),
            action_triggered=response.action
        )
```

Chat tools available:
- `update_learning_config(field, value)` — change learning rate, research depth, etc.
- `reorder_components(component_ids)` — change component priority order
- `get_training_summary()` — return current loss, step count, component status
- `get_weight_report()` — return all components with weights and scores
- `trigger_training(steps)` — start/resume training for N steps

---

## Integration Layer

### OpenRouter Client

```python
# integrations/openrouter.py

from openai import AsyncOpenAI

class OpenRouterClient:
    def __init__(self, api_key: str, default_model: str = "moonshotai/kimi-k2"):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.default_model = default_model
    
    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None
    ) -> str:
        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **({"response_format": response_format} if response_format else {})
        )
        return response.choices[0].message.content
    
    async def chat_stream(self, messages, model=None, **kwargs):
        """Streaming variant for chat interface."""
        stream = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            stream=True,
            **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

### Brave Search Client

```python
# integrations/brave_search.py

import httpx
import trafilatura

class BraveSearchClient:
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def search(self, query: str, count: int = 5) -> list[dict]:
        """Search Brave and return results with title, url, description."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.BASE_URL,
                headers={
                    "X-Subscription-Token": self.api_key,
                    "Accept": "application/json"
                },
                params={"q": query, "count": count, "extra_snippets": "true"}
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("web", {}).get("results", [])
    
    async def search_and_extract(self, query: str, max_pages: int = 3) -> list[dict]:
        """Search, then fetch and extract content from top results."""
        results = await self.search(query)
        extracted = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for result in results[:max_pages]:
                try:
                    page = await client.get(result["url"])
                    content = trafilatura.extract(page.text) or ""
                    extracted.append({
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result.get("description", ""),
                        "content": content[:5000]  # cap to avoid token explosion
                    })
                except Exception:
                    extracted.append({
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result.get("description", ""),
                        "content": ""
                    })
        return extracted
```

---

## API Endpoints

### REST API

```
# Companies
GET    /api/companies                          → list companies
POST   /api/companies                          → create company
GET    /api/companies/:id                      → get company
PUT    /api/companies/:id                      → update company

# Networks
GET    /api/networks                           → list networks (filter by company_id)
POST   /api/networks                           → create network (basic fields)
GET    /api/networks/:id                       → get network with components
PUT    /api/networks/:id                       → update network
POST   /api/networks/:id/generate-plan         → AI auto-populate components
POST   /api/networks/:id/train/start           → start training run
POST   /api/networks/:id/train/pause           → pause training
POST   /api/networks/:id/train/resume          → resume training
GET    /api/networks/:id/training-runs         → list training runs
GET    /api/networks/:id/loss-history          → loss data for charting

# Components
GET    /api/networks/:id/components            → list components
PUT    /api/networks/:id/components/:cid       → update component
POST   /api/networks/:id/components/reorder    → reorder components (body: {ids: [...]})
POST   /api/networks/:id/components            → add component manually

# Outputs
GET    /api/networks/:id/outputs               → list generated outputs
POST   /api/networks/:id/outputs/generate      → generate output (body: {template_id})
GET    /api/networks/:id/outputs/:oid/download → download as file

# Output Templates
GET    /api/output-templates                   → list templates
POST   /api/output-templates                   → create template
PUT    /api/output-templates/:id               → update template

# Feedback
POST   /api/networks/:id/feedback              → submit feedback
GET    /api/networks/:id/feedback              → list feedback

# Activity
GET    /api/networks/:id/activity              → paginated activity log

# Chat
POST   /api/networks/:id/chat                 → send message (body: {mode, message})

# Config
GET    /api/networks/:id/config/:mode          → get config (learn | command)
PUT    /api/networks/:id/config/:mode          → update config
```

### WebSocket

```
WS /ws/networks/:id/activity

Events (server → client):
  training.step       { step, component, score, loss }
  training.research   { topic, source, findings_summary }
  training.weight     { component, old_weight, new_weight, gradient }
  training.complete   { run_id, final_loss, total_steps }
  training.error      { message, detail }
  output.generated    { output_id, template_type, quality_score }
  feedback.received   { feedback_id, source, type }
```

---

## Frontend Pages

### 1. Network Creator (`/networks/new`)

- Title, purpose, ultimate end goal (text fields)
- "Research & Generate Components" button → calls `/generate-plan`
- Loading state with activity feed showing research progress
- Component review table: name, description, priority (dropdown), initial weight (slider), sort order (drag)
- Add/remove component buttons
- Reference file upload (stored as base64 or URLs in `reference_files` JSONB)
- "Create Network" button → POST `/networks` + components

### 2. Training Lab (`/networks/:id/training`)

- Top bar: network title, mode toggle (Learn/Command), status badge
- Left panel:
  - Loss counter (current loss value, large)
  - Step counter
  - Readiness bar (0-100%)
  - Component summary: X strong / Y developing / Z weak
  - Action buttons: Start Training, Pause, Resume
- Centre panel:
  - Component table (placeholder for neural viz): name, weight bar, score bar, status badge, trend arrow
  - Expandable rows for sub-components and research notes
- Right panel:
  - Tabs: Activity | Chat
  - Activity: timestamped event log (WebSocket-driven)
  - Chat: input + message history (learn mode context)
- Bottom strip: loss curve chart (Recharts line chart, updates via WebSocket)

### 3. Learning Config (`/networks/:id/config/learn`)

- How It Works: large textarea
- Training Objective: text field
- Research Depth: number input (1-5)
- Weight-to-Content Mapping: toggle + ratio slider
- Learning Rate: number input
- Components Per Step: number input
- Full Regen Frequency: number input
- Priority Multipliers: four number inputs (critical/high/medium/low)
- Evaluation Criteria: tag input (add/remove criteria)
- Component Hierarchy: drag-to-reorder list
- Model Config: three dropdowns (research/evaluator/generator model)
- Chat panel on right side

### 4. Command Mode (`/networks/:id/command`)

- Output template selector (dropdown or cards)
- "Generate Output" button with progress indicator
- Generated output display (rendered markdown + raw toggle)
- Download button (.md file)
- Quality score display (AI score + optional human score input)
- Output history list (previous generations with scores)
- Chat panel on right side (command mode context)

### 5. Network Manager (`/networks`)

- Card grid: one card per network
  - Title, company, status badge, readiness %, current loss
  - Last activity timestamp
  - Quick actions: Open Lab, Start Training, Archive
- Filters: by company, status, readiness range
- "New Network" button

### Layout Shell

- Left sidebar (collapsible):
  - Logo/title
  - Navigation: Networks, Companies, Templates
  - Active network quick-switch
- Top bar:
  - Current page title
  - Network selector dropdown (when in a network context)
  - Mode toggle (Learn/Command)

### Design System

- Dark theme: backgrounds `#0a0a0a` to `#1a1a1a`, panels `#1e1e1e` to `#2a2a2a`
- Primary accent: `#00ff88` (green) for active/positive
- Warning: `#ffaa00` (amber)
- Error: `#ff4444` (red)
- Text: `#ffffff` / `#a0a0a0` / `#666666` hierarchy
- Component status colours: strong=green, developing=amber, weak=red
- Monospace font for scores and weights
- Subtle border: `#333333`
- Cards: rounded corners, subtle shadow, hover state

---

## Proposed Changes Summary

Since this is greenfield, everything is new. The key files and what they contain:

| File | Purpose | NEW |
|------|---------|-----|
| `backend/app/main.py` | FastAPI app, CORS, router registration, lifespan | NEW |
| `backend/app/config.py` | Pydantic Settings: DB URL, OpenRouter key, Brave key, defaults | NEW |
| `backend/app/database.py` | async SQLAlchemy engine, session factory, Base | NEW |
| `backend/app/models/*.py` | 9 ORM models matching schema above | NEW |
| `backend/app/schemas/*.py` | Pydantic request/response schemas for each entity | NEW |
| `backend/app/routers/*.py` | 8 route files matching API design | NEW |
| `backend/app/services/training_engine.py` | Core training loop with micrograd | NEW |
| `backend/app/services/evaluator.py` | LLM-as-judge batch scoring | NEW |
| `backend/app/services/generator.py` | Skill.md generation from weights | NEW |
| `backend/app/services/research_agent.py` | Brave + content extraction + LLM synthesis | NEW |
| `backend/app/services/chat_service.py` | Dual-mode chat with tool use | NEW |
| `backend/app/engine/value.py` | Micrograd Value class | NEW |
| `backend/app/engine/optimizer.py` | SGD optimizer | NEW |
| `backend/app/integrations/openrouter.py` | OpenAI SDK wrapper for OpenRouter | NEW |
| `backend/app/integrations/brave_search.py` | Brave API + trafilatura | NEW |
| `backend/alembic/versions/001_initial.py` | Initial migration with all tables | NEW |
| `frontend/src/pages/*.tsx` | 5 page components | NEW |
| `frontend/src/components/*.tsx` | 6 shared components | NEW |
| `frontend/src/hooks/*.ts` | WebSocket + API hooks | NEW |
| `frontend/src/stores/*.ts` | Zustand stores | NEW |
| `frontend/src/api/client.ts` | Typed API client | NEW |
| `docker-compose.yml` | Local dev: Postgres + backend + frontend | NEW |
| `railway.toml` | Railway deployment config | NEW |

---

## Wiring Requirements (Failure Prevention Matrix)

| Check | Status |
|-------|--------|
| New route files → registered in `main.py` via `include_router` | Required: 8 routers |
| New tables → Alembic migration | Required: 9 tables in initial migration |
| Services → instantiated in `main.py` lifespan | Required: OpenRouterClient, BraveSearchClient, TrainingEngine |
| WebSocket → endpoint registered in router | Required: `/ws/networks/:id/activity` |
| CORS → configured in `main.py` | Required: allow frontend origin |
| Environment variables → documented in `.env.example` | Required: DATABASE_URL, OPENROUTER_API_KEY, BRAVE_API_KEY |
| Frontend → API base URL configurable via env | Required: VITE_API_URL |
| Railway → Postgres plugin + env vars | Required: DATABASE_URL auto-injected |

---

## Observable Truths

1. **Network creation produces components**
   - Verification: `POST /api/networks` + `POST /api/networks/:id/generate-plan`, then `GET /api/networks/:id/components`
   - Expected: 15-40 components with names, descriptions, priorities, weights

2. **Training reduces loss**
   - Verification: `POST /api/networks/:id/train/start`, wait for 10+ steps, `GET /api/networks/:id/loss-history`
   - Expected: loss_history array shows general downward trend

3. **Weights change during training**
   - Verification: Record component weights before training, compare after 10 steps
   - Expected: At least some weights differ from initial values

4. **Output generation uses trained weights**
   - Verification: Generate output, inspect `weights_snapshot` in `generated_output` row
   - Expected: `weights_snapshot` matches current component weights, output content reflects weight emphasis

5. **WebSocket delivers real-time events**
   - Verification: Connect to `/ws/networks/:id/activity`, start training, observe events
   - Expected: `training.step` events arrive within seconds of each step completing

6. **Chat can read and modify config**
   - Verification: Send "change the learning rate to 0.05" via chat, then `GET /api/networks/:id/config/learn`
   - Expected: `learning_rate` field is 0.05

7. **Database contains all training data**
   - Verification: `SELECT COUNT(*) FROM evaluation WHERE training_run_id = :id`
   - Expected: Row count matches (steps × components_per_step × 3 directions)

---

## Falsifiable Assumptions

| Assumption | Verification | Result |
|------------|-------------|--------|
| Kimi 2.5 is available on OpenRouter as `moonshotai/kimi-k2` | Check OpenRouter model list | UNVERIFIED — confirm exact model ID before implementation |
| Kimi 2.5 can return structured JSON reliably for batch scoring | Test with a sample prompt | UNVERIFIED — may need `response_format: {"type": "json_object"}` or parsing fallbacks |
| Brave Search API returns useful results for AI skill topics | Test with sample queries | UNVERIFIED — domain-specific, may need query engineering |
| trafilatura can extract content from most result URLs | Test with sample URLs | UNVERIFIED — some sites block scrapers |
| Evaluate-only nudging produces meaningful gradient signal | Run training loop, compare loss curves with periodic full-regen checkpoints | UNVERIFIED — core hypothesis, validated by full-regen checkpoints every 10 steps |
| 11-12 API calls per step is fast enough for interactive training | Estimate: ~2-3 sec per LLM call × 12 = 24-36 sec per step | ACCEPTABLE — but should show progress in real-time via WebSocket |
| Round-robin selection doesn't miss important components | Compare to full-sweep training on same network | UNVERIFIED — mitigated by cycling through all components over 6 steps |
| PostgreSQL JSONB is sufficient for loss_history (could grow to 1000+ entries) | Estimate: 1000 × {step: int, loss: float} ≈ 30KB | VERIFIED — well within JSONB limits |
| OpenRouter rate limits (20 req/min free, more with credits) support training | 12 calls/step, ~2 steps/min = 24 req/min | RISK — exceeds free tier. Need paid credits. Confirm user has credits. |

---

## System Invariants

1. **Every component belongs to exactly one network.** No shared components across networks.
2. **Weights are always in [0.0, 1.0] range.** Clamped after every SGD step.
3. **A network can only have one active training run at a time.** Starting a new run pauses any running one.
4. **Training runs are append-only.** Loss history and evaluations are never deleted or modified.
5. **Activity log is append-only and ordered by created_at.** No updates, no deletes.
6. **Config changes during training take effect on the next step,** not retroactively.
7. **Generated outputs are immutable.** Each generation creates a new row with a version number.

---

## Initial Conditions Audit

This is a greenfield project — no pre-existing initial conditions to trace. The design decisions made here become the initial conditions for future work:

| Decision | Scope | Future impact |
|----------|-------|---------------|
| Single-user, no auth | Phase 1 only | Phase 2+ needs auth middleware, user model, session management |
| Company as top-level entity | Data model | Supports multi-tenancy without schema changes |
| JSONB for flexible fields | All config/history fields | Queryable but not type-safe at DB level — may need to extract to columns if frequently queried |
| Asyncio for training (no task queue) | Backend | Long training runs block the event loop if not properly structured — use `asyncio.create_task()` |
| OpenRouter as sole LLM provider | All AI calls | If OpenRouter goes down, everything stops — no fallback provider |
| Evaluate-only nudging as default | Training engine | If hypothesis is wrong, need to refactor to full regeneration per nudge |
