from transformers import BartTokenizer, HfArgumentParser
import chromadb
from chromadb import Client
from chromadb import Collection

from angle_emb import AnglE
import logging
from spacy.lang.en import English

from alinet.qg import Model

import hashlib
import fitz

from dataclasses import dataclass, field
import torch
@dataclass
class EvaluateModelArguments:
    doc_paths: list[str] = field(
        metadata={"help": "List of document paths"},
    )

# Helper function
def generate_sha256_hash_from_text(text):
    # Create a SHA256 hash object
    sha256_hash = hashlib.sha256()
    # Update the hash object with the text encoded to bytes
    sha256_hash.update(text.encode('utf-8'))
    # Return the hexadecimal representation of the hash
    return sha256_hash.hexdigest()


logger = logging.getLogger(__name__)
nlp = English()
nlp.add_pipe("sentencizer")

class Database:
    def __init__(self, 
                pretrained_bart_tokenizer_name: Model = Model.BALANCED_RESOLVED, 
                output_dir: str = "./chromadb"):
        # Tokenizer
        self.tokenizer = BartTokenizer.from_pretrained(pretrained_bart_tokenizer_name)
        
        self.angle : AnglE

        if torch.cuda.is_available():
            self.angle = AnglE.from_pretrained("WhereIsAI/UAE-Large-V1", pooling_strategy="cls").cuda()    
        else:
            self.angle = AnglE.from_pretrained("WhereIsAI/UAE-Large-V1", pooling_strategy="cls")
            
        # ChromaDB client and collection
        self.client: Client = chromadb.PersistentClient(path=output_dir)

    def _get_doc_text(self, path: str):
        texts = []
        doc = fitz.open(path) 
        for page in doc: 
            texts.append(page.get_text())
        return "".join(texts)

    def store_documents(self, collection: Collection, doc_paths: list[str], max_token_limit: int = 512):
        
        for path in doc_paths:
            
            document = self._get_doc_text(path)
            chunks = self._create_document_chunks(document, max_token_limit)

            for doc in chunks:
                embedding = self.angle.encode(doc, to_numpy=True)

                collection.add(
                    embeddings=embedding,
                    documents=doc,
                    ids=generate_sha256_hash_from_text(doc),
                )

    # Makes sure that an old collection with the same name is deleted, so that a new one is created
    def create_collection(self, client, collection_name: str = "default"):
        try:
            client.delete_collection(collection_name)
        except ValueError:
            logger.info(f"{collection_name} does not exist")

        collection: Collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # l2 is the default
        )

        return collection


    # Splits a document into chunks of text, aiming to respect a maximum token limit.
    def _create_document_chunks(self, document: str, chunk_size: int = 512):
        doc = nlp(document)
        sentences = [span.text for span in doc.sents]
        tokenized_sents = self.tokenizer(sentences)

        token_i = 0
        doc_i = 0
        documents = [[]]
        for sent, tokens in zip(sentences, tokenized_sents['input_ids']):
            if token_i + len(tokens) >= chunk_size:
                token_i = 0
                documents.append([])
                doc_i += 1
            documents[doc_i].append(sent)
            token_i += len(tokens)

        return [' '.join(d) for d in documents]


    def add_relevant_context_to_source(self, context: str, collection: Collection):
        query_embedding = self.angle.encode(context, to_numpy=True)

        relevant_query = collection.query(query_embeddings=query_embedding, n_results=1)

        relevant_context = relevant_query["documents"][0][0]

        long_answer_with_relevant_context = f"{context} {relevant_context}"

        context = long_answer_with_relevant_context

        return context


if __name__ == "__main__":
    parser = HfArgumentParser((EvaluateModelArguments,))
    args = parser.parse_args_into_dataclasses()[0]

    db = Database()
    collection = db.create_collection(db.client)
    db.store_documents(collection, doc_paths=args.doc_paths)

    context = "INPUT THE CONTEXT HERE"
    result = db.add_relevant_context_to_source(context, collection)
    print(result)

