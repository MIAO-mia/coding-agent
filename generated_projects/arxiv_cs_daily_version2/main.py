from flask import Flask, render_template, request
import arxiv_fetcher

app = Flask(__name__)

@app.route('/')
def index():
    """Render the homepage with navigation, date filter, and a list of papers based on selected category and date."""
    category = request.args.get('category', '')
    date = request.args.get('date', '')
    papers = arxiv_fetcher.fetch_latest_papers(category, date)
    categories = arxiv_fetcher.CATEGORIES
    return render_template('index.html', papers=papers, categories=categories, selected_category=category, selected_date=date)

@app.route('/paper/<paper_id>')
def paper_detail(paper_id):
    """Render the paper detail page for a specific arXiv paper."""
    paper = arxiv_fetcher.fetch_paper_detail(paper_id)
    if not paper:
        return 'Paper not found', 404
    citations = arxiv_fetcher.generate_citations(paper)
    return render_template('detail.html', paper=paper, citations=citations)

if __name__ == '__main__':
    app.run(debug=True)