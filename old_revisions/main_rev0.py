import os.path


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

def generate_smv_model(board, sokoban_pos, boxes, goals, walls):
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0

    smv_model = f"MODULE main\nVAR\n"

    # Variables for Sokoban position
    smv_model += f"    man_c : 1..{cols};\n"
    smv_model += f"    man_r : 1..{rows};\n"

    # Variables for boxes
    for i, box in enumerate(boxes):
        smv_model += f"    box_{i + 1}_c : 1..{cols};\n"
        smv_model += f"    box_{i + 1}_r : 1..{rows};\n"

    # Variables for goals
    for i, goal in enumerate(goals):
        smv_model += f"    goal_{i + 1}_c : 1..{cols};\n"
        smv_model += f"    goal_{i + 1}_r : 1..{rows};\n"

    # Walls as a 2D array
    smv_model += f"    walls : array 1..{rows} of array 1..{cols} of 0..1;\n"

    # Initial conditions
    smv_model += "ASSIGN\n"
    smv_model += f"    init(man_c) := {sokoban_pos[0]};\n"
    smv_model += f"    init(man_r) := {sokoban_pos[1]};\n"

    for i, box in enumerate(boxes):
        smv_model += f"    init(box_{i + 1}_c) := {box[0]};\n"
        smv_model += f"    init(box_{i + 1}_r) := {box[1]};\n"

    for i, goal in enumerate(goals):
        smv_model += f"    goal_{i + 1}_c := {goal[0]};\n"
        smv_model += f"    goal_{i + 1}_r := {goal[1]};\n"

    # Initialize walls
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            wall_value = 1 if (c, r) in walls else 0
            smv_model += f"    walls[{r}][{c}] := {wall_value};\n"

    # Transitions
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
        smv_model += f"        push_l & (box_{i + 1}_c < {cols}) : box_{i + 1}_c - 1;\n"
        smv_model += f"        push_r & (box_{i + 1}_c > 1) : box_{i + 1}_c + 1;\n"
        smv_model += f"        TRUE: box_{i+1}_c;\n"
        smv_model += "    esac;\n"

        smv_model += f"next(box_{i + 1}_r) :=\n"
        smv_model += "    case\n"
        smv_model += f"        push_u & (box_{i + 1}_r > 1) : box_{i + 1}_r - 1;\n"
        smv_model += f"        push_d & (box_{i + 1}_r < {rows}) : box_{i + 1}_r + 1;\n"
        smv_model += f"        TRUE: box_{i+1}_r;\n"
        smv_model += "    esac;\n"

    # Define conditions
    smv_model += "DEFINE\n"
    smv_model += f"    mv_r := (move = r) & (man_c < {cols}) & (walls[man_r][man_c + 1] = 0) & !box_on_r;\n"
    smv_model += f"    mv_l := (move = l) & (man_c > 1) & (walls[man_r][man_c - 1] = 0) & !box_on_l;\n"
    smv_model += f"    mv_u := (move = u) & (man_r > 1) & (walls[man_r - 1][man_c] = 0) & !box_on_t;\n"
    smv_model += f"    mv_d := (move = d) & (man_r < {rows}) & (walls[man_r + 1][man_c] = 0) & !box_on_b;\n"

    for i in range(len(boxes)):
        smv_model += f"    box_{i + 1}_on_r := (man_c + 1 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_rp1 := (man_c + 2 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_l := (man_c - 1 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_lp1 := (man_c - 2 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_t := (man_c = box_{i + 1}_c) & (man_r - 1 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_tp1 := (man_c = box_{i + 1}_c) & (man_r - 2 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_b := (man_c = box_{i + 1}_c) & (man_r + 1 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_bp1 := (man_c = box_{i + 1}_c) & (man_r + 2 = box_{i + 1}_r);\n"
    smv_model += f"    push_r := (move = r) & (walls[man_r][man_c + 2] = 0)"
    for i in range(len(boxes)):
        if i==0:
            smv_model += f" & box_{i + 1}_on_r"
        else:
            smv_model += f"  box_{i + 1}_on_r"

        for j in range(len(boxes)):
            if i!=j:

                smv_model += f" & !box_{j + 1}_on_rp1"
        if i<(len(boxes))-1:
            smv_model += f"|"
    smv_model +=";\n"
    smv_model += f"    (move = l) & (walls[man_r][man_c - 2] = 0)"
    for i in range(len(boxes)):
        if i==0:
            smv_model += f" & box_{i + 1}_on_l"
        else:
            smv_model += f"  box_{i + 1}_on_l"

        for j in range(len(boxes)):
            if i!=j:

                smv_model += f" & !box_{j + 1}_on_lp1"
        if i<(len(boxes))-1:
            smv_model += f"|"
    smv_model +=";\n"
    smv_model += f"    push_r := (move = r) & (walls[man_r][man_c + 2] = 0)"
    for i in range(len(boxes)):
        if i==0:
            smv_model += f" & box_{i + 1}_on_r"
        else:
            smv_model += f"  box_{i + 1}_on_r"

        for j in range(len(boxes)):
            if i!=j:

                smv_model += f" & !box_{j + 1}_on_rp1"
        if i<(len(boxes))-1:
            smv_model += f"|"
    smv_model +=";\n"
    smv_model += f"    push_u := (move = u) & (walls[man_r - 2][man_c] = 0)"
    for i in range(len(boxes)):
        if i==0:
            smv_model += f" &  box{i + 1}_on_t"
        else:
            smv_model += f"  box{i + 1}_on_t"

        for j in range(len(boxes)):
            if i!=j:

                smv_model += f" & !box_{j + 1}_on_tp1"
        if i<(len(boxes))-1:
            smv_model += f"|"
    smv_model +=";\n"
    smv_model += f"    push_d := (move = d) & (walls[man_r + 2][man_c] = 0)"
    for i in range(len(boxes)):
        if i==0:
            smv_model += f" & box{i + 1}_on_b"
        else:
            smv_model += f"  box{i + 1}_on_b"

        for j in range(len(boxes)):
            if i!=j:

                smv_model += f" & !box_{j + 1}_on_bp1"
        if i<(len(boxes))-1:
            smv_model += f"|"
    smv_model +=";\n"
        #smv_model += f"    push_l := (move = l) & (walls[man_r][man_c - 2] = 0) &box_{i + 1}_on_l;"
        #for j in range(len(boxes)):
        #    if i != j:

        #        smv_model += f"!box_{j + 1}_on_lp1 "
        #smv_model += "\n"
        #smv_model += f"    push_u := (move = u) & (walls[man_r - 2][man_c] = 0) & !box_{j + 1}_on_tp1 & box{i + 1}_on_t;\n"
        #smv_model += f"    push_d := (move = d) & (walls[man_r + 2][man_c] = 0) & !box_{j + 1}_on_bp1 & box{i + 1}_on_b;\n"

    # Winning condition: Any box on any goal
    smv_model += "    win := "
    for i in range(len(boxes)):
        for j in range(len(goals)):
            smv_model += f"(box_{i + 1}_c = goal_{j + 1}_c) & (box_{i + 1}_r = goal_{j + 1}_r)"
            if i < len(boxes) - 1 or j < len(goals) - 1:
                smv_model += " | "
    smv_model += ";\n"

    # LTL specification
    smv_model += "LTLSPEC !F win;\n"

    return smv_model



def generate_smv_model_old_2(board, sokoban_pos, boxes, goals, walls):
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0

    smv_model = f"MODULE main\nVAR\n"

    # Variables for Sokoban position
    smv_model += f"    man_c : 1..{cols};\n"
    smv_model += f"    man_r : 1..{rows};\n"

    # Variables for boxes
    for i, box in enumerate(boxes):
        smv_model += f"    box_{i + 1}_c : 1..{cols};\n"
        smv_model += f"    box_{i + 1}_r : 1..{rows};\n"

    # Variables for goals
    for i, goal in enumerate(goals):
        smv_model += f"    goal_{i + 1}_c : 1..{cols};\n"
        smv_model += f"    goal_{i + 1}_r : 1..{rows};\n"

    # Walls as a 2D array
    smv_model += f"    walls : array 1..{rows} of array 1..{cols} of 0..1;\n"

    # Initial conditions
    smv_model += "ASSIGN\n"
    smv_model += f"    init(man_c) := {sokoban_pos[0]};\n"
    smv_model += f"    init(man_r) := {sokoban_pos[1]};\n"

    for i, box in enumerate(boxes):
        smv_model += f"    init(box_{i + 1}_c) := {box[0]};\n"
        smv_model += f"    init(box_{i + 1}_r) := {box[1]};\n"

    for i, goal in enumerate(goals):
        smv_model += f"    goal_{i + 1}_c := {goal[0]};\n"
        smv_model += f"    goal_{i + 1}_r := {goal[1]};\n"

    # Initialize walls
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            wall_value = 1 if (c, r) in walls else 0
            smv_model += f"    walls[{r}][{c}] := {wall_value};\n"

    # Transitions
    smv_model += "next(man_c) :=\n"
    smv_model += "    case\n"
    smv_model += "        move = r & (mv_r | push_r) & (man_c < {cols}) : man_c + 1;\n"
    smv_model += "        move = l & (mv_l | push_l) & (man_c > 1) : man_c - 1;\n"
    smv_model += "        move = u : man_c;\n"
    smv_model += "        move = d : man_c;\n"
    smv_model += "        TRUE : man_c;\n"
    smv_model += "    esac;\n"

    smv_model += "next(man_r) :=\n"
    smv_model += "    case\n"
    smv_model += "        move = r : man_r;\n"
    smv_model += "        move = l : man_r;\n"
    smv_model += "        move = u & (mv_u | push_u) & (man_r > 1) : man_r - 1;\n"
    smv_model += "        move = d & (mv_d | push_d) & (man_r < {rows}) : man_r + 1;\n"
    smv_model += "        TRUE : man_r;\n"
    smv_model += "    esac;\n"

    for i in range(len(boxes)):
        smv_model += f"next(box_{i + 1}_c) :=\n"
        smv_model += "    case\n"
        smv_model += f"        push_l & (box_{i + 1}_c < {str(cols)}) : box_{i + 1}_c - 1;\n"
        smv_model += f"        push_r & (box_{i + 1}_c > 1) : box_{i + 1}_c + 1;\n"
        smv_model += "        TRUE: box_{i+1}_c;\n"
        smv_model += "    esac;\n"

        smv_model += f"next(box_{i + 1}_r) :=\n"
        smv_model += "    case\n"
        smv_model += f"        push_u & (box_{i + 1}_r > 1) : box_{i + 1}_r - 1;\n"
        smv_model += f"        push_d & (box_{i + 1}_r < {str(rows)}) : box_{i + 1}_r + 1;\n"
        smv_model += "        TRUE: box_{i+1}_r;\n"
        smv_model += "    esac;\n"

    # Define conditions
    smv_model += "DEFINE\n"
    smv_model += "    mv_r := (move = r) & (man_c < {cols}) & (walls[man_r][man_c + 1] = 0) & !box_on_r;\n"
    smv_model += "    mv_l := (move = l) & (man_c > 1) & (walls[man_r][man_c - 1] = 0) & !box_on_l;\n"
    smv_model += "    mv_u := (move = u) & (man_r > 1) & (walls[man_r - 1][man_c] = 0) & !box_on_t;\n"
    smv_model += "    mv_d := (move = d) & (man_r < {rows}) & (walls[man_r + 1][man_c] = 0) & !box_on_b;\n"

    for i in range(len(boxes)):
        smv_model += f"    box_{i + 1}_on_r := (man_c + 1 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_rp1 := (man_c + 2 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_l := (man_c - 1 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_lp1 := (man_c - 2 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_t := (man_c = box_{i + 1}_c) & (man_r - 1 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_tp1 := (man_c = box_{i + 1}_c) & (man_r - 2 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_b := (man_c = box_{i + 1}_c) & (man_r + 1 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_bp1 := (man_c = box_{i + 1}_c) & (man_r + 2 = box_{i + 1}_r);\n"
    for i in range(len(boxes)):
        smv_model += "    push_r := (move = r) & (walls[man_r][man_c + 2] = 0) & !box_on_rp1 & box_on_r;\n"
        smv_model += "    push_l := (move = l) & (walls[man_r][man_c - 2] = 0) & !box_on_lp1 & box_on_l;\n"
        smv_model += "    push_u := (move = u) & (walls[man_r - 2][man_c] = 0) & !box_on_tp1 & box_on_t;\n"
        smv_model += "    push_d := (move = d) & (walls[man_r + 2][man_c] = 0) & !box_on_bp1 & box_on_b;\n"

    # Winning condition: Any box on any goal
    smv_model += "    win := "
    for i in range(len(boxes)):
        for j in range(len(goals)):
            smv_model += f"(box_{i + 1}_c = goal_{j + 1}_c) & (box_{i + 1}_r = goal_{j + 1}_r)"
            if i < len(boxes) - 1 or j < len(goals) - 1:
                smv_model += " | "
    smv_model += ";\n"

    # LTL specification
    smv_model += "LTLSPEC !F win;\n"

    return smv_model
def generate_smv_model_old(board, sokoban_pos, boxes, goals, walls):
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0

    smv_model = f"MODULE main\nVAR\n"

    # Variables for Sokoban position
    smv_model += f"    man_c : 1..{cols};\n"
    smv_model += f"    man_r : 1..{rows};\n"

    # Variables for boxes
    for i, box in enumerate(boxes):
        smv_model += f"    box_{i + 1}_c : 1..{cols};\n"
        smv_model += f"    box_{i + 1}_r : 1..{rows};\n"

    # Variables for goals
    for i, goal in enumerate(goals):
        smv_model += f"    goal_{i + 1}_c : 1..{cols};\n"
        smv_model += f"    goal_{i + 1}_r : 1..{rows};\n"

    # Walls as a 2D array
    smv_model += f"    walls : array 1..{rows} of array 1..{cols} of 0..1;\n"

    # Initial conditions
    smv_model += "ASSIGN\n"
    smv_model += f"    init(man_c) := {sokoban_pos[0]};\n"
    smv_model += f"    init(man_r) := {sokoban_pos[1]};\n"

    for i, box in enumerate(boxes):
        smv_model += f"    init(box_{i + 1}_c) := {box[0]};\n"
        smv_model += f"    init(box_{i + 1}_r) := {box[1]};\n"

    for i, goal in enumerate(goals):
        smv_model += f"    goal_{i + 1}_c := {goal[0]};\n"
        smv_model += f"    goal_{i + 1}_r := {goal[1]};\n"

    # Initialize walls
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            wall_value = 1 if (c, r) in walls else 0
            smv_model += f"    walls[{r}][{c}] := {wall_value};\n"

    # Transitions
    smv_model += "next(man_c) :=\n"
    smv_model += "    case\n"
    smv_model += "        move = r & (mv_r | push_r) & (man_c < {cols}) : man_c + 1;\n"
    smv_model += "        move = l & (mv_l | push_l) & (man_c > 1) : man_c - 1;\n"
    smv_model += "        move = u : man_c;\n"
    smv_model += "        move = d : man_c;\n"
    smv_model += "        TRUE : man_c;\n"
    smv_model += "    esac;\n"

    smv_model += "next(man_r) :=\n"
    smv_model += "    case\n"
    smv_model += "        move = r : man_r;\n"
    smv_model += "        move = l : man_r;\n"
    smv_model += "        move = u & (mv_u | push_u) & (man_r > 1) : man_r - 1;\n"
    smv_model += "        move = d & (mv_d | push_d) & (man_r < {rows}) : man_r + 1;\n"
    smv_model += "        TRUE : man_r;\n"
    smv_model += "    esac;\n"

    for i in range(len(boxes)):
        smv_model += f"next(box_{i + 1}_c) :=\n"
        smv_model += "    case\n"
        smv_model += f"        push_l & (box_{i + 1}_c < {str(cols)}) : box_{i + 1}_c - 1;\n"
        smv_model += f"        push_r & (box_{i + 1}_c > 1) : box_{i + 1}_c + 1;\n"
        smv_model += "        TRUE: box_{i+1}_c;\n"
        smv_model += "    esac;\n"

        smv_model += f"next(box_{i + 1}_r) :=\n"
        smv_model += "    case\n"
        smv_model += f"        push_u & (box_{i + 1}_r > 1) : box_{i + 1}_r - 1;\n"
        smv_model += f"        push_d & (box_{i + 1}_r < {str(rows)}) : box_{i + 1}_r + 1;\n"
        smv_model += "        TRUE: box_{i+1}_r;\n"
        smv_model += "    esac;\n"

    # Define conditions
    smv_model += "DEFINE\n"
    smv_model += "    mv_r := (move = r) & (man_c < {cols}) & (walls[man_r][man_c + 1] = 0) & !box_on_r;\n"
    smv_model += "    mv_l := (move = l) & (man_c > 1) & (walls[man_r][man_c - 1] = 0) & !box_on_l;\n"
    smv_model += "    mv_u := (move = u) & (man_r > 1) & (walls[man_r - 1][man_c] = 0) & !box_on_t;\n"
    smv_model += "    mv_d := (move = d) & (man_r < {rows}) & (walls[man_r + 1][man_c] = 0) & !box_on_b;\n"

    for i in range(len(boxes)):
        smv_model += f"    box_{i + 1}_on_r := (man_c + 1 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_rp1 := (man_c + 2 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_l := (man_c - 1 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_lp1 := (man_c - 2 = box_{i + 1}_c) & (man_r = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_t := (man_c = box_{i + 1}_c) & (man_r - 1 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_tp1 := (man_c = box_{i + 1}_c) & (man_r - 2 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_b := (man_c = box_{i + 1}_c) & (man_r + 1 = box_{i + 1}_r);\n"
        smv_model += f"    box_{i + 1}_on_bp1 := (man_c = box_{i + 1}_c) & (man_r + 2 = box_{i + 1}_r);\n"
    for i in range(len(boxes)):
        smv_model += "    push_r := (move = r) & (walls[man_r][man_c + 2] = 0) & !box_on_rp1 & box_on_r;\n"
        smv_model += "    push_l := (move = l) & (walls[man_r][man_c - 2] = 0) & !box_on_lp1 & box_on_l;\n"
        smv_model += "    push_u := (move = u) & (walls[man_r - 2][man_c] = 0) & !box_on_tp1 & box_on_t;\n"
        smv_model += "    push_d := (move = d) & (walls[man_r + 2][man_c] = 0) & !box_on_bp1 & box_on_b;\n"

    # Winning condition
    smv_model += "    win := "
    for i in range(len(boxes)):
        smv_model += f"(box_{i + 1}_c = goal_{i + 1}_c) & (box_{i + 1}_r = goal_{i + 1}_r)"
        if i < len(boxes) - 1:
            smv_model += " & "
    smv_model += ";\n"

    # LTL specification
    smv_model += "LTLSPEC !F win;\n"

    return smv_model

def run_skoban(path_to_smv):
    pass
# Example board
boards = [
    [
        "#####",
        "#@$.#",
        "#####"
    ],
    [
        "#####",
        "#.$@#",
        "#####"
    ],
    [
        "#######",
        "#@  $ #",
        "#  #  #",
        "#  $. #",
        "#######"
    ],
    [
        "#######",
        "#  .  #",
        "#.$@$ #",
        "#  .  #",
        "#######"
    ],
    [
        "#######",
        "#@    #",
        "# $$  #",
        "#  .. #",
        "#######"
    ],
    [
        "#######",
        "#@    #",
        "#  #  #",
        "# $. $#",
        "#  .. #",
        "#######"
    ],
    [
        "########",
        "#      #",
        "# @$   #",
        "#  # $ #",
        "# $.   #",
        "#   .  #",
        "########"
    ]
]

# Parse the board
i=1
for board in boards:
    sokoban_pos, boxes, goals, walls = parse_board(board)

    # Generate the SMV model
    smv_model = generate_smv_model(board, sokoban_pos, boxes, goals, walls)
    print(smv_model)
    # Print the SMV model
    with open(("sokoban_boards"+str(i)+".smv"), "w") as f:

            f.write(smv_model)
    i=i+1
    resutls=run_skoban("sokoban_boards"+str(i)+".smv")
    if resutls==1:
        print('winnable')
    else:
        print('not winnable')
