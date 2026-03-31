# Neurocache Roadmap

A personal "second brain" AI chat application. This roadmap focuses on what matters for a local, experimental app.

**Strategic moat:** Neurocache's value over commercial tools (Claude Desktop, ChatGPT) is depth of integration with YOUR knowledge — your entire vault as always-on context, structured retrieval with provenance, agent tool use against your data, and a portable knowledge API via MCP. Every feature is evaluated against this.

## Next Up: Enhanced Retrieval

Build on RAG foundation for richer knowledge interactions.

### Cross-Reference Discovery

Surface connections across notes during conversation.

- "Related notes" suggestions based on conversation context
- Concept linking across different sources
- Leverage Obsidian's `[[wiki-links]]` for explicit connections

### Advanced Retrieval

- Re-ranking retrieved results
- Query expansion/reformulation

---

## Future Ideas

Ambitious features worth exploring once the core is mature. Ordered roughly by uniqueness and impact.

### Conversation-to-Knowledge Pipeline

After each conversation, extract key facts, decisions, and insights. Propose them as new Obsidian notes or additions to existing notes. The full loop: read → chat → write → read. This creates a genuine growth loop where using the app makes it smarter.

### Temporal Knowledge Tracking

Track how thinking evolves over time. Surface when you first encountered an idea and how your understanding shifted across notes. No commercial tool does this — genuinely unique.

### Knowledge Gap Detection

Analyze the vault for topics referenced frequently but never deeply explored. "You mention 'reinforcement learning' in 8 notes but have no dedicated material on it." Turns passive retrieval into active learning guidance.

### Obsidian Deep Links in Citations

Make inline citations link directly to notes via `obsidian://open?vault=...&file=...`. The vault name is already in config. Small effort, high UX payoff.

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
- This is a learning project. Optimize for understanding patterns, not production robustness.
- Incremental progress: each item should be completable in a reasonable work session.
