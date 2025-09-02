#!/bin/bash

# Miniconda and rnable environment setup script
# This script installs miniconda, creates the rnable environment with required packages,
# and configures automatic activation

set -e

echo "Starting miniconda and rnable environment setup..."


detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unsupported"
        exit 1
    fi
}


OS=$(detect_os)
echo "Detected OS: $OS"


if [[ "$OS" == "linux" ]]; then
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
elif [[ "$OS" == "macos" ]]; then
    if [[ $(uname -m) == "arm64" ]]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
    else
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
    fi
fi


MINICONDA_DIR="$HOME/miniconda3"


if [[ -d "$MINICONDA_DIR" ]]; then
    echo "Miniconda already installed at $MINICONDA_DIR"
else
    echo "Installing miniconda..."

    wget -O /tmp/miniconda.sh "$MINICONDA_URL"
    
    bash /tmp/miniconda.sh -b -p "$MINICONDA_DIR"
    
    rm /tmp/miniconda.sh
    
    echo "Miniconda installed successfully"
fi

echo "Initializing conda..."
source "$MINICONDA_DIR/bin/activate"
conda init bash

source ~/.bashrc 2>/dev/null || source ~/.bash_profile 2>/dev/null || true

echo "Updating conda..."
conda update -n base -c defaults conda -y


echo "Creating rnable environment with required packages..."
conda create -n rnable -c conda-forge -y \
    python=3.10 \
    r-base \
    dash \
    plotly \
    pandas \
    scikit-learn \
    matplotlib \
    rpy2 \
    libstdcxx-ng


echo "Activating rnable environment..."
source "$MINICONDA_DIR/bin/activate" rnable

echo "Installing R packages (BiocManager and DESeq2)..."
Rscript -e "
# Install BiocManager if not already installed
if (!requireNamespace('BiocManager', quietly = TRUE)) {
    install.packages('BiocManager', repos='https://cran.r-project.org/')
}

# Load BiocManager
library(BiocManager)

# Install DESeq2
BiocManager::install('DESeq2', ask = FALSE, update = FALSE)

# Verify installations
cat('Checking installed packages...\n')
if (requireNamespace('BiocManager', quietly = TRUE)) {
    cat('✓ BiocManager installed successfully\n')
} else {
    cat('✗ BiocManager installation failed\n')
}

if (requireNamespace('DESeq2', quietly = TRUE)) {
    cat('✓ DESeq2 installed successfully\n')
} else {
    cat('✗ DESeq2 installation failed\n')
}
"

echo "Configuring automatic activation of rnable environment..."


if [[ -f ~/.bashrc ]]; then
    cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
fi

ACTIVATION_LINE="conda activate rnable"


if ! grep -q "$ACTIVATION_LINE" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Auto-activate rnable environment" >> ~/.bashrc
    echo "$ACTIVATION_LINE" >> ~/.bashrc
    echo "Added automatic activation to ~/.bashrc"
else
    echo "Automatic activation already configured in ~/.bashrc"
fi


if [[ "$OS" == "macos" ]]; then
    if [[ -f ~/.bash_profile ]]; then
        cp ~/.bash_profile ~/.bash_profile.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    if ! grep -q "$ACTIVATION_LINE" ~/.bash_profile 2>/dev/null; then
        echo "" >> ~/.bash_profile
        echo "# Auto-activate rnable environment" >> ~/.bash_profile
        echo "$ACTIVATION_LINE" >> ~/.bash_profile
        echo "Added automatic activation to ~/.bash_profile"
    fi
fi

echo ""
echo "============================================================"
echo "Setup completed successfully!"
echo "============================================================"
echo ""
echo "Summary of what was installed:"
echo "• Miniconda3 at: $MINICONDA_DIR"
echo "• Environment: rnable"
echo "• Python packages: dash, plotly, pandas, scikit-learn, matplotlib, rpy2"
echo "• R packages: BiocManager, DESeq2"
echo "• System packages: r-base, libstdcxx-ng"
echo ""
echo "The 'rnable' environment will be automatically activated in new terminal sessions."
echo ""
echo "To manually activate the environment: conda activate rnable"
echo "To deactivate: conda deactivate"
echo ""
echo "Please restart your terminal or run: source ~/.bashrc"
echo "============================================================"