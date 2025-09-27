"""FastAPI surface that exposes the Substack MCP actions."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, StreamingResponse

from . import analysis
from .client import SubstackPublicClient
from .models import AuthorProfile, ContentAnalytics, CrawlResult, Note, PostContent, PostSummary


# Intelligent helper functions for dynamic Substack interaction

async def resolve_publication_hint(hint: str) -> str | None:
    """Resolve publication hints to actual handles."""
    hint_lower = hint.lower()

    # Direct handle mapping
    handle_map = {
        "stratechery": "stratechery",
        "ben thompson": "stratechery",
        "platformer": "platformer",
        "casey newton": "platformer",
        "import ai": "importai",
        "importai": "importai",
        "jack clark": "importai",
        "little hakr": "littlehakr",
        "littlehakr": "littlehakr",
        "tech": "stratechery",
        "business": "stratechery",
        "ai": "importai",
        "crypto": "platformer",
        "social media": "platformer"
    }

    for key, value in handle_map.items():
        if key in hint_lower:
            return value

    # If hint looks like a handle, try it directly
    if hint_lower.replace(" ", "").replace("-", "").isalnum():
        return hint_lower.replace(" ", "").replace("-", "")

    return None


async def auto_discover_publications(query: str) -> list[str]:
    """Auto-discover relevant publications based on query content."""
    query_lower = query.lower()
    publications = []

    # Topic-based publication mapping
    if any(term in query_lower for term in ["ai", "artificial intelligence", "machine learning", "gpt", "llm"]):
        publications.extend(["importai", "stratechery"])

    if any(term in query_lower for term in ["tech", "technology", "apple", "google", "microsoft", "meta"]):
        publications.extend(["stratechery", "platformer"])

    if any(term in query_lower for term in ["crypto", "bitcoin", "ethereum", "defi", "web3", "blockchain"]):
        publications.extend(["platformer", "stratechery"])

    if any(term in query_lower for term in ["business", "strategy", "economics", "market"]):
        publications.extend(["stratechery", "platformer"])

    if any(term in query_lower for term in ["social media", "twitter", "facebook", "instagram", "tiktok"]):
        publications.extend(["platformer", "stratechery"])

    if any(term in query_lower for term in ["policy", "regulation", "government", "politics"]):
        publications.extend(["stratechery", "platformer"])

    # Author name detection
    if "ben thompson" in query_lower or "stratechery" in query_lower:
        publications.insert(0, "stratechery")

    if "casey newton" in query_lower or "platformer" in query_lower:
        publications.insert(0, "platformer")

    if "jack clark" in query_lower or "import ai" in query_lower:
        publications.insert(0, "importai")

    # Remove duplicates while preserving order
    return list(dict.fromkeys(publications))


def smart_content_match(query: str, post: PostSummary) -> bool:
    """Intelligent content matching beyond simple string search."""
    query_terms = query.lower().split()
    post_text = f"{post.title} {post.excerpt or ''}".lower()

    # Exact phrase match
    if query.lower() in post_text:
        return True

    # Multiple term match (at least 50% of terms)
    matching_terms = sum(1 for term in query_terms if term in post_text)
    return matching_terms >= max(1, len(query_terms) * 0.5)


async def smart_content_retrieval(target: str, analysis_type: str, client: SubstackPublicClient) -> str:
    """Intelligent content retrieval that handles various target formats."""
    target_lower = target.lower()

    # Handle URLs
    if target.startswith("http"):
        try:
            post = await run_in_threadpool(client.fetch_post, target)
            if analysis_type == "full":
                analytics = await run_in_threadpool(analysis.analyse_post, post, [])
                return f"📰 **{post.summary.title}**\n\n" \
                       f"👤 Author: {post.summary.author}\n" \
                       f"📅 Published: {post.summary.published_at}\n" \
                       f"🔗 URL: {post.summary.url}\n\n" \
                       f"📊 **Analytics:**\n" \
                       f"• Sentiment: {analytics.sentiment.compound:.2f} ({analytics.sentiment_label})\n" \
                       f"• Readability: {analytics.flesch_reading_ease:.1f} (Flesch)\n" \
                       f"• Keywords: {', '.join(analytics.keywords[:5])}\n\n" \
                       f"📄 **Content:**\n{post.text}"
            else:
                return f"📰 **{post.summary.title}**\n\n{post.text[:1000]}..."
        except Exception as e:
            return f"❌ Error fetching URL: {str(e)}"

    # Handle publication names/handles
    handle = await resolve_publication_hint(target)
    if not handle:
        # Try direct as handle
        handle = target.replace(" ", "").lower()

    try:
        if analysis_type == "profile":
            profile = await run_in_threadpool(client.fetch_author_profile, handle)
            if profile:
                return f"👤 **{profile.display_name or handle}**\n\n" \
                       f"📝 Bio: {profile.bio or 'No bio available'}\n" \
                       f"📍 Location: {profile.location or 'Not specified'}\n" \
                       f"👥 Followers: {profile.followers or 'Unknown'}\n" \
                       f"🔗 Publication: {profile.publication.title if profile.publication else handle}"
            else:
                return f"❌ Could not find author profile for '{target}'"

        elif analysis_type in ["summary", "full"]:
            posts = await run_in_threadpool(client.fetch_feed, handle, 5)
            if posts:
                result = f"📚 **Recent posts from {handle}:**\n\n"
                for i, post in enumerate(posts, 1):
                    excerpt = post.excerpt or "No preview available"
                    result += f"{i}. **{post.title}**\n"
                    result += f"   📅 {post.published_at.strftime('%Y-%m-%d') if post.published_at else 'Unknown'}\n"
                    result += f"   {excerpt[:150]}{'...' if len(excerpt) > 150 else ''}\n"
                    result += f"   🔗 {post.url}\n\n"
                return result
            else:
                return f"❌ No posts found for '{target}'"

    except Exception as e:
        return f"❌ Error retrieving content: {str(e)}"

    return f"❌ Could not resolve target '{target}'. Try a URL or known publication name."


async def discover_publications_by_topic(topic: str, client: SubstackPublicClient) -> str:
    """Discover publications by topic with recommendations."""
    topic_lower = topic.lower()

    recommendations = {
        "tech": [
            ("stratechery", "Ben Thompson's analysis of tech strategy and business models"),
            ("platformer", "Casey Newton on social media, AI, and tech policy"),
            ("importai", "Jack Clark's weekly AI research and policy updates")
        ],
        "ai": [
            ("importai", "Comprehensive AI research, policy, and industry analysis"),
            ("stratechery", "Strategic analysis of AI's business impact"),
            ("platformer", "AI policy, ethics, and social implications")
        ],
        "crypto": [
            ("platformer", "Crypto regulation, policy, and industry developments"),
            ("stratechery", "Business strategy perspectives on crypto and Web3")
        ],
        "business": [
            ("stratechery", "Deep dives into business strategy and tech economics"),
            ("platformer", "Creator economy and social media business models")
        ],
        "finance": [
            ("stratechery", "Financial analysis of tech companies and markets"),
            ("platformer", "Fintech and creator monetization trends")
        ]
    }

    # Find matching recommendations
    matches = []
    for key, pubs in recommendations.items():
        if key in topic_lower or any(term in topic_lower for term in key.split()):
            matches.extend(pubs)

    if not matches:
        # Default popular publications
        matches = [
            ("stratechery", "Premier tech business strategy analysis"),
            ("platformer", "Social media, AI, and tech policy coverage"),
            ("importai", "Cutting-edge AI research and developments")
        ]

    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for pub, desc in matches:
        if pub not in seen:
            unique_matches.append((pub, desc))
            seen.add(pub)

    result = f"🔍 **Publications for '{topic}':**\n\n"

    for i, (handle, description) in enumerate(unique_matches[:5], 1):
        try:
            # Try to get recent post as preview
            posts = await run_in_threadpool(client.fetch_feed, handle, 2)
            recent_post = posts[0] if posts else None

            result += f"{i}. **{handle}**\n"
            result += f"   📝 {description}\n"
            if recent_post:
                result += f"   📰 Latest: {recent_post.title}\n"
                result += f"   📅 {recent_post.published_at.strftime('%Y-%m-%d') if recent_post.published_at else 'Recent'}\n"
            result += f"   🔗 https://{handle}.substack.com\n\n"
        except Exception:
            result += f"{i}. **{handle}**\n   📝 {description}\n   🔗 https://{handle}.substack.com\n\n"

    result += f"💡 Try searching within these publications using: search_substack"
    return result


async def analyze_content_trends(focus: str, depth: str, client: SubstackPublicClient) -> str:
    """Analyze content trends and patterns."""
    focus_lower = focus.lower()

    # Determine what to analyze
    handle = await resolve_publication_hint(focus)

    if handle:
        try:
            # Publication-specific analysis
            post_limit = 20 if depth == "deep" else 10
            posts = await run_in_threadpool(client.fetch_feed, handle, post_limit)

            if not posts:
                return f"❌ No posts found for {handle}"

            result = f"📊 **Content Analysis: {handle}**\n\n"

            # Publishing frequency
            if len(posts) > 1 and posts[0].published_at and posts[-1].published_at:
                time_span = (posts[0].published_at - posts[-1].published_at).days
                frequency = len(posts) / max(time_span, 1) * 7  # Posts per week
                result += f"📅 **Publishing Pattern:**\n"
                result += f"• Frequency: ~{frequency:.1f} posts/week\n"
                result += f"• Latest: {posts[0].published_at.strftime('%Y-%m-%d')}\n"
                result += f"• Analyzed: {len(posts)} posts over {time_span} days\n\n"

            # Content themes
            all_titles = " ".join(post.title.lower() for post in posts)
            common_words = {}
            for word in all_titles.split():
                if len(word) > 4:  # Skip short words
                    common_words[word] = common_words.get(word, 0) + 1

            top_themes = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:8]

            result += f"🏷️ **Common Themes:**\n"
            for word, count in top_themes:
                result += f"• {word}: {count} mentions\n"

            result += f"\n📰 **Recent Posts:**\n"
            for i, post in enumerate(posts[:5], 1):
                result += f"{i}. {post.title}\n"
                result += f"   📅 {post.published_at.strftime('%Y-%m-%d') if post.published_at else 'Unknown'}\n\n"

            return result

        except Exception as e:
            return f"❌ Analysis error for {handle}: {str(e)}"

    else:
        # Topic-based analysis across publications
        publications = await auto_discover_publications(focus)[:3]

        if not publications:
            return f"❌ Could not identify relevant publications for '{focus}'"

        result = f"📊 **Trend Analysis: {focus}**\n\n"

        all_matching_posts = []
        for pub in publications:
            try:
                posts = await run_in_threadpool(client.fetch_feed, pub, 10)
                matching = [post for post in posts if smart_content_match(focus, post)]
                all_matching_posts.extend([(post, pub) for post in matching])
            except Exception:
                continue

        if all_matching_posts:
            result += f"🔍 **Found {len(all_matching_posts)} relevant posts across {len(publications)} publications:**\n\n"

            for i, (post, pub) in enumerate(all_matching_posts[:8], 1):
                result += f"{i}. **{post.title}**\n"
                result += f"   📖 {pub} • {post.published_at.strftime('%Y-%m-%d') if post.published_at else 'Recent'}\n"
                excerpt = post.excerpt or "No preview"
                result += f"   {excerpt[:100]}{'...' if len(excerpt) > 100 else ''}\n\n"

            result += f"💡 Searched: {', '.join(publications)}"
        else:
            result += f"No recent content found matching '{focus}'"

        return result


def create_app(client: SubstackPublicClient | None = None) -> FastAPI:
    app = FastAPI(title="Substack MCP", version="0.1.0")
    substack = client or SubstackPublicClient()

    @app.on_event("shutdown")
    def _shutdown() -> None:
        substack.close()

    payload = {
        "service": "Substack MCP",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "mcp_endpoint": "/mcp"
    }

    @app.get("/")
    async def root_info():
        """Return service information for GET requests to root."""
        return JSONResponse(payload)

    @app.get("/health")
    async def healthcheck() -> dict:
        return {
            "status": "ok",
            "throttle_seconds": substack.settings.throttle_seconds,
            "cache_ttl": substack.settings.cache_ttl.total_seconds(),
        }

    @app.get("/publications/{handle}/posts", response_model=list[PostSummary])
    async def list_posts(handle: str, limit: int = Query(10, ge=1, le=50)) -> list[PostSummary]:
        return await run_in_threadpool(substack.fetch_feed, handle, limit)

    @app.get("/posts", response_model=PostContent)
    async def get_post(url: str = Query(..., description="Full URL to a Substack post")) -> PostContent:
        try:
            return await run_in_threadpool(substack.fetch_post, url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/analytics", response_model=list[ContentAnalytics])
    async def get_analytics(handle: str, limit: int = Query(5, ge=1, le=25)) -> list[ContentAnalytics]:
        posts = await run_in_threadpool(substack.fetch_feed, handle, limit)
        results: list[ContentAnalytics] = []
        for summary in posts:
            content = await run_in_threadpool(substack.fetch_post, summary.url, posts)
            results.append(await run_in_threadpool(analysis.analyse_post, content, posts))
        return results

    @app.get("/notes/{handle}", response_model=list[Note])
    async def list_notes(handle: str, limit: int = Query(10, ge=1, le=50)) -> list[Note]:
        return await run_in_threadpool(substack.fetch_notes, handle, limit)

    @app.get("/authors/{handle}/profile", response_model=AuthorProfile)
    async def author_profile(handle: str) -> AuthorProfile:
        profile = await run_in_threadpool(substack.fetch_author_profile, handle)
        if profile is None:
            raise HTTPException(status_code=404, detail="Author not found")
        return profile

    @app.get("/crawl/{handle}", response_model=CrawlResult)
    async def crawl(
        handle: str,
        post_limit: int = Query(5, ge=1, le=25),
        notes_limit: int = Query(10, ge=0, le=50),
        analyse: bool = True,
    ) -> CrawlResult:
        return await run_in_threadpool(substack.crawl_publication, handle, post_limit, analyse, notes_limit)

    # MCP endpoint for ChatGPT custom connectors
    @app.post("/mcp")
    @app.get("/mcp")
    async def mcp_endpoint(request: Request):
        """Handle MCP requests according to Streamable HTTP transport spec."""
        accept_header = request.headers.get("accept", "")

        if request.method == "GET":
            # For GET requests, return SSE stream if requested
            if "text/event-stream" in accept_header:
                async def event_stream():
                    yield "data: {}\n\n"

                return StreamingResponse(
                    event_stream(),
                    media_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                )
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

        elif request.method == "POST":
            try:
                # Get JSON-RPC request
                body = await request.json()

                # Handle basic MCP requests
                if body.get("method") == "tools/list":
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "tools": [
                                {
                                    "name": "search_substack",
                                    "description": "Intelligently search for content across Substack publications. Handles natural language queries and auto-discovers relevant publications.",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "What you're looking for - can be topics, keywords, author names, or general themes. Examples: 'AI regulation', 'crypto DeFi', 'Ben Thompson tech analysis', 'remote work trends'"
                                            },
                                            "publication_hint": {
                                                "type": "string",
                                                "description": "Optional hint about publication (e.g. 'stratechery', 'platformer', 'tech newsletters') - will auto-discover if not provided"
                                            }
                                        },
                                        "required": ["query"]
                                    }
                                },
                                {
                                    "name": "get_content",
                                    "description": "Get full content and analysis from a Substack post or publication. Works with URLs, publication names, or handles.",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "target": {
                                                "type": "string",
                                                "description": "What to fetch - can be a full URL, publication name, or handle. Examples: 'https://stratechery.com/post', 'Ben Thompson latest', 'platformer recent posts'"
                                            },
                                            "analysis_type": {
                                                "type": "string",
                                                "description": "Type of analysis: 'full' (content + analytics), 'summary' (recent posts), 'profile' (author info). Default: 'full'",
                                                "enum": ["full", "summary", "profile"]
                                            }
                                        },
                                        "required": ["target"]
                                    }
                                },
                                {
                                    "name": "discover_publications",
                                    "description": "Discover and explore Substack publications by topic, industry, or theme. Great for finding new sources.",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "topic": {
                                                "type": "string",
                                                "description": "Topic or industry to explore. Examples: 'tech', 'finance', 'AI', 'crypto', 'politics', 'business strategy'"
                                            }
                                        },
                                        "required": ["topic"]
                                    }
                                },
                                {
                                    "name": "analyze_trends",
                                    "description": "Analyze content trends, publishing patterns, and themes across publications or specific authors.",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "focus": {
                                                "type": "string",
                                                "description": "What to analyze - publication name, author, or topic. Examples: 'stratechery publishing patterns', 'AI content trends', 'Casey Newton writing style'"
                                            },
                                            "analysis_depth": {
                                                "type": "string",
                                                "description": "Analysis depth: 'quick' (recent posts), 'deep' (comprehensive analysis), 'comparative' (compare multiple sources)",
                                                "enum": ["quick", "deep", "comparative"]
                                            }
                                        },
                                        "required": ["focus"]
                                    }
                                }
                            ]
                        }
                    })

                elif body.get("method") == "tools/call":
                    params = body.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})

                    # Smart Substack search - handles natural language queries
                    if tool_name == "search_substack":
                        query = arguments.get("query", "")
                        publication_hint = arguments.get("publication_hint", "")

                        if not query:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32602, "message": "Query is required"}
                            })

                        try:
                            # Smart publication discovery based on query and hint
                            publications_to_search = []

                            # If hint provided, try to resolve it
                            if publication_hint:
                                resolved_handle = await resolve_publication_hint(publication_hint)
                                if resolved_handle:
                                    publications_to_search.append(resolved_handle)

                            # Auto-discover publications based on query content
                            auto_publications = await auto_discover_publications(query)
                            publications_to_search.extend(auto_publications)

                            # Remove duplicates and limit to top 3 for performance
                            publications_to_search = list(dict.fromkeys(publications_to_search))[:3]

                            # If no publications found, use popular defaults
                            if not publications_to_search:
                                publications_to_search = ["stratechery", "platformer", "importai"]

                            # Search across publications
                            all_results = []
                            for handle in publications_to_search:
                                try:
                                    posts = await run_in_threadpool(substack.fetch_feed, handle, 15)
                                    matching_posts = [
                                        post for post in posts
                                        if smart_content_match(query, post)
                                    ]

                                    for post in matching_posts[:3]:  # Top 3 per publication
                                        excerpt = post.excerpt or "No preview available"
                                        all_results.append({
                                            "title": post.title,
                                            "excerpt": excerpt[:200] + "..." if len(excerpt) > 200 else excerpt,
                                            "url": str(post.url),
                                            "publication": handle,
                                            "published": post.published_at.strftime("%Y-%m-%d") if post.published_at else "Unknown"
                                        })
                                except Exception:
                                    continue  # Skip failed publications

                            # Format results
                            if all_results:
                                result_text = f"🔍 Found {len(all_results)} results for '{query}':\n\n"
                                for i, result in enumerate(all_results[:8], 1):  # Top 8 overall
                                    result_text += f"{i}. **{result['title']}**\n"
                                    result_text += f"   📖 {result['publication']} • {result['published']}\n"
                                    result_text += f"   {result['excerpt']}\n"
                                    result_text += f"   🔗 {result['url']}\n\n"

                                result_text += f"💡 Searched: {', '.join(publications_to_search)}"
                            else:
                                result_text = f"No results found for '{query}'. Try rephrasing your search or being more specific about the topic or publication."

                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "result": {"content": [{"type": "text", "text": result_text}]}
                            })
                        except Exception as e:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32603, "message": f"Search error: {str(e)}"}
                            })

                    # Smart content retrieval
                    elif tool_name == "get_content":
                        target = arguments.get("target", "")
                        analysis_type = arguments.get("analysis_type", "full")

                        if not target:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32602, "message": "Target is required"}
                            })

                        try:
                            result_text = await smart_content_retrieval(target, analysis_type, substack)
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "result": {"content": [{"type": "text", "text": result_text}]}
                            })
                        except Exception as e:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32603, "message": f"Content retrieval error: {str(e)}"}
                            })

                    # Publication discovery
                    elif tool_name == "discover_publications":
                        topic = arguments.get("topic", "")

                        if not topic:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32602, "message": "Topic is required"}
                            })

                        try:
                            result_text = await discover_publications_by_topic(topic, substack)
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "result": {"content": [{"type": "text", "text": result_text}]}
                            })
                        except Exception as e:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32603, "message": f"Discovery error: {str(e)}"}
                            })

                    # Trend analysis
                    elif tool_name == "analyze_trends":
                        focus = arguments.get("focus", "")
                        analysis_depth = arguments.get("analysis_depth", "quick")

                        if not focus:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32602, "message": "Focus is required"}
                            })

                        try:
                            result_text = await analyze_content_trends(focus, analysis_depth, substack)
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "result": {"content": [{"type": "text", "text": result_text}]}
                            })
                        except Exception as e:
                            return JSONResponse({
                                "jsonrpc": "2.0",
                                "id": body.get("id"),
                                "error": {"code": -32603, "message": f"Analysis error: {str(e)}"}
                            })

                    else:
                        return JSONResponse({
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                        })

                elif body.get("method") == "initialize":
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {
                                "name": "substack-mcp",
                                "version": "0.1.0"
                            }
                        }
                    })

                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {"code": -32601, "message": "Method not found"}
                    })

            except Exception as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id") if 'body' in locals() else None,
                    "error": {"code": -32603, "message": "Internal error"}
                })

    # MCP endpoint at root for ChatGPT discovery
    @app.post("/")
    async def mcp_root_endpoint(request: Request):
        """Handle MCP requests at root path for ChatGPT compatibility."""
        return await mcp_endpoint(request)

    # ChatGPT search aggregation endpoint
    @app.post("/search")
    async def chatgpt_search(request: Request):
        """Handle ChatGPT's search aggregation requests."""
        try:
            body = await request.json()

            # Extract search parameters from ChatGPT's format
            source_params = body.get("source_specific_search_parameters", {})
            connector_id = "slurm_mcp_connector_68d74578ccd88191adf2f7eb8c8f7301"

            if connector_id in source_params:
                params_list = source_params[connector_id]
                if params_list and len(params_list) > 0:
                    search_params = params_list[0]
                    query = search_params.get("query")
                    handle = search_params.get("handle")

                    if query:
                        # Use existing search logic
                        if handle:
                            posts = await run_in_threadpool(substack.fetch_feed, handle, 20)
                            matching_posts = [
                                post for post in posts
                                if query.lower() in post.title.lower() or (post.excerpt and query.lower() in post.excerpt.lower())
                            ]

                            results = []
                            for post in matching_posts[:5]:
                                excerpt = post.excerpt or "No excerpt available"
                                results.append({
                                    "title": post.title,
                                    "content": excerpt,
                                    "url": str(post.url),
                                    "published_at": post.published_at.isoformat() if post.published_at else None,
                                    "source": handle
                                })
                        else:
                            # Generic search response
                            results = [{
                                "title": f"Search Query: {query}",
                                "content": f"To search within a specific publication, provide the publication handle. Available for search: stratechery, platformer, importai, and other Substack handles.",
                                "url": "",
                                "source": "search_guidance"
                            }]

                        return JSONResponse({"results": results})

            # Default empty response
            return JSONResponse({"results": []})

        except Exception as e:
            return JSONResponse({"results": [], "error": str(e)})

    # Handle favicon requests
    @app.get("/favicon.ico")
    async def favicon():
        """Return empty response for favicon requests."""
        return Response(status_code=204)

    return app


# Lazily instantiate a default app so `uvicorn substack_mcp.server:app` works.
app = create_app()
