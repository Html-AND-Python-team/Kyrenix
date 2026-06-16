from pathlib import Path
import re

# =========================
# RUTA DEL ARCHIVO
# =========================
BASE_DIR = Path(__file__).resolve().parent
nv_files = list(BASE_DIR.glob("*.kx"))

if not nv_files:
    print("No hay archivos .nv en la carpeta")
    exit()

FILE_PATH = nv_files[0]

types = {
    "int": int,
    "str": str,
    "float": float,
    "bool": lambda x: x.lower() in ("true", "1", "yes")
}

# =========================
# MEMORIA
# =========================
variables = {}
funciones = {}

# =========================
# TIPOS
# =========================
def parse_value(value, vtype):
    value = value.strip()

    if vtype == "int":
        return int(value)

    elif vtype == "bool":
        return value.lower() == "true"

    elif vtype == "str":
        return value

    return value

# =========================
# EVALUADOR DE EXPRESIONES
# =========================
def evaluate(expr):
    expr = expr.strip()

    # reemplazar variables por sus valores
    for name in variables:
        expr = expr.replace(name, str(variables[name]))

    try:
        return eval(expr)
    except:
        return expr

# =========================
# PARSER NOVA
# =========================
def extract(line):
    line = line.strip().lower()

    # VAR
    if line.startswith("var<"):
        match = re.match(r"var<([^>]+)>\{([^}]+)\}\{([^}]+)\}", line)
        if not match:
            return None, []

        name = match.group(1).strip()
        value = match.group(2).strip()
        vtype = match.group(3).strip()

        return "var", [name, value, vtype]

    # PRINT
    if line.startswith("print<"):
        match = re.match(r"print<([^>]+)>", line)
        if not match:
            return None, []

        return "print", [match.group(1).strip()]

    if line.startswith("call<"):

        match = re.match(r"call<([^>]+)>\{?([^}]*)\}?", line)

        if not match:
            return None

        return "call", [
            match.group(1),
            match.group(2)
        ]
    def parse_if(line):
            line = line.strip()

            # quitar "if<"
            start = line.find("<") + 1
            end = line.find(">")
            var_name = line[start:end]

            rest = line[end+1:].strip()

            blocks = []
            current = ""
            depth = 0

            for c in rest:
                if c == "{":
                    if depth > 0:
                        current += c
                    depth += 1

                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        blocks.append(current)
                        current = ""
                    else:
                        current += c

                else:
                    current += c

            condition = blocks[0]
            block_true = blocks[1] if len(blocks) > 1 else ""
            block_false = blocks[2] if len(blocks) > 2 else ""

            return "if", [var_name, condition, block_true, block_false]

    if line.startswith("if<"):
        return parse_if(line)
    
    if line.startswith("$$"):
        return None

    if line.startswith("func<"):
        match = re.match(r"func<([^>]+)>\{([^}]*)\}\{([\s\S]*)\}", line)
        if not match:
            return None, []
        
        fname = match.group(1).strip()
        argument = match.group(2).strip()
        body = match.group(3).strip()     
        return "function", [fname, argument, body]

    if line.startswith("prompt<"):
        match = re.match(r"prompt<([^>]+)>\{([^}]+)\}\{([^>]+)\}", line)

        if not match:
            return None
        
        vname = match.group(1).strip()
        ask = match.group(2).strip()
        ptype = match.group(3).strip()

        return "prompt", [vname, ask, ptype]



    return None, []
# =========================
# RESOLVER VARIABLES
# =========================
def resolve(expr):
    expr = expr.strip()

    for name in variables:
        expr = expr.replace(name, str(variables[name]))

    return expr

# =========================
# EJECUTOR
# =========================
def execute(line):

    result = extract(line)

    if result is None:
        return

    cmd, args = result

    if cmd is None:
        return

    # ---------------- VAR ----------------
    if cmd == "var":
        name = args[0]
        value = evaluate(args[1])
        vtype = args[2]

        variables[name] = parse_value(str(value), vtype)

    # ---------------- PRINT ----------------
    elif cmd == "print":
        target = args[0]

        result = evaluate(target)

        print(result)

        target = args[0]

    elif cmd == "if":
        var_name = args[0]
        condition = args[1]
        block = args[2]
        block_false = args[3]

        value = variables.get(var_name, None)

        if value is None:
            return
        
        condition = resolve(condition)

        # evaluamos condición simple
        if eval(str(value) + condition):
            execute(block)
        else:
            if block_false:
                execute(block_false)
    
    elif cmd == "function":

        fname = args[0]
        fargs = args[1]
        body = args[2]

        funciones[fname] = {
            "args": fargs,
            "body": body
        }
            
    elif cmd == "prompt":
        vname = args[0]
        ask = evaluate(args[1])
        ptype = args[2]
        try:
            converter = types.get(ptype, str)
            variables[vname] = converter(input(ask))
        except Exception as e:
            print(e)
            print("Check your code")
    
    elif cmd == "call":
        fname = args[0]
        execute(funciones[fname]["body"])

# =========================
# EJECUTAR ARCHIVO
# =========================
def run_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            execute(line)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    run_file(FILE_PATH)