import json

class JSONParser:
    def __init__(self, json_string):
        self.json_string = json_string

    def parse(self):
        try:
            parsed_data = json.loads(self.json_string)
            return parsed_data
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar o JSON: {e}")
            return {}
        

