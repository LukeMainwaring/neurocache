# Demo Workflows

Prompts and workflows that showcase what Neurocache can do that general-purpose chatbots (ChatGPT, Claude) cannot. Organized by uniqueness and impressiveness.

---

## The Best Single Demo

> "I've been thinking about how the Stoic concept of 'memento mori' connects to the Buddhist idea of impermanence. What have I written about either of these ideas, and how do modern psychologists frame this overlap?"

This one prompt triggers the full system. The agent calls `search_knowledge_base` for your notes on Stoicism and Buddhism, then `web_search` for current psychology research, then synthesizes both into a response with inline citations.

**What to watch for:**
- Tool calls appear with live spinner → green checkmark when complete
- Inline `[1]`, `[2]` citations appear in the response as it streams
- Hover a citation → tooltip shows source file path, content type, and match percentage
- Click a citation → modal with full source content and an Obsidian deep link
- "View Sources" button on the user message → all RAG sources with similarity scores
- "View Web Sources" button → web results with titles and URLs

---

## Things No Other Chatbot Can Do

### Knowledge Base Retrieval with Inline Citations

> "What have I written about decision-making frameworks?"

The agent searches your Obsidian vault semantically — finding relevant notes even when you never used that exact phrase. The response cites your own notes with numbered references.

**What to watch for:**
- Citations link directly to the source note. Click one and it opens in Obsidian via `obsidian://` deep link.
- The RAG Sources dialog shows each source's content type (Personal Note, Book Note, Article, etc.), similarity percentage, section header, and a content preview.
- Personal notes rank above book sources thanks to content-type boosting (4% boost for your own writing, 2% for your book notes).

### Conversation-to-Knowledge Extraction

This is the closed loop that makes Neurocache a growing system: conversations generate knowledge that feeds future conversations.

**How to demo:**
1. Have a substantive conversation — ask the agent to help you think through an idea, analyze a concept, or connect themes across your notes
2. In the sidebar, click the thread's dropdown menu → **Extract Insights**
3. The extraction agent analyzes the conversation and generates a structured Obsidian note
4. Preview the note (with edit/preview toggle), adjust the title if needed
5. Click **Save to Vault** → the note is written to your Obsidian vault's `Neurocache Insights/` folder and immediately indexed for search
6. Start a new chat and ask about the topic — the extracted insights now appear as a cited source

**What to watch for:**
- The generated note is well-structured markdown, not a raw transcript dump
- After saving, the success screen shows the file path and an "Open in Obsidian" link
- If you've already extracted from a conversation, a warning banner appears

### Cross-Domain Connections

> "What connections can you find between my notes on [Topic A] and [Topic B]?"

The agent searches both topics, then reasons about patterns and links you might have missed. This treats your reading and writing history as a network of ideas.

**Variations:**
- *"Look at my book notes and tell me which authors would agree with each other and which would argue"*
- *"What have I written about [topic] and where do my ideas contradict each other?"*
- *"I'm writing an essay about [topic]. What ideas from my notes could I draw on?"*

### MCP Server: Your Knowledge Base as a Tool

Neurocache exposes your knowledge base as MCP tools that any compatible client can use — Claude Desktop, Claude Code, Cursor.

**How to demo (Claude Code):**
1. Configure `.mcp.json` with the Neurocache MCP server
2. Ask Claude Code: *"Search my knowledge base for notes about distributed systems"*
3. Claude calls `search_knowledge_base` and gets your notes with full source attribution
4. Ask: *"Get the full document at Books/Designing Data-Intensive Applications/Notes.md"*
5. Claude calls `get_document` and reads the complete note

**Available tools:** `search_knowledge_base`, `get_document`, `list_documents`, `save_to_knowledge_base`

The `save_to_knowledge_base` tool lets external clients write notes back into your vault — the same extraction loop, but from any MCP-compatible client.

---

## End-to-End Workflows

### PDF Book Pipeline

1. Go to **Settings > Knowledge Base** and click a book's **Upload PDF** button
2. Drop a PDF — the preview shows title, author, and page count
3. Confirm upload — the book analysis agent runs in the background
4. Once indexed, the book's `Notes.md` is scaffolded with:
   - 5-10 AI-generated tags
   - 3-paragraph summary (subject, methodology, audience)
   - Key concepts organized by chapter (4-8 per chapter)
   - Empty sections for your highlights, reflections, and connections
5. Chat about the book: *"What are the main arguments in [book title]?"*

**What to watch for:** The response cites both the raw PDF content (Book Source) and your notes about the book (Book Note), with different content types visible in the citations.

### Personalization

1. Go to **Settings > Personalization** and fill in your occupation, background, and custom instructions
2. Ask: *"Explain [complex topic] in terms I'd understand"*

The agent references your profile context. A software engineer gets code analogies; a teacher gets pedagogical framing. This is injected into the system prompt — not just a memory feature, but a persistent lens on every response.

**Variation:** *"Given what you know about my interests, what should I read next?"* — combines your profile with your knowledge base to give recommendations grounded in what you've already read.

---

## Quick Demos

**"Hi, what do you know about me?"** — The agent references your profile and the scope of your knowledge base. Good opener.

**"What happened in AI news this week?"** — Pure web search. Watch the tool call visualization: spinning indicator, collapsible details showing input/output, green checkmark on completion.

**"What's in my knowledge base about [very specific topic]?"** — Direct retrieval. Shows the View Sources button, similarity scoring, and content type labels.

**Auto-generated titles** — Start a new chat with any substantive message. The sidebar updates with an LLM-generated title after the first exchange.

---

## Hybrid Search (Personal + Web)

These prompts show the agent intelligently combining both tools:

> "I read about spaced repetition in [book] — what's the latest research on optimal review intervals?"

Grounds the response in your book notes, then supplements with current research. The response cites both source types with clear attribution.

> "Based on my notes about [topic], what recent news should I be paying attention to?"

Your knowledge base becomes a lens for filtering what's relevant. The agent retrieves your interests first, then searches the web with that context.
