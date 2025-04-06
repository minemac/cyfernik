import re
from html import escape

def extract_songs(content):
    pattern = r'\\beginsong{(.+?)}(?:\[(.*?)\])?(.*?)\\endsong'
    return re.findall(pattern, content, re.DOTALL)

def parse_song_body(body):
    output = []
    lines = body.strip().splitlines()
    verse_number = 1
    in_verse = False

    for line in lines:
        line = line.strip().rstrip("\\")
        line = line.replace(r'\lrep', '[:').replace(r'\rrep', ':]')

        if line.startswith(r'\beginverse'):
            output.append(f'<div class="verse"><div class="verse-number">{verse_number}.</div>')
            verse_number += 1
            in_verse = True
        elif line.startswith(r'\endverse'):
            output.append('</div>')
            in_verse = False
        elif line.startswith(r'\labeledverse{*}'):
            continue  # přeskoč nečíslovanou sloku
        elif line.startswith(r'\labeledverse{'):
            label = re.findall(r'\\labeledverse{(.+?)}', line)
            if label:
                output.append(f'<div class="verse"><div class="verse-number">{escape(label[0])}</div>')
            in_verse = True
        elif line.startswith(r'\beginchorus'):
            output.append('<div class="chorus"><span class="label">R:</span><br>')
        elif line.startswith(r'\endchorus'):
            output.append('</div>')
        elif line.startswith(r'\nolyrics'):
            continue
        elif line == '':
            if in_verse:
                output.append('<br>')
        else:
            output.append(convert_chorded_line(line))

    return '\n'.join(output)

def convert_chorded_line(line):
    chord_pattern = re.compile(r'\\\[(.+?)\]')
    chords = []
    text_parts = []
    pos = 0

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
        chord_here = next((ch for pos, ch in chords if pos == i), None)
        if chord_here:
            chord_line += f'<span class="chord">{escape(chord_here)}</span>'
        else:
            chord_line += ' '
        lyric_line += escape(char)

    return f'<pre class="song-line">{chord_line}\n{lyric_line}</pre>'

def generate_html(songs):
    songs_sorted = sorted(songs, key=lambda s: s[0].lower())

    html = ['''<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Zpěvník</title>
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
    a { color: #81c784; }
    h1, h2 { color: #ffffff; }
    h1 { text-align: center; }
    h2 { margin-top: 2.5em; }
    .verse, .chorus { margin: 1em 0; }
    .verse-number { font-weight: bold; display: inline-block; width: auto; margin-bottom: 0.2em; }
    .chorus .label { font-weight: bold; }
    .chord {
      color: #81d4fa;
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
    @media (max-width: 600px) {
      body { font-size: 16px; padding: 0.5em; }
      .chord { min-width: 2em; }
    }
  </style>
</head>
<body>
  <a id="top"></a>
  <h1>Zpěvník</h1>
  <div class="index">
    <h2>Obsah</h2>
''']

    for idx, (title, meta, _) in enumerate(songs_sorted, start=1):
        num = re.search(r'number=(\d+)', meta or '')
        number = num.group(1) if num else str(idx)
        html.append(f'<a href="#song-{number}">{escape(title)} ({number})</a>')

    html.append('</div><hr>')

    for idx, (title, meta, body) in enumerate(songs_sorted, start=1):
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

# --- Použití ---
with open("songs.tex", encoding="utf-8") as f:
    songs_part = f.read()

with open("nove.tex", encoding="utf-8") as f:
    nove_part = f.read()

all_content = songs_part + "\n" + nove_part
songs = extract_songs(all_content)

html = generate_html(songs)
with open("zpevnik.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Vygenerováno jako zpevnik.html")
