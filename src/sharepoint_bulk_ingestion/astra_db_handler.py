import logging

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_astradb import AstraDBVectorStore
import time


class AstraDBHandler:
    """
    Handles the processing of documents, including splitting them into chunks, generating embeddings, and ingesting
    them into an AstraDB collection.

    :param astra_url: The base URL for the Astra DB API endpoint.
    :param astra_application_token: Authentication token for Astra DB.
    :param astra_keyspace: Namespace (keyspace) for Astra DB.
    :param dry_run: If True, simulates the data ingestion process without making any actual changes to Astra DB.
    """

    def __init__(self, astra_url: str, astra_application_token: str, astra_keyspace: str, collection_name: str,
                 embeddings, max_retries: int = 3, retry_delay: int = 10, dry_run: bool = False):
        """Initializes the AstraDBHandler with database and embedding details, and dry run mode."""
        self.astra_url = astra_url
        self.astra_application_token = astra_application_token
        self.astra_keyspace = astra_keyspace
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dry_run = dry_run

        self.vstore = AstraDBVectorStore(
            embedding=embeddings,
            collection_name=collection_name,
            token=self.astra_application_token,
            api_endpoint=self.astra_url,
            namespace=self.astra_keyspace
        )

    @staticmethod
    def recursive_character_doc_splitter(page_content: str,
                                         metadata: dict = None,
                                         chunk_size: int = 500,
                                         chunk_overlap: int = 100,
                                         length_function: callable = len,
                                         is_separator_regex: bool = False):
        """
        Splits a document into smaller chunks of text based on character count, with optional overlap between chunks.
        This is useful for processing large texts in systems with size limitations per document.

        :param page_content: The content of the document to be split.
        :param metadata: Optional metadata associated with the document. Defaults to None.
        :param chunk_size: The size of each chunk in characters. Defaults to 500.
        :param chunk_overlap: The number of characters to overlap between consecutive chunks. Defaults to 100.
        :param length_function: A callable to measure the length of the text. Defaults to len function.
        :param is_separator_regex: If True, interprets `chunk_size` as a regular expression to find chunk separators.
        Defaults to False.
        :return: A list of Document objects, each representing a chunk of the original document.
        """
        doc = Document(page_content=page_content, metadata=metadata)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function,
            is_separator_regex=is_separator_regex,
        )
        chunks = text_splitter.transform_documents([doc])
        return chunks

    def ingest_chunks_with_embeddings_to_astra_db(self, chunks: list[Document]):
        """
        Ingests given chunks along with their embeddings into an Astra DB collection. This function takes a collection
        of document chunks, each associated with an embedding, and stores them in a specified Astra DB collection. It
        supports a dry run mode that simulates data ingestion without actually persisting the data in Astra DB.

        :param chunks: A collection of document chunks that are to be ingested into Astra DB. Each chunk is expected
                       to be a piece of text or data that, along with its embedding, will be stored in the specified
                       collection.

        :return: None. Logs the outcome of the ingestion process, including the number of documents inserted into
                 Astra DB during an actual run, or the details of the simulated actions during a dry run.
        """
        if self.dry_run:
            logging.info(
                f"[Dry Run] Would persist the chunks in Astra DB: {self.astra_url}. Namespace: {self.astra_keyspace}. "
                f"Chunks: {chunks}")
            return

        for attempt in range(self.max_retries):
            try:
                inserted_ids = self.vstore.add_documents(chunks)
                logging.info(f"\nInserted {len(inserted_ids)} documents.")
                return inserted_ids
            except Exception as e:  # Consider specifying more specific exception(s) based on your context
                logging.error(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < self.max_retries - 1:
                    logging.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logging.error(f"All {self.max_retries} attempts failed. Giving up.")
                    raise

    def get_similarity_search_with_score(self, collection_name: str, embeddings, query: str, k: int = 3):
        vstore = AstraDBVectorStore(
            embedding=embeddings,
            collection_name=collection_name,
            token=self.astra_application_token,
            api_endpoint=self.astra_url,
            namespace=self.astra_keyspace
        )
        return vstore.similarity_search_with_score(query, k=k)

    def get_max_marginal_relevance_search(self, collection_name: str, embeddings, query: str, query_filter: dict,
                                          k: int = 3):
        vstore = AstraDBVectorStore(
            embedding=embeddings,
            collection_name=collection_name,
            token=self.astra_application_token,
            api_endpoint=self.astra_url,
            namespace=self.astra_keyspace
        )
        return vstore.max_marginal_relevance_search(query, k=k, filter=query_filter)
