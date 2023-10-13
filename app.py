from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import tempfile
import os
import logging

app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'obo'}

def convert_obo_to_tsv(obo_file_path):
    # Read the OBO file and convert it to TSV
    print("hi")
    with open(obo_file_path, 'r', encoding='utf-8') as obo_file:
        term_data = []
        current_term = {}

        for line in obo_file:
            line = line.strip()
            if line == '[Term]':
                current_term = {}
            elif line.startswith('id:'):
                current_term['ID'] = line[4:].strip()
            elif line.startswith('name:'):
                current_term['Name'] = line[6:].strip()
            elif line.startswith('def:'):
                current_term['Definition'] = line[5:].strip()
            elif line == '' and current_term:
                term_data.append(current_term)
                current_term = {}

    tsv_df = pd.DataFrame(term_data)
    tsv_df.to_csv('ontology.tsv', sep='\t', index=False)
    return tsv_df

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search_query')
    tsv_df = pd.read_csv('ontology.tsv', sep='\t')  # Load the TSV data

    if search_query:
        # Filter the DataFrame based on the search query
        filtered_df = tsv_df[tsv_df['Name'].str.contains(search_query, case=False, na=False) | tsv_df['Definition'].str.contains(search_query, case=False, na=False)]
        table_html = filtered_df.to_html(classes='table table-striped', index=False, escape=False)
    else:
        # If no search query provided, show the entire table
        table_html = tsv_df.to_html(classes='table table-striped', index=False, escape=False)

    return render_template('view.html', table=table_html, search_query=search_query)


@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Save the uploaded OBO file to a temporary location
        obo_file_path = os.path.join(tempfile.gettempdir(), 'ontology.obo')
        file.save(obo_file_path)

        # Convert the uploaded OBO file to TSV
        convert_obo_to_tsv(obo_file_path)

        # Serve the TSV file for download
        return send_file('ontology.tsv', as_attachment=True, download_name='ontology.tsv')
    else:
        return redirect(request.url)

@app.route('/view', methods=['GET', 'POST'])
def view():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Save the uploaded OBO file to a temporary location
        obo_file_path = os.path.join(tempfile.gettempdir(), 'ontology.obo')
        file.save(obo_file_path)

        # Check if the file exists
        if os.path.exists(obo_file_path):
            # Convert the uploaded OBO file to TSV
            tsv_df = convert_obo_to_tsv(obo_file_path)

            # Convert the DataFrame to an HTML table format
            table_html = tsv_df.to_html(classes='table table-striped', index=False, escape=False)

            # Clean up the temporary OBO file
            os.remove(obo_file_path)

            # Pass the HTML table data to the template for rendering
            return render_template('view.html', table=table_html)
        else:
            # Handle the case where the file doesn't exist
            return "File does not exist."

    else:
        return redirect(request.url)





if __name__ == '__main__':
    app.run(debug=True)