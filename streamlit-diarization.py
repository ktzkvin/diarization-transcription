import streamlit as st
from streamlit_mic_recorder import mic_recorder
import os
from pyannote.audio import Pipeline
from huggingface_hub import login

# Connexion à Hugging Face pour le token d'authentification via un fichier .token
TOKEN_FILE = ".token"

def get_token_from_file():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return file.read().strip()
    return None

def save_token_to_file(token):
    with open(TOKEN_FILE, "w") as file:
        file.write(token)

# Récupérer le token
hf_token = get_token_from_file()

if hf_token:
    st.success("Token loaded from .token file.")
    login(token=hf_token)
    st.session_state.hf_token = hf_token
else:
    manual_token = st.text_input("Enter your Hugging Face Token:", type="password")
    if st.button("Login"):
        if manual_token:
            login(token=manual_token)
            save_token_to_file(manual_token)
            st.session_state.hf_token = manual_token
            st.success("Successfully logged in and token saved!")
        else:
            st.warning("Please provide a valid Hugging Face Token.")

# Configuration de PyAnnote diarization
if "hf_token" in st.session_state:
    st.header("Speaker Diarization Process")
    diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=st.session_state.hf_token)

    # Options avec menus déroulants
    st.subheader("⚙️ Settings")

    speaker_options = [""] + [str(i) for i in range(1, 11)]  # "vide" + 1 à 10

    # Gestion des interdépendances
    if "num_speakers" not in st.session_state:
        st.session_state.num_speakers = ""
    if "min_speakers" not in st.session_state:
        st.session_state.min_speakers = ""
    if "max_speakers" not in st.session_state:
        st.session_state.max_speakers = ""

    def update_num_speakers():
        st.session_state.min_speakers = ""
        st.session_state.max_speakers = ""

    def update_min_max_speakers():
        st.session_state.num_speakers = ""

    # Champs avec interdépendances
    col1, col2, col3 = st.columns(3)
    with col1:
        num_speakers = st.selectbox(
            "Number of Speakers", speaker_options, 
            key="num_speakers", on_change=update_num_speakers
        )
    with col2:
        min_speakers = st.selectbox(
            "Minimum Speakers", speaker_options, 
            key="min_speakers", on_change=update_min_max_speakers
        )
    with col3:
        max_speakers = st.selectbox(
            "Maximum Speakers", speaker_options, 
            key="max_speakers", on_change=update_min_max_speakers
        )

    # Section 1: Enregistrement audio via le microphone
    st.header("Record Audio from Microphone")
    st.write("Click below to record your mic.")

    # Enregistrement de l'audio
    audio = mic_recorder(
        start_prompt="Start recording",
        stop_prompt="Stop recording",
        format="wav"
    )

    chosen_audio_path = None

    if audio and "bytes" in audio:
        chosen_audio_path = "streamlit-records/output.wav"
        with open(chosen_audio_path, "wb") as f:
            f.write(audio["bytes"])
        st.audio(audio["bytes"], format='audio/wav')
        st.success(f"Audio saved as '{chosen_audio_path}'.")
    else:
        st.warning("No audio recorded.")

    st.markdown("---")

    # Section 2: Choisir une source audio existante ou importer un fichier
    st.header("Choose Audio Source")

    if st.button("Import Your Audio"):
        uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3"])
        if uploaded_file is not None:
            chosen_audio_path = "streamlit-records/uploaded_audio.wav"
            with open(chosen_audio_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            st.audio(uploaded_file, format='audio/wav')
            st.success(f"Uploaded audio saved as '{chosen_audio_path}'.")

    if st.button("Use Existing Audio"):
        chosen_audio_path = "audios/audio_DER.wav"
        st.write(f"Using default audio: {chosen_audio_path}")
        st.audio(chosen_audio_path, format='audio/wav')

    st.markdown("---")

    # Lancer la diarization PyAnnote
    if chosen_audio_path and os.path.exists(chosen_audio_path):
        st.header("Running Speaker Diarization")
        with st.spinner("Processing the audio with PyAnnote... This may take a while."):
            diarization_args = {}
            if st.session_state.num_speakers:
                diarization_args["num_speakers"] = int(st.session_state.num_speakers)
            if st.session_state.min_speakers:
                diarization_args["min_speakers"] = int(st.session_state.min_speakers)
            if st.session_state.max_speakers:
                diarization_args["max_speakers"] = int(st.session_state.max_speakers)

            diarization_result = diarization_pipeline(chosen_audio_path, **diarization_args)

        # Afficher les résultats de la diarization
        st.success("Speaker Diarization Completed!")
        diarization_result

    else:
        st.warning("No audio file selected or processed.")
else:
    st.warning("Please log in to Hugging Face to proceed.")