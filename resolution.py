import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from copy import deepcopy
import itertools

# Timeout configuration
TIMEOUT = 60  # seconds

def resolve(clause1, clause2, literal):
    """Generate the resolvent of two clauses with a given literal."""
    resolvent = list(set(clause1 + clause2) - {literal, -literal})
    return resolvent

def is_redundant_clause(clause):
    """Check if a clause contains a literal and its negation (redundant clause)."""
    return any(literal == -other for literal in clause for other in clause)

def find_resolvents(c1, c2):
    """Find all possible resolvents for two clauses."""
    resolvents = []
    for literal in c1:
        if -literal in c2:
            resolvent = resolve(c1, c2, literal)
            if resolvent not in resolvents and not is_redundant_clause(resolvent):
                resolvents.append(resolvent)
    return resolvents

def resolution(clauses):
    """Apply resolution to find a contradiction (if any)."""
    clauses = deepcopy(clauses)
    clause_set = set(map(tuple, clauses))

    while True:
        new = set()
        # Generate unique pairs using combinations
        pairs = itertools.combinations(clauses, 2)

        for c1, c2 in pairs:
            resolvents = find_resolvents(c1, c2)
            for resolvent in resolvents:
                if not resolvent:  # Empty clause found ⇒ UNSAT
                    return 0  # UNSAT
                sorted_resolvent = tuple(sorted(resolvent))
                if sorted_resolvent not in clause_set:
                    new.add(sorted_resolvent)

        if not new:
            # If no new clauses are generated, the set is satisfiable
            return 1  # SAT

        clause_set.update(new)
        clauses.extend([list(clause) for clause in new])

def log_result(log_file, message):
    """Log a message to the specified file."""
    print(message)  # Print to console as well
    with open(log_file, 'a') as file:
        file.write(f"{message}\n")

def process_clause_sets(file_path, log_file="resolution_log.txt"):
    """Process clause sets from a JSON file and apply the resolution algorithm."""
    with open(file_path, 'r') as file:
        clause_sets = json.load(file)

    # Initialize counters for the summary
    solved_sat = 0
    solved_unsat = 0
    timed_out = 0
    total_time = 0.0

    # Log header
    with open(log_file, 'w') as file:
        file.write(f"Resolution Algorithm Log - {time.ctime()}\n\n")

    # Process each clause set
    for idx, clause_set in enumerate(clause_sets, 1):
        log_result(log_file, f"Processing Clause Set {idx}...")

        # Use perf_counter for precise timing
        start_time = time.perf_counter()
        result = None

        # Run with timeout
        with ThreadPoolExecutor() as executor:
            future = executor.submit(resolution, clause_set)
            try:
                result = future.result(timeout=TIMEOUT)
                elapsed_time = time.perf_counter() - start_time
                total_time += elapsed_time
                if result == 0:
                    solved_unsat += 1
                    log_result(log_file, f"Clause Set {idx}: UNSAT (Time: {elapsed_time:.6f}s)")
                elif result == 1:
                    solved_sat += 1
                    log_result(log_file, f"Clause Set {idx}: SAT (Time: {elapsed_time:.6f}s)")

            except TimeoutError:
                elapsed_time = time.perf_counter() - start_time
                timed_out += 1
                log_result(log_file, f"Clause Set {idx}: TIMEOUT after {elapsed_time:.6f}s")

    # Summary of results
    summary = (
        f"\nSummary of Results:\n"
        f"  Solved Clause Sets (SAT): {solved_sat}\n"
        f"  Solved Clause Sets (UNSAT): {solved_unsat}\n"
        f"  Timed Out Clause Sets: {timed_out}\n"
        f"  Total Time Taken: {total_time:.6f}s\n"
        f"  Average Time per Solved Set: "
        f"{(total_time / (solved_sat + solved_unsat)):.6f}s\n" if (solved_sat + solved_unsat) > 0 else "N/A"
    )
    log_result(log_file, summary)

    return {
        "solved_sat": solved_sat,
        "solved_unsat": solved_unsat,
        "timed_out": timed_out,
        "total_time": total_time
    }

# Example usage
file_path = "datasets/clause_sets.json"
process_clause_sets(file_path)
