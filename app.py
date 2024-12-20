import time
import gc
import json
import pickle
import io
import secrets
import os
import re
from PyPDF2 import PdfReader
from docx import Document
from langchain.docstore import document 
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_community.document_loaders import UnstructuredExcelLoader,UnstructuredWordDocumentLoader
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from flask import Flask,request, render_template, redirect, url_for, flash, jsonify
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationSummaryBufferMemory
from dotenv import load_dotenv
from functions import get_chain,get_answer,wrap_text_preserve_new_line
from exception import *

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)  # Required for flash messages
# os.environ['CURL_CA_BUNDLE'] = ''
# Set the new credentials path
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"D:\G01889\Documents\Downloads\client_secret_820887058416-7c10c17qjh42739ca2hc0bn3cn40fdc0.apps.googleusercontent.com.json"
# Upload folder configuration
UPLOAD_FOLDER = 'Document/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['store_answer_feedback'] = 'Store_Ans'

answer_file_path = os.path.join(app.config['store_answer_feedback'], 'answers.json')
feedback_file_path = os.path.join(app.config['store_answer_feedback'], 'feedback.json')

if not os.path.exists(answer_file_path):
    with open(answer_file_path, 'w') as f:
        json.dump([], f)  # Initialize with an empty list

# Define scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/spreadsheets']

def authenticate_and_list_files():
    """Authenticate with Google Drive API and list files."""
    try:
        credentials = None

        # Check for existing token file
        if os.path.exists('token.json'):
            credentials = Credentials.from_authorized_user_file('token.json', SCOPES)

        # If no valid credentials, initiate authentication flow
        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'], SCOPES)
            credentials = flow.run_local_server(port=0)

            # Save credentials for future use
            with open('token.json', 'w') as token_file:
                token_file.write(credentials.to_json())

        return credentials  # Return credentials for further use

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def load_file_data(file_id, credentials):
    """Load data from the selected file based on its type (CSV, Excel, PDF)."""
    try:
        # Use the credentials passed into the function to authenticate the service
        service = build('drive', 'v3', credentials=credentials)

        file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        mime_type = file_metadata.get('mimeType')
        print('mime_type:',mime_type)

        # Get the content of the file
        file_content = service.files().get_media(fileId=file_id).execute()
        
        # print('file_cont::',file_content)
        # Check the file type
        if mime_type == 'application/vnd.ms-excel' or mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            print("Processing Excel file...")
            # Get the content of the file
            loader = UnstructuredExcelLoader(file_path=None, file=io.BytesIO(file_content))
            data = loader.load() 

        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = Document(io.BytesIO(file_content))
            # Extract text from the document
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            # convert text to document
            data = [document.Document(page_content=text)]

        elif mime_type == 'application/pdf':
            pdf_reader = PdfReader(io.BytesIO(file_content))
            text = ""
            # Iterate over each page of the PDF
            for page in pdf_reader.pages:
                # Extract text from the page
                page_text = page.extract_text()
                
                # Add the page text to the text string
                if page_text:  # Ensure that there is text extracted from the page
                    text += page_text + "\n"  # Add a newline after each page's text
                        # convert text to document
            data = [document.Document(page_content=text)]

        elif mime_type=='text/plain':
            print(file_content.decode('utf-8'))
            data = [document.Document(file_content.decode('utf-8'))]
            
        return data
     
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

@app.route('/')
def index():
    try:
        """Render the homepage with a list of allowed files."""

        # Allowed file extensions
        allowed_extensions = ('.xlsx', '.docx','.pdf','.txt')

        credentials = authenticate_and_list_files()
        # Build Google Drive API client
        service = build('drive', 'v3', credentials=credentials)
        FOLDER_ID = '1LSgEkDLL8ulP7Ep-qvbqI2XbKQXf2oui' 
        # Query files within the folder
        query = f"'{FOLDER_ID}' in parents"

        if service:
            files = []
            next_page_token = None

            # Paginate through the results
            while True:
                response = service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name)',
                    pageToken=next_page_token
                ).execute()

                files.extend(response.get('files', []))
                next_page_token = response.get('nextPageToken')

                if not next_page_token:
                    break

            # Print all files in the folder
            if files:
                files_with_id_dict = {}
                print("Files found in the folder:")
                for file in files:
                    files_with_id_dict[file['name']] = file['id']
                    print(f"File Name: {file['name']}, File ID: {file['id']}")
                with open(os.path.join('Document','doc_files.json'), 'w') as fp:
                    json.dump(files_with_id_dict, fp)

                # Get the list of files with allowed extensions
                files = [os.path.basename(f) for f in [key for key,val in files_with_id_dict.items()]if f.endswith(allowed_extensions)]
                
                del[allowed_extensions]
                gc.collect()
                return render_template('index.html', files=files)
            else:
                raise FileNotAvailable()
    except FileNotAvailable as exe:
        return exe

@app.route('/uploads', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    allowed_extensions = ('.csv', '.pdf', '.xlsx', '.txt')
    
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if file and file.filename.lower().endswith(allowed_extensions):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully')
    else:
        flash(f'Invalid file type. Only {", ".join(allowed_extensions)} files are allowed.')
    del[allowed_extensions,file]
    gc.collect()
    return redirect(url_for('index'))

@app.route('/delete/<filename>')
def delete_file(filename):
    """Delete a file.
    Args:
    filename(['String']) : Path of file to be deleted.
    """
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.remove(file_path)
    flash('File deleted successfully.')
    pkl_file_name = filename.split('.')[0]+'.pkl'
    if os.path.exists(os.path.join(pkl_file_name)):                
        os.remove(os.path.join(pkl_file_name))
    del [file_path,pkl_file_name]
    gc.collect()
    return redirect(url_for('index'))

 
# general prompt for model
prompt_temp = '''You are a Guide AI. Your role is to provide guidance strictly from information provided to you Dont go beyond information. Always respond in a concise and professional manner.

Follow these rules to handle user interactions:  
---
### **Rules for User Interactions**  
1. Must Do : 
   -include  URL or Link if provided as a reference for the user to find additional information if required.

1a. **Gratitude or Acknowledgment (e.g., "Thank you," "Thanks," "Great answer"):**  
   - Respond only with:  
     *"I'll do my best to assist you. You're welcome! How can I assist you further?"*  
   - Do not include any additional context or information.  

2. **User Greets (e.g., "Hello," "Hi," "How are you?")**  
   - Respond politely and acknowledge. Examples:  
     - "Hello! How can I assist you today?"  
     - "Hi! How can I help you?"  

3. **Queries Based on Context:**  
   - Answer strictly based on the provided context.  
   - If the query is unrelated or the information is unavailable, respond with:  
     *"The information is not available in the provided context. Please provide more details or connect with a team member."*  

4. **Personal Information Shared by User:**  
   - Discourage sharing sensitive personal details. Example:  
     *"Thank you for sharing, but please avoid disclosing personal information."*  

5. **Full Forms or Definitions:**  
   - Provide full forms only if available in the context.  
   - If unavailable, respond with: *"Information not available in the provided context."*  

6. **Gratitude After Providing an Answer:**  
   - Respond with: *"You're welcome! Feel free to ask if you have any other questions."*  

7. **Unrelated or Unclear Questions:**  
   - If the query is unclear or unrelated, respond with:  
     *"The information is not available in the provided context. Please provide more details or connect with a team member."*  

8. **Response Formatting:**  
   - For gratitude, always use:  
     *"I'll do my best to assist you. You're welcome! How can I assist you further?"*  
   - For standard answers, use: `Answer: [Your Response]`.  
   - For unavailable information, use: `Answer: Not Found.`  

9. Must Do : Whenever you cannot provide a complete answer to a question, include the provided URL as a reference for the user to find additional information if required.

---
### **Examples**  
1. **User Says "Thank You":**  
   - AI Reply: *"I'll do my best to assist you. You're welcome! How can I assist you further?"*  

2. **User Asks a Question with Greeting (e.g., "Hi, can you provide details about X?"):**  
   - AI Reply: *"Hi! Here's the information you requested about X..."*  

3. **User Asks for a Full Form (e.g., "What does DL stand for?"):**  
   - AI Reply: *"DL stands for Deep Learning."*  

4. **User Expresses Gratitude After an Answer:**  
   - AI Reply: *"You're welcome! Feel free to ask if you have any other questions."*  

5. **User Asks an Unrelated or Unclear Question:**  
   - AI Reply: *"The information is not available in the provided context. Please provide more details or connect with a team member."*  
---

**Context:**  
{context}  
{chat_history}  
Human: {question}  
'''

embedings = HuggingFaceBgeEmbeddings()
# model
llm = ChatGroq(model='llama-3.1-70b-versatile',api_key='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',temperature=0,max_retries=2)

chat_memory = ConversationSummaryBufferMemory(llm=llm,memory_key='chat_history',return_messages=True)

@app.route('/ask', methods=['POST'])
def get_ans_from_csv():
    ''' this function is used to get answer from given csv.

    Args:
    doc_file([CSV]): comma separated file 
    query_text :  Question

    Returns: Answer
    '''
    query_text = request.form.get('query_text')
    doc_file = request.form.get('selected_file')
    selected_language = request.form.get('selected_language')
    query_text = query_text.lower() 

    if query_text :
        if not doc_file or doc_file == "Select a document":
            flash("Please select a document to proceed.")
            return redirect(url_for('index'))

        else:
            #to load pickle file 
            pickle_file_name = doc_file.split('.')[0]+'.pkl'
            if os.path.isfile(os.path.join('pkl_files', pickle_file_name)):
                with open(os.path.join('pkl_files',pickle_file_name),mode='rb') as f:
                    vector_index = pickle.load(f)

            else:
                credentials = authenticate_and_list_files()

                with open(os.path.join('Document','doc_files.json'), 'r') as fp:
                    doccument_file =  json.load(fp)
                print('doc_files::::',doccument_file)
                
                documents_id = doccument_file[doc_file]
                print('document_id::',documents_id)
                data = load_file_data(documents_id, credentials)
                if data:
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=700,chunk_overlap=100)
                    docs = text_splitter.split_documents(data)
                    embedings = HuggingFaceBgeEmbeddings()
                    # if pickle file not available
                    vector_index = FAISS.from_documents(docs, embedding=embedings)
                    if not os.path.isfile(os.path.join('pkl_files',pickle_file_name)):
                        with open(os.path.join('pkl_files',pickle_file_name),mode='wb') as f:
                            pickle.dump(vector_index,f)

                else:
                    res_ans = "Failed to load file data."
                    return jsonify({'answer': res_ans})
            # model
            llm = ChatGroq(model='llama-3.1-70b-versatile',api_key='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',temperature=0,max_retries=2)
            prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','chat_history','question'])
            # function is used to get answer
            chain = get_chain(llm,prompt,vector_index,chat_memory)
            res_dict = get_answer(chain,query_text,chat_memory)

            que_ans_dict = {'doc': doc_file, query_text:res_dict}
            res_ans =que_ans_dict[query_text][selected_language]

            del [vector_index,chain,llm,res_dict,que_ans_dict,prompt]
            gc.collect()

        return jsonify({'answer': res_ans})
    else:
        return redirect(url_for('index'))

# @app.route('/ask', methods=['POST'])
# def get_ans_from_csv():
#     ''' this function is used to get answer from given csv.

#     Args:
#     doc_file([CSV]): comma separated file 
#     query_text :  Question

#     Returns: Answer
#     '''
#     # doc_dict = {'question answar list.xlsx':'1PKclGMtRcz7nI1Fz2S3GVHljEO3UrkC-'}

#     query_text = request.form.get('query_text')
#     doc_file = request.form.get('selected_file')
#     print('doc_file::',doc_file)
#     selected_language = request.form.get('selected_language')
#     query_text = query_text.lower() 

#     if query_text :
#         start_time = time.time()
#         if not doc_file or doc_file == "Select a document":
#             flash("Please select a document to proceed.")
#             return redirect(url_for('index'))
#         # else:
#         #     if doc_file.endswith('txt'):
#         #         loader = TextLoader(os.path.join('Document', doc_file), encoding='utf-8')
#         #         prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','chat_history','question'])
#         #         data = loader.load()
#         #     elif doc_file.endswith('csv'):
#         #         loader = CSVLoader(os.path.join('Document',doc_file))
#         #         prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','chat_history','question'])
#         #         data = loader.load()
#         #     elif doc_file.endswith('pdf'):
#         #         loader = PyPDFLoader(os.path.join('Document',doc_file))
#         #         prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','chat_history','question'])
#         #         data = []
#         #         for page in loader.lazy_load():
#         #             data.append(page)
#         #     elif doc_file.endswith(('xlsx','xls')):
#         #         loader = UnstructuredExcelLoader(os.path.join('Document',doc_file))
#         #         prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','chat_history','question'])
#         #         data = loader.load()
#         #         print('data::',data)

#         else:
#             credentials_path = r"D:\G01889\Documents\Downloads\client_secret_820887058416-dkrrclrigimhemn7fsvv8lddttn09bup.apps.googleusercontent.com.json"
#             token_path = r"D:\G01889\Documents\Downloads\token.json"
            
#             with open(os.path.join('Document','doc_files.json'), 'r') as fp:
#                 doccument_file =  json.load(fp)
#             print('doc_files::::',doccument_file)
            
#             documents_id = [doccument_file[doc_file]]
#             print('document_id::',documents_id)
#             data = authenticate_and_load_drive_files(credentials_path,token_path,documents_id)
        
#             embedings = HuggingFaceBgeEmbeddings()
            


#             text_splitter = RecursiveCharacterTextSplitter(chunk_size=700,chunk_overlap=100)
#             docs = text_splitter.split_documents(data)

#             # to load pickle file 
#             pickle_file_name = doc_file.split('.')[0]+'.pkl'
#             if os.path.isfile(os.path.join(pickle_file_name)):
#                 with open(os.path.join(pickle_file_name),mode='rb') as f:
#                     vector_index = pickle.load(f)
#             else:
#                 # if pickle file not available
#                 vector_index = FAISS.from_documents(docs, embedding=embedings)
            
#             # model
#             llm = ChatGroq(model='llama-3.1-70b-versatile',api_key='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',temperature=0,max_retries=2)
#             prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','chat_history','question'])
#             chat_memory = ConversationBufferMemory(memory_key='chat_history',return_messages=True)
#             # function is used to get answer
#             chain = get_chain(llm,prompt,vector_index,chat_memory)
#             res_dict = get_answer(chain,query_text,chat_memory)






#             # credentials_path = r"D:\G01889\Documents\Downloads\client_secret_607970611934-tkq90it16t3lg5mirgj8fho8rekuru2g.apps.googleusercontent.com"
#             # token_path = r"D:\G01889\Documents\Downloads\token.json"

#             # credentials = authenticate_and_load_drive_files(credentials_path,token_path)

#             # loader = GoogleDriveLoader(
#             #     document_ids= [doct_id],
#             #     credentials=credentials,
#             #     )
        
#             # prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','chat_history','question'])
#             # data = loader.load()
    
            
#             # text_splitter = RecursiveCharacterTextSplitter(chunk_size=700,chunk_overlap=100)
#             # docs = text_splitter.split_documents(data)
            
#             # # to load pickle file 
#             # pickle_file_name = doc_file.split('.')[0]+'.pkl'
#             # if os.path.isfile(os.path.join(pickle_file_name)):
#             #     with open(os.path.join(pickle_file_name),mode='rb') as f:
#             #         vector_index = pickle.load(f)
#             # else:
#             #     # if pickle file not available
#             #     vector_index = FAISS.from_documents(docs, embedding=embedings)
#             # # model
#             # llm = ChatGroq(model='llama-3.1-70b-versatile',api_key='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',temperature=0,max_retries=2)
            
#             # # chat_memory = ConversationBufferMemory(memory_key='chat_history',return_messages=True)
#             # # function is used to get answer
#             # chain = get_chain(llm,prompt,vector_index,chat_memory)
#             # res_dict = get_answer(chain,query_text,chat_memory)

#             if not os.path.isfile(os.path.join(pickle_file_name)):
#                 with open(os.path.join(pickle_file_name),mode='wb') as f:
#                         pickle.dump(vector_index,f)

#             # Prepare the answer dictionary
#             que_ans_dict = {'doc': doc_file, query_text:res_dict}
#             res_ans =que_ans_dict[query_text][selected_language]
            
#             del [pickle_file_name,vector_index,chain,llm,
#                 res_dict,que_ans_dict,loader,data,prompt]
#             gc.collect()

#         end_time = time.time()
#         print('time_taken :',end_time-start_time)
#         return jsonify({'answer': res_ans})
#     else:
#         return redirect(url_for('index'))
    

# @app.route('/ask', methods=['POST'])
# def get_ans_from_csv():
#     ''' this function is used to get answer from given csv.

#     Args:
#     doc_file([CSV]): comma separated file 
#     query_text :  Question

#     Returns: Answer
#     '''
#     query_text = request.form.get('query_text')
#     doc_file = request.form.get('selected_file')
#     print('doc_file::',doc_file)
#     selected_language = request.form.get('selected_language')
#     query_text = query_text.lower() 
#     # ext = doc_file.split('.')[1]
#     # Create the ChatPromptTemplate with the updated system prompt


#     if query_text :
#         start_time = time.time()
#         if not doc_file or doc_file == "Select a document":
#             flash("Please select a document to proceed.")
#             return redirect(url_for('index'))
#         else:
#             if doc_file.endswith('txt'):
#                 loader = TextLoader(os.path.join('Document', doc_file), encoding='utf-8')
#                 prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','history','question'])
#                 data = loader.load()

#             elif doc_file.endswith('csv'):
#                 loader = CSVLoader(os.path.join('Document',doc_file))
#                 prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','history','question'])
#                 data = loader.load()
#             elif doc_file.endswith('pdf'):
#                 loader = PyPDFLoader(os.path.join('Document',doc_file))
#                 data = []
#                 for page in loader.lazy_load():
#                     data.append(page)
#             elif doc_file.endswith(('xlsx','xls')):
#                 loader = UnstructuredExcelLoader(os.path.join('Document',doc_file))
#                 prompt =  PromptTemplate(template=prompt_temp,input_variables=['context','history','question'])
#                 data = loader.load()
#                 print('data::',data)
#             text_splitter = RecursiveCharacterTextSplitter(chunk_size=700,chunk_overlap=100)
#             docs = text_splitter.split_documents(data)
            
#             # to load pickle file 
#             pickle_file_name = doc_file.split('.')[0]+'.pkl'
#             if os.path.isfile(os.path.join(pickle_file_name)):
#                 with open(os.path.join(pickle_file_name),mode='rb') as f:
#                     vector_index = pickle.load(f)
#             else:
#                 # if pickle file not available
#                 vector_index = FAISS.from_documents(docs, embedding=embedings)
#             llm = ChatGroq(model='llama-3.1-70b-versatile',api_key='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',temperature=0,max_retries=2)
#             chat_memory = ConversationBufferMemory(return_messages=True)
#             # function is used to get answer
#             chain = get_chain(llm,prompt,vector_index,chat_memory)
#             res_dict = get_answer(chain,query_text,chat_memory)
        

#             if not os.path.isfile(os.path.join(pickle_file_name)):
#                 with open(os.path.join(pickle_file_name),mode='wb') as f:
#                         pickle.dump(vector_index,f)

#             # Prepare the answer dictionary
#             que_ans_dict = {'doc': doc_file, query_text:res_dict}
#             res_ans =que_ans_dict[query_text][selected_language]
            
#             print('res_ans:',res_ans)

#             del [pickle_file_name,vector_index,chain,llm,
#                 res_dict,que_ans_dict,loader,data,prompt]
#             gc.collect()

#         end_time = time.time()
#         print('time_taken :',end_time-start_time)
#         return jsonify({'answer': res_ans})
#     else:
#         return redirect(url_for('index'))
    

@app.route('/save_answers', methods=['POST'])
def save_answers():
    """Save answer data to answers.json."""
    data = request.json
    print('answer_file_path:',answer_file_path)
    with open(answer_file_path, 'r+') as f:
        answers = json.load(f)
        answers.append(data)  # Append new data
        f.seek(0)  # Move to the beginning of the file
        json.dump(answers, f, indent=4)  # Save updated data
    del[data]
    gc.collect()
    return jsonify({'message': 'Answer data saved successfully'}), 200

@app.route('/save_feedback', methods=['POST'])
def save_feedback():
    """Save user feedback."""
    feedback_data = request.json
    # Initialize feedback file if it doesn't exist
    if not os.path.exists(feedback_file_path):
        with open(feedback_file_path, 'w') as f:
            json.dump([], f)  # Start with an empty list
    
    print('feedback_file_path::',feedback_file_path)
    with open(feedback_file_path, 'r+') as f:
        feedbacks = json.load(f)
        feedbacks.append(feedback_data)  # Append new feedback
        f.seek(0)  # Move to the beginning of the file
        json.dump(feedbacks, f, indent=4)  # Save updated feedback

    return jsonify({'message': 'Feedback saved successfully'}), 200


if __name__=='__main__':
    app.run()







