import os
import re
from datetime import datetime
from flask import Flask, request, render_template
from PIL import Image
import pytesseract
from pymongo import MongoClient

app = Flask(__name__)
#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MongoDB connection
#Using cloud MongoDB
connection_string='mongodb+srv://nutriscan_user:Khushi123@cluster-nutriscan.y5zj6y8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster-NutriScan'
client = MongoClient(connection_string)  # Change this if using cloud MongoDB
db = client['nutriscan_db']
scans_collection = db['food_scans']

def extract_nutrition_data(text):
    """Actually parse nutrition facts from OCR text"""
    nutrition_data = {}
    
    patterns = {
        'calories': r'calories\s*(\d+)',
        'fat': r'total fat\s*(\d+\.?\d*)g',
        'saturated_fat': r'saturated fat\s*(\d+\.?\d*)g', 
        'sodium': r'sodium\s*(\d+)mg',
        'carbs': r'total carbohydrate\s*(\d+\.?\d*)g',
        'fiber': r'dietary fiber\s*(\d+\.?\d*)g',
        'sugar': r'total sugars\s*(\d+\.?\d*)g',
        'protein': r'protein\s*(\d+\.?\d*)g'
    }
    
    text_lower = text.lower()
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            nutrition_data[key] = float(match.group(1))
    
    return nutrition_data

def analyze_nutrition(nutrition_data):
    """Analyze nutrition data with real health guidelines"""
    insights = []
    
    if 'sugar' in nutrition_data:
        if nutrition_data['sugar'] > 15:
            insights.append("⚠️ High sugar content")
        elif nutrition_data['sugar'] < 5:
            insights.append("✅ Low sugar content")
    
    if 'sodium' in nutrition_data:
        if nutrition_data['sodium'] > 500:
            insights.append("⚠️ High sodium content")
        elif nutrition_data['sodium'] < 140:
            insights.append("✅ Low sodium content")
    
    if 'fiber' in nutrition_data:
        if nutrition_data['fiber'] > 3:
            insights.append("✅ Good fiber content")
    
    if 'protein' in nutrition_data:
        if nutrition_data['protein'] > 10:
            insights.append("✅ Good protein content")
    
    if 'saturated_fat' in nutrition_data:
        if nutrition_data['saturated_fat'] > 5:
            insights.append("⚠️ High saturated fat")
    
    if not insights:
        insights.append("ℹ️ Basic nutrition info found")
    
    return insights

def get_emoji_feedback(insights):
    good_count = sum(1 for insight in insights if "✅" in insight)
    caution_count = sum(1 for insight in insights if "⚠️" in insight)
    
    if good_count > caution_count:
        return "😊 Healthy Choice!"
    elif caution_count > good_count:
        return "😟 Consider Alternatives"
    else:
        return "😐 Moderate Choice"
    
def cleanup_old_scans():
    """Keep only last 100 scans to save space"""
    try:
        # Keep only the 100 most recent scans, delete older ones
        scans_collection.find().sort('timestamp', -1).skip(100).delete_many({})
        print("Cleaned up old scans")
    except Exception as e:
        print(f"Cleanup error: {e}")

def save_to_database(extracted_text, nutrition_data, insights, emoji_feedback):
    """Save scan data to MongoDB"""
    scan_data = {
        'timestamp': datetime.now(),
        'extracted_text': extracted_text,
        'nutrition_data': nutrition_data,
        'insights': insights,
        'emoji_feedback': emoji_feedback,
        'good_count': sum(1 for insight in insights if "✅" in insight),
        'caution_count': sum(1 for insight in insights if "⚠️" in insight)
    }
    
    result = scans_collection.insert_one(scan_data)
    return result.inserted_id

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/scan', methods=['POST'])
def scan():
    if 'food_image' not in request.files:
        return "No file part", 400

    file = request.files['food_image']
    if file.filename == '':
        return "No selected file", 400

    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        image = Image.open(file_path)
        extracted_text = pytesseract.image_to_string(image)

        nutrition_data = extract_nutrition_data(extracted_text)
        insights = analyze_nutrition(nutrition_data)
        emoji_feedback = get_emoji_feedback(insights)
        
        good_count = sum(1 for insight in insights if "✅" in insight)
        caution_count = sum(1 for insight in insights if "⚠️" in insight)

        # Save to database
        scan_id = save_to_database(extracted_text, nutrition_data, insights, emoji_feedback)

        if os.path.exists(file_path):
            os.remove(file_path)

        return render_template("result.html", 
                             ocr_text=extracted_text,
                             nutrition_data=nutrition_data,
                             insights=insights,
                             emoji_feedback=emoji_feedback,
                             good_count=good_count,
                             caution_count=caution_count,
                             scan_id=str(scan_id))

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/history')
def history():
    """Page to view scan history"""
    scans = scans_collection.find().sort('timestamp', -1).limit(10)
    return render_template("history.html", scans=scans)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

