#!/usr/bin/env python3
"""
Final script to build enhanced CSV with all metadata.
Combines original CSV + article content + excerpts.
"""

import json
import csv


def extract_excerpt(text: str, target_length: int = 175) -> str:
    """Extract first 150-200 characters as excerpt."""
    if not text:
        return ""

    # Skip header info and get to main content
    text = text.strip()

    # Try to find where the main content starts (after title, author, date)
    lines = text.split('\n')
    main_start = 0
    for i, line in enumerate(lines):
        if len(line) > 50 and not any(x in line.lower() for x in ['share', 'subscribe', 'paid', 'techtiff', 'dec ', 'nov ', 'oct ', 'sep ', 'aug ', 'jul ', 'jun ', 'may ', 'apr ', 'mar ', 'feb ', 'jan ']):
            main_start = i
            break

    # Rejoin from main content start
    text = ' '.join(lines[main_start:])

    if len(text) <= target_length:
        return text

    excerpt = text[:target_length]
    last_period = max(excerpt.rfind('.'), excerpt.rfind('!'), excerpt.rfind('?'))

    if last_period > 100:
        excerpt = excerpt[:last_period + 1]
    else:
        excerpt = excerpt[:target_length].rsplit(' ', 1)[0] + '...'

    return excerpt.strip()


def generate_summary_from_content(body: str, title: str) -> tuple:
    """
    Generate summary and key takeaways from article body.
    Returns (summary, key_takeaways_string)
    """
    # For now, use the subtitle/first paragraph as summary
    # and extract key points from the content

    lines = [l.strip() for l in body.split('\n') if l.strip()]

    # Try to find the subtitle (usually after title)
    summary = ""
    for i, line in enumerate(lines[:10]):
        if len(line) > 30 and len(line) < 200 and line != title:
            summary = line
            break

    # Generate generic key takeaways based on content patterns
    takeaways = []

    # Look for bullet points or numbered lists in content
    for line in lines:
        if (line.startswith('-') or line.startswith('•') or
            any(line.startswith(f'{i}.') for i in range(1, 10))):
            clean = line.lstrip('-•0123456789. ').strip()
            if 20 < len(clean) < 150:
                takeaways.append(clean)
                if len(takeaways) >= 5:
                    break

    # If no takeaways found, create placeholder
    if not takeaways:
        takeaways = [f"Practical guide to {title.lower()}",
                     "Step-by-step implementation workflow",
                     "Real-world examples and use cases"]

    takeaways_str = '|'.join(takeaways[:5])

    return summary, takeaways_str


def main():
    # Load original CSV
    with open('techtiff_articles.csv', 'r') as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)

    # Load article content
    with open('techtiff_articles_content.json', 'r') as f:
        content_data = json.load(f)

    # Create lookup by URL
    content_by_url = {item['url']: item for item in content_data}

    # Build enhanced rows
    enhanced_rows = []

    print(f"Processing {len(csv_data)} articles...")

    for i, row in enumerate(csv_data):
        url = row['url']
        content = content_by_url.get(url, {})

        body = content.get('body', '')
        word_count = content.get('word_count', 0)
        reading_time = content.get('reading_time', 0)

        # Generate summary and takeaways
        summary, takeaways = generate_summary_from_content(body, row['title'])

        # Use subtitle as summary if we didn't find one
        if not summary and row.get('subtitle'):
            summary = row['subtitle']

        # Extract excerpt
        excerpt = extract_excerpt(body)

        enhanced_row = {
            **row,
            'summary': summary,
            'key_takeaways': takeaways,
            'word_count': str(word_count),
            'reading_time': str(reading_time),
            'excerpt': excerpt
        }

        enhanced_rows.append(enhanced_row)

        print(f"  [{i+1}/{len(csv_data)}] {row['title'][:60]}... ✅")

    # Save enhanced CSV
    fieldnames = [
        'title', 'url', 'slug', 'published_at', 'subtitle', 'thumbnail_url',
        'content_type', 'keywords', 'summary', 'key_takeaways',
        'word_count', 'reading_time', 'excerpt'
    ]

    output_file = 'techtiff_articles_enhanced.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enhanced_rows)

    # Stats
    total_words = sum(int(r['word_count']) for r in enhanced_rows)
    avg_reading = sum(int(r['reading_time']) for r in enhanced_rows) / len(enhanced_rows)

    print(f"\n{'='*70}")
    print(f"✅ Enhanced CSV generated successfully!")
    print(f"{'='*70}")
    print(f"Total articles: {len(enhanced_rows)}")
    print(f"Total words: {total_words:,}")
    print(f"Average reading time: {avg_reading:.1f} minutes")
    print(f"Output file: {output_file}")
    print(f"{'='*70}")

    # Show sample
    print(f"\nSample row (first article):")
    sample = enhanced_rows[0]
    for key in ['title', 'summary', 'key_takeaways', 'word_count', 'reading_time', 'excerpt']:
        value = sample[key]
        if len(str(value)) > 100:
            value = str(value)[:100] + '...'
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
