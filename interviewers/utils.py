# interviewers/utils.py
import os
from groq import Groq
import pdfplumber
import requests
import cv2
import mediapipe as mp
import numpy as np
from django.conf import settings
from deepface import DeepFace
from django.core.mail import send_mail
from django.conf import settings


def extract_text_from_pdf(pdf_file_path):
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""  # Extract text from each page
            return text.strip()
    except Exception as e:
        return f"Error reading PDF file: {e}"

def generate_interview_questions(pdf_file_path):
    # Initialize the Groq client with API key
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # Extract text from the PDF resume
    resume_content = extract_text_from_pdf(pdf_file_path)
    if resume_content.startswith("Error"):
        return resume_content  # Return error message if PDF reading fails

    # Template for generating interview questions
    template = (
        "You are an experienced interviewer tasked with generating well-structured and insightful interview questions based on the candidate's resume content: {resume_content}. "
        "Your questions should be relevant, professionally phrased, and reflect real-world interview standards.\n\n"

        "1. General Skills-Based Questions:\n"
        "   - Generate a total of **12 questions** assessing the candidate's general professional and soft skills.\n"
        "   - Categorize the questions as follows:\n"
        "     - **3 Easy** questions: Basic, introductory-level questions.\n"
        "     - **3 Medium** questions: More in-depth, practical application-based questions.\n"
        "     - **3 Hard** questions: Complex scenarios requiring problem-solving.\n"
        "     - **3 Extreme Hard** questions: Highly challenging, requiring deep critical thinking.\n\n"

        "2. Technical Skills-Based Questions:\n"
        "   - Generate a total of **12 questions** targeting the candidate’s expertise in programming languages, tools, frameworks, or technologies.\n"
        "   - Categorize the questions as follows:\n"
        "     - **3 Easy** questions: Basic theoretical or conceptual questions.\n"
        "     - **3 Medium** questions: Practical application or troubleshooting scenarios.\n"
        "     - **3 Hard** questions: Advanced, multi-step problem-solving questions.\n"
        "     - **3 Extreme Hard** questions: Expert-level questions involving optimization, architecture, or real-world challenges.\n\n"

        "3. Project-Based Questions:\n"
        "   - Generate a total of **12 questions** specifically about the projects mentioned in the resume.\n"
        "   - Focus on the candidate’s role, technologies used, key challenges, and solutions.\n"
        "   - Categorize the questions as follows:\n"
        "     - **3 Easy** questions: Basic inquiries about project details.\n"
        "     - **3 Medium** questions: Deeper discussions on implementation and impact.\n"
        "     - **3 Hard** questions: Critical problem-solving and technical choices.\n"
        "     - **3 Extreme Hard** questions: Strategic, high-level decision-making challenges.\n\n"

        "4. Behavioral Questions:\n"
        "   - Generate a total of **12 questions** focusing on the candidate’s experience, teamwork, leadership, and problem-solving skills.\n"
        "   - Categorize the questions as follows:\n"
        "     - **3 Easy** questions: Basic situational and self-reflective questions.\n"
        "     - **3 Medium** questions: More complex, experience-driven questions.\n"
        "     - **3 Hard** questions: Handling high-pressure situations and conflicts.\n"
        "     - **3 Extreme Hard** questions: Strategic leadership and ethical dilemma scenarios.\n\n"

        "5. Formatting Rules:\n"
        "   - Organize the questions into clearly labeled sections: 'General Skills Questions', 'Technical Questions', 'Project Questions', and 'Behavioral Questions'.\n"
        "   - Under each section, label the questions clearly by difficulty: 'Easy', 'Medium', 'Hard', and 'Extreme Hard'.\n"
        "   - Do not include any additional comments, explanations, or introductory text beyond the specified instructions.\n"
        "   - If the resume content is invalid or insufficient, return an empty string ('').\n"
        "   - make the test markdown friendly\n"
    )

    # Format the template with the resume content
    prompt = template.format(resume_content=resume_content)

    try:
        # Send request to the Groq API using the formatted prompt
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Groq model choice
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Lower temperature for more focused questions
            max_tokens=4096,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Collect streaming response progressively
        response_chunks = []
        for message in completion:
            chunk = message.choices[0].delta.content or ""
            response_chunks.append(chunk)  # Append each chunk to the list

        # Join all chunks into a complete response
        full_response = "".join(response_chunks)
        return full_response.strip()

    except Exception as e:
        return f"Error generating interview questions: {e}"
    




def schedule_meeting(topic, start_time, zoom_account_id, zoom_client_id, zoom_client_secret):
    # Get OAuth Token
    def get_zoom_access_token():
        url = "https://zoom.us/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "account_credentials",
            "account_id": zoom_account_id
        }
        auth = (zoom_client_id, zoom_client_secret)

        response = requests.post(url, headers=headers, data=payload, auth=auth)

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print("Error getting access token:", response.text)
            return None

    # Schedule the meeting
    access_token = get_zoom_access_token()
    if not access_token:
        return None

    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "topic": topic,
        "type": 2,
        "start_time": start_time,
        "duration": 30,  # 30-minute meeting
        "timezone": "UTC",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "mute_upon_entry": True,
            "waiting_room": False
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return response.json()["join_url"]
    else:
        print("Error scheduling meeting:", response.text)
        return None
    


def send_candidate_email(candidate_email, candidate_name, meeting_link, start_time):
    subject = "Your Interview is Scheduled"
    message = f"""
    Dear {candidate_name},

    Your interview has been scheduled.

    📅 Date & Time: {start_time}
    🔗 Meeting Link: {meeting_link}

    Please ensure that you join the meeting on time.

    Best of luck!

    Regards,
    InsightAi Team
    """

    send_mail(subject, message, settings.EMAIL_HOST_USER, [candidate_email])

def send_interviewer_email(interviewer_email, interviewer_name, candidate_name, meeting_link, start_time):
    subject = "New Interview Scheduled"
    message = f"""
    Dear {interviewer_name},

    You have an upcoming interview scheduled.

    📌 Candidate: {candidate_name}
    📅 Date & Time: {start_time}
    🔗 Meeting Link: {meeting_link}

    Please review the candidate's resume before the interview.

    Regards,
    InsightAi Team
    """

    send_mail(subject, message, settings.EMAIL_HOST_USER, [interviewer_email])







def transcribe_audio(audio_file_path):
    """Transcribes an audio file and analyzes the interview using LLaMA."""

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    print(f"🔍 Transcription started for: {audio_file_path}")

    # Step 1: Transcribe the Audio
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="distil-whisper-large-v3-en",
                file=audio_file,
                response_format="text"
            ).strip()
        
        print(f"✅ Transcription successful: {transcription[:200]}...")  # Print first 200 characters

    except Exception as e:
        print(f"❌ Error transcribing audio: {e}")
        return f"Error transcribing audio: {e}"

    # Step 2: Analyze the Interview using LLaMA
    llama_prompt = f"""
You are an AI-powered interview evaluator assisting the interviewer in assessing a candidate's responses.  
The following is an automatically transcribed interview transcript, with raw and unprocessed text.  
Your task is to extract key insights, assess the quality of responses, and provide a structured evaluation based on the given criteria.
and also provide asked important question and candidate's answer. 

**Interview Transcript (raw):**  
{transcription}  

**Evaluation Criteria:**  
1. **Confidence & Delivery:** Assess whether the candidate speaks with confidence, assurance, and clarity. Explain why you believe they were (or were not) confident based on tone, hesitation, or assertiveness.  
2. **Relevance & Accuracy:** Evaluate whether the candidate’s responses align with the question. Provide reasons if their response was off-topic, partially correct, or completely accurate.  
3. **Coherence & Logical Flow:** Determine if the candidate’s thoughts are structured and make sense. Justify this based on their ability to present ideas sequentially and logically.  
4. **Overall Impression:** Provide a qualitative summary of the candidate’s performance, supported by specific examples from their responses.  
5. **Key Observations:** Highlight any notable strengths or weaknesses, explaining why they stood out.  

Please format your response in a detailed manner. Also, this is interviewer-tailored, so do not provide recommendations for the candidate.  

"""
    
    print(f"🔍 Sending transcription for analysis...")

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": llama_prompt}],
            temperature=0.7,
            max_tokens=4096
        )

        analysis_result = response.choices[0].message.content.strip()
        print(f"✅ Analysis Successful: {analysis_result[:200]}...")  # Print first 200 characters
        return analysis_result

    except Exception as e:
        print(f"❌ Error generating interview analysis: {e}")
        return f"Error generating interview analysis: {e}"






def generate_heatmap(video_path, heatmap_scale=4, stroke_size=5):
    FACE_LANDMARKS = [4, 152, 263, 33, 287, 57]
    EYE_LANDMARKS = [468, 473]
    MODEL_POINTS = np.array([
        (0.0, 0.0, 0.0),        # Nose tip
        (0, -63.6, -12.5),      # Chin
        (-43.3, 32.7, -26),     # Left eye outer corner
        (43.3, 32.7, -26),      # Right eye outer corner
        (-28.9, -28.9, -24.1),  # Left mouth corner
        (28.9, -28.9, -24.1)    # Right mouth corner
    ], dtype="double")

    ALPHA = 0.2
    smoothed_gaze = None

    # Ensure heatmap directory exists
    heatmap_dir = os.path.join(settings.MEDIA_ROOT, 'heatmaps')
    os.makedirs(heatmap_dir, exist_ok=True)

    video_filename = os.path.basename(video_path).split('.')[0]
    heatmap_filename = f"heatmap_{video_filename}.jpg"
    heatmap_path = os.path.join(heatmap_dir, heatmap_filename)
    heatmap_url = f"{settings.MEDIA_URL}heatmaps/{heatmap_filename}"

    # Initialize MediaPipe FaceMesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # High-resolution heatmap
    heatmap_size = (frame_height * heatmap_scale, frame_width * heatmap_scale)
    heatmap = np.zeros(heatmap_size, dtype=np.float32)

    # Camera intrinsic parameters
    focal_length = frame_width
    center = (frame_width / 2, frame_height / 2)
    camera_matrix = np.array([[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]], dtype="double")
    dist_coeffs = np.zeros((4, 1))

    def low_pass_filter(current_gaze):
        nonlocal smoothed_gaze
        if smoothed_gaze is None:
            smoothed_gaze = current_gaze
        else:
            smoothed_gaze = ALPHA * current_gaze + (1 - ALPHA) * smoothed_gaze
        return smoothed_gaze

    def relative(landmark, shape):
        return int(landmark.x * shape[1]), int(landmark.y * shape[0])

    def get_image_points(landmarks, frame_shape):
        return np.array([relative(landmarks.landmark[i], frame_shape) for i in FACE_LANDMARKS], dtype="double")

    def gaze(frame, points):
        nonlocal heatmap
        image_points = get_image_points(points, frame.shape)

        success, rotation_vector, translation_vector = cv2.solvePnP(
            MODEL_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )
        if not success:
            return

        left_pupil = relative(points.landmark[EYE_LANDMARKS[0]], frame.shape)
        current_gaze = np.array(left_pupil)
        smoothed_gaze = low_pass_filter(current_gaze)

        # Scale coordinates to high-resolution heatmap
        y, x = int(smoothed_gaze[1] * heatmap_scale), int(smoothed_gaze[0] * heatmap_scale)
        if 0 <= y < heatmap_size[0] and 0 <= x < heatmap_size[1]:
            cv2.circle(heatmap, (x, y), stroke_size, (1,), -1)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        right_half = frame[:, width // 2:]  # Crop right side

        image_rgb = cv2.cvtColor(right_half, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image_rgb)

        if results.multi_face_landmarks:
            gaze(right_half, results.multi_face_landmarks[0])

    cap.release()

    if heatmap is not None:
        # Normalize and blur for smooth strokes
        heatmap_blur = cv2.GaussianBlur(heatmap, (21, 21), 0)
        heatmap_norm = cv2.normalize(heatmap_blur, None, 0, 255, cv2.NORM_MINMAX)
        heatmap_color = cv2.applyColorMap(np.uint8(heatmap_norm), cv2.COLORMAP_JET)

        # Save high-resolution heatmap
        cv2.imwrite(heatmap_path, heatmap_color)
        return heatmap_url

    return None








client = Groq(api_key=os.environ.get("GROQ_API_KEY"))  # Replace with your Groq API key

def format_time(seconds):
    """Convert seconds to MM:SS format."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def analyze_video_emotions(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return []

    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(frame_rate * 2)  # Process every 2 seconds
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    frame_count = 0
    stress_history = []
    results = []

    current_emotion = None
    start_time = 0
    accumulated_confidence = []
    accumulated_stress = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        right_half = frame[:, width // 2:]
        timestamp = frame_count / frame_rate

        if frame_count % frame_interval == 0:  # Process every 2 seconds
            try:
                analysis = DeepFace.analyze(right_half, actions=['emotion'], enforce_detection=False)
                emotions = analysis[0]['emotion']

                # Normalize confidence values
                total_score = sum(emotions.values())
                if total_score > 0:
                    emotions = {key: (value / total_score) * 100 for key, value in emotions.items()}

                dominant_emotion = max(emotions, key=emotions.get)
                confidence = round(emotions[dominant_emotion], 2)

                # Stress calculation using weighted negative emotion scores
                stress_weights = {"angry": 1.0, "fear": 1.2, "sad": 0.8, "disgust": 1.1}
                positive_weights = {"happy": -0.5, "neutral": -0.3, "surprise": -0.2}

                weighted_stress = sum(stress_weights.get(e, 0) * emotions.get(e, 0) for e in stress_weights)
                weighted_stress += sum(positive_weights.get(e, 0) * emotions.get(e, 0) for e in positive_weights)
                stress_level = round(max(0, min(100, weighted_stress)), 2)

                # Rolling average smoothing for stress
                stress_history.append(stress_level)
                if len(stress_history) > 5:
                    stress_history.pop(0)

                stress_level = round(np.mean(stress_history), 2)

                # Emotion tracking and segment logging
                if dominant_emotion != current_emotion:
                    if current_emotion is not None:
                        avg_confidence = round(np.mean(accumulated_confidence), 2)
                        avg_stress = round(np.mean(accumulated_stress), 2)
                        start_str = format_time(start_time)
                        end_str = format_time(timestamp)
                        results.append((start_str, end_str, current_emotion, avg_confidence, avg_stress))
                        print(f"{start_str} - {end_str} | {current_emotion} | {avg_confidence}% | {avg_stress}%")

                    # Reset for new emotion
                    current_emotion = dominant_emotion
                    start_time = timestamp
                    accumulated_confidence = [confidence]
                    accumulated_stress = [stress_level]
                else:
                    accumulated_confidence.append(confidence)
                    accumulated_stress.append(stress_level)

            except Exception as e:
                print("Error processing frame:", e)

        frame_count += 1

    # Store last recorded segment
    if current_emotion is not None:
        avg_confidence = round(np.mean(accumulated_confidence), 2)
        avg_stress = round(np.mean(accumulated_stress), 2)
        start_str = format_time(start_time)
        end_str = format_time(timestamp)
        results.append((start_str, end_str, current_emotion, avg_confidence, avg_stress))
        print(f"{start_str} - {end_str} | {current_emotion} | {avg_confidence}% | {avg_stress}%")

    cap.release()
    return results

def generate_interview_analysis(emotion_data):
    """Generate interview analysis using Groq API."""
    template = (
        "You are an experienced interviewer tasked with analyzing a candidate's performance during an interview based on their emotional states, confidence levels, and stress levels. "
        "Below is the data collected during the interview:\n\n"
        "**Emotion, Confidence, and Stress Data:**\n"
        "{emotion_data}\n\n"
        "**Instructions for Analysis:**\n"
        "1. Provide a general overview of the candidate's emotional states during the interview. Highlight any significant trends or shifts in emotions.\n"
        "2. Analyze the candidate's confidence levels. Were they consistently confident, or did their confidence fluctuate? If so, when and why?\n"
        "3. Evaluate the candidate's stress levels. Were there moments of high stress? If so, how did the candidate handle it?\n"
        "4. Based on the data, provide insights into the candidate's overall performance. Were they calm and composed, or did they struggle with certain emotions or stress?\n"
        "**Formatting Rules:**\n"
        "- Organize your analysis into clear sections: 'Emotional Analysis', 'Confidence Analysis', 'Stress Analysis', 'Overall Performance'.\n"
        "- Be concise and professional in your analysis.\n"
        "- Do not include any additional comments or explanations beyond the specified instructions.\n"
    )

    # Format the template with the emotion data
    formatted_data = "\n".join([f"{start} - {end}: {emotion} (Confidence: {confidence}%, Stress: {stress}%)" for start, end, emotion, confidence, stress in emotion_data])
    prompt = template.format(emotion_data=formatted_data)

    try:
        # Send request to the Groq API
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Groq model choice
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,  # Lower temperature for more focused analysis
            max_tokens=4096,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Collect streaming response progressively
        response_chunks = []
        for message in completion:
            chunk = message.choices[0].delta.content or ""
            response_chunks.append(chunk)

        # Join all chunks into a complete response
        full_response = "".join(response_chunks)
        return full_response.strip()

    except Exception as e:
        return f"Error generating interview analysis: {e}"





def generate_overall_report(audio_analysis, emotion_analysis):
    """Generate an overall report combining audio and emotion analysis using Groq API."""
    template = (
        "You are an experienced interviewer tasked with generating an overall report for a candidate's performance during an interview. "
        "Below are the results of the audio analysis and emotion analysis:\n\n"
        "**Audio Analysis:**\n"
        "{audio_analysis}\n\n"
        "**Emotion Analysis:**\n"
        "{emotion_analysis}\n\n"
        "**Instructions for the Overall Report:**\n"
        "1. Provide a general overview of the candidate's performance based on the combined analysis.\n"
        "2. Highlight key strengths and weaknesses identified in both the audio and emotion analysis.\n"
        "3. Suggest whether the candidate should be hired or not, based on their performance.\n"
        "4. Provide a detailed explanation for your recommendation.\n"
        "**Formatting Rules:**\n"
        "- Organize your report into clear sections: 'Overview', 'Strengths and Weaknesses', 'Recommendation', and 'Explanation'.\n"
        "- Be concise and professional in your analysis.\n"
        "- Do not include any additional comments or explanations beyond the specified instructions.\n"
    )

    # Format the template with the audio and emotion analysis
    prompt = template.format(audio_analysis=audio_analysis, emotion_analysis=emotion_analysis)

    try:
        # Send request to the Groq API
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Groq model choice
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,  # Lower temperature for more focused analysis
            max_tokens=4096,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Collect streaming response progressively
        response_chunks = []
        for message in completion:
            chunk = message.choices[0].delta.content or ""
            response_chunks.append(chunk)

        # Join all chunks into a complete response
        full_response = "".join(response_chunks)
        return full_response.strip()

    except Exception as e:
        return f"Error generating overall report: {e}"