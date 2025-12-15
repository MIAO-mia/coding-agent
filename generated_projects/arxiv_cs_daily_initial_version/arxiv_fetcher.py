import requests
import xml.etree.ElementTree as ET

ARXIV_API = 'http://export.arxiv.org/api/query'
CATEGORIES = ['cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.MA', 'cs.NE', 'cs.RO', 'cs.SY', 'cs.TH']  # Example arXiv CS categories

def fetch_latest_papers(category=None):
    """Fetch the latest papers from arXiv, optionally filtered by a specific CS category."""
    if category and category not in CATEGORIES:
        category = None  # Default to all categories if invalid
    query = f'cat:{category}' if category else 'cat:cs.*'
    params = {
        'search_query': query,
        'start': 0,
        'max_results': 100,  # Fetch up to 100 papers for daily view
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    try:
        response = requests.get(ARXIV_API, params=params, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        papers = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            paper_id = entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1]
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
            published = entry.find('{http://www.w3.org/2005/Atom}published').text
            categories = [cat.get('term') for cat in entry.findall('{http://www.w3.org/2005/Atom}category')]
            cs_categories = [c for c in categories if c.startswith('cs.')]
            paper_field = cs_categories[0] if cs_categories else 'cs.OTHER'
            papers.append({
                'id': paper_id,
                'title': title,
                'submission_time': published,
                'field': paper_field
            })
        return papers
    except requests.RequestException as e:
        print(f"Error fetching papers from arXiv: {e}")
        return []
    except ET.ParseError as e:
        print(f"Error parsing arXiv response: {e}")
        return []

def fetch_paper_detail(paper_id):
    """Fetch detailed information for a specific arXiv paper by its ID."""
    params = {
        'id_list': paper_id,
        'max_results': 1
    }
    try:
        response = requests.get(ARXIV_API, params=params, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        if entry is None:
            return None
        title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
        authors = [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')]
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
        pdf_link_element = entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]')
        pdf_link = pdf_link_element.get('href') if pdf_link_element is not None else f'https://arxiv.org/pdf/{paper_id}.pdf'
        categories = [cat.get('term') for cat in entry.findall('{http://www.w3.org/2005/Atom}category')]
        return {
            'id': paper_id,
            'title': title,
            'authors': authors,
            'submission_date': published,
            'abstract': summary,
            'pdf_link': pdf_link,
            'categories': categories
        }
    except requests.RequestException as e:
        print(f"Error fetching paper detail from arXiv: {e}")
        return None
    except ET.ParseError as e:
        print(f"Error parsing arXiv detail response: {e}")
        return None

def generate_citations(paper):
    """Generate BibTeX and standard academic citations for a given paper."""
    authors_str = ' and '.join(paper['authors'])
    year = paper['submission_date'][:4] if paper['submission_date'] else 'YYYY'
    paper_id_clean = paper['id'].replace('.', '')
    bibtex = f"@article{{arxiv{paper_id_clean},\n  title = {{{paper['title']}}},\n  author = {{{authors_str}}},\n  journal = {{arXiv preprint}},\n  year = {{{year}}},\n  eprint = {{{paper['id']}}},\n  url = {{https://arxiv.org/abs/{paper['id']}}}\n}}"
    standard = f"{', '.join(paper['authors'])}. \"{paper['title']}.\" arXiv preprint arXiv:{paper['id']} ({paper['submission_date'][:10] if paper['submission_date'] else year})."
    return {
        'bibtex': bibtex,
        'standard': standard
    }