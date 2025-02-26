from flask import Flask, request, jsonify
from langchain_ollama import OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.vectorstores import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import PromptTemplate

app = Flask(__name__)

cachedllm = OllamaLLM(model="llama3.2", temperature=0.5)
embedding = FastEmbedEmbeddings()
folder_path = "db"

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=400,
    length_function=len,
    is_separator_regex=False
)

# Modified prompt to handle both document-based and general questions
raw_prompt = PromptTemplate.from_template("""
<s>[INST] You are a knowledgeable assistant who can answer questions using both document information and general knowledge.

If the provided document context contains relevant information about the question, use it first.
If the question is unrelated to the document or the document doesn't contain relevant information, use your general knowledge to provide a complete answer.

Remember to:
1. Check if the document context is relevant to the question
2. If relevant, use document information and supplement with general knowledge
3. If not relevant, provide a comprehensive answer using your general knowledge[/INST]</s>
[INST] Question: {input}
Document Context: {context}

Please provide a direct answer.
[/INST]
""")

@app.route("/llama", methods=["POST"])
async def llama():
    json_data = request.json
    query = json_data.get("query")
 
    response = await cachedllm.invoke(query)
    return jsonify({"response": response})

@app.route("/documents", methods=["POST"])
def documents():
    file = request.files["file"]
    file_name = file.filename
    save_file = "document/" + file_name
    file.save(save_file)

    loader = PDFPlumberLoader(save_file)
    docs = loader.load_and_split()

    chunks = text_splitter.split_documents(docs)
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=folder_path
    )
    
    vector_store.persist()

    return jsonify({
        "status": "Successfully Uploaded",
        "file_name": file_name,
        "doc_len": len(docs),
        "chunks": len(chunks)
    })

@app.route("/ask_pdf", methods=["POST"])
async def ask_pdf():
    json_data = request.json
    query = json_data.get("query")


    vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
    
    retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 20,
            "lambda_mult": 0.7,
        },
    )


    docs_and_scores = vector_store.similarity_search_with_relevance_scores(query, k=3)
  
    has_relevant_docs = any(score > 0.1 for doc, score in docs_and_scores)

    if has_relevant_docs:
        
        document_chain = create_stuff_documents_chain(
            cachedllm, 
            raw_prompt,
            document_variable_name="context"
        )
        chain = create_retrieval_chain(retriever, document_chain)
        result = await chain.ainvoke({"input": query})
        
        if isinstance(result, dict):
            answer = result.get('answer', '')
        else:
            answer = str(result)
    else:
       
        answer = await cachedllm.invoke(
            f"Please provide a comprehensive answer to this question: {query}"
        )

    return jsonify({
        "answer": answer,
        "source": "document" if has_relevant_docs else "general_knowledge"
    })

@app.route("/video", methods=["POST"])
def video():
    return "video"

def start_app():
    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == "__main__":
    start_app()