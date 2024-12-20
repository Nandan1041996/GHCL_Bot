import textwrap
import gc
import re
from deep_translator import GoogleTranslator
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain


# Define text wrapping function
def wrap_text_preserve_new_line(text, width=110):
    lines = text.split('\n')
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_text = '\n'.join(wrapped_lines)

    del[lines,wrapped_lines]
    gc.collect()
    return wrapped_text 

def get_chain(llm,prompt,vector_index,chat_memory):

    chain = ConversationalRetrievalChain.from_llm(
                                                llm=llm, retriever=vector_index.as_retriever(),
                                                memory = chat_memory,
                                                return_source_documents=False,
                                                combine_docs_chain_kwargs={'prompt': prompt})
      
    del [llm,prompt,vector_index]
    gc.collect()
    return chain

# convert link if available in response
def convert_links_to_hyperlinks(text):
    response =  re.sub(
        r'(https?://\S+)',
        r'<a href="\1" target="_blank">\1</a>',
        text
    )
    print('response::',response)
    return response

def get_answer(chain,query_text,memory):
    ''' this function is used to retrive answer of given query_text

    Args:
    llm : Pretrained Model
    PROMPT : If query_text related question is not available in csv file then it return dont know
    vector_index : Used for faster search of sementic query_text from data
    query_text : Question

    Returns : Answer
    '''
    # RetrivalQA used for retriving answer form asked question 
    
    answer_dict = chain.invoke({'question': query_text,'chat_history':memory})
    print('answer_dict',answer_dict)
    res_dict = {'en':answer_dict['answer']}
   
    answer = answer_dict['answer']

    answer = convert_links_to_hyperlinks(answer)
    print('answer',answer)
     
    # To translate
    tgt_lang_lst = ['gu','hi','ta']
    for tgt_lang in tgt_lang_lst:
        translated = GoogleTranslator(source='en', target = tgt_lang).translate(answer)

        res =wrap_text_preserve_new_line(translated)
        res_dict[tgt_lang] = res
    del [chain,answer_dict,tgt_lang_lst]
    gc.collect()
    return res_dict