from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
from ultralytics import YOLO
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# 1. Load your YOLO model
model = YOLO('best.pt')  # Make sure 'best.pt' is in your backend folder

# ==========================================
# 2. INITIALIZE THE NEW STATE MACHINE DATABASE
# ==========================================
def init_db():
    conn = sqlite3.connect('smc_urbanfix.db')
    c = conn.cursor()
    # Dropping the old sync_status and adding the 8-stage workflow columns
    c.execute('''
        CREATE TABLE IF NOT EXISTS defects (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            defect_class TEXT,
            confidence REAL,
            lat TEXT,
            lng TEXT,
            severity TEXT,
            detected_at TEXT,
            
            -- THE NEW WORKFLOW STATUS COLUMN --
            status TEXT DEFAULT 'REPORTED',
            
            -- METADATA COLUMNS FOR THE NEW WORKFLOW --
            assigned_department TEXT,
            contractor_name TEXT,
            repair_image_url TEXT,
            citizen_feedback TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Run database setup on startup
init_db()

# ==========================================
# 3. THE MAIN AI ANALYSIS ROUTE
# ==========================================
@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'No image uploaded'}), 400
    
    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    
    # Run YOLO Model
    results = model(img)
    
    detections = []
    total_volume_m3 = 0.0 # To track total asphalt needed
    
    # Connect to database to save this batch of detections
    conn = sqlite3.connect('smc_urbanfix.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            class_name = model.names[cls]
            
            # --- REAL MATH FOR PWD ESTIMATOR ---
            pixel_to_meter = 0.01 
            width_m = (x2 - x1) * pixel_to_meter
            height_m = (y2 - y1) * pixel_to_meter
            area_m2 = width_m * height_m
            
            depth_m = 0.1 
            volume_m3 = area_m2 * depth_m
            total_volume_m3 += volume_m3
            
            # Draw bounding box on the image
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(img, f'{class_name} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
            
            severity = "High" if conf > 0.7 else "Medium"
            
            # Generate mock GPS coordinates near Solapur for the demo
            lat = f"17.{random.randint(65000, 67000)}"
            lng = f"75.{random.randint(89000, 91000)}"
            
            # --- THE STATE MACHINE MAGIC HAPPENS HERE ---
            # Step 1: Insert as 'REPORTED'
            c.execute('''
                INSERT INTO defects (defect_class, confidence, lat, lng, severity, detected_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (class_name, conf, lat, lng, severity, now, 'REPORTED'))
            
            record_id = c.lastrowid # Get the ID of the new ticket
            
            # Step 2: Immediately advance to 'AI_ANALYZED' since the neural net just finished
            c.execute('''
                UPDATE defects SET status = ? WHERE record_id = ?
            ''', ('AI_ANALYZED', record_id))
            
            # Append to list to send back to frontend Analyzer table
            detections.append({
                "record_id": record_id, # Sending this to frontend so we can update it later!
                "label": class_name,
                "confidence": conf,
                "location": f"[{lat}, {lng}]",
                "time": now,
                "severity": severity,
                "department": "SMC Road Engineering",
                "status": "AI_ANALYZED"
            })
    
    # Commit changes and close DB connection
    conn.commit()
    conn.close()
    
    # --- CALCULATE FINAL MATERIALS AND COST ---
    total_tons = total_volume_m3 * 2.4
    total_cost = total_tons * 4500
    
    defect_count = len(detections)
    quality_score = max(0, 100 - (defect_count * 5))
    if quality_score > 80:
        health_status = "Good Condition"
    elif quality_score > 50:
        health_status = "Maintenance Required"
    else:
        health_status = "CRITICAL REPAIR"
    
    # Convert drawn image back to Base64 to show on frontend
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    visual_evidence = f"data:image/jpeg;base64,{img_base64}"
    
    return jsonify({
        "status": "success",
        "visual_evidence": visual_evidence,
        "quality_score": quality_score,
        "health_status": health_status,
        "data": detections,
        "est_tons": round(total_tons, 2),
        "est_cost": round(total_cost, 0)
    })

# ==========================================
# 4. NEW ROUTE: ADVANCE THE WORKFLOW
# ==========================================
@app.route('/api/advance_workflow', methods=['POST'])
def advance_workflow():
    """
    Frontend calls this when you click the 'Next Stage' button.
    """
    data = request.json
    record_id = data.get('record_id')
    new_status = data.get('new_status')
    
    allowed_states = [
        'REPORTED', 'AI_ANALYZED', 'SMC_REVIEW', 'DEPT_ASSIGNED', 
        'CONTRACTOR_ASSIGNED', 'REPAIRED', 'CITIZEN_VERIFIED', 'CLOSED'
    ]
    
    if new_status not in allowed_states:
        return jsonify({'status': 'error', 'message': f'Invalid status. Must be one of {allowed_states}'}), 400

    try:
        conn = sqlite3.connect('smc_urbanfix.db')
        c = conn.cursor()
        
        # Base query
        query = "UPDATE defects SET status = ?"
        params = [new_status]
        
        # Add metadata if provided in the frontend request
        if 'assigned_department' in data:
            query += ", assigned_department = ?"
            params.append(data['assigned_department'])
        if 'contractor_name' in data:
            query += ", contractor_name = ?"
            params.append(data['contractor_name'])
            
        query += " WHERE record_id = ?"
        params.append(record_id)
        
        c.execute(query, tuple(params))
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success", 
            "message": f"Ticket {record_id} advanced to {new_status}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# 5. FETCH REAL DATABASE LOGS (Updated)
# ==========================================
@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        conn = sqlite3.connect('smc_urbanfix.db')
        conn.row_factory = sqlite3.Row  
        c = conn.cursor()
        # Now fetches the new status and metadata columns!
        c.execute('SELECT * FROM defects ORDER BY record_id DESC LIMIT 50')
        rows = c.fetchall()
        conn.close()
        
        data = [dict(row) for row in rows]
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)