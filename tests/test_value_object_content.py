from wechat_summarizer.domain.value_objects import ArticleContent


def test_from_html_extracts_text_and_images() -> None:
    html = """
    <div id="js_content">
      <p>Hello</p>
      <img data-src="https://example.com/a.jpg" />
    </div>
    """
    content = ArticleContent.from_html(html)

    assert "Hello" in content.text
    assert content.image_count == 1
    assert content.images[0] == "https://example.com/a.jpg"


def test_clean_html_removes_hidden_styles() -> None:
    html = """
    <div id="js_content">
      <p style="visibility:hidden; opacity:0;">Hidden</p>
      <p>Visible</p>
    </div>
    """

    content = ArticleContent.from_html(html, clean=True)
    lowered = content.html.lower()

    assert "visibility" not in lowered
    assert "opacity" not in lowered
    assert "Visible" in content.text
