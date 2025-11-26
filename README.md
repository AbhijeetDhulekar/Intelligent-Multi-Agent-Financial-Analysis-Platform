
# How to run the piplene 
# Terminal 1:
# change the directory to the env variable
fab_env/scripts/activate

# set up library
cp .env.example .env

#  Run system
python main.py --mode api


# Terminal 2:
# change the directory to the env variable
fab_env/scripts/activate

# set up library
cp .env.example .env

#  Run system
python main.py --mode ui
