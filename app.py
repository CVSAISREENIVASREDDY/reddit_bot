import streamlit as st
import scrap
from model import RedditPersonaAnalyzer
import json 

API_KEY = st.secrets["api_key"]

st.set_page_config(page_title="Reddit Persona Analyzer", page_icon=":guardsman:", layout="wide")
st.title("Reddit Persona Analyzer") 

st.markdown("This app analyzes a Reddit user's posts and comments to build a persona.")

username = st.text_area("Enter your Reddit username:",
              placeholder="e.g., example_user")
if username:
    try:
        analyzer = RedditPersonaAnalyzer(username=username, api_key=API_KEY) 
        persona = analyzer.build_persona() 
        data = json.dumps(persona, indent=2, ensure_ascii=False) 
        st.json(data) 
    except Exception as e:
            st.error(f"An error occurred: {e}") 
else:
    st.warning("Please enter a valid Reddit username.") 

