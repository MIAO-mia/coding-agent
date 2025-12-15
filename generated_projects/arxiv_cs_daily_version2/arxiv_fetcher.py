import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

ARXIV_API = 'http://export.arxiv.org/api/query'
CATEGORIES = ['cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.MA', 'cs.NE', 'cs.RO', 'cs.SY', 'cs.TH']

def fetch_latest_papers(category=None, date=None):
    """Fetch papers from arXiv, optionally filtered by category and/or date."""
    query_parts = []
    if category and category in CATEGORIES:
        query_parts.append(f'cat:{category}')
    else:
        query_parts.append('cat:cs.*')
    
    # Handle date filtering - arXiv uses submittedDate with YYYYMMDD format
    if date:
        try:
            # Convert from YYYY-MM-DD to YYYYMMDD format
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_str = date_obj.strftime('%Y%m%d')
            # arXiv uses date range format: submittedDate:[YYYYMMDD TO YYYYMMDD]
            query_parts.append(f'submittedDate:[{date_str} TO {date_str}]')
        except ValueError:
            print(f"Invalid date format: {date}. Using default behavior.")
    
    search_query = ' AND '.join(query_parts)
    params = {
        'search_query': search_query,
        'start': 0,
        'max_results': 100,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    try:
        response = requests.get(ARXIV_API, params=params, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        papers = []
        
        # Check if there are entries in the response
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        if not entries:
            print(f"No papers found for query: {search_query}")
            return []
        
        for entry in entries:
            try:
                paper_id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                paper_id = paper_id_elem.text.split('/')[-1] if paper_id_elem is not None else 'unknown'
                
                title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else 'No title'
                
                published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
                published = published_elem.text if published_elem is not None else ''
                
                categories = [cat.get('term') for cat in entry.findall('{http://www.w3.org/2005/Atom}category')]
                cs_categories = [c for c in categories if c.startswith('cs.')]
                paper_field = cs_categories[0] if cs_categories else 'cs.OTHER'
                
                papers.append({
                    'id': paper_id,
                    'title': title,
                    'submission_time': published,
                    'field': paper_field
                })
            except Exception as e:
                print(f"Error parsing paper entry: {e}")
                continue
                
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
        
        title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else 'No title'
        
        authors = []
        for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
            name_elem = author.find('{http://www.w3.org/2005/Atom}name')
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text)
        
        published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
        published = published_elem.text if published_elem is not None else ''
        
        summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
        summary = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ''
        
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