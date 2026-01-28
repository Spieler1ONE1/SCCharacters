# Tests

Este directorio contiene las pruebas automatizadas del proyecto.

## Requisitos

Para ejecutar las pruebas, necesitas instalar las dependencias de desarrollo:

```bash
pip install -r requirements.txt
```

Específicamente, este proyecto usa:
- `pytest`
- `pytest-qt` (para pruebas de interfaz gráfica)
- `flake8` (para estilo de código)

## Ejecutar Tests

Para correr todos los tests:

```bash
pytest
```

Para correr un test específico:

```bash
pytest tests/test_navigation_controller.py
```
