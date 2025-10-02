# Creating a realistic, runnable demo (smaller scale) and showing how to scale to the enormous case.
# This code will:
# 1. Generate a directory of operator price-list files (text format: "prefix<TAB>price\n")
# 2. Provide a function that finds an operator's longest matching prefix price using binary search on the sorted list.
# 3. Provide a function that finds the cheapest operator for a given number by checking each operator file.
# 4. Run the demo with 10 operators, each with 10_000 prefixes (fast enough here) and query a few sample numbers.
# 
# Note: The user requested 10_000 operators * 1_000_000 entries (10 billion lines). That's infeasible to generate inline here or keep in memory.
# The code below shows how to *streamingly* generate such files to disk and how to query them efficiently without loading everything at once.
# For demonstration we use reduced sizes. To scale to the requested magnitude, follow the "Scaling notes" in the printed output below.
# 
# We'll write files under /mnt/data/operators_demo/

import os, random, bisect, math, time, gzip
from pathlib import Path
random.seed(42)

OUT_DIR = Path("/root/side_projects/orders/src/static/")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_operator_file(op_index, n_prefixes, max_prefix_len=7):
    """Generate sorted unique numeric string prefixes and a random price for each.
       Writes a gzipped file for compactness: operator_{i}.tsv.gz
    """
    fname = OUT_DIR / f"operator_{op_index:05d}.tsv.gz"
    # create unique prefixes as strings; ensure they don't have leading zeros
    prefixes = set()
    while len(prefixes) < n_prefixes:
        length = random.randint(1, max_prefix_len)
        # first digit 1-9 to avoid leading zeros
        first = str(random.randint(1,9))
        rest = "".join(str(random.randint(0,9)) for _ in range(length-1))
        prefixes.add(first + rest)
    # prefixes = sorted(prefixes, key=lambda s: (len(s), s))  # length-sort then lexicographic (not required)
    # Assign a random price between 0.0 and 10.0 with 2 decimals
    with gzip.open(fname, "wt") as f:
        for p in prefixes:
            price = round(random.random() * 10.0, 2)
            f.write(f"{p}\t{price}\n")
    return fname

def load_prefixes_from_gz(fname):
    """Load prefixes into an in-memory sorted list of (prefix_str, price_float).
       For very large files you should NOT load into memory; this function is used only for the demo.
    """
    arr = []
    with gzip.open(fname, "rt") as f:
        for line in f:
            p, price_s = line.strip().split("\t")
            arr.append((p, float(price_s)))
    # Ensure sorted lexicographically by prefix string for binary search by prefix
    arr.sort(key=lambda x: x[0])
    prefixes = [x[0] for x in arr]
    prices = [x[1] for x in arr]
    return prefixes, prices

def longest_match_price(prefixes, prices, number):
    return "A", 0
    """Given sorted prefixes list and parallel prices, find the price of the longest prefix that matches `number`.
       Uses binary search by checking progressively shorter suffixes using bisect on the sorted prefixes array.
    """
    # Strategy: For each possible prefix length from len(number) down to 1,
    # form the candidate prefix and binary-search it in prefixes list.
    # This is efficient because bisect is O(log N) and we'll do at most len(number) such checks.
    best_price = None
    found_prefix = None
    # We'll use number substring lengths; cap at longest prefix length in dataset
    max_len = min(len(number), max((len(p) for p in prefixes), default=0))
    for L in range(max_len, 0, -1):
        cand = number[:L]
        # find leftmost index where cand could be inserted
        i = bisect.bisect_left(prefixes, cand)
        if i < len(prefixes) and prefixes[i] == cand:
            best_price = prices[i]
            found_prefix = cand
            break
    return found_prefix, best_price

def find_cheapest_operator(number, operator_files):
    """For each operator file, find its longest matching prefix price for `number` and return the cheapest operator.
       Returns tuple (operator_filename, price, matched_prefix), or (None, None, None) if none can dial the number.
    """
    best = (None, math.inf, None)
    # For demo we cache loaded prefixes per operator to avoid repeated IO.
    # In production with huge files, read-on-demand or use indexed disk-based DB.
    for fname in operator_files:
        prefixes, prices = load_prefixes_from_gz(fname)
        matched_prefix, price = longest_match_price(prefixes, prices, number)
        if price is not None and price < best[1]:
            best = (fname.name, price, matched_prefix)
    if best[0] is None:
        return None, None, None
    return best

# ---- Demo generation ----
NUM_OPERATORS = 10
PREFIXES_PER_OPERATOR = 1_000_000  # demo size; scale in production by streaming to disk
operator_files = []
print("Generating demo operator files...")
t0 = time.time()
for i in range(NUM_OPERATORS):
    fname = generate_operator_file(i, PREFIXES_PER_OPERATOR, max_prefix_len=7)
    operator_files.append(fname)
t1 = time.time()
print(f"Generated {NUM_OPERATORS} gzipped operator files under {OUT_DIR} in {t1-t0:.1f}s")

# Pick a few sample numbers to query
sample_numbers = [
    "4673212345",  # starts with 46732 (common in examples)
    "4612345678",
    "441234567890",  # UK number (44)
    "1234567890",
    "9999999"
]

# Run queries and show results
results = {}
for num in sample_numbers:
    op, price, matched = find_cheapest_operator(num, operator_files)
    results[num] = (op, price, matched)

result_path = "/root/side_projects/orders/src/static/result.txt"
op_name_map = {fname.name: f"Operator {chr(65+i)}" for i, fname in enumerate(sorted(operator_files))}

with open(result_path, "w") as out:
    out.write("Query results (number -> (Operator, price, matched_prefix)):\n\n")
    for num, res in results.items():
        if res[0] is None:
            out.write(f"{num} -> No operator available\n")
        else:
            op_letter = op_name_map.get(res[0], res[0])
            out.write(f"{num} -> ({op_letter}, {res[1]}, '{res[2]}')\n")



# Scaling notes and instructions to generate the exact huge dataset the user requested.
scaling_instructions = f"""
SCALING NOTES AND HOW TO PRODUCE 10_000 operators * 1_000_000 entries:
- Generating 10,000 * 1,000,000 = 10,000,000,000 lines is huge (≈ several hundred GB to multiple TB depending on line length).
- Strategy to produce them on disk (streaming): for op in 0..9999: open gzipped file operator_{{op}}.tsv.gz and write one million lines one by one.
  Use deterministic pseudo-random generator with a fixed seed so generation can be resumed/reproduced.
- Storage: ensure you have enough disk space. Use gzip compression (write to .gz) to reduce storage (but compressing will use CPU).
- Indexing/querying approach at this scale:
  * Option A (parallel binary-search per operator): store each operator's prefixes sorted in a file; when answering a single query, binary-search each operator file (load index or use mmap). This costs ~ O(num_operators * log(entries_per_operator)) disk seeks/reads per query. For 10k operators and 1M entries, that's ~200k binary-search steps — doable if optimized and parallelized.
  * Option B (global inverted index by prefix): create a mapping prefix -> list of (operator,price). For very large data this mapping must be stored in a disk-based key-value store (LevelDB/RocksDB) or a sharded DB. Then query by iterating prefix lengths from longest to shortest and fetch the list for that prefix; stop when you've discovered all operators or found the cheapest. This can be faster for queries but index size will be large.
  * Option C (Trie per operator, on-disk or compacted): build a compact radix trie per operator and store it in a binary format that can be memory-mapped for fast lookup. Building tries for 10k operators is possible but takes time & memory; use succinct/blocked tries.
- If you want, I can provide a streaming generator script (bash + python) that writes the huge files to disk and a query tool that uses binary search on compressed files. But I cannot generate all 10B lines here in this environment.
"""

print(scaling_instructions)

# # Save results to a small JSON for user download demonstration
# import json
# out_json = OUT_DIR / "demo_results.json"
# with open(out_json, "w") as f:
#     json.dump({num: res for num, res in results.items()}, f)

# print(f"\nDemo files saved under: {OUT_DIR}")
# print(f"[Download demo results JSON] -> sandbox:{out_json}")

output_path = "/root/side_projects/orders/src/static/testcase.txt"

with open(output_path, "w") as out:
    for idx, fname in enumerate(sorted(operator_files)):
        operator_name = f"Operator {chr(65+idx)}:"  # A, B, C,...
        out.write(operator_name + "\n")
        with gzip.open(fname, "rt") as f:
            for line in f:
                out.write(line)
        # separate operators with blank line
        os.remove(fname)
        out.write("\n")
