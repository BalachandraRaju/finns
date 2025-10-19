#!/bin/bash

# Dhan API Setup Script
# This script guides you through setting up Dhan API integration

echo ""
echo "======================================================================"
echo "  🚀 DHAN API SETUP WIZARD"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if .env file exists
echo "Step 1: Checking environment configuration..."
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create a .env file first."
    exit 1
fi
echo -e "${GREEN}✅ .env file found${NC}"
echo ""

# Step 2: Check if Python is installed
echo "Step 2: Checking Python installation..."
if ! command -v python &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python not found!${NC}"
        echo "Please install Python 3.7 or higher."
        exit 1
    else
        PYTHON_CMD=python3
    fi
else
    PYTHON_CMD=python
fi
echo -e "${GREEN}✅ Python found: $($PYTHON_CMD --version)${NC}"
echo ""

# Step 3: Install dependencies
echo "Step 3: Installing required dependencies..."
$PYTHON_CMD -m pip install requests python-dotenv logzero > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Some dependencies may already be installed${NC}"
fi
echo ""

# Step 4: Guide user to get access token
echo "======================================================================"
echo "  📝 STEP 4: GET YOUR DHAN ACCESS TOKEN"
echo "======================================================================"
echo ""
echo "Please follow these steps to get your Dhan access token:"
echo ""
echo "  1. Open your browser and go to: https://web.dhan.co"
echo "  2. Login with your Dhan credentials"
echo "  3. Click on your profile icon (top right)"
echo "  4. Select 'Access DhanHQ APIs'"
echo "  5. Click on 'Generate Access Token'"
echo "  6. Copy the generated token"
echo ""
echo -e "${YELLOW}⚠️  Note: Token is valid for 24 hours only${NC}"
echo ""
read -p "Press Enter after you have copied your access token..."
echo ""

# Step 5: Update .env file
echo "Step 5: Updating .env file..."
echo ""
read -p "Paste your Dhan access token here: " ACCESS_TOKEN
echo ""

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}❌ No token provided!${NC}"
    exit 1
fi

# Update .env file
if grep -q "DHAN_ACCESS_TOKEN=" .env; then
    # Replace existing token
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/DHAN_ACCESS_TOKEN=.*/DHAN_ACCESS_TOKEN=$ACCESS_TOKEN/" .env
    else
        # Linux
        sed -i "s/DHAN_ACCESS_TOKEN=.*/DHAN_ACCESS_TOKEN=$ACCESS_TOKEN/" .env
    fi
    echo -e "${GREEN}✅ Access token updated in .env file${NC}"
else
    echo "DHAN_ACCESS_TOKEN=$ACCESS_TOKEN" >> .env
    echo -e "${GREEN}✅ Access token added to .env file${NC}"
fi
echo ""

# Step 6: Test authentication
echo "======================================================================"
echo "  🧪 STEP 6: TESTING AUTHENTICATION"
echo "======================================================================"
echo ""
$PYTHON_CMD dhan_auth_helper.py
AUTH_RESULT=$?
echo ""

if [ $AUTH_RESULT -ne 0 ]; then
    echo -e "${RED}❌ Authentication test failed!${NC}"
    echo "Please check your access token and try again."
    exit 1
fi

# Step 7: Download instruments
echo "======================================================================"
echo "  📥 STEP 7: DOWNLOADING INSTRUMENT LIST"
echo "======================================================================"
echo ""
$PYTHON_CMD data-fetch/dhan_instruments.py
echo ""

# Step 8: Run comprehensive tests
echo "======================================================================"
echo "  🧪 STEP 8: RUNNING COMPREHENSIVE TESTS"
echo "======================================================================"
echo ""
read -p "Do you want to run comprehensive tests now? (y/n): " RUN_TESTS
echo ""

if [ "$RUN_TESTS" = "y" ] || [ "$RUN_TESTS" = "Y" ]; then
    $PYTHON_CMD test_dhan_integration.py
    echo ""
fi

# Final message
echo "======================================================================"
echo "  🎉 SETUP COMPLETE!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Review the test results above"
echo "  2. Read DHAN_MIGRATION_GUIDE.md for detailed documentation"
echo "  3. Test LTP fetching: python data-fetch/dhan_ltp_client.py"
echo "  4. Integrate with your existing system"
echo ""
echo "Important reminders:"
echo ""
echo "  ⚠️  Access token expires in 24 hours"
echo "  ⚠️  Ensure Data API subscription is active"
echo "  ⚠️  Never commit .env file to version control"
echo ""
echo "======================================================================"
echo ""

