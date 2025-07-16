import pandas as pd
import numpy as np
import re
import sys
import os
import json
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

# Get the directory where the Python script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'fulldata.csv')
fulldata = pd.read_csv(csv_path, low_memory=False)

# Function to clean anime titles by removing unwanted keywords
def clean_title(title):
    title = title.lower()
    keywords_to_remove = [
        "season", "movie", "part", "ova", "special", "final", "complete",
        "collection", "edition", "chapter", "arc", "episode", "ep", "vol",
        "volume", "tv", "the", "1st", "2nd", "3rd", "4th", "5th", "6th", "7th",
        "8th", "9th", "0th", "first", "second", "third", "fourth", "fifth",
        "sixth", "seventh", "eighth", "ninth", "tenth"
    ]
    pattern = r'\b(?:' + '|'.join(map(re.escape, keywords_to_remove)) + r')\b'
    title = re.sub(pattern, '', title)
    title = re.sub(r'\bs\d+\b', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

# Function to check if the candidate anime is similar to any anime already in the list
def check_similar(candidate, current_list):
    candidate_lower = clean_title(candidate)
    for existing in current_list:
        existing_lower = clean_title(existing)
        if candidate_lower == existing_lower or candidate_lower in existing_lower or existing_lower in candidate_lower:
            return True
    return False

# Main function for getting anime recommendations
def three(anime_name, n=10):
    try:
        # === 1. Prepare Data ===
        anime_stats = fulldata.groupby(['anime_id', 'name', 'genre']).agg(
            avg_rating=('user_rating', 'mean'),
            rating_count=('user_rating', 'count')
        ).reset_index()

        rating_matrix = fulldata.pivot_table(
            index='user_id',
            columns='name',
            values='user_rating',
            fill_value=0
        ).T

        # === 2. Find Target Anime ===
        target_mask = anime_stats['name'].str.lower() == anime_name.lower()
        if not target_mask.any():
            target_mask = anime_stats['name'].str.contains(anime_name, case=False)
            if not target_mask.any():
                return json.dumps({"Error": f"'{anime_name}' not found"})
        
        target_idx = target_mask.idxmax()
        target_name = anime_stats.loc[target_idx, 'name']

        # === 3. Genre Similarity Filter ===
        genres = anime_stats['genre'].str.get_dummies(', ')
        genre_sim = cosine_similarity(genres)

        sim_indices = np.argsort(genre_sim[target_idx])[::-1][1:1001]
        candidate_df = anime_stats.iloc[sim_indices]

        # === 4. KNN Refinement ===
        valid_candidates = [name for name in candidate_df['name'] if name in rating_matrix.index]

        if not valid_candidates:
            return json.dumps({"Error": "No valid candidates for KNN"})

        knn = NearestNeighbors(n_neighbors=min(n+1, len(valid_candidates)), metric='correlation')
        knn.fit(rating_matrix.loc[valid_candidates])

        if target_name not in rating_matrix.index:
            distances, indices = knn.kneighbors(rating_matrix.loc[[valid_candidates[0]]], n_neighbors=n)
        else:
            distances, indices = knn.kneighbors(rating_matrix.loc[[target_name]], n_neighbors=n+1)

        # === 5. Strict Recommendation Filtering ===
        rec_names = []
        target_lower = target_name.lower()

        for idx in indices[0]:
            candidate = valid_candidates[idx]
            candidate_lower = candidate.lower()

            if (candidate_lower == target_lower) or (target_lower in candidate_lower) or (candidate_lower in target_lower):
                continue

            if check_similar(candidate, rec_names):
                continue

            rec_names.append(candidate)

            if len(rec_names) >= n:
                break

        # === 6. Prepare Output ===
        if not rec_names:
            return json.dumps({"Error": "No valid recommendations after filtering"})

        # Convert recommendations to DataFrame
        recommendations_df = pd.DataFrame({
            "Rank": range(1, len(rec_names) + 1),
            "Anime": rec_names
        })

        # Debug: Check if the DataFrame is empty before converting to JSON
        if recommendations_df.empty:
            return json.dumps({"Error": "No valid recommendations after filtering"})

        # Convert the DataFrame to JSON, with the rank as the key
        result_json = recommendations_df.set_index('Rank')['Anime'].to_json()

        # Return the valid JSON response
        return result_json

    except Exception as e:
        # Return the error message as a valid JSON string
        return json.dumps({"Error": "System error", "Details": str(e)})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <anime_name>")
        sys.exit(1)

    anime_name = sys.argv[1]
    recommendations = three(anime_name)

    # Print the recommendations or error in JSON format
    print(recommendations)



# to put all the dependencies
# pip freeze > python/requirements.txt