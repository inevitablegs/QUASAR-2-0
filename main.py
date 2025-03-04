import os
from groq import Groq
import pdfplumber  # Library to extract text from PDF

# Get the API key from system environment variables
API_KEY = os.environ.get("GROQ_API_KEY")

# Check if API key is loaded successfully
if not API_KEY:
    raise ValueError("API key not found. Please set GROQ_API_KEY as an environment variable.")


# Template for generating interview questions from a resume
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
)




# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file_path):
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""  # Extract text from each page
            return text.strip()
    except Exception as e:
        return f"Error reading PDF file: {e}"

# Function to generate interview questions from a resume
def generate_interview_questions(pdf_file_path):
    # Initialize the Groq client with API key
    client = Groq(api_key=API_KEY)

    # Extract text from the PDF resume
    resume_content = extract_text_from_pdf(pdf_file_path)
    if resume_content.startswith("Error"):
        return resume_content  # Return error message if PDF reading fails

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

# Specify the path to the PDF resume file
pdf_file_path = "SaraRes.pdf"

# Call the function and print the result
result = generate_interview_questions(pdf_file_path)
print(result)