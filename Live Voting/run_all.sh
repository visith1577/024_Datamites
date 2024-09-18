#!/bin/zsh

# Start Docker containers
docker-compose up -d

# Run Python scripts simultaneously
python main.py &
python voting.py &
python spark-streaming.py &
python app.py &

# Wait for all background jobs to finish
wait
