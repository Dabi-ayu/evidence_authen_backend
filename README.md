<h1> 📸 Multimedia Evidence Authentication System </h1>
A full-stack web application for verifying the authenticity of digital image evidence using deep learning, metadata analysis, and SHA256-based integrity checks.

<h1>🔍 Overview</h1>
This project provides a forensic tool designed for legal professionals to authenticate multimedia evidence (images) before submission in court or investigations. It detects digital tampering, verifies EXIF metadata, and provides SHA256 hashing for integrity verification.

<h2>⚙️ Features</h2>
🧠 AI-Based Tampering Detection (using a trained ResNet50 model in TensorFlow/Keras)

📂 EXIF Metadata Extraction and Validation

🔒 SHA256 Hash Generation for Integrity Verification

👩‍⚖️ Lawyer Login/Signup

🧾 Forensic Report Generation

🌐 Frontend in React + Vite

🔙 Backend in Django + Django REST Framework

🧪 Image Upload, Verification, and Reporting Interface


<h2>🏗️ Architecture </h2>
Frontend: React + Tailwind CSS

Backend: Django REST Framework

AI Model: ResNet50 fine-tuned for tampering detection

Image Metadata: EXIF analysis using exifread + geopy

Hashing: SHA256 via Python’s hashlib

Database: PostgreSQL (or SQLite for local dev)


<h1>🚀 Getting Started</h1>
<h2>🔧 Prerequisites</h2>
Python 3.10+

Node.js 16+

PostgreSQL (or SQLite)

TensorFlow 2.x

Geopy

pip, npm, virtualenv

<h1> 🐍 Backend Setup (Django) </h1>
git clone https://github.com/yourusername/image_authen_backend.git
cd image_authen_backend

<h3> # Create virtual environment </h3>
python -m venv env
source env/bin/activate  

on Windows: env\Scripts\activate

<h3> # Install dependencies </h3>
pip install -r requirements.txt

# Run migrations and start server
python manage.py migrate
python manage.py runserver


<h4> 🙋‍♀️ Author </h4>
Dabi Clementina Ayu
Final Year Computer Engineering Student
University of Bamenda
📧 Email: [dabiayu8@gmail.com]
🌍 Cameroon
