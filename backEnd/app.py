from flask import Flask, request, jsonify
from datetime import datetime
from models import db, Job
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

# Helper: Validate job payload
def validate_job(data):
    required_fields = ['title', 'company', 'location', 'posting_date', 'job_type']
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return f"Field '{field}' is required and cannot be empty."
    try:
        datetime.strptime(data['posting_date'], '%Y-%m-%d')
    except ValueError:
        return "Invalid date format for 'posting_date'. Use YYYY-MM-DD."
    return None

# ---------------------------
# CREATE
# ---------------------------
@app.route('/jobs', methods=['POST'])
def create_job():
    data = request.get_json()
    error = validate_job(data)
    if error:
        return jsonify({'error': error}), 400

    new_job = Job(
        title=data['title'],
        company=data['company'],
        location=data['location'],
        posting_date=datetime.strptime(data['posting_date'], '%Y-%m-%d').date(),
        job_type=data['job_type'],
        tags=','.join(data.get('tags', []))
    )
    db.session.add(new_job)
    db.session.commit()
    return jsonify(new_job.to_dict()), 201

# ---------------------------
# READ (List & Single)
# ---------------------------
@app.route('/jobs', methods=['GET'])
def get_jobs():
    # Filtering
    job_type = request.args.get('job_type')
    location = request.args.get('location')
    tag = request.args.get('tag')
    sort = request.args.get('sort', 'posting_date_desc')

    query = Job.query

    if job_type:
        query = query.filter_by(job_type=job_type)
    if location:
        query = query.filter_by(location=location)
    if tag:
        query = query.filter(Job.tags.like(f"%{tag}%"))

    if sort == 'posting_date_asc':
        query = query.order_by(Job.posting_date.asc())
    else:
        query = query.order_by(Job.posting_date.desc())

    jobs = query.all()
    return jsonify([job.to_dict() for job in jobs]), 200

@app.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job.to_dict()), 200

# ---------------------------
# UPDATE
# ---------------------------
@app.route('/jobs/<int:job_id>', methods=['PUT', 'PATCH'])
def update_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    data = request.get_json()
    for key in ['title', 'company', 'location', 'posting_date', 'job_type', 'tags']:
        if key in data:
            if key == 'posting_date':
                try:
                    setattr(job, key, datetime.strptime(data[key], '%Y-%m-%d').date())
                except ValueError:
                    return jsonify({'error': "Invalid date format. Use YYYY-MM-DD."}), 400
            elif key == 'tags':
                setattr(job, key, ','.join(data['tags']))
            else:
                setattr(job, key, data[key])

    db.session.commit()
    return jsonify(job.to_dict()), 200

# ---------------------------
# DELETE
# ---------------------------
@app.route('/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    db.session.delete(job)
    db.session.commit()
    return jsonify({'message': 'Job deleted successfully'}), 200

# ---------------------------
# Error Handling: 404 for invalid routes
# ---------------------------
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Not found'}), 404

# ---------------------------
# Run
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
