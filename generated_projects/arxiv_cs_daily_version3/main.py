from flask import Flask, render_template, request
import arxiv_fetcher
from datetime import datetime

app = Flask(__name__)

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.context_processor
def inject_today_date():
    return {'today': datetime.now().strftime('%Y-%m-%d')}

@app.route('/')
def index():
    """Render the homepage with navigation, date filter, and a list of papers based on selected category and date."""
    category = request.args.get('category', '')
    date = request.args.get('date', '')
    papers = arxiv_fetcher.fetch_latest_papers(category, date)
    categories = arxiv_fetcher.CATEGORIES
    return render_template('index.html', 
                         papers=papers, 
                         categories=categories, 
                         selected_category=category, 
                         selected_date=date)

@app.route('/paper/<paper_id>')
def paper_detail(paper_id):
    """Render the paper detail page for a specific arXiv paper."""
    paper = arxiv_fetcher.fetch_paper_detail(paper_id)
    if not paper:
        return render_template('404.html'), 404
    citations = arxiv_fetcher.generate_citations(paper)
    return render_template('detail.html', paper=paper, citations=citations)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)