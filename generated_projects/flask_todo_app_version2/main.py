from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
tasks = []  # In-memory storage for tasks as dictionaries with content and priority

@app.route('/')
def index():
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    task_content = request.form.get('task')
    priority = request.form.get('priority', 'medium')  # default to medium if not provided
    if task_content and task_content.strip():
        # Ensure priority is one of the valid options
        if priority not in ['high', 'medium', 'low']:
            priority = 'medium'  # default to medium if invalid
        tasks.append({'content': task_content.strip(), 'priority': priority})
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete():
    task_index = request.form.get('index')
    if task_index and task_index.isdigit():
        index_int = int(task_index)
        if 0 <= index_int < len(tasks):
            del tasks[index_int]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)