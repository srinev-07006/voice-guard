#!/bin/bash

echo "=========================================="
echo "  VoiceGuard Installation Verification"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counters
passed=0
failed=0

# Function to check file
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((passed++))
    else
        echo -e "${RED}✗${NC} $1 (MISSING)"
        ((failed++))
    fi
}

# Check HTML pages
echo "📄 Checking HTML Pages..."
check_file "index.html"
check_file "dashboard.html"
check_file "analytics.html"
check_file "history.html"
check_file "settings.html"
check_file "about.html"
check_file "setup-guide.html"
echo ""

# Check JavaScript files
echo "📜 Checking JavaScript Files..."
check_file "js/dashboard.js"
check_file "js/analytics.js"
check_file "js/history.js"
check_file "js/settings.js"
echo ""

# Check Python backend
echo "🐍 Checking Python Backend..."
check_file "server.py"
check_file "detector.py"
check_file "requirements.txt"
echo ""

# Check documentation
echo "📚 Checking Documentation..."
check_file "README.md"
check_file "WEB_APP_README.md"
check_file "QUICKSTART.md"
check_file "PROJECT_SUMMARY.md"
check_file "gemchat.pdf"
echo ""

# Check Python installation
echo "🔍 Checking Python Installation..."
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "${GREEN}✓${NC} Python found: $PYTHON_VERSION"
    ((passed++))
else
    echo -e "${RED}✗${NC} Python not found (REQUIRED)"
    ((failed++))
fi
echo ""

# Check if virtual environment exists
echo "🌐 Checking Virtual Environment..."
if [ -d "sih_env" ] || [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment found"
    ((passed++))
else
    echo -e "${YELLOW}⚠${NC} Virtual environment not created yet (run: python -m venv sih_env)"
fi
echo ""

# Summary
echo "=========================================="
echo "  Verification Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$passed${NC}"
echo -e "Failed: ${RED}$failed${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✓ All core files present!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Create virtual environment: python -m venv sih_env"
    echo "2. Activate it: sih_env\Scripts\activate (Windows) or source sih_env/bin/activate (Mac/Linux)"
    echo "3. Install dependencies: pip install -r requirements.txt"
    echo "4. Start server: python -m uvicorn server:app --reload"
    echo "5. Open dashboard.html in your browser"
else
    echo -e "${RED}✗ Some files are missing. Please check the installation.${NC}"
fi

echo ""
echo "=========================================="
