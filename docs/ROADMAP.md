# Neurocache Roadmap

A personal "second brain" AI chat application. This roadmap focuses on what matters for a local, experimental app.

**Strategic moat:** Neurocache's value over commercial tools (Claude Desktop, ChatGPT) is depth of integration with YOUR knowledge — your entire vault as always-on context, structured retrieval with provenance, agent tool use against your data, and a portable knowledge API via MCP. Every feature is evaluated against this.

## Next Up

### Conversation-to-Knowledge Pipeline

After each conversation, extract key facts, decisions, and insights. Propose them as new Obsidian notes or additions to existing notes. Subsumes note write-back — the agent gains tools to create and append to notes in the vault. The full loop: read → chat → write → read. This creates a genuine growth loop where using the app makes it smarter.

### Temporal Knowledge Tracking + Memory Layer

Track how thinking evolves over time. Surface when you first encountered an idea and how your understanding shifted across notes. No commercial tool does this — genuinely unique. Build a memory layer that extracts and timestamps facts from conversations and notes, enabling queries like "when did I first explore this idea?" and "how has my thinking changed?" Technology choice (Mem0, custom pipeline, or alternatives) to be determined after research.

---

## Future Ideas

Experimental features worth exploring if time permits.

### Cross-Reference Discovery

Parse Obsidian `[[wiki-links]]` during ingestion, store as edges, and retrieve linked notes alongside semantic matches. Combine explicit links with embedding proximity for "related notes." Infrastructure-level improvement to retrieval quality.

### Advanced Retrieval

Re-ranking retrieved results, query expansion/reformulation. Standard IR techniques — useful but not differentiating.

### Knowledge Gap Detection

Analyze the vault for topics referenced frequently but never deeply explored. "You mention 'reinforcement learning' in 8 notes but have no dedicated material on it." Turns passive retrieval into active learning guidance.

---

## Deferred Features

Features documented here to avoid re-adding them prematurely. These make sense for a production app but are unnecessary overhead for local experimentation.

### Web Content Ingestion

URL scraping and web content capture. Can add later if needed.

### Deployment Infrastructure

CI/CD, monitoring, production deployment. Handle when/if the app goes public.


### Model Upgrades & Reasoning

Experiment with reasoning models and tune `ModelSettings` (e.g., `openai_reasoning_effort`) once the core chat and RAG flow is working well. Just a config change — no architectural work needed.

### Multi-Agent Architecture

Specialized agents for different tasks: research agent (deep multi-query search), daily review agent (surfaces unvisited notes), writing assistant (drafts from your notes). Defer unless a specific use case demands it — the single agent covers most cases today.

---

## Notes

- Obsidian is the primary knowledge source. Keep the ingestion pipeline simple.
- This is a learning project approaching portfolio readiness. Optimize for understanding patterns and demonstrable features.
- Incremental progress: each item should be completable in a reasonable work session.
