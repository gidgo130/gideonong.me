"""Parse a University of Tulsa unofficial transcript PDF (FastReport, 3-column layout)
into transcript-data.json. Reads only course, term and total lines - never the name,
date-of-birth, high-school or ID fields in the page header.

Usage:  python parse_transcript.py <transcript.pdf> [-o transcript-data.json]
Needs:  pdfplumber  (pip install pdfplumber)
"""
import argparse, json, re
from datetime import date

COURSE = re.compile(r'^([A-Z]{2,4})\s+(\d{4})\s+(.+?)\s+(\d)\s+(?:([A-Z][+-]?)\s+)?(\d+\.\d+)$')
TOTAL = re.compile(r'^(UT|UA)\*\s+(\d+)\s+AT\s+(\d+)\s+ERN\s+(\d+)\s+GPH\s+([\d.]+)\s+PT\s+([\d.]+)\s+GPA$')
TERM = re.compile(r'^(Fall|Spring|Summer|Winter) Term (\d{4})$')
EXAM = re.compile(r'^Credit by Exam:\s*(.+)$')
PRINTED = re.compile(r'\b([A-Z][a-z]{2}) (\d{1,2}) (\d{4})\b')

def pages(pdf_path):
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        return [p.extract_text(layout=True) or '' for p in pdf.pages]

def column_stream(text):
    """Column 1 lines, then column 2, then column 3 (the transcript reads down each column).
    Everything above the 'DEPT NO.' header row (name, birth date, IDs) is skipped."""
    lines = text.split('\n')
    start = next(i for i, l in enumerate(lines) if 'DEPT NO.' in l) + 1
    cols = [[], [], []]
    for l in lines[start:]:
        if '|' not in l:
            continue
        for c, part in enumerate(l.split('|')[:3]):
            s = re.sub(r'\s+', ' ', part).strip()
            if s:
                cols[c].append(s)
    return cols[0] + cols[1] + cols[2]

def printed_date(text):
    """The print date sits top-right of the header ('Sep 14 2026'); only that is read from the header."""
    head = text.split('DEPT NO.')[0]
    m = PRINTED.search(head)
    if not m:
        return None
    mon = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(m.group(1)) + 1
    return f'{m.group(3)}-{mon:02d}-{int(m.group(2)):02d}'

def parse(pdf_path):
    texts = pages(pdf_path)
    blocks, cur = [], None
    for t in texts:
        for line in column_stream(t):
            m, e = TERM.match(line), EXAM.match(line)
            if m or e:
                cur = ({'kind': 'term', 'season': m.group(1), 'year': int(m.group(2)), 'courses': []} if m
                       else {'kind': 'exam', 'source': e.group(1).strip(), 'courses': []})
                blocks.append(cur); continue
            m = COURSE.match(line)
            if m and cur is not None:
                dept, num, title, cr, grd, pts = m.groups()
                cur['courses'].append({'code': f'{dept} {num}', 'transcript_title': title.strip(),
                                       'credits': int(cr), 'grade': grd or '', 'points': float(pts)})
                continue
            m = TOTAL.match(line)
            if m and cur is not None:
                key = 'term_totals' if m.group(1) == 'UT' else 'cumulative_totals'
                cur[key] = {'earned': int(m.group(2)), 'attempted': int(m.group(3)), 'gpa_hours': int(m.group(4)),
                            'grade_points': float(m.group(5)), 'gpa': float(m.group(6))}
    return {'transcript_printed': printed_date(texts[0]), 'parsed_on': date.today().isoformat(), 'blocks': blocks}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf'); ap.add_argument('-o', '--out', default='transcript-data.json')
    a = ap.parse_args()
    data = parse(a.pdf)
    n = sum(len(b['courses']) for b in data['blocks'])
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f'parsed {len(data["blocks"])} blocks, {n} courses -> {a.out}')

if __name__ == '__main__':
    main()
