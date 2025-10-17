#!/bin/bash

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "================================================================================"
echo "⏱️  TESTE DE PERFORMANCE - AI AGENTS"
echo "================================================================================"
echo ""
echo "🕐 Início: $(date +%H:%M:%S)"
echo ""

# Verificar .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
    exit 1
fi

# Carregar .env
source .env

# Verificar credenciais
if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo -e "${RED}❌ DATABRICKS_HOST ou DATABRICKS_TOKEN não configurados no .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Host: ${DATABRICKS_HOST:0:50}...${NC}"
echo -e "${GREEN}✅ Token configurado${NC}"
echo ""

# Verificar arquivos
TF_COUNT=$(ls -1 databricks_tf_files/*.tf 2>/dev/null | wc -l | xargs)
UCX_COUNT=$(ls -1 ucx_export/*.xlsx 2>/dev/null | wc -l | xargs)

echo -e "${GREEN}✅ Arquivos Terraform: $TF_COUNT${NC}"
echo -e "${GREEN}✅ Arquivos UCX: $UCX_COUNT${NC}"
echo ""

# Limpar outputs anteriores
echo "🗑️  Limpando reports anteriores..."
rm -f output_summary_agent/*.md 2>/dev/null || true
echo ""

# Configurar agentes (TODOS os 4)
export SELECTED_AGENTS="terraform_reader,databricks_specialist,ucx_analyst,report_generator"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 AGENTES SELECIONADOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Terraform Analysis Expert"
echo "2. Databricks Optimization Specialist"
echo "3. UCX Migration Analyst"
echo "4. Technical Documentation Specialist (Report Generator)"
echo ""
echo "🚀 Iniciando análise..."
echo "⏳ Aguarde (pode levar 5-15 minutos)..."
echo ""

# Marcar tempo de início
START_TIME=$(date +%s)

# Executar agentes
cd databricks_summary_agent
uv run python src/terraform_file_summary_agent/main.py run
EXIT_CODE=$?
cd ..

# Calcular tempo
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

echo ""
echo "================================================================================"
echo "📊 RESULTADO FINAL"
echo "================================================================================"
echo ""

# Contar reports
REPORT_COUNT=$(ls -1 output_summary_agent/*.md 2>/dev/null | wc -l | xargs)

if [ $EXIT_CODE -eq 0 ] && [ $REPORT_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ SUCESSO!${NC}"
else
    echo -e "${RED}⚠️  PROBLEMA (exit code: $EXIT_CODE)${NC}"
fi

echo ""
echo -e "${BLUE}📊 Reports gerados: $REPORT_COUNT${NC}"

if [ $REPORT_COUNT -gt 0 ]; then
    for file in output_summary_agent/*.md; do
        if [ -f "$file" ]; then
            SIZE=$(du -h "$file" | cut -f1)
            BASENAME=$(basename "$file")
            echo -e "   ${GREEN}✓${NC} $BASENAME ($SIZE)"
        fi
    done
fi

echo ""
echo -e "${BLUE}⏱️  Tempo total: ${MINUTES}m ${SECONDS}s${NC}"
echo ""
echo "🕐 Fim: $(date +%H:%M:%S)"
echo "================================================================================"
echo ""

# Sugestão para README
if [ $EXIT_CODE -eq 0 ] && [ $REPORT_COUNT -gt 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 SUGESTÃO PARA README:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "- **AI Agents Analysis**: ~${MINUTES} minutos ($REPORT_COUNT reports)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

exit $EXIT_CODE

