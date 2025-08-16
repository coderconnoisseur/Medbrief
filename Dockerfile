## Use micromamba base image for conda-managed binary packages
FROM mambaorg/micromamba:1.4.0

# Set working dir
WORKDIR /app

# Copy environment file and requirements
COPY requirements.txt ./
COPY entrypoint.sh ./

# Install spaCy and scispaCy from conda-forge (binary wheels) to avoid building C extensions
RUN micromamba install -n base -y -c conda-forge \
    python=3.11 \
    spacy=3.7.* \
    scispacy=0.5.* && micromamba clean --all -y

# Upgrade pip and install remaining pip packages inside the micromamba 'base' env
RUN micromamba run -n base -- python -m pip install --upgrade pip setuptools wheel && \
    micromamba run -n base -- pip install --no-deps -r requirements.txt

# Copy app sources
COPY . .

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

# Default PORT env
ENV PORT=8000
ENTRYPOINT ["/app/entrypoint.sh"]