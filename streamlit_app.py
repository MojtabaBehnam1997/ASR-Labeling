import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

def main():
    st.title("ASR Labeling Platform")
    
    # File upload section
    with st.expander("Upload Audio"):
        uploaded_file = st.file_uploader("Choose audio file", type=["wav", "mp3"])
        if uploaded_file and st.button("Upload"):
            files = {"file": uploaded_file}
            response = requests.post(f"{BACKEND_URL}/upload/", files=files)
            st.write(response.json())

    # File listing section
    with st.expander("View Files"):
        response = requests.get(f"{BACKEND_URL}/files/")
        if response.status_code == 200:
            files = response.json()
            st.table(files)
        else:
            st.error("Failed to fetch files")

if __name__ == "__main__":
    main()