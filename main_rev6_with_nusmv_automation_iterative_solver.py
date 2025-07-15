import os,subprocess,time, re


def parse_board(board):
    sokoban_pos = None
    boxes = []
    goals = []
    walls = []

    for r, row in enumerate(board):
        for c, cell in enumerate(row):
            if cell == '@' or cell == '+':
                sokoban_pos = (c + 1, r + 1)  # +1 to convert to 1-based indexing
            if cell == '$' or cell == '*':
                boxes.append((c + 1, r + 1))
            if cell == '.' or cell == '*' or cell == '+':
                goals.append((c + 1, r + 1))
            if cell == '#':
                walls.append((c + 1, r + 1))

    return sokoban_pos, boxes, goals, walls

def generate_smv_model(board, sokoban_pos, boxes, goals, walls,target_box=None):
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0

    smv_model = f"MODULE main\nVAR\n"
    smv_model += f"    move : {{l,u,r,d}};\n"
    smv_model += f"    man_c : 1..{cols};\n"
    smv_model += f"    man_r : 1..{rows};\n"

    for i, box in enumerate(boxes):
        smv_model += f"    box_{i + 1}_c : 1..{cols};\n"
        smv_model += f"    box_{i + 1}_r : 1..{rows};\n"

    for i, goal in enumerate(goals):
        smv_model += f"    goal_{i + 1}_c : 1..{cols};\n"
        smv_model += f"    goal_{i + 1}_r : 1..{rows};\n"

    smv_model += f"    walls : array 1..{rows} of array 1..{cols} of 0..1;\n"

    smv_model += "ASSIGN\n"
    smv_model += f"    init(man_c) := {sokoban_pos[0]};\n"
    smv_model += f"    init(man_r) := {sokoban_pos[1]};\n"

    for i, box in enumerate(boxes):
        smv_model += f"    init(box_{i + 1}_c) := {box[0]};\n"
        smv_model += f"    init(box_{i + 1}_r) := {box[1]};\n"

    for i, goal in enumerate(goals):
        smv_model += f"    goal_{i + 1}_c := {goal[0]};\n"
        smv_model += f"    goal_{i + 1}_r := {goal[1]};\n"

    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            wall_value = 1 if (c, r) in walls else 0
            smv_model += f"    walls[{r}][{c}] := {wall_value};\n"

    smv_model += "next(man_c) :=\n"
    smv_model += "    case\n"
    smv_model += f"        move = r & (mv_r | push_r) & (man_c < {cols}) : man_c + 1;\n"
    smv_model += f"        move = l & (mv_l | push_l) & (man_c > 1) : man_c - 1;\n"
    smv_model += "        move = u : man_c;\n"
    smv_model += "        move = d : man_c;\n"
    smv_model += "        TRUE : man_c;\n"
    smv_model += "    esac;\n"

    smv_model += "next(man_r) :=\n"
    smv_model += "    case\n"
    smv_model += "        move = r : man_r;\n"
    smv_model += "        move = l : man_r;\n"
    smv_model += f"        move = u & (mv_u | push_u) & (man_r > 1) : man_r - 1;\n"
    smv_model += f"        move = d & (mv_d | push_d) & (man_r < {rows}) : man_r + 1;\n"
    smv_model += "        TRUE : man_r;\n"
    smv_model += "    esac;\n"

    for i in range(len(boxes)):
        smv_model += f"next(box_{i + 1}_c) :=\n"
        smv_model += "    case\n"
        smv_model += f"        push_l & box_{i + 1}_on_l & (box_{i + 1}_c < {cols}) : box_{i + 1}_c - 1;\n"
        smv_model += f"        push_r & box_{i + 1}_on_r & (box_{i + 1}_c > 1) : box_{i + 1}_c + 1;\n"
        smv_model += f"        TRUE: box_{i+1}_c;\n"
        smv_model += "    esac;\n"

        smv_model += f"next(box_{i + 1}_r) :=\n"
        smv_model += "    case\n"
        smv_model += f"        push_u & box_{i + 1}_on_t & (box_{i + 1}_r > 1) : box_{i + 1}_r - 1;\n"
        smv_model += f"        push_d & box_{i + 1}_on_b & (box_{i + 1}_r < {rows}) : box_{i + 1}_r + 1;\n"
        smv_model += f"        TRUE: box_{i+1}_r;\n"
        smv_model += "    esac;\n"

    smv_model += "DEFINE\n"
    # Define mv_* conditions
    smv_model += f"    mv_r := (move = r) & (man_c < {cols}) & (walls[man_r][man_c + 1] = 0)"
    for i in range(len(boxes)):
        smv_model += f" & !box_{i+1}_on_r"
    smv_model += ";\n"

    smv_model += f"    mv_l := (move = l) & (man_c > 1) & (walls[man_r][man_c - 1] = 0)"
    for i in range(len(boxes)):
        smv_model += f" & !box_{i+1}_on_l"
    smv_model += ";\n"

    smv_model += f"    mv_u := (move = u) & (man_r > 1) & (walls[man_r - 1][man_c] = 0)"
    for i in range(len(boxes)):
        smv_model += f" & !box_{i+1}_on_t"
    smv_model += ";\n"

    smv_model += f"    mv_d := (move = d) & (man_r < {rows}) & (walls[man_r + 1][man_c] = 0)"
    for i in range(len(boxes)):
        smv_model += f" & !box_{i+1}_on_b"
    smv_model += ";\n"

    # Define box positions
    for i in range(len(boxes)):
        smv_model += f"    box_{i + 1}_on_r := (man_c + 1 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_rp1 := (man_c + 2 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_l := (man_c - 1 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_lp1 := (man_c - 2 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_t := (man_c = box_{i + 1}_c) & (man_r - 1 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_tp1 := (man_c = box_{i + 1}_c) & (man_r - 2 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_b := (man_c = box_{i + 1}_c) & (man_r + 1 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_bp1 := (man_c = box_{i + 1}_c) & (man_r + 2 = box_{i + 1}_r);\n"

    # Define push conditions
    directions = [
        ('r', 'man_c + 2', 'on_r', 'on_rp1'),
        ('l', 'man_c - 2', 'on_l', 'on_lp1'),
        ('u', 'man_r - 2', 'on_t', 'on_tp1'),
        ('d', 'man_r + 2', 'on_b', 'on_bp1')
    ]
    for move_dir, wall_pos, on_suffix, next_suffix in directions:
        smv_model += f"    push_{move_dir} := (move = {move_dir}) & (walls"
        if move_dir in ['u', 'd']:
            wall_coord = f"man_r {'- 2' if move_dir == 'u' else '+ 2'}" if move_dir in ['u', 'd'] else f"man_c {'+ 2' if move_dir == 'r' else '- 2'}"
            smv_model += f"[{wall_coord}][man_c] = 0) & ("
        else:
            wall_coord = f"man_c {'+ 2' if move_dir == 'r' else '- 2'}" if move_dir in ['r', 'l'] else f"man_r {'- 2' if move_dir == 'u' else '+ 2'}"
            smv_model += f"[man_r][{wall_coord}] = 0) & ("
        for i in range(len(boxes)):
            smv_model += f"(box_{i+1}_{on_suffix}"
            for j in range(len(boxes)):
                if j != i:
                    smv_model += f" & !box_{j+1}_{next_suffix}"
            smv_model += ")"
            if i < len(boxes) - 1:
                smv_model += " | "
        smv_model += ");\n"

    # Win condition
    smv_model += "    win := "
    if target_box is None:
        for i in range(len(boxes)):
            smv_model += "("
            for j in range(len(goals)):
                smv_model += f"(box_{i+1}_c = goal_{j+1}_c & box_{i+1}_r = goal_{j+1}_r)"
                if j < len(goals) - 1:
                    smv_model += " | "
            smv_model += ")"
            if i < len(boxes) - 1:
                smv_model += " & "

    else:
        # now do exactly box target_box (1-based) against all goals
        k = target_box - 1   # convert to 0-based index
        smv_model += "("
        for j in range(len(goals)):
            smv_model += f"(box_{k+1}_c = goal_{j+1}_c & box_{k+1}_r = goal_{j+1}_r)"
            if j < len(goals) - 1:
                smv_model += " | "
        smv_model += ")"
    smv_model += ";\n"
    smv_model += "LTLSPEC !F win;\n"



    return smv_model


def run_nusmv_and_check(filename,bound=20,engine='sat'):
    # Commands to run in NuSMV interactive mode
    # SAT‐based bounded check of !F win up to 'bound'
    run_cmd = f"check_ltlspec_bmc -k {bound}"

    
    commands = "\n".join([
        f"set engine {engine}", #switch to BDD or SAT
        "read_model",
        "flatten_hierarchy",
        "encode_variables",
        "build_boolean_model",
        "bmc_setup",
        run_cmd, 
        "quit"
    ]) + "\n"


    
    try:
        # Time the whole NuSMV invocation:
        start = time.perf_counter()
        # Run NuSMV with the commands
        result = subprocess.run(
            [r"G:\My Drive\Asaf\Masters and PhD\PhD\Courses\Formal Verification and Synthesis - Hilel Kugler\nuXmv\bin\nuXmv.exe", "-int", filename],
            input=commands.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60  # seconds
        )
        elapsed = time.perf_counter() - start

        

        output = result.stdout.decode("utf-8")
        error_output = result.stderr.decode("utf-8")


        if error_output:
            print("NuSMV error output:\n", error_output)

        # Debug: show nuXmv’s verdict
        print(f"\n--- nuXmv output for {filename} ---\n{output}")

        # Extract CPU & memory from NuSMV’s stdout if present:
        cpu = None
        mem = None
        m = re.search(r"cpu time.*?([0-9]+\.[0-9]+)", output, re.IGNORECASE)
        if m: cpu = float(m.group(1))
        m = re.search(r"memory used.*?([0-9]+\.[0-9]+)\s*mb", output, re.IGNORECASE)
        if m: mem = float(m.group(1))
        
        # Parse the result of check_ltlspec_bmc
        #If spec is true we loose no winning condition exisits
        #When spec is false we win 
        if "is false" in output.lower():
            print("\n LTL Specification FAILED (is false).")
            winnable = True
        
        else:
            print("\n  Could not find counter example to fail LTL check")
            winnable = False
        # Return a summary dict
        return {
            "filename": filename,
            "engine": engine,
            "spec": run_cmd,
            "winnable": winnable,
            "elapsed": elapsed,
            "cpu": cpu,
            "mem": mem,
            "stdout": output,
            "stderr": error_output
        }    
    
    except FileNotFoundError:
        print("Error: NuSMV executable not found. Make sure it is installed and in your PATH.")
    except subprocess.TimeoutExpired:
        print("Error: NuSMV process timed out.")

def run_iterative_solve(board, bound=20):
    sokoban_pos, boxes, goals, walls = parse_board(board)
    stats = []
    for k in range(1, len(boxes)+1):
        # generate model that only checks box k
        model = generate_smv_model(board, sokoban_pos, boxes, goals, walls, target_box=k)
        fname = f"sokoban_box{k}.smv"
        with open(fname, "w") as f:
            f.write(model)

        start = time.perf_counter()
        success = run_nusmv_and_check(fname, bound)
        elapsed = time.perf_counter() - start
        stats.append((k, elapsed, success))

        # if you want to “fix” box k in place before moving on,
        # you’d update sokoban_pos, boxes, etc., here.

    return stats


def run_skoban(out_dir, boards,bmc_bound=20):
    results = []
    os.makedirs(out_dir, exist_ok=True)

    for idx, board in enumerate(boards, start=1):
        print(f"\n=== Processing board #{idx} ===")
        try:
            sokoban_pos, boxes, goals, walls = parse_board(board)
            smv = generate_smv_model(board, sokoban_pos, boxes, goals, walls)

            fname = os.path.join(out_dir, f"sokoban_{idx}.smv")
            with open(fname, "w") as f:
                f.write(smv)

            # 1) SAT-based BMC with your negated spec !F win
            sat_stats = run_nusmv_and_check(filename=fname,bound=bmc_bound,engine="sat")
            sat_stats.update({"board": idx})
            results.append(sat_stats)
            print(f"--> SAT (bound={bmc_bound}) says: {'winnable' if sat_stats['winnable'] else 'NOT winnable'}")

            # 2) “Depth 0” under the BDD engine (still checking !F win)
            bdd_stats = run_nusmv_and_check(filename=fname,bound=bmc_bound,engine="bdd")
            bdd_stats.update({"board": idx})
            results.append(bdd_stats)
            print(f"--> BDD (bound=0) says: {'winnable' if bdd_stats['winnable'] else 'NOT winnable'}")

        except Exception as e:
            # Catch any Python errors (e.g. file not found, model-gen bug)
            print(f"!!! ERROR on board {idx}: {e}")
            # continue with next board rather than aborting
            continue
    return results

#Example usage
if __name__ == "__main__":
    # Example board
    boards = [
        [
            "#####",
            "#@$.#",
            "#####"
        ],
        [
            "#####",
            "#$@.#",
            "#####"
        ],
        [
            "#######",
            "#@    #",
            "#  .$ #",
            "#   ###",
            "#  $  #",
            "#   #.#",
            "#######"
        ],
        [
            "#######",
            "###.###",
            "###$###",
            "#.$@$.#",
            "###$###",
            "###.###",
            "#######"
        ],
        [
            "#######",
            "#@    #",
            "#   ..#",
            "#  #$$#",
            "#  #  #",
            "#  #  #",
            "#######"
        ],
        [
            "########",
            "#@     #",
            "#    ###",
            "# $ #  #",
            "#   # $#",
            "# . # .#",
            "########"
        ],
        [
            "###########",
            "#      ####",
            "#  #   .###",
            "# $     ###",
            "#  @#   ###",
            "###    *###",
            "#####     #",
            "#######   #",
            "#######   #",
            "###########"
        ],
    ]

    # 1) Add after you define your boards list:
    complex_level = [
                    "######  ###",
                    "#..  # ##@##",
                    "#..  ###   #",
                    "#..     $$ #",
                    "#..  # # $ #",
                    "#..### # $ #",
                    "#### $ #$  #",
                    "#  $# $ #",
                    "# $  $  #",
                    "#  ##   #",
                    "#########",
                    ]

            # pick a directory to drop your generated SMV files
    out_dir = r"G:\My Drive\Asaf\Masters and PhD\PhD\Courses\Formal Verification and Synthesis - Hilel Kugler\Final Project\main\generated_models_part4"

    # Pad to rectangular shape
    width = max(len(row) for row in complex_level)
    complex_level = [row.ljust(width) for row in complex_level]

    # 2) Append it to your boards
    boards.append(complex_level)

    # 3) Call run_skoban as usual:
    # pick the board you want (1‐based index)
    board_number = 8

    # pull it straight out of the `boards` list
    selected_board = boards[board_number - 1]

    # now run it just like you do in run_skoban,
    # but on this single board:
    print(f"\n=== Processing single board #{board_number} ===")
    stats = run_skoban(out_dir, boards=[selected_board],bmc_bound=20)

    # Example: print a simple summary table
    print("\nSummary:")
    print("| Board | Engine | Bound | Winnable | Time (s) | CPU (s) | Mem (MB) |")
    print("|:-----:|:------:|:-----:|:--------:|:--------:|:-------:|:--------:|")
    for r in stats:
        print(f"|   {r['board']}   | {r['engine'].upper():<3}   |  {r['spec'].split()[-1]:<3}   "
              f"|   {'Yes' if r['winnable'] else 'No'}    | "
              f"{r['elapsed']:.2f}    | "
              f"{(r['cpu'] or 0):.2f}    | "
              f"{(r['mem'] or 0):.2f}    |")

    print("=== Iterative one box solver ===")
    it_stats = run_iterative_solve(selected_board, bound=20)
    total = sum(t for (_, t, _) in it_stats)
    for idx, t, ok in it_stats:
        print(f" Box {idx}: {'OK' if ok else 'FAIL'} in {t:.2f}s")
    print(f" Total time: {total:.2f}s")

