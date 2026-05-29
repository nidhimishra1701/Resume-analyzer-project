from db import insert_data
import streamlit as st
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import fitz
import io
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", quiet=True)


def generate_suggestions(text, score):
    suggestions = []
    text = text.lower()

    # Sections
    if "project" not in text:
        suggestions.append("Add 2–3 strong projects with description.")

    if "experience" not in text:
        suggestions.append("Include internship or work experience.")

    # Skills
    skills = ["python", "sql", "excel", "machine learning"]
    for skill in skills:
        if skill not in text:
            suggestions.append(f"Add {skill} to improve job matching.")

    # Length
    if len(text) < 300:
        suggestions.append("Resume is too short. Add more details.")

    # Score-based
    if score < 50:
        suggestions.append("Your resume needs major improvement.")
    elif score < 75:
        suggestions.append("Your resume is good but can be improved.")
    else:
        suggestions.append("Strong resume! Minor improvements only.")

    return suggestions
st.set_page_config(page_title="Resume Analyzer", page_icon="📄", layout="wide")

# Custom CSS for minor tweaks
st.markdown("""
<style>
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4CAF50;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #A0AEC0;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/942/942748.png", width=100)
    st.header("📌 About")
    st.info("""
    This tool helps you:
    - Measure how your resume matches a job description
    - Identify important job keywords
    """)
    st.header("⚙️ How It works")
    st.write("""
    1. Upload your resume (PDF)
    2. Paste the job description
    3. Click **Analyze Match**
    4. Review score & match chart
    """)


def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text("text")
        doc.close()
        print("DEBUG:", text[:200])
        if not text.strip():
            st.error("Could not extract text from PDF.")
            return ""
        return text.strip()
    
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text)
    return " ".join([word for word in words if word not in stop_words])

def calculate_similarity(resume_text, job_description):
    resume_processed = remove_stopwords(clean_text(resume_text))
    job_processed = remove_stopwords(clean_text(job_description))
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resume_processed, job_processed])
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100
    return round(score, 2), resume_processed, job_processed

def generate_review(resume_text, similarity_score):
    word_count = len(resume_text.split())
    review = ""
    
    if word_count < 100:
        review += "Your resume is quite short, which might mean you are missing key details about your experiences. "
    elif word_count > 600:
        review += "Your resume is very detailed, but be careful not to make it too long for recruiters to quickly scan. "
    else:
        review += "Your resume has a great, professional length. "
        
    if similarity_score < 40:
        review += "However, the overall match with this specific job description is low. You should heavily tailor your resume to highlight the required skills."
    elif similarity_score < 70:
        review += "You have a solid foundation for this role! With a few tweaks to emphasize specific keywords, you'll be a great fit."
    else:
        review += "Fantastic! Your resume is highly aligned with this job description. You clearly have the right experience."
        
    return review

def main():
    st.markdown('<p class="main-header">📄 Resume & Job Match Analyzer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Upload your resume and paste a job description to see how well they match!</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        st.subheader("📥 Input Data")
        uploaded_file = st.file_uploader("Upload your resume (PDF)", type=['pdf'])
        job_description = st.text_area("Paste the job description", height=250)
        analyze_btn = st.button("✨ Analyze Match", use_container_width=True, type="primary")

        if analyze_btn:
            if not uploaded_file:
                st.warning("⚠️ Please upload your resume")
            elif not job_description:
                st.warning("⚠️ Please paste the job description")
            else:
                with st.spinner("Analyzing your resume...."):
                   score = st.session_state.get('similarity_score', 0)
                   resume_text = st.session_state.get('resume_review', "")
                   suggestions = generate_suggestions(resume_text, score)
                   if resume_text:
                        similarity_score, resume_processed, job_processed = calculate_similarity(resume_text, job_description)
                        resume_review = generate_review(resume_text, similarity_score)

                        st.session_state['resume_text'] = resume_text
                        st.session_state['score'] = similarity_score
                        st.session_state['resume_review'] = resume_review
                   else:
                        st.error("Could not extract text from PDF.")

        # Save Result section now moved correctly to the left column!
        if 'score' in st.session_state:
            st.markdown("---")
            with st.expander("💾 Save Result to Database", expanded=True):
                st.write("Save this match score to your MySQL database.")
                name = st.text_input("Enter Name")
                email = st.text_input("Enter Email")
                if st.button("Save Result", use_container_width=True):
                    insert_data(name, email, st.session_state['resume_text'], st.session_state['score'])
                    st.success("Saved to MySQL Database ✅")

    with col2:
        st.subheader("📊 Analysis Results")
        
        if 'score' in st.session_state:
            similarity_score = st.session_state['score']

            # Visuals
            st.metric("Match Score", f"{similarity_score:.2f}%")
            
            # Styled Progress bar
            if similarity_score < 40:
                st.error("Low Match. Consider tailoring your resume.")
                st.progress(int(similarity_score)/100)
            elif similarity_score < 70:
                st.warning("Good Match. Your resume aligns fairly well.")
                st.progress(int(similarity_score)/100)
            else:
                st.success("Excellent Match! Your resume strongly aligns.")
                st.progress(int(similarity_score)/100)

            st.markdown("---")
            st.write("**Match Visualization**")
            fig, ax = plt.subplots(figsize=(6, 0.5))
            
            # Set transparent background for matplotlib
            fig.patch.set_alpha(0.0)
            ax.set_facecolor('none')
            
            colors = ['#ff4b4b', '#ffa726', '#0f9d58']
            color_index = min(int(similarity_score // 33), 2)
            ax.barh([0], [similarity_score], color=colors[color_index])
            ax.set_xlim(0, 100)
            ax.set_yticks([])
            
            # Style text color for dark mode compatibility
            ax.spines['bottom'].set_color('#FFFFFF')
            ax.spines['top'].set_color('none')
            ax.spines['left'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.tick_params(axis='x', colors='#FFFFFF')

            st.pyplot(fig)
            
            st.markdown("---")
            st.subheader("📝 Resume Review")
            st.info(st.session_state['resume_review'])
            st.markdown("""
<div style="background-color:#fff3cd;padding:15px;border-radius:10px;margin-bottom:10px">
<h4>📌 Suggestions</h4>
</div>
""", unsafe_allow_html=True)
            st.subheader("📌 Suggestions for Improvement")

            if suggestions:
             for s in suggestions:
               st.warning(s)
            else:
              st.success("Your resume looks good!")
        else:
            st.info("👈 Upload your PDF and Job Description, then click Analyze to see results here.")

if __name__ == "__main__":
    main()  
