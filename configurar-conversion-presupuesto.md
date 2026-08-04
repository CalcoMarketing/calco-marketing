name: Generar calendario editorial

# Corre el día 25 de cada mes a las 12:00 UTC (09:00 en Montevideo),
# así el calendario del mes siguiente queda listo con una semana de
# margen para conseguir las fotos del taller.
#
# También se puede correr a mano desde la pestaña Actions del repositorio,
# con el botón "Run workflow", eligiendo mes y proveedor de IA.

on:
  schedule:
    - cron: '0 12 25 * *'
  workflow_dispatch:
    inputs:
      mes:
        description: 'Mes a generar (AAAA-MM). Vacío = el mes que viene.'
        required: false
        type: string
      proveedor:
        description: 'Proveedor de IA'
        required: false
        default: 'anthropic'
        type: choice
        options:
          - anthropic
          - deepseek

permissions:
  contents: write

jobs:
  generar:
    runs-on: ubuntu-latest

    steps:
      - name: Clonar el repositorio
        uses: actions/checkout@v4

      - name: Instalar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Instalar dependencias
        run: pip install -r requirements.txt

      - name: Generar el calendario
        env:
          # Se pasan las dos claves. El motor usa solo la del proveedor elegido.
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          PROVEEDOR_IA: ${{ inputs.proveedor || 'anthropic' }}
        run: |
          if [ -n "${{ inputs.mes }}" ]; then
            python content_engine.py --mes "${{ inputs.mes }}"
          else
            python content_engine.py
          fi

      - name: Guardar el resultado en el repositorio
        run: |
          git config user.name  "Calco Marketing Bot"
          git config user.email "marketing@calco.uy"
          git add contenido/
          if git diff --staged --quiet; then
            echo "No hay cambios para guardar."
          else
            git commit -m "Calendario editorial generado automáticamente"
            git push
          fi

      - name: Avisar si falló
        if: failure()
        run: |
          echo "La generación del calendario falló."
          echo "Revisar:"
          echo "1) que el secreto del proveedor elegido exista y sea válido"
          echo "   (ANTHROPIC_API_KEY o DEEPSEEK_API_KEY)"
          echo "2) que la cuenta del proveedor tenga saldo"
          echo "3) el archivo contenido/_fallo_*.txt si se generó"
