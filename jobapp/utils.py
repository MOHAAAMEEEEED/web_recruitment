from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import BertTokenizer, BertModel

# Load BERT model and tokenizer for sentence embeddings
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

def get_bert_embedding(text):
    """ Generate BERT embeddings for a given text """
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    # Use the embeddings of the [CLS] token (first token)
    return outputs.last_hidden_state[:, 0, :].squeeze().numpy()

def calculate_similarity_score(job_description, transcription):
    # TF-IDF Similarity
    documents = [job_description, transcription]
    
    # Use TF-IDF to vectorize the text
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    # Calculate cosine similarity between the job description and the transcription using TF-IDF
    tfidf_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0][0]
    
    # BERT Similarity
    job_description_embedding = get_bert_embedding(job_description)
    transcription_embedding = get_bert_embedding(transcription)
    
    # Calculate cosine similarity between BERT embeddings
    bert_similarity = cosine_similarity([job_description_embedding], [transcription_embedding])[0][0]
    
    # Combine the two similarity scores (you can adjust the weight of each if desired)
    combined_similarity_score = 0.5 * tfidf_similarity + 0.5 * bert_similarity
    
    # Return the combined similarity score (a value between 0 and 1)
    return combined_similarity_score