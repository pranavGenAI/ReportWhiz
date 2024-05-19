import streamlit as st
import re
from PyPDF2 import PdfReader
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

st.set_page_config(page_title="Report Generator ", layout="wide")

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
            background: linear-gradient(45deg, rgb(245, 58, 126) 30%, rgb(200, 1, 200) 55%, rgb(197, 45, 243) 20%);
            background-size: 300% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradientAnimation 10s ease-in-out infinite;
        }
    </style>
    <p class="animated-gradient-text">
        ReportWhiz: A report generation tool!
    </p>
""", unsafe_allow_html=True)

#st.image("https://media1.tenor.com/m/6o864GYN6wUAAAAC/interruption-sorry.gif", width=1000)
#st.image("https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjl2dGNiYThobHplMG81aGNqMjdsbWwwYWJmbTBncGp6dHFtZTFzMSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/CGP9713UVzQ0BQPhSf/giphy.gif", width=50)


# This is the first API key input; no need to repeat it in the main function.
api_key = st.secrets['GEMINI_API_KEY']
#api_key = 'AIzaSyAJT6_IYPjUtUyT14uzZ8BSON7rDul7Ab8'

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
    prompt_template = """You are an intelligent AI assistant. Your works is to help write reports on\
        a variety of topics. Write a detailed report as per user question and return the result formatted in HTML document.
            Context for answer: {context}
            Question from user: {question}

        Your responses should be formatted in HTML document following the rules as listed below:
                    
        - <h2> tags For headers and <h4> tags for sub-headers
        - <ul> tags for unordered listings and <ol> for ordered listings
        - <b> tag for bolding of text
        - </br> tag for breakline
        - Follow all the other HTML syntax

        Response should only be in HTML document format like mentioned above keep the font size 14 and just return the response with tags
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3, google_api_key=api_key)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    print("Prompt ***** --->", prompt)
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question, api_key):
    with st.spinner("Writing Report ..."):
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
                #new_db = FAISS.load_local("faiss_index", embeddings)
                new_db = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)
                docs = new_db.similarity_search(user_question)
                chain = get_conversational_chain()
                response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
                print("Response is....",response)
                para_ = response['output_text']
                response = response['output_text']
                fileName = 'https://github.com/pranavGenAI/ReportWhiz/tree/e165a5c380f32beda1bdd2582ca2070447fc800a/output/output.pdf'
                #fileName = 'output/output.pdf'
                # context_user_question = "Suggest the 6 word title for the text. Do not use tags while framing this response: " + response
                # subTitle = chain({"input_documents": docs,"question": context_user_question}, return_only_outputs=True)
                # subTitle = subTitle['output_text']
                # subTitle = subTitle.replace("*","")
                # subTitle = subTitle.replace("<b>","")
                # subTitle = subTitle.replace("</b>","")
                # para_ = para_.replace("*","")
                # para_ = para_.replace("<BR>","<BR/>")
                print("para_ printed here-------------------->>>",para_)
                soup = BeautifulSoup(para_, 'html.parser')

                # Extract the title
                para_title = soup.title.string

                # match = re.search(r'<h2>(.*?)</h2>', para_)
                # para_title = match.group(1)

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
                                    <h1>ReportWhiz: A Report Generation Tool!</h1>
                                    </div>
                                    <div class="subtitle">
                                    <h3>''' + para_title + '''</h3>
                                    </div>

                                    <!-- content section -->
                                    <div class="content"> ''' + para_ + '''</div>
                                </body>
                                </html>
                            '''
                
                @st.experimental_dialog("Edit the report", width= 'large')
                def edit_report():
                    output_ = st.text_area("Edit your report", html_string)
                    if st.button("Submit"):
                        print("Inside submit button")
                        st.session_state.vote = output_
                        print("Opening pdf to write")
                        with open(pdf_path, "wb") as pdf_file:
                            print("PDF opened")
                        
                            pisa_status = pisa.CreatePDF(output_, dest=pdf_file)
                        print("done with report")
                        st.write("Report Generated Successfully. Please check directory ", fileName)
                        st.rerun()
                edit_report()

fname = 'https://github.com/pranavGenAI/ReportWhiz/tree/e165a5c380f32beda1bdd2582ca2070447fc800a/output/output.pdf'
with open(fname, "rb") as f:
    st.download_button("Download Report from here!!", f, fname)
    st.success("Report Delivered to the location !!!")
                        

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
    st.header("ReportWiz Tool")

    user_question = st.text_input("What report do you want to generate?", key="user_question")
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
        if st.button("Generate Report"):
            if user_question and api_key:  # Ensure API key and user question are provided
                user_input(user_question, api_key)
   
    with st.sidebar:
        st.image("https://www.vgen.it/wp-content/uploads/2021/04/logo-accenture-ludo.png", width=150)
        st.markdown("")
        st.markdown("")
        
        st.title("ReportWiz 📋💬")
        pdf_docs = st.file_uploader("Upload your Files and Click on the Submit & Process Button", accept_multiple_files=True, key="pdf_uploader")
        if st.button("Submit & Process", key="process_button") and api_key:  # Check if API key is provided before processing
            with st.spinner("Reading & Processing Content..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks, api_key)
                st.success("Done")
        #st.image("https://media.tenor.com/s1Y9XfdN08EAAAAi/bot.gif", width=200)


if __name__ == "__main__":
    with open('waves.css') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    main()
