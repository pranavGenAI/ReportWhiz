import streamlit as st
import base64
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
from reportlab.pdfgen import canvas
from reportlab.lib import colors 
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Frame, SimpleDocTemplate


st.set_page_config(page_title="BidBooster ", layout="wide")

st.markdown("""
## BidBooster 🤗💬: Answers your RFP related query.

### How It Works?

Follow these simple steps to interact with the chatbot:
1. **Upload the RFP document and click on submit & process** (Please note: the base LLM model is fine-tuned on LCBO ESG RFP documents. Results may vary for other documents).
2. **Ask a Question:** Once the document is processed, ask any question related to its content for a precise answer.
3. Ensure your **prompt is clear and complete** with some context for better result.
""")
#st.image("https://media1.tenor.com/m/6o864GYN6wUAAAAC/interruption-sorry.gif", width=1000)
st.image("https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjl2dGNiYThobHplMG81aGNqMjdsbWwwYWJmbTBncGp6dHFtZTFzMSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/CGP9713UVzQ0BQPhSf/giphy.gif", width=50)


# This is the first API key input; no need to repeat it in the main function.
api_key = st.secrets['GEMINI_API_KEY']

if 'responses' not in st.session_state:
    st.session_state['responses'] = ["How can I assist you?"]

if 'requests' not in st.session_state:
    st.session_state['requests'] = []


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
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
    prompt_template = """
    Answer the question as detailed as possible from the provided context. Change the wording of answer and start in the most polite way. Write the summary of answer and then provide the detail answer. Start with polite and nice statement. You can use greetings if you want. Don't provide the wrong answer. If you are giving answer and not using context to frame the answer then let the user know that the answer is not from the context.\n\n. And remember to format your answer in nicer way. End your response with disclaimer telling about the answer is from the context. Remember to be polite and start answer with assistant greetings. 
    Context:\n {context}?\n
    Question: \n{question}\n .Make sure you are summarizing and changing the wording of context before you write answer in easy to understand language and format it in better way. Provide the disclaimer in best possible way at the of question saying the answer is based on the context and accuracy needs to be checked from the source.

    Answer:
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
                para_ = response
                fileName = 'C:/Users/pranav.baviskar/Desktop/Learning/GenAI/BidBooster/out2.pdf'
                context_user_question = "Only Suggest the title for the text and enclose it within the tag <b> </b>: " + response
                subTitle = chain(context_user_question=context_user_question)
                subTitle = subTitle.replace("*","")
                para_ = para_.replace("*","")
                print("para_ printed here-------------------->>>",para_)
                # creating a pdf object 
                pdf = canvas.Canvas(fileName) 
                
                # setting the title of the document 
                pdf.setTitle(documentTitle) 
                pdf.setFillColorRGB(0, 0, 0) 
                #pdf.setFont("Graphik-Bold", 24) 
                pdf.drawCentredString(290, 820, subTitle) 
            
                # drawing a line 
                pdf.line(30, 810, 550, 810) 
                    
                # creating a multiline text using 
                # textline and for loop 
                text = pdf.beginText(40, 680) 
                text.setFont("Times-Roman", 13) 
                text.setFillColor(colors.black) 
                # for font in pdf.getAvailableFonts():
                #     print(font)
                #     pdf.setFont(font, 18)
                #     pdf.setFont("Helvetica", 18)
                flow_obj = []
            
                styles = getSampleStyleSheet()
            
                text = para_
                p_text = Paragraph(text, style=styles["Normal"])
                flow_obj.append(p_text)
                frame = Frame(50,50,500,750, showBoundary=1)
                frame.addFromList(flow_obj,pdf)
                pdf.save()                
                st.write("Report Generated Successfully. Please check directory ", out)
                st.success("Report Delivered to the location !!!")

def get_conversation_string():
    conversation_string = ""
    for i in range(len(st.session_state['responses'])-1):
        
        conversation_string += "Human: "+st.session_state['requests'][i] + "\n"
        conversation_string += "Bot: "+ st.session_state['responses'][i+1] + "\n"
    return conversation_string

def query_refiner(conversation, user_question):
    prompt=f"""
    Given the following user query and conversation log, formulate a question that would be the most relevant to provide the user with an answer from a knowledge base.\n\nCONVERSATION LOG: \n{conversation}\n\nQuery: {user_question}\n\nRefined Query:"

    """
    
    prompt = PromptTemplate(template=prompt, input_variables=["conversation","user_question"])
    print("Prompt is....",prompt)
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3, google_api_key=api_key)
    chat_llm_chain = LLMChain(
        llm=model,
        prompt=prompt,
        verbose=True
    )    
    response = chat_llm_chain.predict(user_question=user_question)
    print("Response of refined query is ----->",response)
    return response

st.markdown("""
<style>
.small-font {
    font-size:13px !important;
    color: lightgrey !important;
}
</style>
""", unsafe_allow_html=True)

def main():
    st.header("BidBooster Chatbot")

    user_question = st.text_input("Ask a Question from the RFP Files", key="user_question")

    if user_question and api_key:  # Ensure API key and user question are provided
        user_input(user_question, api_key)
        if user_question:
            with st.spinner("thinking ..."):
                conversation_string = get_conversation_string()
                # st.code(conversation_string)
                refined_query = query_refiner(conversation_string, user_question)
                st.markdown('<p class="small-font">---------------------------------------------------------------------------------------------------------------------</p>', unsafe_allow_html=True)
                
                st.markdown('<p class="small-font">Query Suggestion!!</p>', unsafe_allow_html=True)
                query_suggestion = "Your query suggestion here"
                st.markdown(f'<p class="small-font">{refined_query}</p>', unsafe_allow_html=True)
                #st.write(refined_query)


    with st.sidebar:
        st.title("BidBooster 🤗💬")
        pdf_docs = st.file_uploader("Upload your RFP Files and Click on the Submit & Process Button", accept_multiple_files=True, key="pdf_uploader")
        if st.button("Submit & Process", key="process_button") and api_key:  # Check if API key is provided before processing
            with st.spinner("Reading & Processing Content..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks, api_key)
                st.success("Done")
        st.image("https://media.tenor.com/s1Y9XfdN08EAAAAi/bot.gif", width=200)


if __name__ == "__main__":
    main()
