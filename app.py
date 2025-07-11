import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import pymysql.cursors
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret')

# Enable CORS only for the autocomplete endpoint and specific origins
CORS(app, resources={
    r"/autocomplete_company": {
        "origins": [
            "https://indonesiaminer.com",
            "https://staging.indonesiaminer.com",
            "http://127.0.0.1:8000"
        ]
    }
})

# MySQL connection configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'user_kartu'),
    'password': os.getenv('DB_PASS', 'P@ssw0rd123!'),
    'db': os.getenv('DB_NAME', 'db_kartunama'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)

@app.route('/autocomplete_company', methods=['GET'])
def autocomplete_company():
    query = request.args.get('q', '').strip()
    suggestions = []
    if len(query) >= 4:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                like_pattern = f"%{query}%"
                cur.execute(
                    """
                    SELECT DISTINCT u.company_name,
                                    u.company_address,
                                    u.ms_company_category_id AS category_id,
                                    c.name AS category_name
                    FROM users AS u
                    JOIN ms_company_category AS c
                      ON u.ms_company_category_id = c.id
                    WHERE u.company_address IS NOT NULL
                      AND TRIM(u.company_address) <> ''
                      AND u.company_name LIKE %s
                    ORDER BY u.company_name ASC
                    LIMIT 5
                    """,
                    (like_pattern,)
                )
                rows = cur.fetchall()
                for row in rows:
                    suggestions.append({
                        'company_name': row['company_name'],
                        'company_address': row['company_address'],
                        'category_id': row['category_id'],
                        'category_name': row['category_name']
                    })
        finally:
            conn.close()
    return jsonify(suggestions)

@app.route('/', methods=['GET', 'POST'])
def form_card():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM ms_company_category ORDER BY name ASC")
            categories = cur.fetchall()
    finally:
        conn.close()

    if request.method == 'POST':
        full_name        = request.form.get('full_name', '').strip()
        company_name     = request.form.get('company_name', '').strip()
        phone            = request.form.get('phone', '').strip()
        job_title        = request.form.get('job_title', '').strip()
        job_title_tier   = request.form.get('job_title_tier', '').strip()
        email_business   = request.form.get('email_business', '').strip().lower()
        company_address  = request.form.get('company_address', '').strip()
        office_number    = request.form.get('office_number', '').strip()
        category_id      = request.form.get('category_id')

        # Validate required fields
        if not all([full_name, company_name, phone, job_title, job_title_tier, email_business, category_id]):
            flash(
                'Fields Full Name, Company Name, Phone, Job Title, Job Title Tier, '
                'Business Email, and Company Category are required.',
                'danger'
            )
            return render_template('form.html', categories=categories)

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Check duplicate email
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM kartu_nama WHERE email_business=%s",
                    (email_business,)
                )
                result = cur.fetchone()
                if result and result['cnt'] > 0:
                    flash('Business email already exists.', 'warning')
                    return render_template('form.html', categories=categories)

                # Insert data
                cur.execute(
                    """
                    INSERT INTO kartu_nama (
                        nama,
                        company_name,
                        phone,
                        job_title,
                        job_title_tier,
                        email_business,
                        company_address,
                        office_number,
                        category_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        full_name,
                        company_name,
                        phone,
                        job_title,
                        job_title_tier,
                        email_business,
                        company_address or None,
                        office_number or None,
                        category_id
                    )
                )
                conn.commit()
                flash('Business card data saved successfully!', 'success')
        finally:
            conn.close()

        return redirect(url_for('form_card'))

    return render_template('form.html', categories=categories)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)
