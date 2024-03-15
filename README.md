
<documents>
<p align="center">
    <img src="./assets/logo.png" width = 30% >
</p>

#

The doc knowledge AI assistant application is an AI-powered conversational tool designed to enhance customer engagement and increase sales efficiency. It utilizes a cutting-edge retrieve-augment chatbot architecture to provide sales representatives with quick access to historical customer data and generate informed responses during live chats.

The application interfaces with an organization's SharePoint instance to ingest customer data including profiles, previous communications, and case study records. This raw data is then preprocessed and embedded into dense vector representations optimized for semantic search. At runtime, user queries are augmented and used to retrieve the most relevant data to contextually guide response generation powered by large language models. 

The full-stack architecture combines data processing, storage, and machine learning components offered through AWS, including Bedrock, AstraDB, and EC2. Custom components handle tasks like data augmentation, text embeddings, retrieval, and response generation. The frontend is built using Streamlit and delivered through Streamlit Cloud for ease of access.

Overall, the doc knowledge AI assistant application aims to tap into collective knowledge and history to assist sales representatives in providing quick, informed, and personalized responses to customer questions and needs. The document discusses the architecture and components powering the solution to deliver next-generation conversational experiences.


## Project Structure

Below is the project structure for **doc-knowledge-ai-assistant**, providing an overview of the main components and their purpose:

```
├── assets/                  # Media assets such as logos
├── docs/                    # Documentation for the project
├── scripts/                 # Maintenance and setup scripts
├── src/                     # Contains all source code
│   ├── sharepoint_bulk_ingestion/ # Module for SharePoint data ingestion
│   │   ├── __init__.py      # Package initialization
│   │   ├── ...              # Additional module files
│   │   └── requirements.txt # Dependencies for sharepoint_bulk_ingestion module
├── terraform/               # Terraform configurations
│   ├── terraform_infra/     # Infrastructure as code for setting up the environment
│   └── terraform_deployment/ # Terraform scripts for deployment procedures
├── tests/                   # Automated tests
├── .gitignore               # Specifies intentionally untracked files to ignore
├── LICENSE                  # The license under which the project is made available
├── README.md                # Project overview, setup instructions, and guidelines
└── setup.sh                 # Script to set up the project's environment (venv setup)
```



## Architecture Overview

<img src="./docs/Version Current/doc-knowledge-ai-assistant-v1-svg-100.svg"> 

The doc knowledge AI assistant application is built using a Retrieve-Augment Chatbot architecture with the following main components:

- esynergy documents hosted in Microsoft SharePoint
- Data preprocessing using Langchain Framework and Azure SaaS Services
- Vector database search using AstraDB  
- AWS Bedrock for text embedding models
- Anthopic Claude2 large language model for text generation 
- esynergy customized retrieval and augmentation
- FastAPI and Nginx for API deployment
- [Streamlit](https://streamlit.io/) frontend deployed on Streamlit Cloud

## Data Flow 

1. The SharePoint data is temporarily downloaded for preprocessing using the Microsoft Graph API
2. Langchain Framework is used to recursively split files into chunks for processing 
3. File chunks are vectorized into embeddings using AWS Bedrock Titan model
4. Embedded chunks are indexed in AstraDB as the vector database 
5. User query is taken as input in the Streamlit frontend 
6. Query is augmented using EsyNergy customized techniques
7. Relevant document chunks retrieved from vector database using optimized MMR
8. AWS Bedrock Claude2 model generates a response for the query from chunks  
9. Response is returned to the user via the API and displayed in Streamlit

## Components

### Data Processing

- The raw SharePoint data in CSV/JSON/Doc/Docx/HTML/PDF formats (more formats supported except MP4, MP3 or other codec based formats) is temporarily downloaded for preprocessing using the Microsoft Graph API 
- Langchain Framework splits data into chunks for vectorization
- AWS Bedrock Titan model creates dense vector embeddings 
- AstraDB indexes vectors for fast nearest neighbor search

### Query Processing 

- EsyNergy customized retrieval using MMR reranking
- Query augmentation techniques like paraphrasing 
- Retrieved relevant document chunks from vector database 

### Response Generation  

- AWS Bedrock Claude2 generates responses for queries
- Fine-tuned for conversational response generation 
- Contextual responses created from retrieved documents

### Deployment 

- FastAPI framework for building API with Python  
- Nginx web server for API deployment on AWS EC2
- Streamlit framework for building frontend
- Streamlit cloud for managed deployment of frontend app

## AWS GenAI Services

### [AWS Bedrock](https://aws.amazon.com/bedrock/)

AWS Bedrock provides managed access to state-of-the-art models for text generation and embedding. 

**[Titan Embeddings Model](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)**

- Dense vector embedding model for encoding text 
- Maps text strings to vectors in high-dimensional space
- Allows semantic similarity calculation via cosine distance
- Indexed in AstraDB for efficient nearest neighbor search

**[Claude2 Language Model](https://aws.amazon.com/bedrock/claude/)** 

- Large conversational language model with 2.7B parameters
- Fine-tuned on dialog data for natural responses  
- Generates informed responses based on retrieved documents
- Integrated via Bedrock model APIs

### [AstraDB](https://www.datastax.com/products/astra-db)

- Fully managed Apache Cassandra compatible NoSQL database 
- Provides document and graph data models
- Scales elastically while maintaining low latency
- Secure, resilient and highly available 

## Use Cases

- **Retrieving Case Studies** - Sales reps can rapidly pull up relevant case studies, projects, and customer success stories by querying the system during a chat. This provides supporting proof for product capabilities.

- **Getting Project Details** - When chatting with a customer about an ongoing or past project, reps can obtain specifics like timelines, milestones, and deliverables quickly without having to search across multiple systems.

- **Generating New Case Studies** - The system can auto-generate draft case studies using an existing case study as a template, replacing names, stats, and other details as provided by the sales rep. 

- **Improving Case Studies** - Reps can ask the system for suggestions on improving a case study, such as adding more metrics, focusing on certain details, or clarifying the challenges faced.

- **Drafting Communications** - The application can draft emails, chat messages, social media posts, etc. tailored for a customer based on past interactions and knowledge.

- **Generating Reports** - Sales reps can ask for customized reports or comparisons across projects, campaigns, and other initiatives to extract key insights.

- **Analytics** - The stored data can provide various analytics on campaigns, lead conversion rates, customer sentiment, conversational metrics, and more to inform strategy.

In summary, the chatbot acts as an AI assistant to augment the sales rep's knowledge and productivity when engaging with customers. The data-driven responses reduce repetitive searching tasks while improving quality of interactions.

## Additional Information

The following are the further information about the tech stack used for the application.

**[Langchain Framework](https://python.langchain.com/docs/get_started/introduction)**

- Open source library for working with large language models
- Used here for data splitting and preprocessing  
- Recursive splitting to break documents into chunks
- Prepares data for vectorization

**Query Processing** 

- **EsyNergy Custom Retrieval** - Reranking and query augmentation techniques to optimize relevant document retrieval
- **MMR** - Algorithm for retrieving diverse set of relevant documents, balanced across topics/aspects
- **Query Paraphrasing** - Rewrites queries into additional variations to improve coverage

**[FastAPI](https://fastapi.tiangolo.com/)**
- Python web framework for building APIs
- Uses Pydantic for request data validation 
- Async routes supported for performance
- Generated Open API documentation

**[Nginx](https://docs.nginx.com/)**
- High performance open source web server 
- Handles client requests and proxies to API
- Configured for security, logging, traffic shaping
- Deployed on AWS EC2 instance
