from datetime import datetime

from substack_mcp import analysis
from substack_mcp.models import PostContent, PostSummary


def test_analyse_post_generates_metrics():
    summary = PostSummary(
        id="1",
        title="Sample",
        url="https://example.substack.com/p/sample",
        published_at=datetime.utcnow(),
    )
    content = PostContent(
        summary=summary,
        html="<p>Hello world</p>",
        text="Hello world. This is a simple test post for analytics.",
    )

    result = analysis.analyse_post(content)

    assert result.summary.title == "Sample"
    assert result.sentiment is not None
    assert result.sentiment.compound is not None
    assert result.lexical_diversity is not None
    assert result.extra["word_count"] > 0
