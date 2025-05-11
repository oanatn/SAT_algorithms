import random
import time
import math
from collections import defaultdict
import json


def negate(literal):
    """Negate a literal."""
    return -literal


def apply_literal(formula, literal):
    """Apply a literal to the formula by removing satisfied clauses and simplifying."""
    neg_literal = negate(literal)
    new_formula = []
    
    for clause in formula:
        if literal in clause:
            continue  # clause is satisfied
        if neg_literal in clause:
            new_clause = [l for l in clause if l != neg_literal]
            if not new_clause:  # empty clause ⇒ UNSAT
                return None
            new_formula.append(new_clause)
        else:
            new_formula.append(clause)
    return new_formula


def find_unit_clause(formula):
    """Find a unit clause (a clause with exactly one literal)."""
    for clause in formula:
        if len(clause) == 1:
            return clause[0]
    return None


def unit_propagation(formula):
    """Apply unit propagation to simplify the formula."""
    assignment = {}
    while True:
        unit_clause = find_unit_clause(formula)
        if unit_clause:
            assignment[unit_clause] = True
            formula = apply_literal(formula, unit_clause)
            if formula is None:
                return None, assignment  # UNSAT
            continue
        break
    return formula, assignment


def unit_subsumption(formula, assignment):
    """Simplify the formula by removing clauses satisfied by the current assignment."""
    if formula is None or [] in formula:
        return None  # UNSAT due to empty clause
    
    new_formula = []
    for clause in formula:
        if not any(literal in assignment for literal in clause):
            new_formula.append(clause)
    return new_formula


def monotone_literal_fixing(formula):
    """Fix monotone literals and apply their assignments to simplify the formula."""
    assignment = {}
    for clause in formula:
        for literal in clause:
            if -literal not in [lit for subclause in formula for lit in subclause]:
                assignment[literal] = True
                formula = [c for c in formula if literal not in c]  # Remove satisfied clauses
                break
    return formula, assignment


def choose_literal(formula):
    """C-SAT heuristic: Choose the literal with the maximum weight."""
    literal_scores = defaultdict(float)
    for clause in formula:
        k = len(clause)
        if k == 0:
            continue
        weight = math.log(1 + 1 / (4 ** k - 2 ** (k + 1)))
        for lit in clause:
            literal_scores[lit] += weight
    return max(literal_scores, key=literal_scores.get, default=None)


def dpll(formula, log_file="dpll_log.txt"):
    """DPLL algorithm with C-SAT heuristic, unit propagation, subsumption, and monotone literal fixing."""
    formula, unit_assignments = unit_propagation(formula)
    if formula is None or [] in formula:
        return False, formula  # UNSAT due to empty clause or contradiction

    formula = unit_subsumption(formula, unit_assignments)
    if formula is None or [] in formula:
        return False, formula  # UNSAT after subsumption

    formula, mono_assignments = monotone_literal_fixing(formula)
    unit_assignments.update(mono_assignments)

    if not formula:
        return True, formula  # SAT (no clauses left, all satisfied)

    if [] in formula:
        return False, formula  # UNSAT due to empty clause

    # Now apply the C-SAT branching rule
    literal = choose_literal(formula)
    if not literal:
        return False, formula  # No literal to choose, hence UNSAT

    # Try assigning the literal positively
    new_formula = apply_literal(formula, literal)
    if new_formula is not None:
        new_formula, _ = unit_propagation(new_formula)
        if new_formula is None or [] in new_formula:
            return False, new_formula
        new_formula = unit_subsumption(new_formula, unit_assignments)
        new_formula, _ = monotone_literal_fixing(new_formula)
        sat, final_formula = dpll(new_formula, log_file)
        if sat:
            return True, final_formula

    # Try assigning the literal negatively
    new_formula = apply_literal(formula, negate(literal))
    if new_formula is not None:
        new_formula, _ = unit_propagation(new_formula)
        if new_formula is None or [] in new_formula:
            return False, new_formula
        new_formula = unit_subsumption(new_formula, unit_assignments)
        new_formula, _ = monotone_literal_fixing(new_formula)
        sat, final_formula = dpll(new_formula, log_file)
        if sat:
            return True, final_formula

    return False, formula  # UNSAT


def log_results(result, start_time):
    """Log the results with only SAT or UNSAT, and the time."""
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    status = "SAT" if result else "UNSAT"
    log_message = f"{status} ({elapsed_time:.6f}s)"
    print(log_message)
    return log_message, elapsed_time


def process_clause_sets(file_path, log_file="dpll_log.txt"):
    """Process clause sets from a file and apply the DPLL algorithm."""
    with open(file_path, 'r') as file:
        clause_sets = json.load(file)

    total_time = 0
    solved_count = 0
    unsolved_count = 0
    total_count = len(clause_sets)
    all_logs = []

    for idx, clause_set in enumerate(clause_sets, 1):
        print(f"Processing Clause Set {idx}...")
        start_time = time.perf_counter()
        result, _ = dpll(clause_set, log_file)
        log_message, elapsed_time = log_results(result, start_time)
        all_logs.append(log_message)
        total_time += elapsed_time
        solved_count += result
        unsolved_count += not result

    average_time = total_time / total_count if total_count > 0 else 0
    summary_message = f"\nSolved clause sets (SAT): {solved_count}/{total_count}\n"
    summary_message += f"Solved clause sets (UNSAT): {unsolved_count}/{total_count}\n"
    summary_message += f"Total time: {total_time:.6f}s\n"
    summary_message += f"Average time: {average_time:.6f}s\n"
    print(summary_message)

    with open(log_file, 'a') as file:
        for log in all_logs:
            file.write(log + "\n")
        file.write(summary_message + "\n")


file_path = "datasets/clause_sets.json"  # Path to your clause sets
process_clause_sets(file_path)
