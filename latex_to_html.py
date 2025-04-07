import re
from html import escape

# Extract songs from LaTeX content using regex
def extract_songs(content):
    # Regex pattern to match songs between \beginsong and \endsong
    pattern = r'\\beginsong{(.+?)}(?:\[(.*?)\])?(.*?)\\endsong'
    return re.findall(pattern, content, re.DOTALL)

# Parse the body of a song and convert it to HTML
def parse_song_body(body):
    output = []
    lines = body.strip().splitlines()
    verse_number = 1
    in_verse = False

    for line in lines:
        # Clean up and process the line
        line = line.strip().rstrip("\\")
        line = line.replace(r'\lrep', '[:').replace(r'\rrep', ':]').replace(r'\#', '#')
        line = line.replace(r'\%', '%').replace(r'\&', '&')  # Replace escaped % and &
        line = line.replace('~', ' ')  # Replace ~ with a space
        line = re.sub(r'\\rep\{\d+\}', '', line)  # Remove \rep{} with a number inside
        # Remove \emph and \musicnote, keeping the text inside the braces as plain text
        line = re.sub(r'\\emph\{([^{}]*?)\}', lambda m: m.group(1), line)
        line = re.sub(r'\\musicnote\{([^{}]*?)\}', lambda m: m.group(1), line)
        if line.startswith(r'\beginverse*'):  # Unnumbered verse
            output.append('<div class="verse">')
            in_verse = True
            continue
        if line.startswith('%'):  # Skip comments
            continue
        elif line.startswith(r'\beginverse'):  # Start a new verse
            output.append(f'<div class="verse"><div class="verse-number">{verse_number}.</div>')
            verse_number += 1
            in_verse = True
        elif line.startswith(r'\endverse'):  # End the current verse
            output.append('</div>')
            in_verse = False
        elif line.startswith(r'\labeledverse{*}'):  # Unnumbered verse without a label
            output.append('<div class="verse">')
            in_verse = True
        elif line.startswith(r'\labeledverse{'):  # Labeled verse
            label = re.findall(r'\\labeledverse{(.+?)}', line)
            if label:
                output.append(f'<div class="verse"><div class="verse-number">{escape(label[0])}</div>')
            in_verse = True
        elif line.startswith(r'\beginchorus'):  # Start a chorus
            output.append('<div class="chorus"><span class="label">R:</span><br>')
        elif line.startswith(r'\endchorus'):  # End the chorus
            output.append('</div>')
        elif line.startswith(r'\nolyrics'):  # Skip lines marked as no lyrics
            continue
        elif line == '':  # Empty line within a verse
            if in_verse:
                output.append('<br>')
        elif r'\brk' in line:  # Line break
            line = line.replace('\\brk', '\n')  # Replace with newline
            output.append(convert_chorded_line(line).replace('\n', '<br>'))  # Convert to HTML
        else:  # Regular line
            output.append(convert_chorded_line(line))

    return '\n'.join(output)

# Convert a line with chords to HTML
def convert_chorded_line(line):
    chord_pattern = re.compile(r'\\\[(.+?)\]')  # Match chords in the format \[chord]
    chords = []
    text_parts = []
    pos = 0

    # Extract chords and their positions
    for match in chord_pattern.finditer(line):
        chord = match.group(1)
        start, end = match.span()
        text = line[pos:start]
        text_parts.append(text)
        chords.append((len(''.join(text_parts)), chord))
        pos = end

    text_parts.append(line[pos:])
    text_line = ''.join(text_parts)

    chord_line = ''
    lyric_line = ''
    for i, char in enumerate(text_line):
        # Add chords above the corresponding lyrics
        chord_here = next((ch for pos, ch in chords if pos == i), None)
        if chord_here:
            chord_line += f'<span class="chord">{escape(chord_here)}</span>'
        else:
            chord_line += ' '
        lyric_line += escape(char)

    return f'<pre class="song-line">{chord_line}\n{lyric_line}</pre>'

# Generate the final HTML document
def generate_html(songs):
    # Sort songs alphabetically by title
    songs_sorted = sorted(songs, key=lambda s: s[0].lower())
    html = ['''<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cyferník</title>
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <link rel="stylesheet" href="styles.css">
  <style>
    body {
      font-family: sans-serif;
      background-color: #000000;
      color: #e0e0e0;
      margin: 1em;
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }
    a { color:rgb(255, 166, 0); }
    h1, h2 { color: #ffffff; font-family: bahnschrift; }
    h1 { text-align: center; }
    h2 { margin-top: 2.5em; }
    .verse, .chorus { margin: 1em 0; }
    .verse-number { font-weight: bold; display: inline-block; width: auto; margin-bottom: 0.2em; color: #000000; background-color: rgb(255, 255, 255); padding: 0.2em; border-radius: 0.3em;}
    .chorus .label { font-weight: bold; color: #000000; background-color: rgb(255, 166, 0); padding: 0.2em; border-radius: 0.3em; }
    .chord {
      color: rgb(255, 166, 0);
      font-weight: bold;
      display: inline-block;
      min-width: 2.5em;
      text-align: center;
    }
    .song-line {
      font-family: monospace;
      white-space: pre;
      margin: 0.3em 0;
    }
    .index a {
      text-decoration: none;
      display: block;
      margin: 0.2em 0;
    }
    .song {
      padding-bottom: 2em;
      border-bottom: 1px solid #222;
    }
    .back-to-top {
      margin-top: 1em;
      text-align: right;
      font-size: 0.9em;
    }
    .back-to-top a {
        color: #000000;
        background-color: rgb(255, 166, 0);
        padding: 0.5em;
        border-radius: 0.3em;
        text-decoration: none;
        font-family: bahnschrift;
    }
    .download-links {
      text-align: center;
      color:rgb(76, 76, 76);
    }
    .download-links a {
      color:rgb(76, 76, 76);
      text-decoration: none;
    }
    @media (max-width: 600px) {
      body { font-size: 16px; padding: 0.5em; }
      .chord { min-width: 2em; }
    }
  </style>
</head>
<body>
  <a id="top"></a>
  <div class="download-links">
    <a href="zpevnik-dark.pdf" download>stáhnout pdf verzi (tmavá verze)</a>, <a href="zpevnik-light.pdf" download>stáhnout pdf verzi (světlá verze)</a>
  </div>
<h1 style="text-align: center;">Osadní zpěvník T.O.</h1>
<div style="text-align: center;">
    <img src="cyfernik-logo.png" alt="Cyferník Logo" style="width: 50%;">
</div>
  <div class="index">
    <h2>Obsah</h2>
''']

    current_letter = None
    for idx, (title, meta, _) in enumerate(songs_sorted, start=1):
        # Group songs by the first letter of their title
        first_letter = title[0].upper()
        if first_letter != current_letter:
            if current_letter is not None:
                html.append('</div>')
            current_letter = first_letter
            html.append(f'<h3>{current_letter}</h3><div>')
        num = re.search(r'number=(\d+)', meta or '')
        number = num.group(1) if num else str(idx)
        html.append(f'<a href="#song-{number}">{escape(title)} ({number})</a>')

    if current_letter is not None:
        html.append('</div>')

    html.append('</div><hr>')

    for idx, (title, meta, body) in enumerate(songs, start=1):
        # Add each song to the HTML
        num = re.search(r'number=(\d+)', meta or '')
        number = num.group(1) if num else str(idx)
        author_match = re.search(r'by={(.*?)}', meta or '')
        author = author_match.group(1) if author_match else ''
        html.append(f'<div class="song" id="song-{number}">')
        html.append(f'<h2>{number}. {escape(title)}</h2>')
        if author:
            html.append(f'<p><i>{escape(author)}</i></p>')
        html.append(parse_song_body(body))
        html.append(f'<div class="back-to-top"><a href="#top">↑ Nahoru</a></div>')
        html.append('</div>')

    html.append('</body></html>')
    return '\n'.join(html)

# --- Main script ---
# Read LaTeX files containing songs
with open("songs.tex", encoding="utf-8") as f:
    songs_part = f.read()

with open("nove.tex", encoding="utf-8") as f:
    nove_part = f.read()

# Combine content from both files
all_content = songs_part + "\n" + nove_part
songs = extract_songs(all_content)

# Add numbering to songs based on their order
for idx, song in enumerate(songs, start=1):
    title, meta, body = song
    meta = (meta or '') + f' number={idx}'
    songs[idx - 1] = (title, meta, body)

# Generate the HTML file
html = generate_html(songs)
with open("zpevnik.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Vygenerováno jako zpevnik.html")
