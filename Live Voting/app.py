import time
import simplejson as json
from kafka import KafkaConsumer
import pandas as pd
from datetime import datetime
import requests
from vote_prediction.model import predict_win_probabilities, create_model, VotingFeatureExtractor, read_csv, train_model

# Function to create a Kafka consumer
def create_kafka_consumer(topic_name):
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    return consumer

def predict():
    csv_file_path = "train.csv"  
    
    feature_extractor = VotingFeatureExtractor()
    model = create_model()
    
    print("Training model...")
    trained_model, final_metric = train_model(model, feature_extractor, read_csv(csv_file_path))
    
    print(f"\nTraining completed. Final MacroF1 score: {final_metric.get():.4f}")

    return trained_model, feature_extractor


def make_prediction(trained_model, feature_extractor, voter_data):

    if voter_data is not None:
        new_vote = {
            "voter_id": voter_data['voter_id'],
            "voting_time": voter_data['voting_time'],
            "polling_station_id": voter_data['polling_station_id'],
            "candidate_id": voter_data['candidate_id'],
            "district_id": voter_data['district_id'],
            "vote_type": voter_data['vote_type']
        }
    
        new_features = feature_extractor.extract(new_vote)
        probabilities = predict_win_probabilities(trained_model, new_features)
        
        print("Predicted win probabilities:")
        for candidate, probability in probabilities.items():
            print(f"{candidate}: {probability:.2%}")
        
        result = {candidate: float(probability) for candidate, probability in probabilities.items()}

        return result

    else:
        print("No new vote data available.")


def get_new_vote():
    consumer = create_kafka_consumer("votes_topic")
    messages = consumer.poll(timeout_ms=1000)
    
    sub_message_1 = None

    for message in messages.values():
        for sub_message in message:
            sub_message_1 = sub_message.value
            break
    
    return sub_message_1

def fetch_data_from_kafka(consumer, csv_file):
    messages = consumer.poll(timeout_ms=1000)
    data = []

    for message in messages.values():
        for sub_message in message:
            data.append(sub_message.value)
    
    # Append the messages to a CSV file
    if data:
        df = pd.DataFrame(data)
        df.to_csv(csv_file, mode='a', header=not pd.io.common.file_exists(csv_file), index=False)

def process_and_save_data(df, csv_file):
    if not df.empty:
        # Group by 'candidate_name' and 'candidate_id' and count occurrences
        grouped_df = df.groupby('candidate_id').size().reset_index(name='count_each_at_time')
        
        # Add a timestamp column for when the data is processed
        grouped_df['time_stamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Append the grouped data to the grouped CSV file
        grouped_df[['candidate_id', 'time_stamp', 'count_each_at_time']].to_csv(
            csv_file, 
            mode='a', 
            header=not pd.io.common.file_exists(csv_file), 
            index=False
        )

# Function to display Kafka data and save to CSV
def display_kafka_data():
    consumer = create_kafka_consumer("votes_topic")
    csv_file = 'kafka_messages.csv'
    
    # Fetch data from Kafka and append to CSV
    fetch_data_from_kafka(consumer, csv_file)
    if pd.io.common.file_exists(csv_file):
        process_and_save_data(pd.read_csv(csv_file), 'grouped_votes.csv')


# Run the function to display data
if __name__ == "__main__":

    i = None

    data = None

    while True:
        display_kafka_data()
        time.sleep(5)  

        vote = get_new_vote()

        while(i is None):
            print("Model not yet trained. Training model...")
            model, feature_extractor = predict()
            i = 1
        
        data = make_prediction(model, feature_extractor, vote)
        try:
            response = requests.post('http://localhost:8502/receive_data', json=data)
        except requests.exceptions.RequestException as e:
            print(f"Failed to send data: {e}")
