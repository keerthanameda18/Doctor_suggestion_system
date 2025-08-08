from flask import Flask, render_template_string, request, jsonify
from rapidfuzz import process, fuzz
from spellchecker import SpellChecker
import re

app = Flask(__name__)

# Emergency symptoms that require immediate medical attention
EMERGENCY_SYMPTOMS = {
    'chest pain': 'Severe chest pain can indicate heart attack. Call emergency services immediately!',
    'heart attack': 'Call emergency services immediately!',
    'stroke': 'Signs of stroke require immediate emergency care!',
    'seizure': 'Active seizures require immediate medical attention!',
    'difficulty breathing': 'Severe breathing problems need immediate care!',
    'can\'t breathe': 'Breathing difficulties require immediate emergency care!',
    'shortness of breath': 'Severe breathing problems may need immediate care!',
    'severe bleeding': 'Heavy bleeding requires immediate medical attention!',
    'blood loss': 'Significant blood loss requires emergency care!',
    'unconscious': 'Loss of consciousness requires immediate emergency care!',
    'severe head injury': 'Head injuries can be serious - seek immediate care!',
    'poisoning': 'Poisoning requires immediate emergency treatment!',
    'overdose': 'Drug overdose requires immediate emergency care!',
    'severe burns': 'Severe burns need immediate medical treatment!',
    'broken bone': 'Suspected fractures should be evaluated immediately!',
    'suicide': 'If you\'re having thoughts of self-harm, please call emergency services immediately!',
    'suicidal': 'If you\'re having thoughts of self-harm, please call emergency services immediately!',
    'allergic reaction': 'Severe allergic reactions can be life-threatening!',
    'anaphylaxis': 'Anaphylaxis is a medical emergency! Call emergency services now!',
    'severe pain': 'Severe, sudden pain may indicate a serious condition requiring immediate care!',
    'high fever': 'Very high fever (over 103°F/39.4°C) may need immediate attention!',
    'dehydration': 'Severe dehydration can be dangerous and may need emergency treatment!'
}

# Enhanced symptom mapping with more comprehensive coverage
SYMPTOM_TO_DOCTOR = {
    'fever': ['General Physician'],
    'cold': ['General Physician'],
    'cough': ['General Physician'],
    'fatigue': ['General Physician'],
    'tired': ['General Physician'],
    'leg pain': ['General Physician'],
    'headache': ['General Physician'],
    'head hurts': ['General Physician'],
    'dizzy': ['General Physician'],
    'dizziness': ['General Physician'],
    'yellow mucus': ['General Physician'],
    'mucus': ['General Physician'],
    'toothache': ['Dentist'],
    'tooth ache': ['Dentist'],
    'tooth pain': ['Dentist'],
    'toothpain': ['Dentist'],
    'tooth hurt': ['Dentist'],
    'tooth hurts': ['Dentist'],
    'teeth pain': ['Dentist'],
    'teeth hurt': ['Dentist'],
    'dental pain': ['Dentist'],
    'gum pain': ['Dentist'],
    'bleeding gums': ['Dentist'],
    'cavity': ['Dentist'],
    'sensitive teeth': ['Dentist'],
    'wisdom tooth': ['Dentist'],
    'braces': ['Dentist'],
    'dental': ['Dentist'],
    'mouth': ['Dentist'],
    'chest pain': ['General Physician', 'Cardiologist'],
    'heart': ['General Physician', 'Cardiologist'],
    'skin': ['General Physician', 'Dermatologist'],
    'rash': ['General Physician', 'Dermatologist'],
    'acne': ['General Physician', 'Dermatologist'],
    'stomach': ['Gastroenterologist'],
    'abdomen': ['Gastroenterologist'],
    'nausea': ['General Physician', 'Gastroenterologist'],
    'puke': ['General Physician', 'Gastroenterologist'],
    'puking': ['General Physician', 'Gastroenterologist'],
    'diarrhea': ['General Physician', 'Gastroenterologist'],
    'diarrhoea': ['General Physician', 'Gastroenterologist'],
    'loose motions': ['General Physician', 'Gastroenterologist'],
    'loose stools': ['General Physician', 'Gastroenterologist'],
    'vomiting': ['General Physician', 'Gastroenterologist'],
    'indigestion': ['General Physician', 'Gastroenterologist'],
    'gas': ['General Physician', 'Gastroenterologist'],
    'bloating': ['General Physician', 'Gastroenterologist'],
    'constipation': ['General Physician', 'Gastroenterologist'],
    'loss of appetite': ['General Physician', 'Gastroenterologist'],
    'no appetite': ['General Physician', 'Gastroenterologist'],
    'dont feel like eating': ['General Physician', 'Gastroenterologist'],
    'not hungry': ['General Physician', 'Gastroenterologist'],
    'cant eat': ['General Physician', 'Gastroenterologist'],
    'cannot eat': ['General Physician', 'Gastroenterologist'],
    'eating problems': ['General Physician', 'Gastroenterologist'],
    'appetite loss': ['General Physician', 'Gastroenterologist'],
    'food aversion': ['General Physician', 'Gastroenterologist'],
    'diabetes': ['Endocrinologist'],
    'thyroid': ['Endocrinologist'],
    'eye': ['Ophthalmologist'],
    'vision': ['Ophthalmologist'],
    'ear': ['ENT Specialist'],
    'nose': ['ENT Specialist'],
    'throat': ['ENT Specialist'],
    'joint': ['General Physician', 'Orthopedic'],
    'bone': ['General Physician', 'Orthopedic'],
    'anxiety': ['Psychiatrist'],
    'depression': ['Psychiatrist'],
    'bipolar': ['Psychiatrist'],
    'schizophrenia': ['Psychiatrist'],
    'adhd': ['Psychiatrist'],
    'autism': ['Psychiatrist'],
    'pregnancy': ['Gynaecologist'],
    'period': ['Gynaecologist'],
    'pcod': ['Gynaecologist'],
    'pcos': ['Gynaecologist'],
    'fibroid': ['Gynaecologist'],
    'endometriosis': ['Gynaecologist'],
    'menopause': ['Gynaecologist'],
    'infertility': ['Gynaecologist'],
    'child': ['Pediatrician'],
    'baby': ['Pediatrician'],
    'asthma': ['General Physician', 'Pulmonologist'],
    'breathing': ['General Physician', 'Pulmonologist'],
    'lung': ['General Physician', 'Pulmonologist'],
    'arthritis': ['General Physician', 'Rheumatologist'],
    'lupus': ['General Physician', 'Rheumatologist'],
    'psoriasis': ['Dermatologist'],
    'eczema': ['Dermatologist'],
    'migraine': ['General Physician', 'Neurologist'],
    'seizure': ['General Physician', 'Neurologist'],
    'paralysis': ['General Physician', 'Neurologist'],
    'stroke': ['General Physician', 'Neurologist'],
    'cancer': ['Oncologist'],
    'tumor': ['Oncologist'],
    'leukemia': ['Oncologist'],
    'lymphoma': ['Oncologist'],
    'chemotherapy': ['Oncologist'],
    'radiation': ['Oncologist'],
}

# Emergency hotlines (you can customize these based on your region)
EMERGENCY_CONTACTS = {
    'ambulance': '102',
    'police': '100',
    'fire': '101',
    'disaster': '108',
    'women_helpline': '1091',
    'child_helpline': '1098'
}

def check_emergency_symptoms(user_input):
    """Check if user input contains emergency symptoms"""
    user_input_lower = user_input.lower()
    
    for emergency_symptom, warning in EMERGENCY_SYMPTOMS.items():
        if emergency_symptom in user_input_lower:
            return True, emergency_symptom, warning
    
    # Check for fuzzy matches on emergency symptoms
    for emergency_symptom, warning in EMERGENCY_SYMPTOMS.items():
        best_match, score, _ = process.extractOne(user_input_lower, [emergency_symptom], scorer=fuzz.token_set_ratio)
        if score >= 80:  # Lower threshold for emergency detection
            return True, emergency_symptom, warning
    
    return False, None, None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Doctor Suggestion System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-color: #4A90E2;
            --secondary-color: #7B68EE;
            --accent-color: #FF6B6B;
            --emergency-color: #FF4757;
            --success-color: #2ED573;
            --warning-color: #FFA726;
            --background-light: #F8F9FA;
            --background-dark: #1A1A2E;
            --text-light: #333333;
            --text-dark: #FFFFFF;
            --card-light: #FFFFFF;
            --card-dark: #16213E;
            --border-light: #E1E8ED;
            --border-dark: #2D3748;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            background: var(--background-light);
            color: var(--text-light);
            transition: all 0.3s ease;
            min-height: 100vh;
        }

        body.dark-mode {
            background: var(--background-dark);
            color: var(--text-dark);
        }

        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 18px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
        }

        .theme-toggle:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(74, 144, 226, 0.4);
        }

        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .main-card {
            background: var(--card-light);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            width: 100%;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        body.dark-mode .main-card {
            background: var(--card-dark);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .main-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        }

        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            text-align: center;
            margin-bottom: 30px;
            color: #666;
            font-size: 1rem;
        }

        body.dark-mode .subtitle {
            color: #AAA;
        }

        .form-group {
            margin-bottom: 25px;
            position: relative;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            font-size: 1rem;
        }

        .input-container {
            position: relative;
        }

        input[type="text"] {
            width: 100%;
            padding: 15px 50px 15px 20px;
            border: 2px solid var(--border-light);
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: transparent;
            color: inherit;
        }

        body.dark-mode input[type="text"] {
            border-color: var(--border-dark);
        }

        input[type="text"]:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
            transform: translateY(-1px);
        }

        .voice-btn {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 8px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        .voice-btn:hover {
            background: var(--secondary-color);
        }

        .voice-btn.recording {
            background: var(--emergency-color);
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .submit-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(74, 144, 226, 0.3);
        }

        .submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .emergency-alert {
            background: var(--emergency-color);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            border: none;
            animation: emergency-flash 2s ease-in-out infinite alternate;
        }

        @keyframes emergency-flash {
            0% { box-shadow: 0 0 5px var(--emergency-color); }
            100% { box-shadow: 0 0 20px var(--emergency-color); }
        }

        .emergency-contacts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }

        .emergency-contact {
            background: rgba(255, 255, 255, 0.2);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            text-decoration: none;
            color: white;
            transition: all 0.3s ease;
        }

        .emergency-contact:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }

        .result {
            margin-top: 25px;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid var(--success-color);
            background: rgba(46, 213, 115, 0.1);
            animation: slideInUp 0.5s ease-out;
        }

        .error-result {
            border-left-color: var(--warning-color);
            background: rgba(255, 167, 38, 0.1);
        }

        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .doctor-list {
            list-style: none;
            padding: 0;
        }

        .doctor-item {
            padding: 12px;
            margin: 8px 0;
            background: rgba(74, 144, 226, 0.1);
            border-radius: 8px;
            border-left: 3px solid var(--primary-color);
            transition: all 0.3s ease;
        }

        .doctor-item:hover {
            transform: translateX(5px);
            background: rgba(74, 144, 226, 0.15);
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .main-card {
                padding: 25px;
                margin: 10px;
            }
            
            h1 {
                font-size: 1.8rem;
            }
            
            .theme-toggle {
                top: 10px;
                right: 10px;
                padding: 10px;
                font-size: 16px;
            }
        }

        .accessibility-skip {
            position: absolute;
            left: -10000px;
            top: auto;
            width: 1px;
            height: 1px;
            overflow: hidden;
        }

        .accessibility-skip:focus {
            position: static;
            width: auto;
            height: auto;
        }
    </style>
</head>
<body>
    <a href="#main-content" class="accessibility-skip">Skip to main content</a>
    
    <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle dark mode" title="Switch to Dark Mode" id="theme-button">
        <span id="theme-icon">🌙</span>
    </button>

    <div class="container">
        <div class="main-card" id="main-content">
            <h1>🏥 Smart Doctor Finder</h1>
            <p class="subtitle">Get instant doctor recommendations based on your symptoms</p>
            
            <form method="post" onsubmit="showLoading()">
                <div class="form-group">
                    <label for="symptoms">Describe your symptoms or health concerns:</label>
                    <div class="input-container">
                        <input 
                            type="text" 
                            id="symptoms" 
                            name="symptoms" 
                            required 
                            autocorrect="on" 
                            spellcheck="true"
                            placeholder="e.g., headache, fever, stomach pain..."
                            aria-describedby="symptoms-help"
                        >
                        <button type="button" class="voice-btn" onclick="toggleVoiceInput()" aria-label="Voice input">
                            🎤
                        </button>
                    </div>
                    <small id="symptoms-help">Be as specific as possible for better recommendations</small>
                </div>
                
                <button type="submit" class="submit-btn">
                    Find Suitable Doctor
                </button>
            </form>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Analyzing your symptoms...</p>
            </div>

            {% if emergency %}
            <div class="emergency-alert" role="alert">
                <h3>⚠️ MEDICAL EMERGENCY DETECTED</h3>
                <p><strong>{{ emergency_warning }}</strong></p>
                <p>Please seek immediate medical attention or contact emergency services:</p>
                <div class="emergency-contacts">
                    <a href="tel:102" class="emergency-contact">📞 Ambulance: 102</a>
                    <a href="tel:108" class="emergency-contact">🚑 Emergency: 108</a>
                </div>
            </div>
            {% endif %}

            {% if doctor %}
            <div class="result">
                <h3>💡 Recommended Doctor{{ 's' if doctor|length > 1 else '' }}:</h3>
                <ul class="doctor-list">
                {% for d in doctor %}
                    <li class="doctor-item">{{ d }}</li>
                {% endfor %}
                </ul>
                <p><small>💡 <strong>Tip:</strong> Consider booking an appointment or consulting online for convenience.</small></p>
            </div>
            {% elif error %}
            <div class="result error-result">
                <h3>🤔 {{ error }}</h3>
                <p>You can also try rephrasing your symptoms or contact a general physician for guidance.</p>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        // Theme toggle functionality
        function toggleTheme() {
            const body = document.body;
            const themeIcon = document.getElementById('theme-icon');
            const themeButton = document.getElementById('theme-button');
            
            body.classList.toggle('dark-mode');
            
            if (body.classList.contains('dark-mode')) {
                themeIcon.textContent = '☀️';
                themeButton.title = 'Switch to Light Mode';
                localStorage.setItem('theme', 'dark');
            } else {
                themeIcon.textContent = '🌙';
                themeButton.title = 'Switch to Dark Mode';
                localStorage.setItem('theme', 'light');
            }
        }

        // Load saved theme
        function loadTheme() {
            const savedTheme = localStorage.getItem('theme');
            const themeIcon = document.getElementById('theme-icon');
            const themeButton = document.getElementById('theme-button');
            
            if (savedTheme === 'dark') {
                document.body.classList.add('dark-mode');
                themeIcon.textContent = '☀️';
                themeButton.title = 'Switch to Light Mode';
            } else {
                themeButton.title = 'Switch to Dark Mode';
            }
        }

        // Voice input functionality
        let recognition;
        let isRecording = false;

        function toggleVoiceInput() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert('Voice input is not supported in your browser. Please try Chrome or Edge.');
                return;
            }

            const voiceBtn = document.querySelector('.voice-btn');
            const symptomsInput = document.getElementById('symptoms');

            if (isRecording) {
                recognition.stop();
                return;
            }

            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'en-US';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = function() {
                isRecording = true;
                voiceBtn.classList.add('recording');
                voiceBtn.innerHTML = '⏹️';
                symptomsInput.placeholder = 'Listening...';
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                symptomsInput.value = transcript;
            };

            recognition.onend = function() {
                isRecording = false;
                voiceBtn.classList.remove('recording');
                voiceBtn.innerHTML = '🎤';
                symptomsInput.placeholder = 'e.g., headache, fever, stomach pain...';
            };

            recognition.onerror = function(event) {
                console.error('Speech recognition error:', event.error);
                isRecording = false;
                voiceBtn.classList.remove('recording');
                voiceBtn.innerHTML = '🎤';
                symptomsInput.placeholder = 'e.g., headache, fever, stomach pain...';
            };

            recognition.start();
        }

        // Loading animation
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.querySelector('.submit-btn').disabled = true;
        }

        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', loadTheme);

        // Accessibility: Allow Enter key on voice button
        document.querySelector('.voice-btn').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleVoiceInput();
            }
        });

        // Auto-focus on symptoms input
        document.getElementById('symptoms').focus();
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    doctor = None
    error = None
    emergency = False
    emergency_warning = None
    
    if request.method == 'POST':
        user_input = request.form['symptoms'].lower().strip()
        
        # First, check for emergency symptoms
        is_emergency, emergency_symptom, warning = check_emergency_symptoms(user_input)
        if is_emergency:
            emergency = True
            emergency_warning = warning
        
        # Continue with normal doctor suggestion even if emergency (they might still want to know)
        found = False
        words = user_input.split()
        n = len(words)
        spell = SpellChecker()
        
        # Check all unigrams and bigrams for exact, fuzzy, and autocorrected matches
        for size in [2, 1]:  # bigrams first, then unigrams
            for i in range(n - size + 1):
                phrase = ' '.join(words[i:i+size])
                
                # Exact match
                if phrase in SYMPTOM_TO_DOCTOR:
                    doctor = SYMPTOM_TO_DOCTOR[phrase]
                    found = True
                    break
                
                # Enhanced fuzzy match with lower threshold for better matching
                best_match, score, _ = process.extractOne(phrase, SYMPTOM_TO_DOCTOR.keys(), scorer=fuzz.ratio)
                if score >= 75:  # Lower threshold for better matching
                    doctor = SYMPTOM_TO_DOCTOR[best_match]
                    found = True
                    break
                
                # Try partial ratio for better matching
                best_match, score, _ = process.extractOne(phrase, SYMPTOM_TO_DOCTOR.keys(), scorer=fuzz.partial_ratio)
                if score >= 80:
                    doctor = SYMPTOM_TO_DOCTOR[best_match]
                    found = True
                    break
                
                # Autocorrected match with improved correction
                corrected_words = []
                for word in phrase.split():
                    # Try spell correction
                    corrected = spell.correction(word)
                    if corrected is None:
                        # If spell checker fails, try custom corrections for common medical terms
                        if 'tooth' in word and 'pain' in word:
                            corrected = 'tooth pain'
                        elif 'tooth' in word and ('ach' in word or 'pain' in word):
                            corrected = 'toothache'
                        elif word.startswith('tooth') and len(word) > 5:
                            # Handle common tooth-related typos
                            corrected = 'toothache'
                        else:
                            corrected = word
                    corrected_words.append(corrected)
                
                corrected_phrase = ' '.join(corrected_words)
                
                # Check exact match on corrected phrase
                if corrected_phrase in SYMPTOM_TO_DOCTOR:
                    doctor = SYMPTOM_TO_DOCTOR[corrected_phrase]
                    found = True
                    break
                
                # Fuzzy match on corrected phrase
                best_match, score, _ = process.extractOne(corrected_phrase, SYMPTOM_TO_DOCTOR.keys(), scorer=fuzz.ratio)
                if score >= 75:
                    doctor = SYMPTOM_TO_DOCTOR[best_match]
                    found = True
                    break
            
            if found:
                break
        
        if not found:
            error = 'Sorry, we could not determine the right doctor. Please consult a General Physician.'
    
    return render_template_string(HTML_TEMPLATE, 
                                doctor=doctor, 
                                error=error, 
                                emergency=emergency, 
                                emergency_warning=emergency_warning)

@app.route('/api/emergency-check', methods=['POST'])
def emergency_check_api():
    """API endpoint for checking emergency symptoms"""
    data = request.get_json()
    symptoms = data.get('symptoms', '')
    
    is_emergency, emergency_symptom, warning = check_emergency_symptoms(symptoms)
    
    return jsonify({
        'is_emergency': is_emergency,
        'symptom': emergency_symptom,
        'warning': warning,
        'emergency_contacts': EMERGENCY_CONTACTS
    })

if __name__ == '__main__':
    app.run(debug=True)