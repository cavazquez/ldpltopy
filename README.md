<p align="center">
<img src="assets/ldpltopy-logo.png" alt="ldpltopy" width="200">
</p>

<div align="center">

[![🐍 Python](https://img.shields.io/badge/🐍_Python-3.13-yellow?logo=python&logoColor=white)](https://www.python.org/)
[![📜 LDPL](https://img.shields.io/badge/📜_LDPL-language_subset-3776AB)](https://docs.ldpl-lang.org/)
[![⚡ uv](https://img.shields.io/badge/⚡_uv-package_manager-7057ff)](https://docs.astral.sh/uv/)
[![⌨️ Typer](https://img.shields.io/badge/⌨️_Typer-CLI-009688)](https://typer.tiangolo.com/)
[![🦀 Ruff](https://img.shields.io/badge/🦀_Ruff-lint_format-261616?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)
[![🔷 mypy](https://img.shields.io/badge/🔷_mypy-strict-2d50a5)](https://www.mypy-lang.org/)
[![🧪 pytest](https://img.shields.io/badge/🧪_pytest-tests-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)
[![⏱️ pytest-benchmark](https://img.shields.io/badge/⏱️_pytest_benchmark-benchmarks-lightgrey)](https://pytest-benchmark.readthedocs.io/)
[![🎬 GitHub Actions](https://img.shields.io/badge/🎬_GitHub_Actions-CI-2088FF?logo=githubactions&logoColor=white)](.github/workflows/ci.yml)
[![📦 setuptools](https://img.shields.io/badge/📦_setuptools-build-3776AB)](https://setuptools.pypa.io/)
[![📜 License](https://img.shields.io/badge/📜_License-GPL--3.0-blue)](LICENSE)

</div>

# ldpltopy

Transpilador en **Python 3.13** que convierte un **subset documentado de [LDPL](https://docs.ldpl-lang.org/)** a código Python 3.13. La arquitectura es por fases (**lexer → parser recursivo → AST propio → emisión de Python**), no un conversor monolítico basado en expresiones regulares sobre el programa completo.

Referencia oficial del lenguaje: [documentación LDPL](https://docs.ldpl-lang.org/) (estructura `data:` / `procedure:`, tipos `number` y `text`, E/S, flujo, etc.).

## Requisitos

- ⚡ [uv](https://docs.astral.sh/uv/)
- 🐍 Python **3.13** (el repo incluye `.python-version` para `uv sync`)

## Instalación

```bash
git clone git@github.com:cavazquez/ldpltopy.git
cd ldpltopy
uv sync --group dev
```

## Uso con uv

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

### Chequeos locales (paridad con CI)

```bash
./scripts/check-ci.sh
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

## Benchmarks (pytest-benchmark)

Incluidos en `tests/test_benchmarks.py` (tokenizar líneas, parsear, transpilar y ejecutar el Python generado en un caso simple):

```bash
uv run pytest tests/test_benchmarks.py --benchmark-only
```

En CI los benchmarks se desactivan (`--benchmark-disable`) para tiempos estables.

## Licencia

Este proyecto se distribuye bajo la **GNU General Public License v3.0** (SPDX: `GPL-3.0-only`). El texto completo está en el archivo [`LICENSE`](LICENSE).
