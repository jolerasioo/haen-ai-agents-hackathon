import json



# Mock Cosmos DB client for the citizen data
class MockCosmosClient:
    data_path = './data/citizen_data.json'
    def __init__(self):
        with open(self.data_path, 'r') as f:
            self.data = json.load(f)

    def get_all_citizen_data(self):
        return self.data
    
data_path = './data/citizen_data.json'

def get_all_citizen_data():
    with open(data_path, 'r') as f:
        data = json.load(f)
    return data['citizenDb']



