"""
instancia.py
=============
Lector (parser) del formato de texto de Hurink (1994) para el
Flexible Job Shop Scheduling Problem (FJSP).

"""


class Instancia:
    """Representa una instancia FJSP ya parseada."""

    def __init__(self, nombre, n_trabajos, n_maquinas, flexibilidad, trabajos):
        self.nombre = nombre
        self.n_trabajos = n_trabajos
        self.n_maquinas = n_maquinas
        self.flexibilidad = flexibilidad
        self.trabajos = trabajos

        # Metadatos derivados utiles para la codificacion del cromosoma.
        self.n_ops = [len(t) for t in trabajos]
        self.total_ops = sum(self.n_ops)

        # offset[j]: posicion canonica de la 1a operacion del trabajo j en
        # un vector "plano" que recorre los trabajos en orden.
        self.offset = [0] * n_trabajos
        acum = 0
        for j in range(n_trabajos):
            self.offset[j] = acum
            acum += self.n_ops[j]

    def indice_plano(self, j, o):
        """Convierte (trabajo j, operacion o) al indice del vector plano."""
        return self.offset[j] + o

    def __repr__(self):
        return ("Instancia(%s: %d trabajos, %d maquinas, %d operaciones, "
                "flex=%s)" % (self.nombre, self.n_trabajos, self.n_maquinas,
                              self.total_ops, self.flexibilidad))


def leer_instancia(ruta, nombre=None):
    """Lee un archivo de Hurink y devuelve un objeto Instancia."""
    with open(ruta, "r") as f:
        # Tokenizamos el archivo completo en numeros: el formato es robusto a la
        # cantidad de espacios/saltos de linea, asi que trabajar con un flujo
        # de tokens evita errores por espaciado irregular.
        tokens = f.read().split()

    pos = 0

    def siguiente_int():
        nonlocal pos
        v = int(tokens[pos])
        pos += 1
        return v

    #  Encabezado 
    n_trabajos = siguiente_int()
    n_maquinas = siguiente_int()
    # El factor de flexibilidad puede ser entero ("2") o decimal ("2.50").
    flexibilidad = float(tokens[pos])
    pos += 1

    # Cuerpo: un bloque por trabajo 
    trabajos = []
    for _ in range(n_trabajos):
        n_operaciones = siguiente_int()
        operaciones = []
        for _ in range(n_operaciones):
            n_alternativas = siguiente_int()
            alternativas = []
            for _ in range(n_alternativas):
                maquina = siguiente_int() - 1   # a base 0
                tiempo = siguiente_int()
                alternativas.append((maquina, tiempo))
            operaciones.append(alternativas)
        trabajos.append(operaciones)

    if nombre is None:
        nombre = ruta

    inst = Instancia(nombre, n_trabajos, n_maquinas, flexibilidad, trabajos)

    # Verificacion de consistencia: todos los tokens deben haberse consumido.
    if pos != len(tokens):
        raise ValueError(
            "Parser: sobran %d tokens en %s (posible formato inesperado)"
            % (len(tokens) - pos, ruta))

    return inst


if __name__ == "__main__":
    # Pequeña prueba manual del parser.
    import os
    base = os.path.join(os.path.dirname(__file__), "instancias")
    for sub in ("edata", "rdata", "vdata"):
        for nom in ("la01", "la06", "la11", "la16", "la21"):
            ruta = os.path.join(base, sub, nom + ".txt")
            inst = leer_instancia(ruta, "%s/%s" % (sub, nom))
            print(inst)
