import streamlit as st
import re
from PyPDF2 import PdfReader
from streamlit.components.v1 import html
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
#from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import LLMChain
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Flowable, FrameBreak, KeepTogether, PageBreak, Spacer
from reportlab.platypus import Frame, PageTemplate, KeepInFrame
from reportlab.lib.units import cm
from reportlab.platypus import (Table, TableStyle, BaseDocTemplate)
from xhtml2pdf import pisa
from bs4 import BeautifulSoup
from pdf2docx import Converter
import html2docx
import io

st.set_page_config(page_title="Bid Generator ", layout="wide")

background_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Underwater Bubble Background</title>
    <style>
        body {
            margin: 0;
            overflow: hidden;
            background: linear-gradient(45deg, #161d20 5%, #161d29 47.5%,#161d53 ,#161d52 95%);
         }
        canvas {
            display: block;
        }
    </style>
</head>
<body>
    <canvas id="bubblefield"></canvas>
    <script>
        // Setup canvas
        const canvas = document.getElementById('bubblefield');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        // Arrays to store bubbles
        let bubbles = [];
        const numBubbles = 100;
        const glowDuration = 1000; // Glow duration in milliseconds

        // Function to initialize bubbles
        function initializeBubbles() {
            for (let i = 0; i < numBubbles; i++) {
                bubbles.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    radius: Math.random() * 5 + 2, // Adjusted smaller bubble size
                    speedX: Math.random() * 0.5 - 0.25, // Adjusted slower speed
                    speedY: Math.random() * 0.5 - 0.25, // Adjusted slower speed
                    glow: false,
                    glowStart: 0
                });
            }
        }

        // Draw function
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw bubbles
            for (let i = 0; i < numBubbles; i++) {
                let bubble = bubbles[i];

                // Calculate glow intensity based on time elapsed since glow started
                let glowIntensity = 0;
                if (bubble.glow) {
                    let elapsedTime = Date.now() - bubble.glowStart;
                    glowIntensity = 0.8 * (1 - elapsedTime / glowDuration); // Decreasing glow intensity over time
                    if (elapsedTime >= glowDuration) {
                        bubble.glow = false; // Reset glow state after glow duration
                    }
                }

                ctx.beginPath();
                ctx.arc(bubble.x, bubble.y, bubble.radius, 0, Math.PI * 2);

                // Set glow effect if bubble should glow
                if (glowIntensity > 0) {
                    let gradient = ctx.createRadialGradient(bubble.x, bubble.y, 0, bubble.x, bubble.y, bubble.radius);
                    gradient.addColorStop(0, `rgba(255, 255, 255, ${glowIntensity})`);
                    gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
                    ctx.fillStyle = gradient;
                } else {
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.1)'; // Adjusted bubble transparency to 70%
                }
                
                ctx.fill();

                // Move bubbles based on speed
                bubble.x += bubble.speedX;
                bubble.y += bubble.speedY;

                // Wrap bubbles around edges of canvas
                if (bubble.x < -bubble.radius) {
                    bubble.x = canvas.width + bubble.radius;
                }
                if (bubble.x > canvas.width + bubble.radius) {
                    bubble.x = -bubble.radius;
                }
                if (bubble.y < -bubble.radius) {
                    bubble.y = canvas.height + bubble.radius;
                }
                if (bubble.y > canvas.height + bubble.radius) {
                    bubble.y = -bubble.radius;
                }
            }
            
            requestAnimationFrame(draw);
        }

        // Mouse move event listener to move bubbles towards cursor
        canvas.addEventListener('mousemove', function(event) {
            let mouseX = event.clientX;
            let mouseY = event.clientY;
            for (let i = 0; i < numBubbles; i++) {
                let bubble = bubbles[i];
                let dx = mouseX - bubble.x;
                let dy = mouseY - bubble.y;
                let distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < 50) {
                    bubble.speedX = dx * 0.01;
                    bubble.speedY = dy * 0.01;
                    if (!bubble.glow) {
                        bubble.glow = true;
                        bubble.glowStart = Date.now();
                    }
                }
            }
        });

        // Start animation
        initializeBubbles();
        draw();

        // Resize canvas on window resize
        window.addEventListener('resize', function() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            initializeBubbles();  // Reinitialize bubbles on resize
        });
    </script>
</body>
</html>
"""

# Embed the HTML code into the Streamlit app
st.components.v1.html(background_html, height=1000)
st.markdown("""
<style>
    iframe {
        position: fixed;
        left: 0;
        right: 0;
        top: 0;
        bottom: 0;
        border: none;
        height: 100%;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        @keyframes gradientAnimation {
            0% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
            100% {
                background-position: 0% 50%;
            }
        }

        .animated-gradient-text {
            font-family: "Graphik Semibold";
            font-size: 42px;
            background: linear-gradient(45deg, #22ebe8 30%, #dc14b7 55%, #fe647b 20%);
            background-size: 300% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradientAnimation 20s ease-in-out infinite;
        }
    </style>
    <p class="animated-gradient-text">
        Bid Creation Bot : Generates Bid Document!
    </p>
""", unsafe_allow_html=True)




# This is the first API key input; no need to repeat it in the main function.
api_key = st.secrets['GEMINI_API_KEY']
#api_key = 'AIzaSyCiPGxwD04JwxifewrYiqzufyd25VjKBkw'

if 'responses' not in st.session_state:
    st.session_state['responses'] = ["How can I assist you?"]

if 'requests' not in st.session_state:
    st.session_state['requests'] = []


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        print("Reading PDF --->", pdf)
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=40000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks, api_key):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """You are an intelligent Bid assistant. Your works is to help write RFP document on a given topics. Write a detailed RFP as per user question and return the result formatted in HTML document. RFP should be as detailed as possible and should contain all the sections which a typical RFP has.
            Context for answer: {context}
            Question from user: {question}

        Include sections like:
        1. Introduction
        2. Purpose
        3. Scope of Work
        4. Proposal Guidelines
        5. Timeline
        6. Qualifications / Evaluation Criteria
        7. Proposal Submission Requirements
        8. Budget / Cost Proposal
        9. Terms and Conditions
        10. Contract Terms
        11. Contact Information
        12. Appendices / Attachments
        
        Your responses should be formatted in HTML document following the rules as listed below:
                    
        - <h2> tags For headers and <h4> tags for sub-headers
        - you must use <ul> tags for unordered listings and <ol> for ordered listings
        - <b> tag for bolding of text
        - </br> tag for breakline
        - Follow all the other HTML syntax

        Response should only be in HTML document format like mentioned above keep the font size 14, you must use <ul> or <ol> tag wherver required without adding style tag for these two and just return the response with tags
        Use divider to seperate each section.
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=st.session_state.temperature, google_api_key=api_key)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    print("Prompt ***** --->", prompt)
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question, api_key):
    with st.spinner("Writing RFP ..."):
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
                #new_db = FAISS.load_local("faiss_index", embeddings)
                new_db = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)
                docs = new_db.similarity_search(user_question)
                chain = get_conversational_chain()
                response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
                #print("Response is....",response)
                para_ = response['output_text']
                response = response['output_text']
                fileName = 'output.pdf'
                #print("para_ printed here-------------------->>>",para_)
                soup = BeautifulSoup(para_, 'html.parser')
                # Extract the title
                para_title = soup.title.string
                pdf_path = fileName
                html_string ='''
                            <!DOCTYPE html>
                                <html lang="en">
                                <head>
                                    <meta charset="UTF-8" />
                                    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                                    <title>Document</title>
                                    <style>
                                    .header {
                                        background-color: #A020F0;
                                        color: #ffffff; /* White text */
                                        padding: 0 px;
                                        text-align: center;
                                        line-height: 1.5; 
                                        padding-top: 20 px;
                                        font-size: 22 px;
                                    }
                                    .subtitle {
                                        background-color: #D14BA1;
                                        color: #ffffff; 
                                        padding: 0 px;
                                        text-align: center;
                                        padding-top: 15 px;
                                        line-height: 1.5; 
                                        font-size: 18 px;
                                    }
                                    .content {
                                        padding: 0 px;
                                        line-height: 1.5; 
                                    }
                                    </style>
                                </head>
                                <body>
                                    <logo class="logo">
                                    <img src='https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Accenture.svg/2560px-Accenture.svg.png' width="80" height="30" />
                                    </logo>               
                                    <div class="header">
                                    <h1>Bid Creation Bot!</h1>
                                    </div>
                                    <div class="subtitle">
                                    <h3>''' + para_title + '''</h3>
                                    </div>

                                    <!-- content section -->
                                    <div class="content"> ''' + para_ + '''</div>
                                </body>
                                </html>
                            '''
                
                @st.experimental_dialog("Edit the RFP", width= 'large')
                def edit_report():
                    output_ = st.text_area("Edit your RFP", html_string)
                    if st.button("Submit"):
                        print("Inside submit button")
                        st.session_state.vote = output_
                        print("Opening pdf to write")
                        with open(pdf_path, "wb") as pdf_file:
                            print("PDF opened")
                        
                            pisa_status = pisa.CreatePDF(output_, dest=pdf_file)
                        print("done with RFP")
                        st.write("RFP Generated Successfully. Please check directory ", fileName)
                        st.success("RFP Delivered to the location !!!")
                        #st.rerun()
                edit_report()
                st.success("RFP Delivered to the location !!!")

                        

fname = "output.pdf"
pdf_path = "output.pdf"
docx_path = "output.docx"
cv = Converter(pdf_path)
cv.convert(docx_path)
cv.close()

with open(fname, "rb") as f:
    st.download_button("Download .pdf version of RFP!", f, fname)

if st.button("Convert and Download DOCX"):
    # Convert HTML to DOCX using html2docx
    docx_buffer = io.BytesIO()
    html2docx.convert(output_, docx_buffer)
    docx_buffer.seek(0)  # Rewind the buffer
                    
    # Provide the download button
    st.download_button(
    label="Download DOCX",
    data=docx_buffer,
    file_name="output.docx",
    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# with open(docx_path, "rb") as docx_file:
#     docx_bytes = docx_file.read()
#     st.download_button("Download .docx version of RFP!", data=docx_bytes, file_name="output.docx")




def get_conversation_string():
    conversation_string = ""
    for i in range(len(st.session_state['responses'])-1):
        
        conversation_string += "Human: "+st.session_state['requests'][i] + "\n"
        conversation_string += "Bot: "+ st.session_state['responses'][i+1] + "\n"
    return conversation_string

st.markdown("""
<style>
.small-font {
    font-size:13px !important;
    color: lightgrey !important;
}
</style>
""", unsafe_allow_html=True)

def main():
    st.header("Bid Creation Bot")

    user_question = st.text_input("What RFP do you want to generate?", key="user_question")
    if user_question:
        m = st.markdown("""
        <style>
        div.stButton > button:first-child {
            background:linear-gradient(45deg, #c9024b 45%, #ba0158 55%, #cd006d 70%);
            
            color: white;

        }

        div.stButton > button:hover {
            background:linear-gradient(45deg, #ce026f 45%, #970e79 55%, #6c028d 70%);
            background-color:#ce1126;
        }

        div.stButton > button:active {
            position:relative;
            top:3px;
        }

        </style>""", unsafe_allow_html=True)
        if st.button("Generate RFP"):
            if user_question and api_key:  # Ensure API key and user question are provided
                user_input(user_question, api_key)
   
    with st.sidebar:
        st.image("https://www.vgen.it/wp-content/uploads/2021/04/logo-accenture-ludo.png", width=120)
        st.markdown("")
        st.markdown("")
        st.title("Bid Creation Bot")
        pdf_docs = st.file_uploader("Upload your Files and Click on the Submit & Process Button", accept_multiple_files=True, key="pdf_uploader")
        if st.button("Submit & Process", key="process_button") and api_key:  # Check if API key is provided before processing
            with st.spinner("Reading & Processing Content..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks, api_key)
                st.success("Done")

        with st.expander("**Models and parameters**"):

            # model parameters
            st.session_state.temperature = st.slider(
                "temperature",
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.1,
            )
            st.session_state.top_p = st.slider(
                "top_p",
                min_value=0.1,
                max_value=1.0,
                value=0.95,
                step=0.05,
            )

        

if __name__ == "__main__":
    st.markdown('''<style>
        .stApp > header {
        background-color: transparent;
    }
    .stApp {
        background: linear-gradient(45deg, #0a1621 20%, #0E1117 45%, #0E1117 55%, #3a5683 90%);
        animation: my_animation 20s ease infinite;
        background-size: 200% 200%;
        background-attachment: fixed;
    }
    @keyframes my_animation {
        0% {background-position: 0% 0%;}
        50% {background-position: 100% 100%;}
        100% {background-position: 0% 0%;}
    }
    [data-testid=stSidebar] {
        background: linear-gradient(360deg, #1a2631 95%, #161d29 10%);
    }
    div.stButton > button:first-child {
        background:linear-gradient(45deg, #c9024b 45%, #ba0158 55%, #cd006d 70%);
        color: white;
        border: none;
    }
    div.stButton > button:hover {
        background:linear-gradient(45deg, #ce026f 45%, #970e79 55%, #6c028d 70%);
        background-color:#ce1126;
    }
    div.stButton > button:active {
        position:relative;
        top:3px;
    }    

    </style>''', unsafe_allow_html=True)
    main()
