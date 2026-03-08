#!/bin/bash
# WayFare MVP Backend - Development Environment Setup Script (Linux/Mac)
# This script automates the setup of the development environment

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="venv"
MODELS_DIR="wayfare/models"
ONNX_MODEL_NAME="bge-small-zh-v1.5.onnx"
ONNX_MODEL_URL="https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/main/onnx/model.onnx"
QDRANT_PORT=6333
QDRANT_CONTAINER_NAME="wayfare-qdrant"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}WayFare MVP Backend Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if Python 3 is installed
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

# Check if Docker is installed
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker is not installed. Qdrant container will not be started."
    print_warning "Please install Docker and run: docker run -p 6333:6333 qdrant/qdrant"
    DOCKER_AVAILABLE=false
else
    print_success "Docker found"
    DOCKER_AVAILABLE=true
fi

# Step 1: Create virtual environment
print_status "Creating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created at $VENV_DIR"
fi

# Step 2: Activate virtual environment and install dependencies
print_status "Installing dependencies..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
    print_success "Dependencies installed from requirements-dev.txt"
else
    print_error "requirements-dev.txt not found!"
    exit 1
fi

# Step 3: Create models directory
print_status "Setting up models directory..."
if [ ! -d "$MODELS_DIR" ]; then
    mkdir -p "$MODELS_DIR"
    print_success "Created directory: $MODELS_DIR"
else
    print_success "Models directory already exists"
fi

# Step 4: Download ONNX model
print_status "Downloading ONNX model..."
ONNX_MODEL_PATH="$MODELS_DIR/$ONNX_MODEL_NAME"

if [ -f "$ONNX_MODEL_PATH" ]; then
    print_warning "ONNX model already exists at $ONNX_MODEL_PATH. Skipping download."
else
    print_status "Downloading BAAI/bge-small-zh-v1.5 ONNX model (~100MB)..."
    
    # Try using curl first, fallback to wget
    if command -v curl &> /dev/null; then
        curl -L "$ONNX_MODEL_URL" -o "$ONNX_MODEL_PATH" --progress-bar
    elif command -v wget &> /dev/null; then
        wget "$ONNX_MODEL_URL" -O "$ONNX_MODEL_PATH" --show-progress
    else
        print_error "Neither curl nor wget found. Please install one of them."
        print_warning "You can manually download the model from:"
        print_warning "$ONNX_MODEL_URL"
        print_warning "And save it to: $ONNX_MODEL_PATH"
        exit 1
    fi
    
    if [ -f "$ONNX_MODEL_PATH" ]; then
        print_success "ONNX model downloaded successfully"
    else
        print_error "Failed to download ONNX model"
        exit 1
    fi
fi

# Step 5: Start Qdrant Docker container
if [ "$DOCKER_AVAILABLE" = true ]; then
    print_status "Starting Qdrant Docker container..."
    
    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${QDRANT_CONTAINER_NAME}$"; then
        # Container exists, check if it's running
        if docker ps --format '{{.Names}}' | grep -q "^${QDRANT_CONTAINER_NAME}$"; then
            print_warning "Qdrant container is already running"
        else
            # Container exists but not running, start it
            print_status "Starting existing Qdrant container..."
            docker start "$QDRANT_CONTAINER_NAME"
            print_success "Qdrant container started"
        fi
    else
        # Container doesn't exist, create and start it
        print_status "Creating and starting Qdrant container..."
        docker run -d \
            --name "$QDRANT_CONTAINER_NAME" \
            -p "$QDRANT_PORT:6333" \
            -v "$(pwd)/.wayfare/qdrant_storage:/qdrant/storage" \
            qdrant/qdrant
        
        if [ $? -eq 0 ]; then
            print_success "Qdrant container started on port $QDRANT_PORT"
        else
            print_error "Failed to start Qdrant container"
            exit 1
        fi
    fi
    
    # Wait for Qdrant to be ready
    print_status "Waiting for Qdrant to be ready..."
    sleep 3
    
    # Check if Qdrant is responding
    if command -v curl &> /dev/null; then
        if curl -s "http://localhost:$QDRANT_PORT/health" > /dev/null 2>&1; then
            print_success "Qdrant is ready and responding"
        else
            print_warning "Qdrant container started but not responding yet. It may need more time to initialize."
        fi
    fi
else
    print_warning "Skipping Qdrant container setup (Docker not available)"
fi

# Step 6: Verify installation
print_status "Verifying installation..."

# Check if verify_dependencies.py exists
if [ -f "verify_dependencies.py" ]; then
    python verify_dependencies.py
    if [ $? -eq 0 ]; then
        print_success "All dependencies verified"
    else
        print_warning "Some dependencies may be missing. Check the output above."
    fi
else
    print_warning "verify_dependencies.py not found. Skipping verification."
fi

# Final summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Activate the virtual environment:"
echo -e "     ${YELLOW}source $VENV_DIR/bin/activate${NC}"
echo ""
echo -e "  2. Set your API key (if using LLM features):"
echo -e "     ${YELLOW}export OPENAI_API_KEY='your-api-key-here'${NC}"
echo ""
echo -e "  3. Run tests:"
echo -e "     ${YELLOW}pytest tests/${NC}"
echo ""
echo -e "  4. Start the backend:"
echo -e "     ${YELLOW}python wayfare/main.py${NC}"
echo ""

if [ "$DOCKER_AVAILABLE" = true ]; then
    echo -e "${BLUE}Qdrant Management:${NC}"
    echo -e "  Stop Qdrant:  ${YELLOW}docker stop $QDRANT_CONTAINER_NAME${NC}"
    echo -e "  Start Qdrant: ${YELLOW}docker start $QDRANT_CONTAINER_NAME${NC}"
    echo -e "  View logs:    ${YELLOW}docker logs $QDRANT_CONTAINER_NAME${NC}"
    echo ""
fi

echo -e "${GREEN}Happy coding! 🚀${NC}"
