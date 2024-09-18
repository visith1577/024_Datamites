from river import metrics, compose, preprocessing
from river import forest
from datetime import datetime
import csv
import random

class VotingFeatureExtractor:
    def __init__(self):
        self.total_votes = 0
        self.candidate_votes = {}
        self.district_votes = {}
        self.polling_station_votes = {}
        self.vote_type_counts = {}

    def extract(self, vote):
        self.total_votes += 1
        # Update candidate votes
        self.candidate_votes[vote['candidate_id']] = self.candidate_votes.get(vote['candidate_id'], 0) + 1

        # Update district votes
        self.district_votes[vote['district_id']] = self.district_votes.get(vote['district_id'], 0) + 1

        # Update polling station votes
        self.polling_station_votes[vote['polling_station_id']] = self.polling_station_votes.get(vote['polling_station_id'], 0) + 1

        # Update vote type counts
        self.vote_type_counts[vote['vote_type']] = self.vote_type_counts.get(vote['vote_type'], 0) + 1

        # Extract time features
        timestamp = datetime.fromisoformat(vote['voting_time'].replace('Z', '+00:00'))

        features = {
            'total_votes': self.total_votes,
            'time_of_day': timestamp.hour + timestamp.minute / 60,
            'candidate_votes': self.candidate_votes[vote['candidate_id']],
            'candidate_vote_share': self.candidate_votes[vote['candidate_id']] / self.total_votes,
            'district_votes': self.district_votes[vote['district_id']],
            'district_vote_share': self.district_votes[vote['district_id']] / self.total_votes,
            'polling_station_votes': self.polling_station_votes[vote['polling_station_id']],
            'polling_station_vote_share': self.polling_station_votes[vote['polling_station_id']] / self.total_votes,
            'vote_type_count': self.vote_type_counts[vote['vote_type']],
            'vote_type_share': self.vote_type_counts[vote['vote_type']] / self.total_votes
        }

        return features


def create_model():
    return compose.Pipeline(
        ('feat', preprocessing.StandardScaler()),
        ('clf', forest.ARFClassifier(n_models=10, seed=42))
    )


def read_csv(filepath):
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield row


def train_model(model, feature_extractor, data_iterator):
    metric = metrics.MacroF1()

    for i, vote in enumerate(data_iterator):
        X = feature_extractor.extract(vote)
        y = vote['candidate_id']

        # Make prediction (handle cases where model can't predict)
        y_pred = model.predict_one(X)
        metric.update(y, y_pred)

        # Train the model
        model.learn_one(X, y)

        # Print progress
        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1} votes. Current MacroF1 score: {metric.get():.4f}")

    return model, metric


def predict_win_probabilities(model, features):
    return model.predict_proba_one(features)
