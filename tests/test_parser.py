from core.parsing import parse_poem_html


def test_parse_poem_html_extracts_fields():
    html = """
    <html>
      <head>
        <title>Friedrich Wilhelm Kaulisch - Mutterliebe</title>
        <meta name="Author" content=" Friedrich Wilhelm Kaulisch ">
      </head>
      <body>
        <p><b>Mutterliebe</b></p>
        <p>Wenn Du noch eine Mutter hast<br>
           so danke Gott und sei zufrieden</p>
      </body>
    </html>
    """
    poem = parse_poem_html("https://hor.de/gedichte/test.htm", html)
    assert poem.title == "Mutterliebe"
    assert poem.author == "Friedrich Wilhelm Kaulisch"
    assert "Wenn Du noch eine Mutter hast" in poem.text
