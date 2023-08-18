import json

def print_json_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
        print(json.dumps(data, indent=4))
if __name__ == "__main__":
    filename = input("Filename: ")
    print_json_file(filename)
