# Demo Prompts

Prompts and workflows that showcase Neurocache's capabilities. Organized by what's most impressive to show someone — hybrid personal + web intelligence, deep knowledge base retrieval, and things no general-purpose chatbot can do.

---

## The Best Single Demo Prompt

> "I've been thinking about how the Stoic concept of 'memento mori' connects to the Buddhist idea of impermanence. What have I written about either of these ideas, and how do modern psychologists frame this overlap?"

**Why it's great:** Triggers both `search_knowledge_base` (scans personal notes and book notes for Stoicism, Buddhism, impermanence) and `web_search` (finds current psychology research). The agent synthesizes your own thinking with external knowledge, draws cross-domain connections, and cites your sources alongside web results. This is the core "second brain" promise — your ideas enriched with the world's knowledge.

**Tool chain:** `search_knowledge_base("stoic memento mori")` + `search_knowledge_base("buddhist impermanence")` -> `web_search("psychology mortality salience impermanence")` -> synthesized response with View Sources + View Web Sources buttons

---

## Knowledge Base Retrieval (impossible in ChatGPT/Claude)

### "What notes do I have about decision-making frameworks?"

General-purpose chatbots know nothing about your notes. The agent searches your Obsidian vault semantically — finding relevant content even if you never used the exact phrase "decision-making framework." Shows source attribution with similarity scores, file paths, and section headers.

**Tool chain:** `search_knowledge_base("decision-making frameworks")` -> response citing your notes -> View Sources button shows similarity %, file path, content type

### "Summarize the key ideas from the last three books I read"

The agent searches across your book notes (which have higher priority than raw PDF content) and synthesizes themes. If you've written highlights and reflections in your Notes.md files, those surface first thanks to content-type boosting.

**Tool chain:** `search_knowledge_base("book key ideas takeaways")` -> response drawing from Book Notes (2% boost) and Personal Notes (4% boost)

### "What have I written about [specific topic] and where do my ideas contradict each other?"

This is something no tool can do — finding internal contradictions in your own thinking across notes written months apart. The agent retrieves relevant chunks, then reasons about tensions and evolution in your thinking.

**Tool chain:** `search_knowledge_base("[topic]")` -> LLM reasoning across multiple retrieved chunks -> response highlighting contradictions with source citations

---

## Hybrid Personal + Web Search (the "second brain" advantage)

### "I read about spaced repetition in [Book X] — what's the latest research on optimal review intervals?"

Grounds the conversation in what you already know (your book notes), then supplements with current research. Shows the agent intelligently combining both tools.

**Tool chain:** `search_knowledge_base("spaced repetition [Book X]")` -> `web_search("spaced repetition optimal review intervals 2025 research")` -> synthesized response with both source types

### "Based on my notes about [topic], what recent news should I be paying attention to?"

Your personal knowledge base becomes a lens for filtering what's relevant in the world. The agent retrieves your interests/positions first, then searches the web with that context.

**Tool chain:** `search_knowledge_base("[topic]")` -> `web_search("[topic] recent developments")` -> personalized news briefing

### "I've been researching [topic] — compare what I've gathered so far with the current expert consensus"

The agent retrieves your research notes, then fact-checks and extends them against the latest thinking. Shows where you're aligned with experts and where you might want to dig deeper.

**Tool chain:** `search_knowledge_base("[topic] research")` -> `web_search("[topic] expert consensus")` -> comparative analysis

---

## Cross-Domain Connections (what a second brain is for)

### "What connections can you find between my notes on [Topic A] and [Topic B]?"

The power of a second brain is surfacing non-obvious links. The agent searches both topics in your knowledge base and uses LLM reasoning to find patterns you might have missed.

**Tool chain:** `search_knowledge_base("[Topic A]")` + `search_knowledge_base("[Topic B]")` -> LLM synthesis of connections

### "Look at my book notes and tell me which authors would agree with each other and which would argue"

Requires retrieving notes across multiple books and reasoning about intellectual positions. A genuinely novel interaction that treats your reading history as a network of ideas.

**Tool chain:** `search_knowledge_base("book notes key arguments positions")` -> LLM analysis of intellectual alignment/tension

### "I'm writing an essay about [topic]. What ideas from my notes could I draw on?"

Turns your knowledge base into a research assistant. The agent retrieves relevant fragments and organizes them as potential essay material, with citations back to your original notes.

**Tool chain:** `search_knowledge_base("[topic]")` -> organized outline with source attributions

---

## Web Search (real-time intelligence)

### "What happened in AI news this week?"

Simple but shows the agent knows when NOT to search the knowledge base. Current events go straight to web search.

**Tool chain:** `web_search("AI news this week")` -> summary with View Web Sources

### "Explain the latest paper from [researcher/lab] on [topic]"

Shows the agent fetching and synthesizing cutting-edge research. Good for demonstrating web search quality.

**Tool chain:** `web_search("[researcher] [topic] paper 2025")` -> accessible explanation with source links

---

## Personalization in Action

### Setup: Configure your profile first

Go to Settings > Personalization and fill in:
- **Nickname**: What you want to be called
- **Occupation**: Your professional context
- **About You**: Your background, interests, what you're working on
- **Custom Instructions**: Specific behavior preferences

### "Explain [complex topic] in terms I'd understand"

With your occupation and background filled in, the agent tailors its explanation. A software engineer gets analogies from code; a teacher gets pedagogical framing. Same question, different user profiles, completely different answers.

### "Given what you know about my interests, what should I read next?"

The agent combines your profile (About You) with your knowledge base (what you've already read) to make genuinely personalized recommendations — not generic bestseller lists.

**Tool chain:** `search_knowledge_base("books reading interests")` -> LLM reasoning with user profile context -> tailored recommendations

---

## Book Upload Workflow (show the full pipeline)

### Step-by-step demo

1. **Go to Settings > Knowledge Base** and click a book's Upload PDF button
2. **Drop a PDF** — watch the preview extract title, author, and page count
3. **Confirm upload** — observe the background AI analysis kick off
4. **Check the book entry** — once indexed, the Notes.md gets scaffolded with:
   - AI-generated tags (5-10 topical, lowercase, hyphenated)
   - 3-paragraph summary (what, approach, audience)
   - Key concepts organized by chapter
   - Empty sections for your highlights, reflections, and connections
5. **Start chatting** — ask about the book's content and get answers grounded in both the PDF and your notes

> "What are the main arguments in [just-uploaded book]?"

**Why it's great:** Shows the full pipeline from raw PDF to intelligent conversation in minutes. The AI analysis provides immediate structure, and RAG makes the content instantly searchable.

---

## Quick Wins (simple but satisfying)

### "Hi, what do you know about me?"

Shows the personalization working — the agent references your profile, interests, and the scope of your knowledge base. Good opener for a demo.

### "What's in my knowledge base about [very specific topic]?"

Quick, direct retrieval. Shows the View Sources button and similarity scoring in action.

### "Search the web for [anything current]"

Shows web search tool execution in real-time — the spinning indicator, collapsible tool call details, and web source links.

---

## Conversation Thread Features

### Auto-generated titles

Start a new chat with any substantive message. Watch the sidebar update with an LLM-generated title after the first exchange. Shows polish and attention to detail.

### Multi-thread workflows

Open several threads on different topics — one for a research project, one for book discussion, one for current events. Shows that Neurocache maintains separate conversation contexts, each with their own history and source citations.
