import json
import os

def read_cnf_file(filename):
    clauses = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            # Skip comments and the problem line
            if line.startswith('c') or line.startswith('p') or line.startswith('%'):
                continue
            # Convert the clause line to a list of integers
            clause = list(map(int, line.split()))[:-1]  # Exclude the trailing 0
            if clause:
                clauses.append(clause)
    return clauses

def append_to_json(clause_set, json_filename="clause_sets.json"):
    # If the JSON file doesn't exist, create it
    if not os.path.exists(json_filename):
        with open(json_filename, 'w') as json_file:
            json.dump([], json_file)

    # Now try to load the data
    try:
        with open(json_filename, 'r') as json_file:
            data = json.load(json_file)
    except json.JSONDecodeError:
        print(f"Warning: {json_filename} was empty or corrupted. Reinitializing...")
        data = []

    # Append the new clause set as a whole
    data.append(clause_set)

    # Custom write to match your format
    with open(json_filename, 'w') as json_file:
        json_file.write("[\n")
        for idx, clause_set in enumerate(data):
            # Write each clause set on its own line, with a comma if not the last
            json_file.write(f"{json.dumps(clause_set)}")
            if idx < len(data) - 1:
                json_file.write(",\n")
        json_file.write("\n]")
        
# Example usage
cnf_filename = "in.cnf"  # Change this to your .cnf file name
clause_set = read_cnf_file(cnf_filename)
append_to_json(clause_set)
print(f"Appended clauses from {cnf_filename} to clause_sets.json")
