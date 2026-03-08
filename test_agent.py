import os
import sys

# Pre-load keys since we are testing locally without Streamlit secrets
with open("bq-key.json", "r") as f:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bq-key.json"

import streamlit as st
import os

if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

# Grab the Google Key from the terminal or test
from core_brain import get_omnicortex_brain
from langchain_core.messages import HumanMessage

def test():
    try:
        print("Loading OmniCortex Brain...")
        brain = get_omnicortex_brain()
        
        prompt = "what was the status of kse100 index on friday closing"
        print(f"\nUser: {prompt}\n")
        
        response = brain.invoke(
            {"messages": [HumanMessage(content=prompt)]}
        )
        
        print("\nOmniCortex Output:\n===================\n")
        print(response["messages"][-1].content)
        print("\n===================\n")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
