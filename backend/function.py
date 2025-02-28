# functions.py
from langchain_community.document_loaders import WebBaseLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter

model_local = ChatOllama(model="qwen2.5:0.5b")
conversation_memory = []

def urlSpliter(url: str):
   
    urls = [url]
    docs = [WebBaseLoader(u).load() for u in urls]
    docs_list = [item for sublist in docs for item in sublist]
    
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, chunk_overlap=50)
    doc_splits = text_splitter.split_documents(docs_list)
    
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=OllamaEmbeddings(model='mxbai-embed-large'),
        persist_directory="./chroma_db"  
    )
    vectorstore.persist()
    
    return vectorstore.as_retriever()

def textToEmbedding(file_path: str):
    
    # Load the text file
    loader = TextLoader(file_path)
    documents = loader.load()
    
    # Split text into chunks
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, 
        chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(documents)
    
    # Create embeddings and store in Chroma
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=OllamaEmbeddings(model='mxbai-embed-large'),
        persist_directory="./chroma_db"
    )
    vectorstore.persist()
    
    return vectorstore.as_retriever()

def load_retriever():
    
    embedding = OllamaEmbeddings(model='mxbai-embed-large')
   
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        collection_name="rag-chroma",
        embedding_function=embedding
    )
    return vectorstore.as_retriever()

def ollama(prompt: str):

    global conversation_memory
    memory_context = "\n".join(conversation_memory) if conversation_memory else "None"

    template = (
        "You are a friendly, engaging conversationalist.\n"
        "Conversation history:\n{memory}\n\n"
        "User: {prompt}\n"
        "Your response:"
    )
    
    input_data = {"memory": memory_context, "prompt": prompt}
    
    chain_prompt = ChatPromptTemplate.from_template(template)
    chain = chain_prompt | model_local | StrOutputParser()
    
    result = chain.invoke(input_data)
    
    conversation_memory.append("User: " + prompt)
    conversation_memory.append("Assistant: " + result)
    
    return result

def Rag(user_input: str, retriever):
    # Retriever
    docs = retriever.get_relevant_documents(user_input)
    doc_context = "\n\n".join([doc.page_content for doc in docs])
    
    try:
        global conversation_memory
        conv_context = "\n".join(conversation_memory) if conversation_memory else ""
    except NameError:
        conv_context = ""
    
    combined_context = (
        f"Document context:\n{doc_context}\n\n"
        f"Conversation history:\n{conv_context}"
    )
    
    versatile_template = (
   
    "Consider the following context and the user's input, and provide a response that best addresses the user's intent.\n\n"
    "Context:\n{context}\n\n"
    "User input:\n{user_input}\n\n"
    "Always consider the last message, ans stick to that context"
    "Your response should be in a Bulleted form"
    "Your response:"
)

    input_data = {"context": combined_context, "user_input": user_input}
    prompt_template = ChatPromptTemplate.from_template(versatile_template)
    chain = prompt_template | model_local | StrOutputParser()
    result = chain.invoke(input_data)
    return result