import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from collections import Counter

# Timeout configuration
TIMEOUT = 60  # seconds

def unit_propagation(clauses):
    assignment = {}
    while True:
        unit_clauses = [c for c in clauses if len(c) == 1]
        if not unit_clauses:
            break
        for unit in unit_clauses:
            literal = unit[0]
            assignment[literal] = True
            clauses = [list(c) for c in clauses if literal not in c]  # Convert to lists here
            for clause in clauses:
                if -literal in clause:
                    clause.remove(-literal)
    return clauses, assignment

def monotone_literal_fixing(clauses):
    assignment = {}
    all_literals = [literal for clause in clauses for literal in clause]
    counter = Counter(all_literals)
    for literal, count in counter.items():
        if -literal not in counter:
            assignment[literal] = True
            clauses = [list(c) for c in clauses if literal not in c]  # Convert to lists here
    return clauses, assignment

def is_redundant_clause(clause):
    """Check if a clause contains a literal and its negation (redundant clause)."""
    return any(literal == -other for literal in clause for other in clause)

def find_resolvents(c1, c2):
    """Find all possible resolvents for two clauses."""
    resolvents = []
    for literal in c1:
        if -literal in c2:
            resolvent = list(set(c1 + c2) - {literal, -literal})
            if resolvent and not is_redundant_clause(resolvent) and resolvent not in resolvents:
                resolvents.append(resolvent)
    return resolvents

def davis_putnam(clauses):
    final_assignment = {}
    previous_clauses = set()  # To track the clauses processed in the current iteration

    while clauses:
        # Apply Unit Propagation as long as possible
        try:
            clauses, unit_assignments = unit_propagation(clauses)
            final_assignment.update(unit_assignments)
        except Exception:
            return 0, {}  # Return UNSAT on failure

        # Apply Monotone Literal Fixing as long as possible
        try:
            clauses, mono_assignments = monotone_literal_fixing(clauses)
            final_assignment.update(mono_assignments)
        except Exception:
            return 0, {}  # Return UNSAT on failure

        # If clauses became empty, it's satisfiable
        if not clauses:
            return 1, final_assignment  # SAT
        
        # If there's an empty clause, it's unsatisfiable
        if [] in clauses:
            return 0, {}  # UNSAT

        # Perform resolution on the clause set
        new_clauses = set()
        pairs = [(clauses[i], clauses[j]) for i in range(len(clauses)) for j in range(i + 1, len(clauses))]

        for c1, c2 in pairs:
            resolvents = find_resolvents(c1, c2)
            for resolvent in resolvents:
                if not resolvent:  # If empty clause found ⇒ UNSAT
                    return 0, {}
                new_clauses.add(tuple(sorted(resolvent)))

        # If no new clauses were added, return SAT (no progress made)
        if new_clauses == previous_clauses:
            return 1, final_assignment  # SAT (no progress made)

        # Update the clauses with new ones and avoid duplicates
        previous_clauses = new_clauses
        clauses = list(set(map(tuple, clauses + list(new_clauses))))  # Convert clauses to tuples for uniqueness

        # Remove redundant clauses
        clauses = [list(clause) for clause in clauses if not is_redundant_clause(clause)]  # Convert to lists here

        # After resolution, check again for unit propagation and monotone literal fixing
        try:
            clauses, unit_assignments = unit_propagation(clauses)
            clauses, mono_assignments = monotone_literal_fixing(clauses)
            final_assignment.update(unit_assignments)
            final_assignment.update(mono_assignments)
        except Exception:
            return 0, {}  # Return UNSAT on failure

        # If no progress has been made after simplification and resolution, return SAT
        if not clauses:
            return 1, final_assignment  # SAT

    return 1, final_assignment  # SAT if clause set is empty

# === LOGGING AND PROCESSING ===

def log_result(log_file, message):
    """Log a message to the specified file."""
    with open(log_file, 'a') as file:
        file.write(f"{message}\n")
    print(message)  # Print to the console as well

def process_clause_sets(file_path, log_file="davis_putnam_log.txt"):
    """Process clause sets from a JSON file and apply the Davis-Putnam algorithm."""
    # Reading the file with multiple clause sets (assuming a JSON file format)
    with open(file_path, 'r') as file:
        clause_sets = json.load(file)

    # Initialize counters for the summary
    solved = 0
    timed_out = 0
    total_time = 0.0

    # Log header
    with open(log_file, 'w') as file:
        file.write(f"Davis-Putnam Algorithm Log - {time.ctime()}\n\n")

    # Process each clause set
    for idx, clause_set in enumerate(clause_sets, 1):
        log_result(log_file, f"Processing Clause Set {idx}...")

        start_time = time.perf_counter()  # Use perf_counter for better precision
        result = None

        # Run with timeout
        with ThreadPoolExecutor() as executor:
            future = executor.submit(davis_putnam, clause_set)
            try:
                result, _ = future.result(timeout=TIMEOUT)
                elapsed_time = time.perf_counter() - start_time  # Use perf_counter for elapsed time
                total_time += elapsed_time
                solved += 1
                log_result(log_file, f"Clause Set {idx}: {'SAT' if result == 1 else 'UNSAT'} (Time: {elapsed_time:.6f}s)")

            except TimeoutError:
                elapsed_time = time.perf_counter() - start_time
                timed_out += 1
                log_result(log_file, f"Clause Set {idx}: TIMEOUT after {elapsed_time:.6f}s")
                continue  # Continue processing next clause set after a timeout

    # Summary of results
    summary = (
        f"\nSummary of Results:\n"
        f"Solved Clause Sets: {solved}\n"
        f"Timed Out Clause Sets: {timed_out}\n"
        f"Total Time Taken: {total_time:.6f}s\n"
        f"Average Time per Solved Set: {total_time/solved:.6f}s" if solved > 0 else "N/A"
    )
    log_result(log_file, summary)

    return {
        "solved": solved,
        "timed_out": timed_out,
        "total_time": total_time
    }

# Example usage
file_path = "datasets/clause_sets.json"
process_clause_sets(file_path)
