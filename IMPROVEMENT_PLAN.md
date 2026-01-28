# Plan de Mejoras Globales (SCCharacters)

Este documento describe el plan para implementar las mejoras sugeridas de arquitectura, calidad de código y automatización.

## 1. Integración Continua (CI/CD)
**Objetivo**: Automatizar pruebas y verficación de estilo en cada cambio.
- [ ] Crear flujo de trabajo en `.github/workflows/main.yml`.
- [ ] Configurar linter (`flake8`) y runner de tests (`pytest`).

## 2. Infraestructura de Estilo y Pruebas
**Objetivo**: Asegurar consistencia y prevenir errores.
- [ ] Actualizar `requirements.txt` con dependencias de desarrollo (`pytest`, `pytest-qt`, `flake8`, `mypy`).
- [ ] Crear configuración de `pytest.ini`.
- [ ] Crear tests unitarios básicos para servicios críticos (`ConfigurationManager`, `CharacterService`).

## 3. Refactorización de Arquitectura (MainWindow)
**Objetivo**: Reducir la complejidad de `MainWindow` delegando lógica a controladores.
- [ ] Crear paquete `src/ui/controllers`.
- [ ] Implementar `NavigationController` (Manejo de tabs y vistas).
- [ ] Implementar `GameDialogController` (Manejo de diálogos de instalación/juego).
- [ ] Refactorizar `MainWindow` para usar estos controladores en lugar de método directos.

## 4. Mejoras de UI/UX
- [ ] Revisar y mejorar feedback asíncrono (asegurar que no haya operaciones bloqueantes en el hilo principal).
- [ ] Verificar navegación por teclado básica.

---
**Estado**: En Progreso
