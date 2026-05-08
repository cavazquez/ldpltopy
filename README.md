# ldpltopy

Transpilador en **Python 3.13** que convierte un **subset documentado de [LDPL](https://docs.ldpl-lang.org/)** a código Python 3.13. La arquitectura es por fases (**lexer → parser recursivo → AST propio → emisión de Python**), no un conversor monolítico basado en expresiones regulares sobre el programa completo.

Referencia oficial del lenguaje: [documentación LDPL](https://docs.ldpl-lang.org/) (estructura `data:` / `procedure:`, tipos `number` y `text`, E/S, flujo, etc.).

## Requisitos

- [uv](https://docs.astral.sh/uv/)
- Python **3.13** (el repo incluye `.python-version` para `uv sync`)

## Instalación

```bash
git clone git@github.com:cavazquez/ldpltopy.git
cd ldpltopy
uv sync --group dev
```

## Uso con `uv`

Emitir Python por **stdout**:

```bash
uv run ldpltopy programa.ldpl
```

Escribir a un archivo:

```bash
uv run ldpltopy programa.ldpl -o salida.py
```

Ejecutar el módulo:

```bash
uv run python -m ldpltopy programa.ldpl
```

## Ejemplo mínimo (`procedure:` sin variables)

```ldpl
procedure:
display "Hello World!" crlf
```

## Ejemplo con variables y bucle

Ver `tests/fixtures/09_while.ldpl` y el Python esperado en `tests/fixtures/09_while_expected.py`.

## Subset LDPL implementado (v0.1)

Este proyecto **no** implementa LDPL completo. La primera versión cubre un subconjunto **pequeño, testeado y extensible**, alineado con la especificación donde aplica:

- Secciones **`data:`** (opcional) y **`procedure:`** (obligatoria).
- Declaraciones **`nombre is number|text`** (acepta sinónimos plurales `numbers` / `texts` como en la documentación).
- **`store`** (un solo valor por línea en este subset).
- **`display`** y **`print`** (este último equivale a `display` + salto de línea, como en la [documentación de E/S](https://docs.ldpl-lang.org/io/)).
- Literales de texto con comillas y secuencias de escape habituales; literales numéricos según el estilo LDPL (sin `+` explícito al inicio).
- **`in … join …`** concatenando valores (números formateados sin `.0` cuando corresponden a enteros).
- **`in … solve …`** con expresiones `+ - * /`, paréntesis y menos unario.
- **`accept`** (texto: `input()`; número: bucle con `Redo from start` como en la documentación).
- **`if … then` / `else` / `end if`** y **`while … do` / `repeat`**.
- Comparaciones: **`is equal to`**, **`is not equal to`**, **`is greater than`**, **`is less than`**, **`is greater than or equal to`**, **`is less than or equal to`** (según [control de flujo](https://docs.ldpl-lang.org/flow/)).
- **`lf`** / **`crlf`** como parte de `display` / `join` (emitidos como `\n`; la emisión usa `print(..., end="")` para no duplicar saltos).

### Tabla de cobertura

| Característica LDPL | Estado |
| --- | --- |
| Secciones `data:` / `procedure:` | **Soportado** (subset) |
| Tipos escalares `number`, `text` | **Soportado** |
| Listas, mapas, multicontenedores | **Pendiente** |
| `sub` / `call`, `parameters`, `local data` | **Pendiente** |
| `for`, `for each`, `break`, `continue` | **Pendiente** |
| `include`, `flag`, `extension` | **Pendiente** |
| Aritmética completa (`add`, `multiply`, `floor`, etc.) | **Parcial** (solo `in solve` con `+ - * /` y paréntesis) |
| Texto avanzado (`replace`, `split`, `trim`, …) | **Pendiente** (solo `join` básico) |
| E/S avanzada (`load file`, `write to file`, …) | **Pendiente** |
| Condiciones compuestas (`and` / `or` / paréntesis) | **Pendiente** |
| `goto` / `label`, `create statement`, extensiones C++ | **Pendiente** |
| Insensibilidad a mayúsculas (A–Z) | **Soportado** en identificadores/palabras clave tokenizadas |

## Calidad y tests

```bash
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest --benchmark-disable
```

## Benchmarks (`pytest-benchmark`)

Incluidos en `tests/test_benchmarks.py` (tokenizar líneas, parsear, transpilar y ejecutar el Python generado en un caso simple):

```bash
uv run pytest tests/test_benchmarks.py --benchmark-only
```

En CI los benchmarks se desactivan (`--benchmark-disable`) para tiempos estables.

## Licencia

Ver `LICENSE` (Apache-2.0 según el repositorio).
