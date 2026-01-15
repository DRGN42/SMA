from core.chunking import chunk_poem_lines


def test_chunk_poem_lines_default():
    text = "Line 1\nLine 2\n\nLine 3"
    chunks = chunk_poem_lines(text)
    assert len(chunks) == 2
    assert chunks[0].text == "Line 1\nLine 2"
    assert chunks[1].text == "Line 3"


def test_chunk_poem_lines_max_chars():
    text = "Line 1\nLine 2\nLine 3"
    chunks = chunk_poem_lines(text, max_chars_per_chunk=10)
    assert len(chunks) == 3
