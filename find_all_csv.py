import os

def search_csv(start_dir):
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if file.endswith('.csv'):
                print(os.path.abspath(os.path.join(root, file)))

search_csv('.')
