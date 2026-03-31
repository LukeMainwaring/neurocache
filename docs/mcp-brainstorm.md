  The Big Five MCP Plays for Neurocache

  1. Expose Neurocache itself as an MCP Server — DONE. FastMCP server mounted on /mcp in the FastAPI app (streamable-http) with stdio support via python -m neurocache.mcp. Three tools: search_knowledge_base, get_document, list_documents. Knowledge base is now queryable from Claude Code, Cursor, Claude Desktop, or any MCP-compatible client.

  2. Web Search Tool — DONE. Added Pydantic AI's built-in WebSearchTool via OpenAIResponsesModel. The agent blends personal knowledge with live web results, with source citations displayed in the frontend.

  3. Note Write-Back to Obsidian — A brain that only reads is half a brain. Let the agent create notes, append to daily notes, and capture conversation insights directly in your vault. Exposed via MCP, this
  means any tool can write to your knowledge base.

  4. User-Configurable MCP Servers — Use Pydantic AI's load_mcp_servers() to let users plug in whatever tools they want (GitHub, Calendar, code execution, etc.). This is effectively a plugin system for free.

  5. Agentic RAG via Tool Use — DONE. RAG is now a tool the agent calls iteratively, reasoning about what to search for and refining queries.

  My suggested build order: #5, #2, and #1 are done. Next up: #3 (note write-back) and #4 (user-configurable MCP servers).
