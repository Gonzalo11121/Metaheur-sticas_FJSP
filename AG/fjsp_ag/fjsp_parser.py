

class Instancia:
  

    def __init__(self, nombre, n_jobs, n_machines, trabajos):
        self.nombre = nombre
        self.n_jobs = n_jobs
        self.n_machines = n_machines
        self.trabajos = trabajos
        self.n_ops_por_job = [len(tr) for tr in trabajos]
        self.total_ops = sum(self.n_ops_por_job)

        # trabajo, operacion
        self.op_global = {}
        self.op_jo = []
        gid = 0
        for j in range(n_jobs):
            for o in range(self.n_ops_por_job[j]):
                self.op_global[(j, o)] = gid
                self.op_jo.append((j, o))
                gid += 1


def leer_instancia(ruta, nombre=None):
    """Lee un archivo de instancia Hurink y devuelve un objeto Instancia."""
    with open(ruta, "r") as f:
        lineas = f.read().splitlines()

    # Quitar lineas vacias al final, conservando el orden.
    lineas = [ln for ln in lineas if ln.strip() != ""]

    # numero de trabajos y de maquinas 
    cabecera = lineas[0].split()
    n_jobs = int(cabecera[0])
    n_machines = int(cabecera[1])
 

    # flujo de enteros 
    tokens = []
    for ln in lineas[1:]:
        tokens.extend(ln.split())
    nums = [int(float(t)) for t in tokens]

    trabajos = []
    idx = 0
    for _ in range(n_jobs):
        n_ops = nums[idx]; idx += 1
        operaciones = []
        for _ in range(n_ops):
            n_alt = nums[idx]; idx += 1
            alternativas = []
            for _ in range(n_alt):
                maquina = nums[idx] - 1      # a base 0
                tiempo = nums[idx + 1]
                idx += 2
                alternativas.append((maquina, tiempo))
            operaciones.append(alternativas)
        trabajos.append(operaciones)

    if nombre is None:
        nombre = ruta
    return Instancia(nombre, n_jobs, n_machines, trabajos)


if __name__ == "__main__":
    # Prueba rapida del parser
    import sys
    ruta = sys.argv[1] if len(sys.argv) > 1 else "instancias/edata/la01.txt"
    inst = leer_instancia(ruta)
    print("Instancia:", inst.nombre)
    print("Trabajos :", inst.n_jobs, "| Maquinas:", inst.n_machines,
          "| Operaciones totales:", inst.total_ops)
    print("Operaciones por trabajo:", inst.n_ops_por_job)
    print("Trabajo 0, operacion 0, alternativas:", inst.trabajos[0][0])
