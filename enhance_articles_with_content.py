#!/usr/bin/env python3
"""
Enhance TechTiff articles CSV with full content analysis for SEO/AEO/GEO optimization.

Fetches full article content from Substack and generates:
- AI-generated summaries (2-3 sentences)
- Key takeaways (3-5 bullet points)
- Word count and reading time
- Article excerpts (first 150-200 chars)
"""

import csv
import os
import sys
import time
from typing import Optional, List, Dict, Any
from anthropic import Anthropic

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from substack_mcp.client import SubstackPublicClient
from substack_mcp.models import PostContent


# Initialize clients
substack_client = SubstackPublicClient()
claude_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def generate_summary_and_takeaways(article_text: str, title: str) -> Dict[str, str]:
    """
    Use Claude to generate a summary and key takeaways from article text.

    Returns:
        {
            'summary': '2-3 sentence summary',
            'key_takeaways': 'Takeaway 1|Takeaway 2|Takeaway 3'
        }
    """
    prompt = f"""Analyze this article and provide:

1. A 2-3 sentence SEO-optimized summary that captures the main value proposition
2. 3-5 key takeaways as short, actionable bullet points

Article Title: {title}

Article Content:
{article_text[:4000]}  # Limit to ~4000 chars to stay within context

Format your response EXACTLY as:
SUMMARY: [your 2-3 sentence summary]
TAKEAWAYS:
- [takeaway 1]
- [takeaway 2]
- [takeaway 3]
- [takeaway 4]
- [takeaway 5]"""

    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text

        # Parse response
        summary = ""
        takeaways = []

        lines = content.split('\n')
        in_takeaways = False

        for line in lines:
            line = line.strip()
            if line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
            elif line.startswith('TAKEAWAYS:'):
                in_takeaways = True
            elif in_takeaways and line.startswith('-'):
                takeaway = line.lstrip('- ').strip()
                if takeaway:
                    takeaways.append(takeaway)

        return {
            'summary': summary,
            'key_takeaways': '|'.join(takeaways) if takeaways else ''
        }

    except Exception as e:
        print(f"  Error generating AI content: {e}")
        return {
            'summary': '',
            'key_takeaways': ''
        }


def extract_excerpt(text: str, target_length: int = 175) -> str:
    """
    Extract first 150-200 characters from article body as excerpt.
    Ensures complete sentences.
    """
    if not text:
        return ""

    # Clean up text
    text = text.strip()

    # If text is shorter than target, return it all
    if len(text) <= target_length:
        return text

    # Try to find sentence boundary near target length
    excerpt = text[:target_length]

    # Look for sentence ending (., !, ?)
    last_period = max(excerpt.rfind('.'), excerpt.rfind('!'), excerpt.rfind('?'))

    if last_period > 100:  # If we found a sentence ending after 100 chars
        excerpt = excerpt[:last_period + 1]
    else:
        # No good sentence boundary, just truncate and add ellipsis
        excerpt = excerpt[:target_length].rsplit(' ', 1)[0] + '...'

    return excerpt.strip()


def process_article(row: Dict[str, str], index: int, total: int) -> Dict[str, str]:
    """
    Process a single article: fetch content, generate summaries, extract metadata.

    Returns enhanced row with new fields.
    """
    url = row['url']
    title = row['title']

    print(f"  [{index}/{total}] {title[:60]}...")

    try:
        # Fetch full article content
        post_content: PostContent = substack_client.fetch_post(url)

        # Extract article body text
        article_text = post_content.text or ""

        if not article_text:
            print(f"    ⚠️  No content found for article")
            return {
                **row,
                'summary': '',
                'key_takeaways': '',
                'word_count': '0',
                'reading_time': '0',
                'excerpt': ''
            }

        # Generate AI summary and takeaways
        print(f"    📝 Generating summary and takeaways...")
        ai_content = generate_summary_and_takeaways(article_text, title)

        # Extract metadata
        word_count = post_content.word_count or len(article_text.split())
        reading_time = post_content.minute_read or max(1, word_count // 200)  # ~200 wpm
        excerpt = extract_excerpt(article_text)

        # Build enhanced row
        enhanced_row = {
            **row,
            'summary': ai_content['summary'],
            'key_takeaways': ai_content['key_takeaways'],
            'word_count': str(word_count),
            'reading_time': str(reading_time),
            'excerpt': excerpt
        }

        print(f"    ✅ Success: {word_count} words, {reading_time} min read")

        return enhanced_row

    except Exception as e:
        print(f"    ❌ Error: {e}")
        return {
            **row,
            'summary': '',
            'key_takeaways': '',
            'word_count': '0',
            'reading_time': '0',
            'excerpt': ''
        }


def load_existing_csv(filename: str) -> List[Dict[str, str]]:
    """Load existing CSV data."""
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_enhanced_csv(data: List[Dict[str, str]], filename: str):
    """Save enhanced CSV with new fields."""
    if not data:
        print("No data to save!")
        return

    fieldnames = [
        'title', 'url', 'slug', 'published_at', 'subtitle', 'thumbnail_url',
        'content_type', 'keywords', 'summary', 'key_takeaways',
        'word_count', 'reading_time', 'excerpt'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"\n✅ Saved {len(data)} articles to {filename}")


def main():
    input_file = "techtiff_articles.csv"
    output_file = "techtiff_articles_enhanced.csv"

    print(f"🚀 Starting article enhancement process...")
    print(f"📂 Input: {input_file}")
    print(f"📂 Output: {output_file}")

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Load existing articles
    print(f"\n📖 Loading existing articles...")
    articles = load_existing_csv(input_file)
    total = len(articles)
    print(f"   Found {total} articles to process")

    # Process articles in chunks
    enhanced_articles = []
    chunk_size = 10

    for i in range(0, total, chunk_size):
        chunk = articles[i:i + chunk_size]
        chunk_num = (i // chunk_size) + 1
        total_chunks = (total + chunk_size - 1) // chunk_size

        print(f"\n📦 Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} articles)...")

        for j, article in enumerate(chunk):
            enhanced = process_article(article, i + j + 1, total)
            enhanced_articles.append(enhanced)

            # Small delay between articles to be respectful
            time.sleep(0.5)

        # Delay between chunks
        if i + chunk_size < total:
            print(f"   ⏳ Waiting before next chunk...")
            time.sleep(2)

    # Save results
    print(f"\n💾 Saving enhanced articles...")
    save_enhanced_csv(enhanced_articles, output_file)

    # Print summary statistics
    successful = sum(1 for a in enhanced_articles if a['summary'])
    failed = total - successful
    total_words = sum(int(a['word_count']) for a in enhanced_articles)
    avg_reading_time = sum(int(a['reading_time']) for a in enhanced_articles) / total if total > 0 else 0

    print(f"\n{'='*60}")
    print(f"📊 SUMMARY STATISTICS")
    print(f"{'='*60}")
    print(f"Total articles processed: {total}")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"Total word count: {total_words:,}")
    print(f"Average reading time: {avg_reading_time:.1f} minutes")
    print(f"\n📄 Output file: {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
