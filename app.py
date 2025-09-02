import streamlit as st
import pdfplumber
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import io
import base64

# This function applies a simple CSS style for a background color.
# It replaces the need for an external image file.
def set_background_style():
    """Sets a simple gradient background style."""
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(to right, #4facfe, #00f2fe);
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            color: white;
        }
        /* Main title, labels and markdown headers white */
        h1, h2, h3, h4, h5, h6, label, .stMarkdown h1, .stMarkdown h2 {
            color: white !important;
        }
        /* Make radio option labels white */
        div.stRadio > label > div {
            color: white !important;
        }
        /* Textarea container and input elements with transparent background */
        div.stTextarea, textarea, input, select {
            background-color: rgba(255, 255, 255, 0.2) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px;
        }
        textarea::placeholder {
            color: rgba(255, 255, 255, 0.7) !important;
            opacity: 1;
        }
        .st-emotion-cache-1c7y2re {
            background-color: transparent !important;
        }
        /* Sidebar styling */
        .stSidebar label,
        .stSidebar > div > div > label,
        .stSidebar div[data-testid="stMarkdownContainer"] > p {
            color: black !important;
        }
        .stSidebar div[role="combobox"] {
            color: black !important;
        }
        /* Button styling */
        button {
            background-color: rgba(255, 215, 128, 0.85) !important;
            color: #2f2f2f !important;
            font-weight: 600;
            border-radius: 4px;
            border: none;
            padding: 6px 12px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        button:hover {
            background-color: rgba(255, 215, 128, 1) !important;
        }
        </style>
        """, unsafe_allow_html=True)

# Set the page title and apply the background style
st.set_page_config(page_title="Text to Speech Converter")
set_background_style()

# Main app title
st.title("Text to Speech Converter")

# Sidebar for audio customization
st.sidebar.title("Audio Customization")
voice = st.sidebar.selectbox("Select Voice", [
    "en-US_AllisonV3Voice",
    "en-US_LisaVoice",
    "en-US_MichaelV3Voice",
    "en-GB_KateV3Voice",
    "es-ES_EnriqueV3Voice"
])
pitch = st.sidebar.slider("Pitch (%)", -50, 50, 0)

# Input mode selection
input_mode = st.radio("Input Mode:", ["Write Text", "Upload File"])
text = ""

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            pt = page.extract_text()
            if pt:
                text += pt + "\n"
    return text

# Container for text input or file uploader
with st.container():
    if input_mode == "Write Text":
        text = st.text_area("Enter text here", height=250)
    elif input_mode == "Upload File":
        uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                text = extract_text_from_pdf(uploaded_file)
            else:
                text = uploaded_file.read().decode("utf-8")
            st.subheader("Extracted Text Preview")
            st.write(text[:500] + "...")

# IBM Watson Text to Speech credentials
# IMPORTANT: Replace these with your actual credentials.
# Do not share them publicly.
apikey = "pHmW-cWHbi-uA4l9TBJWeEG34_ELLk5crXaQQfNK2HSW"
url = "https://api.au-syd.text-to-speech.watson.cloud.ibm.com/instances/4718a086-a601-49de-8682-3c2cc846c54e"

authenticator = IAMAuthenticator(apikey)
tts = TextToSpeechV1(authenticator=authenticator)
tts.set_service_url(url)

# Button to generate the audiobook
if st.button("Generate Audiobook") and text.strip():
    with st.spinner("Generating audio..."):
        # SSML for controlling pitch
        ssml_text = f"""<speak><prosody pitch="{pitch}%">{text}</prosody></speak>"""
        try:
            response = tts.synthesize(ssml_text, accept="audio/wav", voice=voice).get_result()
            audio_bytes = response.content
            st.session_state['audio_buffer'] = io.BytesIO(audio_bytes)
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.pop('audio_buffer', None)

# Audio playback and download controls
if 'audio_buffer' in st.session_state and st.session_state['audio_buffer']:
    st.audio(st.session_state['audio_buffer'], format="audio/wav")
    st.download_button(
        label="Download Audiobook",
        data=st.session_state['audio_buffer'],
        file_name="audiobook.wav",
        mime="audio/wav"
    )
else:
    st.info("Generate audio to see playback and download controls.")
