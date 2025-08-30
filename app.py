import streamlit as st
import pdfplumber
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import io
import base64

# Set the page title (first Streamlit command)
st.set_page_config(page_title="Text to Speech Converter")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
    }}
    /* Main title, labels and markdown headers white */
    h1, h2, h3, h4, h5, h6, label, .stMarkdown h1, .stMarkdown h2 {{
        color: white !important;
    }}
    /* Make radio option labels for Write Text and Upload File white */
    div.stRadio > label > div {{
        color: white !important;
    }}
    /* Textarea container and input elements with transparent background */
    div.stTextarea, textarea, input, select {{
        background-color: rgba(255, 105, 180, 0.6) !important;
        color: #333333 !important;
        border: none !important;
        border-radius: 8px;
    }}
    /* This targets the internal Streamlit component to ensure transparency */
    .st-emotion-cache-1c7y2re {{
        background-color: transparent !important;
    }}
    textarea::placeholder {{
        color: rgba(255, 154, 206, 0.8) !important;
        opacity: 1;
    }}
    /* Sidebar labels black except custom header */
    .stSidebar label, 
    .stSidebar > div > div > label, 
    .stSidebar div[data-testid="stMarkdownContainer"] > p {{
        color: black !important;
    }}
    /* Sidebar voice dropdown option text black */
    .stSidebar div[role="combobox"] {{
        color: black !important;
    }}
    div[data-testid="stVerticalBlock"], div[data-testid="stSidebar"] > div:first-child {{
        background-color: rgba(0,0,0,0) !important;
        box-shadow: none !important;
    }}
    div[data-testid="container-text-entry"],
    div[data-testid="container-audio-controls"],
    div[data-testid="container-download"],
    div[data-testid="container-info-message"] {{
        background-color: rgba(0,0,0,0) !important;
        box-shadow: none !important;
        padding: 0;
    }}
    /* Buttons styling */
    button {{
        background-color: rgba(255, 215, 128, 0.85) !important;
        color: #2f2f2f !important;
        font-weight: 600;
        border-radius: 4px;
        border: none;
        padding: 6px 12px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }}
    button:hover {{
        background-color: rgba(255, 215, 128, 1) !important;
    }}
    .custom-audio-header {{
        color: black !important;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 0.5em;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Set your background image path (replace with your own path)
image_path = r"C:\Users\udayk\OneDrive\Desktop\texttoaudioibm\bg.jpg"
set_png_as_page_bg(image_path)

# Main app title
st.title("Text to Speech Converter")

# Sidebar header with custom black color
st.sidebar.markdown('<div class="custom-audio-header">Audio Customization</div>', unsafe_allow_html=True)

# Sidebar inputs
voice = st.sidebar.selectbox("Select Voice", [
    "en-US_AllisonV3Voice",
    "en-US_LisaVoice",
    "en-US_MichaelV3Voice",
    "en-GB_KateV3Voice",
    "es-ES_EnriqueV3Voice"
])

pitch = st.sidebar.slider("Pitch (%)", -50, 50, 0)

input_mode = st.radio("Input Mode:", ["Write Text", "Upload File"])

text = ""

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            pt = page.extract_text()
            if pt:
                text += pt + "\n"
    return text

with st.container(key="container-text-entry"):
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

# IBM Watson TTS credentials
apikey = "oamD3B0KQy_iX8LNtEfIzzwhn_R-zqQkmwqebfrDO2LW"  # Replace with your actual API key
url = "https://api.au-syd.text-to-speech.watson.cloud.ibm.com/instances/6de164ed-aa7c-4ee6-b350-03dd0d0b3932"  # Replace with your actual service URL

authenticator = IAMAuthenticator(apikey)
tts = TextToSpeechV1(authenticator=authenticator)
tts.set_service_url(url)

if st.button("Generate Audiobook") and text.strip():
    with st.spinner("Generating audio..."):
        ssml_text = f"""<speak><prosody pitch="{pitch}%">{text}</prosody></speak>"""
        response = tts.synthesize(ssml_text, accept="audio/wav", voice=voice).get_result()
        audio_bytes = response.content
        st.session_state['audio_buffer'] = io.BytesIO(audio_bytes)

if 'audio_buffer' in st.session_state:
    with st.container(key="container-audio-controls"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Play Audio"):
                st.audio(st.session_state['audio_buffer'])
                st.session_state['audio_buffer'].seek(0)
        with col2:
            if st.button("Stop Audio"):
                st.session_state.pop('audio_buffer', None)
                st.experimental_rerun()

    with st.container(key="container-download"):
        if 'audio_buffer' in st.session_state:
            st.download_button(
                label="Download Audiobook",
                data=st.session_state['audio_buffer'],
                file_name="audiobook.wav",
                mime="audio/wav"
            )
else:
    with st.container(key="container-info-message"):
        st.info("Generate audio to see playback controls.")
